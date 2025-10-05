"""
Autonomous maintenance, scheduling, and watchdog capabilities.
"""
from typing import Dict, List, Optional, Callable
import threading
import time
from datetime import datetime
import schedule
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class DatabaseWatchdog(FileSystemEventHandler):
    """Watches for database changes and triggers auto-restart if needed."""
    
    def __init__(self, restart_callback: Optional[Callable] = None):
        self.restart_callback = restart_callback
        self.last_modified = time.time()
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
        
        # Debounce: only trigger if enough time has passed
        current_time = time.time()
        if current_time - self.last_modified < 5:
            return
        
        self.last_modified = current_time
        
        if self.restart_callback:
            print(f"Database change detected: {event.src_path}")
            self.restart_callback()


class MaintenanceScheduler:
    """Manages scheduled maintenance tasks."""
    
    def __init__(self):
        self._jobs = []
        self._running = False
        self._scheduler_thread = None
        self._watchdog_observer = None
    
    def schedule_task(
        self,
        func: Callable,
        interval: str,
        *args,
        **kwargs
    ) -> str:
        """
        Schedule a maintenance task.
        
        Args:
            func: Function to execute
            interval: Schedule interval (e.g., "every().hour", "every().day.at('02:00')")
            *args, **kwargs: Arguments to pass to the function
        
        Returns:
            Job ID
        """
        # Parse interval and schedule
        job = None
        if interval == "hourly":
            job = schedule.every().hour.do(func, *args, **kwargs)
        elif interval == "daily":
            job = schedule.every().day.do(func, *args, **kwargs)
        elif interval == "weekly":
            job = schedule.every().week.do(func, *args, **kwargs)
        elif interval.startswith("every_"):
            # Custom intervals like "every_30_minutes"
            parts = interval.split("_")
            if len(parts) == 3:
                unit = parts[2]  # minutes, hours, etc.
                count = int(parts[1])
                if unit == "minutes":
                    job = schedule.every(count).minutes.do(func, *args, **kwargs)
                elif unit == "hours":
                    job = schedule.every(count).hours.do(func, *args, **kwargs)
        
        if job:
            self._jobs.append(job)
            return str(id(job))
        
        return ""
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        if self._watchdog_observer:
            self._watchdog_observer.stop()
            self._watchdog_observer.join(timeout=5)
    
    def start_watchdog(self, path: str, restart_callback: Optional[Callable] = None):
        """
        Start file system watchdog for monitoring database changes.
        
        Args:
            path: Path to monitor
            restart_callback: Callback function to call on changes
        """
        if self._watchdog_observer:
            return
        
        event_handler = DatabaseWatchdog(restart_callback)
        self._watchdog_observer = Observer()
        self._watchdog_observer.schedule(event_handler, path, recursive=False)
        self._watchdog_observer.start()
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self._running:
            schedule.run_pending()
            time.sleep(1)
    
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get list of scheduled jobs."""
        return [
            {
                "job_id": str(id(job)),
                "next_run": str(job.next_run),
                "interval": str(job.interval)
            }
            for job in self._jobs
        ]
    
    def schedule_health_check(self, interval: str = "every_5_minutes"):
        """Schedule periodic health checks."""
        from .health import get_health_monitor
        
        def health_check_task():
            monitor = get_health_monitor()
            status = monitor.get_health_status()
            if status["status"] in ["warning", "critical", "unhealthy"]:
                print(f"Health check warning: {status['status']} - {status['issues']}")
        
        return self.schedule_task(health_check_task, interval)
    
    def schedule_cache_cleanup(self, interval: str = "hourly"):
        """Schedule periodic cache cleanup."""
        from .cache import get_memory_cache
        
        def cache_cleanup_task():
            cache = get_memory_cache()
            # Cleanup is automatic when accessing cache, but we can log stats
            stats = cache.get_stats()
            print(f"Cache stats: {stats['active_entries']} active, {stats['expired_count']} expired")
        
        return self.schedule_task(cache_cleanup_task, interval)


class AutoScaler:
    """Intelligent scaling and adjustment based on ecosystem metrics."""
    
    def __init__(self):
        self.metrics_history = []
        self.scaling_decisions = []
    
    def analyze_and_scale(self, metrics: Dict) -> Dict:
        """
        Analyze metrics and make scaling decisions.
        
        Args:
            metrics: Current system metrics
        
        Returns:
            Scaling recommendations
        """
        self.metrics_history.append({
            "timestamp": time.time(),
            "metrics": metrics
        })
        
        # Keep only last 100 metrics
        if len(self.metrics_history) > 100:
            self.metrics_history.pop(0)
        
        recommendations = {
            "scale_up": False,
            "scale_down": False,
            "reason": "",
            "suggested_action": None
        }
        
        # Analyze CPU usage
        cpu_percent = metrics.get("cpu_percent", 0)
        if cpu_percent > 80:
            recommendations["scale_up"] = True
            recommendations["reason"] = "High CPU usage detected"
            recommendations["suggested_action"] = "increase_workers"
        elif cpu_percent < 20 and len(self.metrics_history) > 10:
            # Check if consistently low
            recent_cpu = [m["metrics"].get("cpu_percent", 0) for m in self.metrics_history[-10:]]
            if all(c < 30 for c in recent_cpu):
                recommendations["scale_down"] = True
                recommendations["reason"] = "Consistently low CPU usage"
                recommendations["suggested_action"] = "decrease_workers"
        
        # Analyze memory usage
        memory_percent = metrics.get("memory_percent", 0)
        if memory_percent > 85:
            recommendations["scale_up"] = True
            recommendations["reason"] = "High memory usage detected"
            recommendations["suggested_action"] = "increase_memory_limit"
        
        self.scaling_decisions.append({
            "timestamp": time.time(),
            "recommendations": recommendations
        })
        
        return recommendations


# Global instances
_maintenance_scheduler = None
_auto_scaler = None

def get_maintenance_scheduler() -> MaintenanceScheduler:
    """Get or create the global maintenance scheduler."""
    global _maintenance_scheduler
    if _maintenance_scheduler is None:
        _maintenance_scheduler = MaintenanceScheduler()
    return _maintenance_scheduler

def get_auto_scaler() -> AutoScaler:
    """Get or create the global auto scaler."""
    global _auto_scaler
    if _auto_scaler is None:
        _auto_scaler = AutoScaler()
    return _auto_scaler
