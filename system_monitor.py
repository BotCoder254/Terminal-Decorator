#!/usr/bin/env python3

import psutil
import time
import os
import platform
import socket
import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import subprocess
from art import text2art, art

class SystemMonitor:
    def __init__(self):
        self.command_history = defaultdict(int)
        self.command_times = defaultdict(list)
        self.start_time = time.time()

    def get_system_info(self) -> Dict[str, str]:
        """Get basic system information"""
        return {
            'os': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname(),
            'uptime': self._get_uptime()
        }

    def get_cpu_info(self) -> Dict[str, float]:
        """Get CPU usage information"""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        return {
            'total': psutil.cpu_percent(interval=1),
            'per_cpu': cpu_percent,
            'freq': psutil.cpu_freq().current if hasattr(psutil.cpu_freq(), 'current') else 0,
            'cores': psutil.cpu_count(),
            'threads': psutil.cpu_count(logical=True)
        }

    def get_memory_info(self) -> Dict[str, float]:
        """Get memory usage information"""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        return {
            'total': mem.total / (1024 ** 3),  # GB
            'available': mem.available / (1024 ** 3),
            'percent': mem.percent,
            'swap_total': swap.total / (1024 ** 3),
            'swap_used': swap.used / (1024 ** 3),
            'swap_percent': swap.percent
        }

    def get_disk_info(self) -> List[Dict[str, str]]:
        """Get disk usage information"""
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total': usage.total / (1024 ** 3),
                    'used': usage.used / (1024 ** 3),
                    'free': usage.free / (1024 ** 3),
                    'percent': usage.percent
                })
            except (PermissionError, FileNotFoundError):
                continue
        return disks

    def get_network_info(self) -> Dict[str, Dict[str, float]]:
        """Get network usage information"""
        net_io = psutil.net_io_counters()
        net_if = psutil.net_if_stats()
        return {
            'bytes_sent': net_io.bytes_sent,
            'bytes_recv': net_io.bytes_recv,
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
            'interfaces': {
                iface: {
                    'speed': stats.speed if hasattr(stats, 'speed') else 0,
                    'mtu': stats.mtu,
                    'up': stats.isup
                }
                for iface, stats in net_if.items()
            }
        }

    def get_process_info(self) -> List[Dict[str, str]]:
        """Get information about top processes"""
        processes = []
        for proc in sorted(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']),
                          key=lambda p: p.info['cpu_percent'],
                          reverse=True)[:5]:
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu_percent': proc.info['cpu_percent'],
                    'memory_percent': proc.info['memory_percent']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return processes

    def get_command_history_stats(self) -> Dict[str, any]:
        """Get command history statistics"""
        history_file = os.path.expanduser('~/.bash_history')
        try:
            with open(history_file, 'r') as f:
                history = f.readlines()
            
            for cmd in history:
                cmd = cmd.strip()
                if cmd:
                    self.command_history[cmd] += 1
            
            return {
                'total_commands': len(history),
                'unique_commands': len(self.command_history),
                'top_commands': sorted(self.command_history.items(),
                                    key=lambda x: x[1],
                                    reverse=True)[:5]
            }
        except FileNotFoundError:
            return {'error': 'History file not found'}

    def _get_uptime(self) -> str:
        """Get system uptime in human-readable format"""
        uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time())
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    def get_ascii_header(self, style: str = 'random') -> str:
        """Generate ASCII art header with system info"""
        styles = ['block', 'banner3-D', 'colossal', 'doom', 'epic', 'isometric1', 'larry3d']
        
        if style == 'random':
            style = styles[int(time.time()) % len(styles)]
        
        hostname = socket.gethostname()
        header = text2art(f"System Monitor", font=style)
        header += "\n" + text2art(hostname, font='small')
        
        # Add decorative border
        width = max(len(line) for line in header.split('\n'))
        border = '=' * width
        
        return f"{border}\n{header}\n{border}"

    def get_all_metrics(self) -> Dict[str, any]:
        """Get all system metrics in one call"""
        return {
            'system': self.get_system_info(),
            'cpu': self.get_cpu_info(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'network': self.get_network_info(),
            'processes': self.get_process_info(),
            'history': self.get_command_history_stats()
        }

if __name__ == '__main__':
    monitor = SystemMonitor()
    print(monitor.get_ascii_header())
    print("\nSystem Metrics:")
    metrics = monitor.get_all_metrics()
    import json
    print(json.dumps(metrics, indent=2)) 