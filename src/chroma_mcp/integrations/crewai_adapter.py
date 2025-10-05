"""CrewAI integration adapter for Chroma MCP.

This module provides integration with CrewAI for orchestrating role-playing
AI agents with persistent memory backed by Chroma vector database.
"""

from typing import Dict, List, Any, Optional
import json
import time


class CrewAIAdapter:
    """Adapter for integrating CrewAI with Chroma MCP.
    
    This adapter enables:
    - Agent memory persistence
    - Multi-agent conversation history
    - Task and goal tracking
    - Agent knowledge sharing
    """
    
    def __init__(self, chroma_client, collection_name: str = "crewai_memory"):
        """Initialize the CrewAI adapter.
        
        Args:
            chroma_client: Chroma client instance
            collection_name: Name of the collection to store agent memory
        """
        self.client = chroma_client
        self.collection_name = collection_name
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists for storing agent memory."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection if it doesn't exist
            self.collection = self.client.create_collection(self.collection_name)
    
    def store_agent_memory(
        self,
        agent_id: str,
        memory_content: str,
        memory_type: str = "experience",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store agent memory in Chroma.
        
        Args:
            agent_id: Unique identifier for the agent
            memory_content: The memory content
            memory_type: Type of memory (experience, knowledge, conversation, etc.)
            metadata: Optional metadata
        
        Returns:
            The ID of the stored memory
        """
        memory_id = f"{agent_id}_{int(time.time() * 1000)}"
        meta = metadata or {}
        meta.update({
            "agent_id": agent_id,
            "memory_type": memory_type,
            "type": "agent_memory",
            "timestamp": time.time()
        })
        
        self.collection.add(
            ids=[memory_id],
            documents=[memory_content],
            metadatas=[meta]
        )
        return memory_id
    
    def retrieve_agent_memories(
        self,
        agent_id: str,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories for an agent.
        
        Args:
            agent_id: The agent identifier
            query: Optional semantic query for memory retrieval
            memory_type: Optional filter by memory type
            n_results: Number of memories to retrieve
        
        Returns:
            List of relevant memories
        """
        where_filter = {
            "$and": [
                {"agent_id": agent_id},
                {"type": "agent_memory"}
            ]
        }
        if memory_type:
            where_filter["$and"].append({"memory_type": memory_type})
        
        if query:
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter
            )
            
            memories = []
            for i, doc in enumerate(results.get("documents", [[]])[0]):
                memories.append({
                    "content": doc,
                    "metadata": results.get("metadatas", [[]])[0][i],
                    "relevance": 1 - results.get("distances", [[]])[0][i]
                })
        else:
            results = self.collection.get(
                where=where_filter,
                limit=n_results,
                include=["documents", "metadatas"]
            )
            
            memories = []
            for i, doc in enumerate(results.get("documents", [])):
                memories.append({
                    "content": doc,
                    "metadata": results.get("metadatas", [])[i]
                })
        
        return memories
    
    def store_task_result(
        self,
        task_id: str,
        agent_id: str,
        result: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a task result.
        
        Args:
            task_id: Unique task identifier
            agent_id: Agent who completed the task
            result: Task result
            metadata: Optional metadata
        
        Returns:
            The ID of the stored result
        """
        meta = metadata or {}
        meta.update({
            "task_id": task_id,
            "agent_id": agent_id,
            "type": "task_result",
            "timestamp": time.time()
        })
        
        self.collection.upsert(
            ids=[task_id],
            documents=[result],
            metadatas=[meta]
        )
        return task_id
    
    def store_conversation(
        self,
        conversation_id: str,
        speaker_id: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a conversation message.
        
        Args:
            conversation_id: Conversation identifier
            speaker_id: ID of the agent speaking
            message: The message content
            metadata: Optional metadata
        
        Returns:
            The ID of the stored message
        """
        message_id = f"{conversation_id}_{speaker_id}_{int(time.time() * 1000)}"
        meta = metadata or {}
        meta.update({
            "conversation_id": conversation_id,
            "speaker_id": speaker_id,
            "type": "conversation",
            "timestamp": time.time()
        })
        
        self.collection.add(
            ids=[message_id],
            documents=[message],
            metadatas=[meta]
        )
        return message_id
    
    def get_conversation_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history.
        
        Args:
            conversation_id: The conversation identifier
            limit: Maximum number of messages to retrieve
        
        Returns:
            List of conversation messages
        """
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"conversation_id": conversation_id},
                        {"type": "conversation"}
                    ]
                },
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            messages = []
            for i, doc in enumerate(results.get("documents", [])):
                messages.append({
                    "message": doc,
                    "metadata": results.get("metadatas", [])[i]
                })
            
            # Sort by timestamp
            messages.sort(key=lambda x: x["metadata"].get("timestamp", 0))
            return messages
        except Exception:
            return []
    
    def share_knowledge(
        self,
        knowledge_id: str,
        knowledge_content: str,
        source_agent_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Share knowledge among agents.
        
        Args:
            knowledge_id: Unique knowledge identifier
            knowledge_content: The knowledge to share
            source_agent_id: Agent sharing the knowledge
            metadata: Optional metadata
        
        Returns:
            The ID of the shared knowledge
        """
        meta = metadata or {}
        meta.update({
            "source_agent_id": source_agent_id,
            "type": "shared_knowledge",
            "timestamp": time.time()
        })
        
        self.collection.upsert(
            ids=[knowledge_id],
            documents=[knowledge_content],
            metadatas=[meta]
        )
        return knowledge_id
    
    def query_shared_knowledge(
        self,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Query shared knowledge across agents.
        
        Args:
            query: Query for knowledge retrieval
            n_results: Number of results to return
        
        Returns:
            List of relevant knowledge items
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"type": "shared_knowledge"}
        )
        
        knowledge_items = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            knowledge_items.append({
                "content": doc,
                "metadata": results.get("metadatas", [[]])[0][i],
                "relevance": 1 - results.get("distances", [[]])[0][i]
            })
        
        return knowledge_items
