#!/usr/bin/env python3

import os
import sys
import time
import yaml
import psutil
import threading
import asyncio
import subprocess
from typing import Optional, Dict, Any, List
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.style import Style
from rich.theme import Theme
from rich.syntax import Syntax
from datetime import datetime
from animation_manager import AnimationManager
from system_monitor import SystemMonitor
from theme_manager import ThemeManager
from text_manager import TextManager
from performance_manager import PerformanceManager
from tool_integration import ToolIntegration
from security_manager import SecurityManager, SecurityError
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout as PTLayout

class TerminalDecorator:
    def __init__(self, config_path: str = "config.yaml"):
        # Initialize security manager first
        self.security_manager = SecurityManager()
        
        # Load config securely
        self.load_config(config_path)
        
        # Initialize core components
        self.console = Console()
        self.performance_manager = PerformanceManager(self.config)
        self.tool_integration = ToolIntegration()
        
        # Lazy load other components
        self._init_core_features()
        self.running = True
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    @property
    def shell_config_path(self) -> Path:
        """Get the current shell's config file path"""
        shell = os.environ.get('SHELL', '').split('/')[-1]
        if shell == 'zsh':
            return Path.home() / '.zshrc'
        elif shell == 'bash':
            return Path.home() / '.bashrc'
        else:
            return Path.home() / f'.{shell}rc'

    def load_config(self, config_path: str):
        """Load configuration file securely"""
        try:
            config_path = Path(config_path)
            if not self.security_manager.sandbox_manager.is_path_allowed(config_path):
                raise SecurityError(f"Access denied to config file: {config_path}")
            
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        
        except Exception as e:
            self.console.print(f"[red]Error loading config: {e}[/]")
            self.config = {
                'performance': {
                    'fps': 60,
                    'max_concurrent': 5,
                    'hardware_acceleration': True,
                    'smooth_transitions': True,
                    'buffer_size': 1024,
                    'vsync': True
                }
            }

    def backup_shell_config(self) -> bool:
        """Create a backup of the shell configuration file"""
        try:
            config_path = self.shell_config_path
            if config_path.exists():
                backup_path = self.security_manager.backup_manager.create_backup(config_path)
                if backup_path:
                    self.console.print(f"[green]Created backup of {config_path}[/]")
                    return True
            return False
        except Exception as e:
            self.console.print(f"[red]Backup failed: {e}[/]")
            return False

    def restore_shell_config(self, backup_path: Optional[Path] = None) -> bool:
        """Restore shell configuration from backup"""
        try:
            config_path = self.shell_config_path
            success = self.security_manager.backup_manager.restore_backup(config_path, backup_path)
            if success:
                self.console.print(f"[green]Restored {config_path} from backup[/]")
            else:
                self.console.print(f"[red]Failed to restore {config_path}[/]")
            return success
        except Exception as e:
            self.console.print(f"[red]Restore failed: {e}[/]")
            return False

    def create_security_panel(self) -> Panel:
        """Create a panel showing security information"""
        table = Table(show_header=False, box=None)
        
        # Show backup status
        backups = self.security_manager.backup_manager.list_backups(self.shell_config_path)
        backup_count = len(backups)
        latest_backup = backups[0]['timestamp'] if backups else "None"
        
        table.add_row(
            Text("Shell Config:", style="cyan"),
            Text(str(self.shell_config_path), style="blue")
        )
        table.add_row(
            Text("Backups:", style="cyan"),
            Text(str(backup_count), style="green")
        )
        table.add_row(
            Text("Latest Backup:", style="cyan"),
            Text(latest_backup, style="yellow")
        )
        
        # Show file integrity status
        integrity_status = self.security_manager.verify_file_integrity(self.shell_config_path)
        table.add_row(
            Text("File Integrity:", style="cyan"),
            Text("✓ Valid" if integrity_status else "✗ Modified", style="green" if integrity_status else "red")
        )
        
        return Panel(
            table,
            title="Security Status",
            border_style="red"
        )

    async def handle_command(self, command: str) -> None:
        """Execute commands securely"""
        try:
            # Special handling for fzf integration
            if command.strip() == "fzf" and self.tool_integration.fzf_support:
                try:
                    result = await self.security_manager.secure_command_execution("fzf")
                    if result.returncode == 0:
                        self.console.print(f"Selected: {result.stdout.strip()}")
                    return
                except Exception as e:
                    self.console.print(f"[red]Error running fzf: {e}[/]")
                    return

            # Regular command handling with animations and security
            if (not self.performance_manager.feature_manager.is_feature_loaded('animations') and 
                self.performance_manager.get_average_metrics().cpu_usage < 60):
                self.load_feature('animations')
            
            try:
                if self.performance_manager.feature_manager.is_feature_loaded('animations'):
                    self.animation_manager.handle_event("command_start", command=command)
                else:
                    self.console.print(f"Executing: {command}")
                
                # Execute command in sandbox
                result = await self.security_manager.secure_command_execution(command)
                
                if result.returncode == 0:
                    if self.performance_manager.feature_manager.is_feature_loaded('animations'):
                        self.animation_manager.handle_event("command_success")
                    self.console.print("[green]Command completed successfully[/]")
                    if result.stdout:
                        print(result.stdout)
                else:
                    if self.performance_manager.feature_manager.is_feature_loaded('animations'):
                        self.animation_manager.handle_event("command_error")
                    self.console.print("[red]Command failed[/]")
                    if result.stderr:
                        print(result.stderr)
            
            except SecurityError as e:
                self.console.print(f"[red]Security error: {e}[/]")
            except Exception as e:
                self.console.print(f"[red]Error executing command: {e}[/]")

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/]")

    def _update_loop(self) -> None:
        with Live(self.layout, refresh_per_second=self.config['performance']['fps']) as live:
            while self.running:
                try:
                    # Optimize performance before updating
                    self.performance_manager.optimize_performance()
                    
                    # Update layout components based on loaded features
                    self.layout["header"].update(self.create_header())
                    
                    # Main area with git info and system info
                    if self.performance_manager.feature_manager.is_feature_loaded('system_monitor'):
                        self.layout["main"].split(
                            self.create_git_panel(),
                            self.create_system_info()
                        )
                    
                    # Sidebar with security, tasks and tool status
                    self.layout["sidebar"].split(
                        self.create_security_panel(),
                        self.create_task_panel(),
                        self.create_tool_status_panel(),
                        self.create_performance_panel()
                    )
                    
                    # Update footer if text effects are loaded
                    if self.performance_manager.feature_manager.is_feature_loaded('text_effects'):
                        self.layout["footer"].update(self.create_footer())
                    
                    # Apply theme transitions if animations are enabled and system resources permit
                    if (self.performance_manager.feature_manager.is_feature_loaded('animations') and 
                        self.performance_manager.get_average_metrics().cpu_usage < 70):
                        self.theme_manager.update()
                    
                    # Adaptive refresh rate based on system load
                    metrics = self.performance_manager.get_average_metrics()
                    sleep_time = max(0.25, 1 / self.config['performance']['fps'])
                    if metrics.cpu_usage > 80:
                        sleep_time *= 2  # Reduce refresh rate under high load
                    
                    time.sleep(sleep_time)
                
                except Exception as e:
                    self.console.print(f"[red]Update error: {e}[/]", file=sys.stderr)
                    if self.ensure_accessibility():
                        self.accessibility.announce_error(str(e))

    def stop(self) -> None:
        """Safely stop the terminal decorator"""
        try:
            self.running = False
            self.performance_manager.cleanup()
            self.tool_integration.cleanup()
            if self.update_thread.is_alive():
                self.update_thread.join()
        except Exception as e:
            self.console.print(f"[red]Error during shutdown: {e}[/]")
        finally:
            # Always try to backup config on exit
            self.backup_shell_config()

    def __del__(self):
        self.stop()

async def main():
    config = {
        'performance': {
            'fps': 60,
            'max_concurrent': 5,
            'hardware_acceleration': True,
            'smooth_transitions': True,
            'buffer_size': 1024,
            'vsync': True
        }
    }
    
    decorator = TerminalDecorator(config)
    
    try:
        # Create initial backup
        decorator.backup_shell_config()
        
        # Example usage with security features
        await decorator.handle_command("ls -la")
        time.sleep(1)
        
        await decorator.handle_command("git status")
        time.sleep(1)
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        decorator.stop()
        print("\nTerminal decorator stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        decorator.stop()

if __name__ == "__main__":
    asyncio.run(main()) 