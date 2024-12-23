#!/usr/bin/env python3

import os
import sys
import subprocess
import threading
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import json
from pathlib import Path
import asyncio
from functools import lru_cache

@dataclass
class GitStatus:
    branch: str
    is_clean: bool
    staged: int
    unstaged: int
    untracked: int
    commits_ahead: int
    commits_behind: int
    conflicts: List[str]
    last_commit: str
    last_commit_time: datetime

@dataclass
class TaskStatus:
    name: str
    schedule: str
    last_run: datetime
    next_run: datetime
    status: str
    pid: Optional[int]

class GitIntegration:
    def __init__(self):
        self.repo_path = None
        self._find_git_repo()
        self.status_cache_time = 2  # Cache git status for 2 seconds
        self._last_status: Optional[Tuple[float, GitStatus]] = None

    def _find_git_repo(self):
        """Find the git repository from current directory upwards"""
        current = Path.cwd()
        while current != current.parent:
            if (current / '.git').is_dir():
                self.repo_path = current
                break
            current = current.parent

    def _run_git_command(self, *args) -> str:
        """Run a git command and return its output"""
        if not self.repo_path:
            return ""
        try:
            result = subprocess.run(
                ['git'] + list(args),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=2
            )
            return result.stdout.strip()
        except (subprocess.TimeoutError, subprocess.SubprocessError):
            return ""

    @lru_cache(maxsize=1)
    def get_status(self) -> Optional[GitStatus]:
        """Get current git repository status with caching"""
        if not self.repo_path:
            return None

        current_time = time.time()
        if (self._last_status and 
            current_time - self._last_status[0] < self.status_cache_time):
            return self._last_status[1]

        try:
            # Get branch info
            branch = self._run_git_command('symbolic-ref', '--short', 'HEAD')
            if not branch:
                branch = self._run_git_command('rev-parse', '--short', 'HEAD')

            # Get status counts
            status = self._run_git_command('status', '--porcelain')
            staged = len([line for line in status.split('\n') if line.startswith('A ')])
            unstaged = len([line for line in status.split('\n') if line[1] == 'M'])
            untracked = len([line for line in status.split('\n') if line.startswith('??')])

            # Get ahead/behind counts
            ahead_behind = self._run_git_command('rev-list', '--count', '--left-right', '@{upstream}...HEAD')
            behind, ahead = map(int, ahead_behind.split()) if ahead_behind else (0, 0)

            # Get conflicts
            conflicts = [
                line.split()[1] for line in status.split('\n')
                if line.startswith('UU')
            ]

            # Get last commit info
            last_commit = self._run_git_command('log', '-1', '--pretty=format:%h %s')
            last_commit_time_str = self._run_git_command('log', '-1', '--pretty=format:%ci')
            last_commit_time = datetime.strptime(last_commit_time_str, '%Y-%m-%d %H:%M:%S %z')

            status = GitStatus(
                branch=branch,
                is_clean=not (staged + unstaged + untracked),
                staged=staged,
                unstaged=unstaged,
                untracked=untracked,
                commits_ahead=ahead,
                commits_behind=behind,
                conflicts=conflicts,
                last_commit=last_commit,
                last_commit_time=last_commit_time
            )

            self._last_status = (current_time, status)
            return status

        except Exception as e:
            logging.error(f"Error getting git status: {e}")
            return None

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, TaskStatus] = {}
        self._load_tasks()
        self.monitor_thread = threading.Thread(target=self._monitor_tasks, daemon=True)
        self.monitor_thread.start()

    def _load_tasks(self):
        """Load tasks from cron and systemd"""
        self._load_cron_tasks()
        self._load_systemd_tasks()

    def _load_cron_tasks(self):
        """Load user's crontab entries"""
        try:
            crontab = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if crontab.returncode == 0:
                for line in crontab.stdout.splitlines():
                    if line.strip() and not line.startswith('#'):
                        schedule, *command = line.split(None, 5)
                        name = ' '.join(command)
                        self.tasks[name] = TaskStatus(
                            name=name,
                            schedule=schedule,
                            last_run=self._get_last_run(name),
                            next_run=self._calculate_next_run(schedule),
                            status="scheduled",
                            pid=None
                        )
        except Exception as e:
            logging.error(f"Error loading crontab: {e}")

    def _load_systemd_tasks(self):
        """Load user's systemd timers"""
        try:
            timers = subprocess.run(
                ['systemctl', '--user', 'list-timers', '--all'],
                capture_output=True,
                text=True
            )
            if timers.returncode == 0:
                for line in timers.stdout.splitlines()[1:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 5:
                            name = parts[4]
                            self.tasks[name] = TaskStatus(
                                name=name,
                                schedule=parts[2],
                                last_run=datetime.strptime(parts[1], '%Y-%m-%d %H:%M:%S'),
                                next_run=datetime.strptime(parts[0], '%Y-%m-%d %H:%M:%S'),
                                status="active" if "active" in parts else "inactive",
                                pid=self._get_pid(name)
                            )
        except Exception as e:
            logging.error(f"Error loading systemd timers: {e}")

    def _get_last_run(self, task_name: str) -> datetime:
        """Get last run time from system logs"""
        try:
            log = subprocess.run(
                ['journalctl', '--user', '-u', task_name, '-n', '1'],
                capture_output=True,
                text=True
            )
            if log.returncode == 0 and log.stdout:
                match = re.search(r'\w{3} \d{2} \d{2}:\d{2}:\d{2}', log.stdout)
                if match:
                    return datetime.strptime(match.group(), '%b %d %H:%M:%S')
        except Exception:
            pass
        return datetime.min

    def _calculate_next_run(self, schedule: str) -> datetime:
        """Calculate next run time from cron schedule"""
        # Simplified calculation - in practice, use a cron parser library
        return datetime.now()

    def _get_pid(self, service_name: str) -> Optional[int]:
        """Get PID of running systemd service"""
        try:
            result = subprocess.run(
                ['systemctl', '--user', 'show', service_name, '--property=MainPID'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pid = int(result.stdout.split('=')[1])
                return pid if pid > 0 else None
        except Exception:
            pass
        return None

    def _monitor_tasks(self):
        """Monitor task status changes"""
        while True:
            for name, task in self.tasks.items():
                # Update task status
                if task.pid:
                    try:
                        os.kill(task.pid, 0)  # Check if process is running
                        task.status = "running"
                    except OSError:
                        task.status = "stopped"
                        task.pid = None
            time.sleep(5)

class ToolIntegration:
    def __init__(self):
        self.git = GitIntegration()
        self.task_manager = TaskManager()
        self.tmux_support = self._check_tmux()
        self.fzf_support = self._check_fzf()
        self.htop_support = self._check_htop()

    def _check_tmux(self) -> bool:
        """Check if tmux is available and get version"""
        try:
            result = subprocess.run(['tmux', '-V'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _check_fzf(self) -> bool:
        """Check if fzf is available"""
        try:
            result = subprocess.run(['fzf', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def _check_htop(self) -> bool:
        """Check if htop is available"""
        try:
            result = subprocess.run(['htop', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def get_git_info(self) -> Dict[str, Any]:
        """Get formatted git repository information"""
        status = self.git.get_status()
        if not status:
            return {'available': False}

        return {
            'available': True,
            'branch': status.branch,
            'clean': status.is_clean,
            'changes': {
                'staged': status.staged,
                'unstaged': status.unstaged,
                'untracked': status.untracked
            },
            'remote': {
                'ahead': status.commits_ahead,
                'behind': status.commits_behind
            },
            'conflicts': status.conflicts,
            'last_commit': {
                'hash': status.last_commit.split()[0],
                'message': ' '.join(status.last_commit.split()[1:]),
                'time': status.last_commit_time.strftime('%Y-%m-%d %H:%M:%S')
            }
        }

    def get_task_info(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get formatted task information"""
        return {
            'cron_tasks': [
                {
                    'name': name,
                    'schedule': task.schedule,
                    'last_run': task.last_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'next_run': task.next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': task.status
                }
                for name, task in self.task_manager.tasks.items()
                if 'cron' in task.schedule
            ],
            'systemd_tasks': [
                {
                    'name': name,
                    'schedule': task.schedule,
                    'last_run': task.last_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'next_run': task.next_run.strftime('%Y-%m-%d %H:%M:%S'),
                    'status': task.status,
                    'pid': task.pid
                }
                for name, task in self.task_manager.tasks.items()
                if 'systemd' in task.schedule
            ]
        }

    def get_tool_status(self) -> Dict[str, bool]:
        """Get status of integrated tools"""
        return {
            'tmux': self.tmux_support,
            'fzf': self.fzf_support,
            'htop': self.htop_support
        }

    async def create_tmux_session(self, name: str, window_configs: List[Dict[str, Any]]) -> bool:
        """Create a new tmux session with specified windows"""
        if not self.tmux_support:
            return False

        try:
            # Create new session
            result = await asyncio.create_subprocess_exec(
                'tmux', 'new-session', '-d', '-s', name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await result.communicate()

            # Create windows
            for config in window_configs:
                window_name = config.get('name', 'window')
                command = config.get('command', '')
                
                # Create window
                result = await asyncio.create_subprocess_exec(
                    'tmux', 'new-window', '-t', f'{name}:', '-n', window_name,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()

                if command:
                    # Send command to window
                    result = await asyncio.create_subprocess_exec(
                        'tmux', 'send-keys', '-t', f'{name}:{window_name}', command, 'C-m',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()

            return True

        except Exception as e:
            logging.error(f"Error creating tmux session: {e}")
            return False

    def cleanup(self):
        """Cleanup resources"""
        # Cleanup will be implemented as needed
        pass

# Example usage
if __name__ == "__main__":
    # Initialize tool integration
    tool_integration = ToolIntegration()
    
    try:
        # Print git status
        git_info = tool_integration.get_git_info()
        print("\nGit Status:")
        print(json.dumps(git_info, indent=2))
        
        # Print task information
        task_info = tool_integration.get_task_info()
        print("\nTask Status:")
        print(json.dumps(task_info, indent=2))
        
        # Print tool status
        tool_status = tool_integration.get_tool_status()
        print("\nTool Status:")
        print(json.dumps(tool_status, indent=2))
        
        # Example tmux session creation
        if tool_integration.tmux_support:
            window_configs = [
                {"name": "editor", "command": "vim"},
                {"name": "terminal", "command": ""},
                {"name": "monitor", "command": "htop"}
            ]
            
            asyncio.run(tool_integration.create_tmux_session("dev", window_configs))
            print("\nCreated tmux session 'dev'")
    
    finally:
        tool_integration.cleanup() 