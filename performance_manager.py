#!/usr/bin/env python3

import os
import sys
import time
import psutil
import threading
import importlib
from typing import Dict, Any, Optional, Set, List
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import logging
from functools import lru_cache

@dataclass
class PerformanceMetrics:
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    io_operations: int = 0
    thread_count: int = 0
    load_time: float = 0.0
    frame_time: float = 0.0

class FeatureManager:
    def __init__(self):
        self.loaded_features: Set[str] = set()
        self.feature_dependencies: Dict[str, List[str]] = {
            'animations': ['rich', 'numpy'],
            'system_monitor': ['psutil'],
            'themes': ['rich.theme', 'colorama'],
            'accessibility': ['pyttsx3', 'pyaccessibility'],
            'network': ['psutil', 'requests'],
            'text_effects': ['rich.text', 'rich.style'],
        }
        self.feature_modules: Dict[str, Any] = {}
        self.loading_lock = threading.Lock()

    def is_feature_loaded(self, feature: str) -> bool:
        return feature in self.loaded_features

    def load_feature(self, feature: str) -> bool:
        if feature in self.loaded_features:
            return True

        with self.loading_lock:
            try:
                # Check dependencies
                for dependency in self.feature_dependencies.get(feature, []):
                    importlib.import_module(dependency)
                
                # Load the feature module
                module_name = f"{feature}_manager"
                self.feature_modules[feature] = importlib.import_module(module_name)
                self.loaded_features.add(feature)
                logging.info(f"Successfully loaded feature: {feature}")
                return True
            
            except ImportError as e:
                logging.error(f"Failed to load feature {feature}: {e}")
                return False

    def unload_feature(self, feature: str) -> bool:
        if feature not in self.loaded_features:
            return True

        with self.loading_lock:
            try:
                # Cleanup feature resources
                if hasattr(self.feature_modules[feature], 'cleanup'):
                    self.feature_modules[feature].cleanup()
                
                # Remove from loaded features
                self.loaded_features.remove(feature)
                del self.feature_modules[feature]
                logging.info(f"Successfully unloaded feature: {feature}")
                return True
            
            except Exception as e:
                logging.error(f"Failed to unload feature {feature}: {e}")
                return False

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 100
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

    def start_monitoring(self):
        if not self.monitoring:
            self.monitoring = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()

    def _monitor_loop(self):
        while self.monitoring:
            metrics = self._collect_metrics()
            self.metrics_history.append(metrics)
            
            # Keep history size bounded
            if len(self.metrics_history) > self.max_history_size:
                self.metrics_history.pop(0)
            
            time.sleep(1)  # Collect metrics every second

    def _collect_metrics(self) -> PerformanceMetrics:
        return PerformanceMetrics(
            cpu_usage=self.process.cpu_percent(),
            memory_usage=self.process.memory_percent(),
            io_operations=sum(self.process.io_counters()),
            thread_count=self.process.num_threads(),
            load_time=time.time(),
            frame_time=self._measure_frame_time()
        )

    def _measure_frame_time(self) -> float:
        start_time = time.perf_counter()
        # Simulate frame rendering
        time.sleep(0.001)
        return time.perf_counter() - start_time

    @lru_cache(maxsize=128)
    def get_average_metrics(self, window: int = 10) -> PerformanceMetrics:
        if not self.metrics_history:
            return PerformanceMetrics()

        window = min(window, len(self.metrics_history))
        recent_metrics = self.metrics_history[-window:]
        
        return PerformanceMetrics(
            cpu_usage=sum(m.cpu_usage for m in recent_metrics) / window,
            memory_usage=sum(m.memory_usage for m in recent_metrics) / window,
            io_operations=sum(m.io_operations for m in recent_metrics) // window,
            thread_count=sum(m.thread_count for m in recent_metrics) // window,
            load_time=sum(m.load_time for m in recent_metrics) / window,
            frame_time=sum(m.frame_time for m in recent_metrics) / window
        )

