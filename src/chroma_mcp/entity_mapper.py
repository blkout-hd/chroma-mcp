"""
Entity relationship mapping for connected data.
"""
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import json


class Entity:
    """Represents an entity in the relationship graph."""
    
    def __init__(self, entity_id: str, entity_type: str, properties: Optional[Dict] = None):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.properties = properties or {}
        self.relationships: Set[str] = set()
    
    def to_dict(self) -> Dict:
        """Convert entity to dictionary."""
        return {
            "id": self.entity_id,
            "type": self.entity_type,
            "properties": self.properties,
            "relationships": list(self.relationships)
        }


class Relationship:
    """Represents a relationship between entities."""
    
    def __init__(
        self,
        relationship_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict] = None
    ):
        self.relationship_id = relationship_id
        self.source_id = source_id
        self.target_id = target_id
        self.relationship_type = relationship_type
        self.properties = properties or {}
    
    def to_dict(self) -> Dict:
        """Convert relationship to dictionary."""
        return {
            "id": self.relationship_id,
            "source": self.source_id,
            "target": self.target_id,
            "type": self.relationship_type,
            "properties": self.properties
        }


class EntityRelationshipMapper:
    """Maps and manages entity relationships."""
    
    def __init__(self):
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._entity_index: Dict[str, Set[str]] = defaultdict(set)  # type -> entity_ids
        self._relationship_index: Dict[Tuple[str, str], Set[str]] = defaultdict(set)  # (source, target) -> rel_ids
    
    def add_entity(
        self,
        entity_id: str,
        entity_type: str,
        properties: Optional[Dict] = None
    ) -> Entity:
        """Add an entity to the graph."""
        entity = Entity(entity_id, entity_type, properties)
        self._entities[entity_id] = entity
        self._entity_index[entity_type].add(entity_id)
        return entity
    
    def add_relationship(
        self,
        relationship_id: str,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Optional[Dict] = None
    ) -> Optional[Relationship]:
        """Add a relationship between entities."""
        # Check if entities exist
        if source_id not in self._entities or target_id not in self._entities:
            return None
        
        relationship = Relationship(
            relationship_id,
            source_id,
            target_id,
            relationship_type,
            properties
        )
        
        self._relationships[relationship_id] = relationship
        self._relationship_index[(source_id, target_id)].add(relationship_id)
        
        # Update entity relationships
        self._entities[source_id].relationships.add(relationship_id)
        self._entities[target_id].relationships.add(relationship_id)
        
        return relationship
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Entity]:
        """Get all entities of a specific type."""
        entity_ids = self._entity_index.get(entity_type, set())
        return [self._entities[eid] for eid in entity_ids]
    
    def get_relationship(self, relationship_id: str) -> Optional[Relationship]:
        """Get a relationship by ID."""
        return self._relationships.get(relationship_id)
    
    def get_relationships_between(
        self,
        source_id: str,
        target_id: str
    ) -> List[Relationship]:
        """Get all relationships between two entities."""
        rel_ids = self._relationship_index.get((source_id, target_id), set())
        return [self._relationships[rid] for rid in rel_ids]
    
    def get_connected_entities(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None
    ) -> List[Tuple[Entity, Relationship]]:
        """Get all entities connected to a given entity."""
        if entity_id not in self._entities:
            return []
        
        entity = self._entities[entity_id]
        connected = []
        
        for rel_id in entity.relationships:
            rel = self._relationships[rel_id]
            
            # Filter by relationship type if specified
            if relationship_type and rel.relationship_type != relationship_type:
                continue
            
            # Get the connected entity
            other_id = rel.target_id if rel.source_id == entity_id else rel.source_id
            other_entity = self._entities.get(other_id)
            
            if other_entity:
                connected.append((other_entity, rel))
        
        return connected
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[Tuple[str, str]]]:
        """Find a path between two entities using BFS."""
        if source_id not in self._entities or target_id not in self._entities:
            return None
        
        if source_id == target_id:
            return []
        
        visited = set()
        queue = [(source_id, [])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if len(path) >= max_depth:
                continue
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            # Get connected entities
            connected = self.get_connected_entities(current_id)
            
            for entity, rel in connected:
                new_path = path + [(current_id, rel.relationship_id)]
                
                if entity.entity_id == target_id:
                    return new_path + [(entity.entity_id, "")]
                
                queue.append((entity.entity_id, new_path))
        
        return None
    
    def export_graph(self) -> Dict:
        """Export the entire graph as a dictionary."""
        return {
            "entities": [entity.to_dict() for entity in self._entities.values()],
            "relationships": [rel.to_dict() for rel in self._relationships.values()]
        }
    
    def import_graph(self, graph_data: Dict):
        """Import graph data."""
        # Clear existing data
        self._entities.clear()
        self._relationships.clear()
        self._entity_index.clear()
        self._relationship_index.clear()
        
        # Import entities
        for entity_data in graph_data.get("entities", []):
            self.add_entity(
                entity_data["id"],
                entity_data["type"],
                entity_data.get("properties")
            )
        
        # Import relationships
        for rel_data in graph_data.get("relationships", []):
            self.add_relationship(
                rel_data["id"],
                rel_data["source"],
                rel_data["target"],
                rel_data["type"],
                rel_data.get("properties")
            )
    
    def get_statistics(self) -> Dict:
        """Get graph statistics."""
        entity_type_counts = {
            entity_type: len(entity_ids)
            for entity_type, entity_ids in self._entity_index.items()
        }
        
        relationship_type_counts = defaultdict(int)
        for rel in self._relationships.values():
            relationship_type_counts[rel.relationship_type] += 1
        
        return {
            "total_entities": len(self._entities),
            "total_relationships": len(self._relationships),
            "entity_types": entity_type_counts,
            "relationship_types": dict(relationship_type_counts)
        }


# Global entity relationship mapper instance
_er_mapper = None

def get_er_mapper() -> EntityRelationshipMapper:
    """Get or create the global entity relationship mapper."""
    global _er_mapper
    if _er_mapper is None:
        _er_mapper = EntityRelationshipMapper()
    return _er_mapper
