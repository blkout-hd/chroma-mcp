"""
Swarm pheromone trail tracking and code smell monitoring.
Tracks patterns and anomalies in operations.
"""
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import time
import hashlib
import json


class PheromoneTrail:
    """Represents a pheromone trail for tracking operation patterns."""
    
    def __init__(self, trail_id: str, initial_strength: float = 1.0):
        self.trail_id = trail_id
        self.strength = initial_strength
        self.last_update = time.time()
        self.access_count = 0
        self.metadata = {}
    
    def reinforce(self, amount: float = 0.1):
        """Reinforce the pheromone trail."""
        self.strength = min(1.0, self.strength + amount)
        self.last_update = time.time()
        self.access_count += 1
    
    def evaporate(self, rate: float = 0.01):
        """Evaporate the pheromone trail over time."""
        time_passed = time.time() - self.last_update
        evaporation = rate * time_passed / 60  # per minute
        self.strength = max(0.0, self.strength - evaporation)
        self.last_update = time.time()


class SwarmTracker:
    """Tracks swarm patterns and pheromone trails."""
    
    def __init__(self, evaporation_rate: float = 0.01):
        self.evaporation_rate = evaporation_rate
        self._trails: Dict[str, PheromoneTrail] = {}
        self._operation_patterns = defaultdict(list)
    
    def _generate_trail_id(self, operation_type: str, collection: str, query: str) -> str:
        """Generate unique trail ID."""
        data = f"{operation_type}:{collection}:{query}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def track_operation(
        self,
        operation_type: str,
        collection_name: str,
        query: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Track an operation and reinforce its pheromone trail.
        
        Args:
            operation_type: Type of operation (query, insert, update, etc.)
            collection_name: Collection name
            query: Optional query string
            metadata: Optional operation metadata
        
        Returns:
            Trail ID
        """
        query_str = query or ""
        trail_id = self._generate_trail_id(operation_type, collection_name, query_str)
        
        if trail_id not in self._trails:
            self._trails[trail_id] = PheromoneTrail(trail_id)
            self._trails[trail_id].metadata = {
                "operation_type": operation_type,
                "collection": collection_name,
                "query": query_str,
                "first_seen": time.time()
            }
        
        # Reinforce trail
        trail = self._trails[trail_id]
        trail.reinforce()
        
        # Track pattern
        self._operation_patterns[collection_name].append({
            "timestamp": time.time(),
            "operation": operation_type,
            "trail_id": trail_id
        })
        
        return trail_id
    
    def get_hot_trails(self, min_strength: float = 0.5, limit: int = 10) -> List[Dict]:
        """
        Get the hottest (most reinforced) trails.
        
        Args:
            min_strength: Minimum trail strength
            limit: Maximum number of trails to return
        
        Returns:
            List of hot trails
        """
        # Evaporate all trails first
        for trail in self._trails.values():
            trail.evaporate(self.evaporation_rate)
        
        # Filter and sort
        hot_trails = [
            {
                "trail_id": trail.trail_id,
                "strength": trail.strength,
                "access_count": trail.access_count,
                "metadata": trail.metadata
            }
            for trail in self._trails.values()
            if trail.strength >= min_strength
        ]
        
        hot_trails.sort(key=lambda x: x["strength"], reverse=True)
        return hot_trails[:limit]
    
    def get_collection_patterns(self, collection_name: str) -> Dict[str, Any]:
        """Get operation patterns for a collection."""
        patterns = self._operation_patterns.get(collection_name, [])
        
        if not patterns:
            return {"collection": collection_name, "patterns": []}
        
        # Analyze patterns
        operation_counts = defaultdict(int)
        recent_operations = []
        
        current_time = time.time()
        for pattern in patterns[-100:]:  # Last 100 operations
            operation_counts[pattern["operation"]] += 1
            if current_time - pattern["timestamp"] < 3600:  # Last hour
                recent_operations.append(pattern)
        
        return {
            "collection": collection_name,
            "total_operations": len(patterns),
            "operation_counts": dict(operation_counts),
            "recent_operations": len(recent_operations),
            "patterns": patterns[-10:]  # Last 10 patterns
        }


class CodeSmellMonitor:
    """Monitors for code smells and anti-patterns in operations."""
    
    def __init__(self):
        self._smells: List[Dict] = []
        self._checks = {
            "excessive_queries": self._check_excessive_queries,
            "large_batch_size": self._check_large_batch_size,
            "inefficient_filtering": self._check_inefficient_filtering,
            "duplicate_operations": self._check_duplicate_operations
        }
    
    def analyze_operation(
        self,
        operation_type: str,
        collection_name: str,
        params: Dict[str, Any]
    ) -> List[Dict]:
        """
        Analyze an operation for code smells.
        
        Args:
            operation_type: Type of operation
            collection_name: Collection name
            params: Operation parameters
        
        Returns:
            List of detected code smells
        """
        smells = []
        
        for check_name, check_func in self._checks.items():
            result = check_func(operation_type, collection_name, params)
            if result:
                smell = {
                    "smell_type": check_name,
                    "operation": operation_type,
                    "collection": collection_name,
                    "description": result["description"],
                    "severity": result["severity"],
                    "suggestion": result["suggestion"],
                    "timestamp": time.time()
                }
                smells.append(smell)
                self._smells.append(smell)
        
        # Keep only last 1000 smells
        if len(self._smells) > 1000:
            self._smells = self._smells[-1000:]
        
        return smells
    
    def _check_excessive_queries(
        self,
        operation_type: str,
        collection_name: str,
        params: Dict
    ) -> Optional[Dict]:
        """Check for excessive queries."""
        if operation_type == "query" and params.get("n_results", 0) > 100:
            return {
                "description": f"Query requesting {params['n_results']} results, which may be excessive",
                "severity": "warning",
                "suggestion": "Consider paginating results or reducing n_results"
            }
        return None
    
    def _check_large_batch_size(
        self,
        operation_type: str,
        collection_name: str,
        params: Dict
    ) -> Optional[Dict]:
        """Check for large batch sizes."""
        if operation_type == "add" and "documents" in params:
            doc_count = len(params["documents"])
            if doc_count > 1000:
                return {
                    "description": f"Adding {doc_count} documents in single batch",
                    "severity": "warning",
                    "suggestion": "Consider batching into smaller groups (e.g., 500 documents)"
                }
        return None
    
    def _check_inefficient_filtering(
        self,
        operation_type: str,
        collection_name: str,
        params: Dict
    ) -> Optional[Dict]:
        """Check for inefficient filtering."""
        if "where" in params and isinstance(params["where"], dict):
            # Check for overly complex filters
            filter_str = json.dumps(params["where"])
            if len(filter_str) > 500:
                return {
                    "description": "Complex metadata filter detected",
                    "severity": "info",
                    "suggestion": "Consider simplifying filters or using indexed fields"
                }
        return None
    
    def _check_duplicate_operations(
        self,
        operation_type: str,
        collection_name: str,
        params: Dict
    ) -> Optional[Dict]:
        """Check for duplicate operations."""
        # This would require tracking recent operations
        # Simplified check here
        return None
    
    def get_smell_report(self) -> Dict[str, Any]:
        """Get a report of detected code smells."""
        if not self._smells:
            return {"total_smells": 0, "by_type": {}, "recent": []}
        
        by_type = defaultdict(int)
        by_severity = defaultdict(int)
        
        for smell in self._smells:
            by_type[smell["smell_type"]] += 1
            by_severity[smell["severity"]] += 1
        
        return {
            "total_smells": len(self._smells),
            "by_type": dict(by_type),
            "by_severity": dict(by_severity),
            "recent": self._smells[-10:]  # Last 10 smells
        }


# Global instances
_swarm_tracker = None
_code_smell_monitor = None

def get_swarm_tracker() -> SwarmTracker:
    """Get or create the global swarm tracker."""
    global _swarm_tracker
    if _swarm_tracker is None:
        _swarm_tracker = SwarmTracker()
    return _swarm_tracker

def get_code_smell_monitor() -> CodeSmellMonitor:
    """Get or create the global code smell monitor."""
    global _code_smell_monitor
    if _code_smell_monitor is None:
        _code_smell_monitor = CodeSmellMonitor()
    return _code_smell_monitor