class PerformanceManager:
    def __init__(self, config: Dict[str, Any]):
        self.config = config.get('performance', {})
        self.feature_manager = FeatureManager()
        self.resource_monitor = ResourceMonitor()
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.get('max_concurrent', 5),
            thread_name_prefix="PerfMgr"
        )
        self.setup_logging()
        self.resource_monitor.start_monitoring()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('performance.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    def optimize_performance(self):
        metrics = self.resource_monitor.get_average_metrics()
        
        # Automatic performance optimization based on metrics
        if metrics.cpu_usage > 80:
            self._reduce_cpu_usage()
        
        if metrics.memory_usage > 70:
            self._optimize_memory()
        
        if metrics.frame_time > 1/30:  # Below 30 FPS
            self._optimize_rendering()

    def _reduce_cpu_usage(self):
        # Reduce update frequency
        if self.config.get('fps', 60) > 30:
            self.config['fps'] = 30
            logging.info("Reduced FPS to optimize CPU usage")
        
        # Disable non-essential features
        for feature in ['animations', 'text_effects']:
            if self.feature_manager.is_feature_loaded(feature):
                self.feature_manager.unload_feature(feature)
                logging.info(f"Unloaded {feature} to reduce CPU usage")

    def _optimize_memory(self):
        # Clear caches
        self.resource_monitor.get_average_metrics.cache_clear()
        
        # Reduce history size
        self.resource_monitor.max_history_size = 50
        
        # Unload unused features
        current_time = time.time()
        for feature, module in list(self.feature_manager.feature_modules.items()):
            if hasattr(module, 'last_used') and current_time - module.last_used > 300:  # 5 minutes
                self.feature_manager.unload_feature(feature)
                logging.info(f"Unloaded inactive feature: {feature}")

    def _optimize_rendering(self):
        # Disable animations
        if self.config.get('smooth_transitions'):
            self.config['smooth_transitions'] = False
            logging.info("Disabled smooth transitions to improve rendering performance")
        
        # Reduce visual effects
        if self.config.get('hardware_acceleration') and metrics.cpu_usage > 90:
            self.config['hardware_acceleration'] = False
            logging.info("Disabled hardware acceleration due to high CPU usage")

    def load_feature_async(self, feature: str):
        return self.thread_pool.submit(self.feature_manager.load_feature, feature)

    def get_performance_stats(self) -> Dict[str, Any]:
        metrics = self.resource_monitor.get_average_metrics()
        return {
            'cpu_usage': f"{metrics.cpu_usage:.1f}%",
            'memory_usage': f"{metrics.memory_usage:.1f}%",
            'io_operations': metrics.io_operations,
            'thread_count': metrics.thread_count,
            'frame_time': f"{metrics.frame_time*1000:.1f}ms",
            'fps': f"{1/metrics.frame_time:.1f}" if metrics.frame_time > 0 else "N/A",
            'loaded_features': list(self.feature_manager.loaded_features)
        }

    def cleanup(self):
        self.resource_monitor.stop_monitoring()
        self.thread_pool.shutdown(wait=True)
        for feature in list(self.feature_manager.loaded_features):
            self.feature_manager.unload_feature(feature)

    def __del__(self):
        self.cleanup()

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = {
        'performance': {
            'max_concurrent': 5,
            'fps': 60,
            'hardware_acceleration': True,
            'smooth_transitions': True,
            'buffer_size': 1024,
            'vsync': True
        }
    }
    
    try:
        # Initialize performance manager
        perf_manager = PerformanceManager(config)
        
        # Load some features
        perf_manager.load_feature_async('animations')
        perf_manager.load_feature_async('system_monitor')
        
        # Monitor and optimize performance
        while True:
            perf_manager.optimize_performance()
            stats = perf_manager.get_performance_stats()
            print("\nPerformance Stats:")
            for key, value in stats.items():
                print(f"{key}: {value}")
            time.sleep(5)
    
    except KeyboardInterrupt:
        print("\nShutting down performance manager...")
        perf_manager.cleanup() 