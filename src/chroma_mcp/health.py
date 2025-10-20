"""
Health checking and monitoring capabilities for Chroma MCP.
"""
from typing import Dict, List, Optional
import time
import psutil
from datetime import datetime


class HealthMonitor:
    """Monitors health and performance of the Chroma MCP server."""
    
    def __init__(self):
        self.start_time = time.time()
        self._metrics = {
            "queries": 0,
            "inserts": 0,
            "errors": 0,
            "last_error": None,
            "collections_accessed": set()
        }
    
    def record_query(self, collection_name: str):
        """Record a query operation."""
        self._metrics["queries"] += 1
        self._metrics["collections_accessed"].add(collection_name)
    
    def record_insert(self, collection_name: str):
        """Record an insert operation."""
        self._metrics["inserts"] += 1
        self._metrics["collections_accessed"].add(collection_name)
    
    def record_error(self, error: str):
        """Record an error."""
        self._metrics["errors"] += 1
        self._metrics["last_error"] = {
            "message": error,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_system_metrics(self) -> Dict:
        """Get system resource metrics."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
            "disk_usage_percent": psutil.disk_usage('/').percent
        }
    
    def get_health_status(self) -> Dict:
        """Get comprehensive health status."""
        uptime = time.time() - self.start_time
        system_metrics = self.get_system_metrics()
        
        # Determine health status
        health = "healthy"
        issues = []
        
        if system_metrics["cpu_percent"] > 80:
            health = "warning"
            issues.append("High CPU usage")
        
        if system_metrics["memory_percent"] > 80:
            health = "warning"
            issues.append("High memory usage")
        
        if system_metrics["disk_usage_percent"] > 90:
            health = "critical"
            issues.append("Critical disk usage")
        
        error_rate = self._metrics["errors"] / max(1, self._metrics["queries"] + self._metrics["inserts"])
        if error_rate > 0.1:
            health = "unhealthy"
            issues.append(f"High error rate: {error_rate:.2%}")
        
        return {
            "status": health,
            "uptime_seconds": uptime,
            "uptime_human": self._format_uptime(uptime),
            "issues": issues,
            "metrics": {
                "queries": self._metrics["queries"],
                "inserts": self._metrics["inserts"],
                "errors": self._metrics["errors"],
                "collections_accessed": len(self._metrics["collections_accessed"]),
                "error_rate": error_rate
            },
            "system": system_metrics,
            "last_error": self._metrics["last_error"],
            "timestamp": datetime.now().isoformat()
        }
    
    def _format_uptime(self, seconds: float) -> str:
        """Format uptime in human-readable format."""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        parts.append(f"{secs}s")
        
        return " ".join(parts)
    
    def reset_metrics(self):
        """Reset metrics."""
        self._metrics = {
            "queries": 0,
            "inserts": 0,
            "errors": 0,
            "last_error": None,
            "collections_accessed": set()
        }


# Global health monitor instance
_health_monitor = None

def get_health_monitor() -> HealthMonitor:
    """Get or create the global health monitor."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor
