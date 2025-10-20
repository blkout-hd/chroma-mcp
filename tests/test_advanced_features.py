"""
Basic tests for new advanced features.
"""
import pytest
from chroma_mcp.cache import MemoryCache
from chroma_mcp.health import HealthMonitor
from chroma_mcp.security import SensitiveDataDetector, EncryptionManager
from chroma_mcp.swarm import SwarmTracker, CodeSmellMonitor
from chroma_mcp.entity_mapper import EntityRelationshipMapper
from chroma_mcp.maintenance import AutoScaler


def test_memory_cache():
    """Test memory cache basic functionality."""
    cache = MemoryCache(max_size=10)
    
    # Test set and get
    cache.set("key1", "value1", ttl=3600)
    assert cache.get("key1") == "value1"
    
    # Test non-existent key
    assert cache.get("nonexistent") is None
    
    # Test cache stats
    stats = cache.get_stats()
    assert stats["total_entries"] >= 1
    assert stats["max_size"] == 10


def test_health_monitor():
    """Test health monitoring."""
    monitor = HealthMonitor()
    
    # Record operations
    monitor.record_query("test_collection")
    monitor.record_insert("test_collection")
    
    # Get health status
    status = monitor.get_health_status()
    assert "status" in status
    assert "uptime_seconds" in status
    assert "metrics" in status
    assert status["metrics"]["queries"] >= 1
    assert status["metrics"]["inserts"] >= 1


def test_sensitive_data_detector():
    """Test sensitive data detection."""
    detector = SensitiveDataDetector()
    
    # Test with email
    text = "Contact us at test@example.com"
    result = detector.detect(text)
    assert result["has_sensitive_data"] is True
    assert "email" in result["detections"]
    
    # Test with no sensitive data
    text = "This is a normal text"
    result = detector.detect(text)
    assert result["has_sensitive_data"] is False


def test_encryption_manager():
    """Test encryption functionality."""
    manager = EncryptionManager(password="test-password")
    
    # Test encryption and decryption
    original = "secret data"
    encrypted = manager.encrypt(original)
    assert encrypted != original
    
    decrypted = manager.decrypt(encrypted)
    assert decrypted == original


def test_swarm_tracker():
    """Test swarm pheromone tracking."""
    tracker = SwarmTracker()
    
    # Track operations
    trail_id = tracker.track_operation("query", "test_collection", "search term")
    assert trail_id is not None
    
    # Track same operation again to reinforce
    tracker.track_operation("query", "test_collection", "search term")
    
    # Get hot trails
    hot_trails = tracker.get_hot_trails(min_strength=0.0, limit=10)
    assert len(hot_trails) >= 1


def test_code_smell_monitor():
    """Test code smell detection."""
    monitor = CodeSmellMonitor()
    
    # Test with excessive query results
    smells = monitor.analyze_operation(
        "query",
        "test_collection",
        {"n_results": 150}
    )
    assert len(smells) >= 1
    assert any("excessive" in smell["smell_type"] for smell in smells)


def test_entity_relationship_mapper():
    """Test entity relationship mapping."""
    mapper = EntityRelationshipMapper()
    
    # Add entities
    entity1 = mapper.add_entity("user1", "User", {"name": "Alice"})
    entity2 = mapper.add_entity("user2", "User", {"name": "Bob"})
    
    assert entity1.entity_id == "user1"
    assert entity2.entity_id == "user2"
    
    # Add relationship
    rel = mapper.add_relationship("rel1", "user1", "user2", "FOLLOWS")
    assert rel is not None
    assert rel.source_id == "user1"
    assert rel.target_id == "user2"
    
    # Get statistics
    stats = mapper.get_statistics()
    assert stats["total_entities"] == 2
    assert stats["total_relationships"] == 1


def test_auto_scaler():
    """Test auto scaling recommendations."""
    scaler = AutoScaler()
    
    # Test with high CPU
    metrics = {"cpu_percent": 85, "memory_percent": 50}
    recommendations = scaler.analyze_and_scale(metrics)
    assert recommendations["scale_up"] is True
    assert "CPU" in recommendations["reason"]
    
    # Test with low CPU
    for _ in range(10):
        metrics = {"cpu_percent": 15, "memory_percent": 30}
        scaler.analyze_and_scale(metrics)
    
    recommendations = scaler.analyze_and_scale({"cpu_percent": 15, "memory_percent": 30})
    assert recommendations["scale_down"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
