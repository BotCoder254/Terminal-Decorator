#!/usr/bin/env python3

import os
import sys
import pwd
import grp
import stat
import shutil
import hashlib
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import json
import asyncio
from dataclasses import dataclass
from functools import wraps

@dataclass
class SecurityContext:
    user: str
    group: str
    permissions: int
    environment: Dict[str, str]
    allowed_paths: Set[Path]
    restricted_commands: Set[str]

class BackupManager:
    def __init__(self, backup_dir: Optional[str] = None):
        self.backup_dir = Path(backup_dir) if backup_dir else Path.home() / '.terminal_decorator' / 'backups'
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._setup_backup_structure()

    def _setup_backup_structure(self):
        """Create necessary backup directories with proper permissions"""
        # Create subdirectories
        (self.backup_dir / 'shell_configs').mkdir(exist_ok=True)
        (self.backup_dir / 'system_configs').mkdir(exist_ok=True)
        (self.backup_dir / 'logs').mkdir(exist_ok=True)

        # Secure the backup directory
        self._secure_directory(self.backup_dir)

    def _secure_directory(self, path: Path):
        """Apply secure permissions to directory"""
        # Set directory permissions to 700 (rwx------)
        path.chmod(0o700)
        
        # Set owner to current user
        os.chown(path, os.getuid(), os.getgid())

    def create_backup(self, file_path: Path, category: str = 'shell_configs') -> Optional[Path]:
        """Create a backup of a file with timestamp"""
        try:
            if not file_path.exists():
                logging.warning(f"File not found: {file_path}")
                return None

            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"{file_path.name}_{timestamp}.bak"
            backup_path = self.backup_dir / category / backup_name

            # Create backup with original permissions
            shutil.copy2(file_path, backup_path)
            
            # Store metadata
            metadata = {
                'original_path': str(file_path),
                'timestamp': timestamp,
                'hash': self._calculate_file_hash(file_path),
                'permissions': oct(file_path.stat().st_mode)[-3:],
                'owner': pwd.getpwuid(file_path.stat().st_uid).pw_name
            }
            
            metadata_path = backup_path.with_suffix('.meta')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            logging.info(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            logging.error(f"Backup failed for {file_path}: {e}")
            return None

    def restore_backup(self, original_path: Path, backup_path: Optional[Path] = None) -> bool:
        """Restore a file from backup"""
        try:
            if backup_path is None:
                # Find the most recent backup
                category = 'shell_configs' if 'rc' in original_path.name else 'system_configs'
                backups = list((self.backup_dir / category).glob(f"{original_path.name}_*.bak"))
                if not backups:
                    logging.error(f"No backups found for {original_path}")
                    return False
                backup_path = max(backups, key=lambda p: p.stat().st_mtime)

            if not backup_path.exists():
                logging.error(f"Backup not found: {backup_path}")
                return False

            # Verify backup integrity
            metadata_path = backup_path.with_suffix('.meta')
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                current_hash = self._calculate_file_hash(backup_path)
                if current_hash != metadata['hash']:
                    logging.error(f"Backup integrity check failed for {backup_path}")
                    return False

            # Create a temporary copy first
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                shutil.copy2(backup_path, tmp.name)
                
                # Verify the temporary copy
                if self._calculate_file_hash(Path(tmp.name)) != self._calculate_file_hash(backup_path):
                    os.unlink(tmp.name)
                    logging.error("Temporary copy verification failed")
                    return False
                
                # Restore permissions and ownership
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    os.chmod(tmp.name, int(metadata['permissions'], 8))
                    if os.getuid() == 0:  # Only try to change owner if root
                        uid = pwd.getpwnam(metadata['owner']).pw_uid
                        os.chown(tmp.name, uid, os.getgid())

                # Atomic replace
                shutil.move(tmp.name, original_path)

            logging.info(f"Successfully restored {original_path} from backup")
            return True

        except Exception as e:
            logging.error(f"Restore failed for {original_path}: {e}")
            return False

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def list_backups(self, original_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """List available backups with metadata"""
        backups = []
        
        def process_backup_dir(directory: Path):
            for backup_file in directory.glob("*.bak"):
                metadata_path = backup_file.with_suffix('.meta')
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    metadata['backup_path'] = str(backup_file)
                    metadata['size'] = backup_file.stat().st_size
                    if original_path is None or Path(metadata['original_path']) == original_path:
                        backups.append(metadata)

        for category in ['shell_configs', 'system_configs']:
            process_backup_dir(self.backup_dir / category)
        
        return sorted(backups, key=lambda x: x['timestamp'], reverse=True)

class SandboxManager:
    def __init__(self):
        self.context = self._create_security_context()

    def _create_security_context(self) -> SecurityContext:
        """Create a security context for sandboxed execution"""
        return SecurityContext(
            user=pwd.getpwuid(os.getuid()).pw_name,
            group=grp.getgrgid(os.getgid()).gr_name,
            permissions=0o700,
            environment=self._get_safe_environment(),
            allowed_paths=self._get_allowed_paths(),
            restricted_commands=self._get_restricted_commands()
        )

    def _get_safe_environment(self) -> Dict[str, str]:
        """Create a sanitized environment dictionary"""
        safe_env = {}
        allowed_vars = {
            'HOME', 'USER', 'SHELL', 'PATH', 'TERM', 'LANG',
            'LC_ALL', 'EDITOR', 'VISUAL', 'DISPLAY'
        }
        
        for var in allowed_vars:
            if var in os.environ:
                safe_env[var] = os.environ[var]

        # Ensure PATH is restricted to safe directories
        safe_paths = [
            '/usr/local/bin',
            '/usr/bin',
            '/bin',
            '/usr/local/sbin',
            '/usr/sbin',
            '/sbin'
        ]
        safe_env['PATH'] = ':'.join(p for p in safe_paths if os.path.exists(p))
        
        return safe_env

    def _get_allowed_paths(self) -> Set[Path]:
        """Get set of allowed paths for file operations"""
        home = Path.home()
        return {
            home,
            home / '.terminal_decorator',
            home / '.config',
            home / '.local/share',
            Path('/tmp'),
            Path('/var/tmp')
        }

    def _get_restricted_commands(self) -> Set[str]:
        """Get set of restricted commands"""
        return {
            'rm -rf /',
            'chmod -R 777',
            'dd if=/dev/zero',
            ':(){ :|:& };:',  # Fork bomb
            '> /dev/sda',
            'mkfs',
            'fdisk',
            'mkswap',
            'sudo rm',
            'sudo chmod',
            'sudo chown'
        }

    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is allowed for file operations"""
        try:
            path = path.resolve()
            return any(
                str(path).startswith(str(allowed_path))
                for allowed_path in self.context.allowed_paths
            )
        except Exception:
            return False

    def is_command_safe(self, command: str) -> bool:
        """Check if a command is safe to execute"""
        command = command.strip().lower()
        return not any(
            restricted in command
            for restricted in self.context.restricted_commands
        )

    async def run_sandboxed(self, command: str) -> subprocess.CompletedProcess:
        """Run a command in a sandboxed environment"""
        if not self.is_command_safe(command):
            raise SecurityError(f"Command not allowed: {command}")

        # Create a temporary directory for the sandbox
        with tempfile.TemporaryDirectory() as sandbox_dir:
            # Set up sandbox environment
            env = self.context.environment.copy()
            env['SANDBOX_DIR'] = sandbox_dir

            # Run the command with restricted privileges
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=sandbox_dir
            )
            
            stdout, stderr = await process.communicate()
            
            return subprocess.CompletedProcess(
                args=command,
                returncode=process.returncode,
                stdout=stdout.decode(),
                stderr=stderr.decode()
            )

class SecurityManager:
    def __init__(self):
        self.backup_manager = BackupManager()
        self.sandbox_manager = SandboxManager()
        self._setup_logging()

    def _setup_logging(self):
        """Set up security-related logging"""
        log_file = Path.home() / '.terminal_decorator' / 'logs' / 'security.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def secure_file_operation(self, func):
        """Decorator for secure file operations"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Check file paths
                for arg in args:
                    if isinstance(arg, (str, Path)):
                        path = Path(arg)
                        if not self.sandbox_manager.is_path_allowed(path):
                            raise SecurityError(f"Access denied to path: {path}")
                
                # Create backup if modifying files
                if func.__name__ in ['write_file', 'modify_file', 'delete_file']:
                    self.backup_manager.create_backup(Path(args[0]))
                
                return func(*args, **kwargs)
            
            except Exception as e:
                logging.error(f"Security error in {func.__name__}: {e}")
                raise
        
        return wrapper

    async def secure_command_execution(self, command: str) -> subprocess.CompletedProcess:
        """Execute a command securely"""
        try:
            logging.info(f"Executing command: {command}")
            return await self.sandbox_manager.run_sandboxed(command)
        
        except Exception as e:
            logging.error(f"Command execution failed: {e}")
            raise

    def verify_file_integrity(self, file_path: Path) -> bool:
        """Verify file integrity against its backup"""
        try:
            backups = self.backup_manager.list_backups(file_path)
            if not backups:
                return True  # No backup to compare against
            
            latest_backup = Path(backups[0]['backup_path'])
            current_hash = self.backup_manager._calculate_file_hash(file_path)
            backup_hash = backups[0]['hash']
            
            return current_hash == backup_hash
        
        except Exception as e:
            logging.error(f"Integrity check failed for {file_path}: {e}")
            return False

class SecurityError(Exception):
    """Custom exception for security-related errors"""
    pass

# Example usage
if __name__ == "__main__":
    security_manager = SecurityManager()
    
    try:
        # Example: Backup shell config
        shell_config = Path.home() / '.zshrc'
        if shell_config.exists():
            security_manager.backup_manager.create_backup(shell_config)
        
        # Example: List backups
        backups = security_manager.backup_manager.list_backups()
        print("\nAvailable backups:")
        print(json.dumps(backups, indent=2))
        
        # Example: Secure command execution
        async def run_example():
            result = await security_manager.secure_command_execution('ls -la')
            print("\nCommand output:")
            print(result.stdout)
        
        asyncio.run(run_example())
    
    except SecurityError as e:
        print(f"Security error: {e}")
    except Exception as e:
        print(f"Error: {e}") 