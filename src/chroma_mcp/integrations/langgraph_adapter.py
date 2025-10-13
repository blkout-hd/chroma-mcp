"""LangGraph integration adapter for Chroma MCP.

This module provides integration between LangGraph (stateful multi-actor applications)
and Chroma vector database for persistent state management and memory.
"""

from typing import Dict, List, Any, Optional
import json


class LangGraphAdapter:
    """Adapter for integrating LangGraph with Chroma MCP.
    
    This adapter enables:
    - Persistent state storage for LangGraph workflows
    - Graph state serialization/deserialization
    - Checkpoint management for graph execution
    - Memory persistence across graph runs
    """
    
    def __init__(self, chroma_client, collection_name: str = "langgraph_state"):
        """Initialize the LangGraph adapter.
        
        Args:
            chroma_client: Chroma client instance
            collection_name: Name of the collection to store graph states
        """
        self.client = chroma_client
        self.collection_name = collection_name
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists for storing graph states."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection if it doesn't exist
            self.collection = self.client.create_collection(self.collection_name)
    
    def save_graph_state(
        self,
        graph_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Save a graph state to Chroma.
        
        Args:
            graph_id: Unique identifier for the graph
            state: The state dictionary to save
            metadata: Optional metadata about the state
        
        Returns:
            The ID of the saved state
        """
        state_json = json.dumps(state)
        meta = metadata or {}
        meta.update({
            "graph_id": graph_id,
            "type": "langgraph_state"
        })
        
        self.collection.upsert(
            ids=[graph_id],
            documents=[state_json],
            metadatas=[meta]
        )
        return graph_id
    
    def load_graph_state(self, graph_id: str) -> Optional[Dict[str, Any]]:
        """Load a graph state from Chroma.
        
        Args:
            graph_id: The ID of the graph state to load
        
        Returns:
            The state dictionary, or None if not found
        """
        try:
            result = self.collection.get(
                ids=[graph_id],
                include=["documents"]
            )
            if result["documents"]:
                return json.loads(result["documents"][0])
            return None
        except Exception:
            return None
    
    def save_checkpoint(
        self,
        graph_id: str,
        checkpoint_id: str,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """Save a checkpoint for a graph execution.
        
        Args:
            graph_id: The graph identifier
            checkpoint_id: Unique checkpoint identifier
            checkpoint_data: The checkpoint data
        
        Returns:
            The checkpoint ID
        """
        checkpoint_json = json.dumps(checkpoint_data)
        full_id = f"{graph_id}_checkpoint_{checkpoint_id}"
        
        self.collection.upsert(
            ids=[full_id],
            documents=[checkpoint_json],
            metadatas=[{
                "graph_id": graph_id,
                "checkpoint_id": checkpoint_id,
                "type": "langgraph_checkpoint"
            }]
        )
        return full_id
    
    def list_checkpoints(self, graph_id: str) -> List[Dict[str, Any]]:
        """List all checkpoints for a graph.
        
        Args:
            graph_id: The graph identifier
        
        Returns:
            List of checkpoint metadata
        """
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"graph_id": graph_id},
                        {"type": "langgraph_checkpoint"}
                    ]
                },
                include=["metadatas"]
            )
            return results.get("metadatas", [])
        except Exception:
            return []
    
    def query_similar_states(
        self,
        query_state: Dict[str, Any],
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Query for similar graph states using semantic search.
        
        Args:
            query_state: The state to use as a query
            n_results: Number of similar states to return
        
        Returns:
            List of similar states with metadata
        """
        query_json = json.dumps(query_state)
        results = self.collection.query(
            query_texts=[query_json],
            n_results=n_results,
            where={"type": "langgraph_state"}
        )
        
        similar_states = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            similar_states.append({
                "state": json.loads(doc),
                "metadata": results.get("metadatas", [[]])[0][i],
                "distance": results.get("distances", [[]])[0][i]
            })
        
        return similar_states
