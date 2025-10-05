"""n8n workflow integration adapter for Chroma MCP.

This module provides extensibility hooks for n8n workflow automation,
enabling Chroma to be used within n8n workflows.
"""

from typing import Dict, List, Any, Optional, Callable
import json


class N8NAdapter:
    """Adapter for n8n workflow integration with Chroma MCP.
    
    This adapter enables:
    - Webhook endpoints for workflow triggers
    - Data transformation for n8n nodes
    - Workflow state persistence
    - Custom node extensibility
    """
    
    def __init__(self, chroma_client, collection_name: str = "n8n_workflows"):
        """Initialize the n8n adapter.
        
        Args:
            chroma_client: Chroma client instance
            collection_name: Name of the collection to store workflow data
        """
        self.client = chroma_client
        self.collection_name = collection_name
        self._ensure_collection()
        self.webhook_handlers: Dict[str, Callable] = {}
    
    def _ensure_collection(self):
        """Ensure the collection exists for storing workflow data."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection if it doesn't exist
            self.collection = self.client.create_collection(self.collection_name)
    
    def register_webhook(
        self,
        webhook_name: str,
        handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    ):
        """Register a webhook handler for n8n workflow triggers.
        
        Args:
            webhook_name: Name of the webhook
            handler: Function to handle webhook data
        """
        self.webhook_handlers[webhook_name] = handler
    
    def trigger_webhook(
        self,
        webhook_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a registered webhook.
        
        Args:
            webhook_name: Name of the webhook to trigger
            data: Data to pass to the handler
        
        Returns:
            Result from the webhook handler
        """
        if webhook_name not in self.webhook_handlers:
            raise ValueError(f"Webhook '{webhook_name}' not registered")
        
        handler = self.webhook_handlers[webhook_name]
        return handler(data)
    
    def store_workflow_state(
        self,
        workflow_id: str,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store workflow execution state.
        
        Args:
            workflow_id: Unique workflow identifier
            state: Workflow state data
            metadata: Optional metadata
        
        Returns:
            The ID of the stored state
        """
        state_json = json.dumps(state)
        meta = metadata or {}
        meta.update({
            "workflow_id": workflow_id,
            "type": "workflow_state"
        })
        
        self.collection.upsert(
            ids=[workflow_id],
            documents=[state_json],
            metadatas=[meta]
        )
        return workflow_id
    
    def load_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Load workflow execution state.
        
        Args:
            workflow_id: The workflow identifier
        
        Returns:
            The workflow state, or None if not found
        """
        try:
            result = self.collection.get(
                ids=[workflow_id],
                include=["documents"]
            )
            if result["documents"]:
                return json.loads(result["documents"][0])
            return None
        except Exception:
            return None
    
    def store_workflow_data(
        self,
        data_id: str,
        data: str,
        workflow_id: str,
        node_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store data from a workflow node.
        
        Args:
            data_id: Unique data identifier
            data: The data content
            workflow_id: Associated workflow ID
            node_name: Optional node name that produced the data
            metadata: Optional metadata
        
        Returns:
            The ID of the stored data
        """
        meta = metadata or {}
        meta.update({
            "workflow_id": workflow_id,
            "type": "workflow_data"
        })
        if node_name:
            meta["node_name"] = node_name
        
        self.collection.upsert(
            ids=[data_id],
            documents=[data],
            metadatas=[meta]
        )
        return data_id
    
    def query_workflow_data(
        self,
        query: str,
        workflow_id: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Query workflow data using semantic search.
        
        Args:
            query: Query string
            workflow_id: Optional workflow filter
            n_results: Number of results to return
        
        Returns:
            List of matching workflow data
        """
        where_filter = {"type": "workflow_data"}
        if workflow_id:
            where_filter["workflow_id"] = workflow_id
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        workflow_data = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            workflow_data.append({
                "data": doc,
                "metadata": results.get("metadatas", [[]])[0][i],
                "relevance": 1 - results.get("distances", [[]])[0][i]
            })
        
        return workflow_data
    
    def transform_for_n8n(
        self,
        chroma_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform Chroma results for n8n workflow consumption.
        
        Args:
            chroma_result: Result from Chroma query
        
        Returns:
            Transformed data suitable for n8n
        """
        # Transform Chroma result format to n8n-friendly format
        n8n_data = {
            "json": {},
            "binary": {}
        }
        
        if "documents" in chroma_result:
            n8n_data["json"]["documents"] = chroma_result["documents"]
        
        if "metadatas" in chroma_result:
            n8n_data["json"]["metadatas"] = chroma_result["metadatas"]
        
        if "distances" in chroma_result:
            n8n_data["json"]["distances"] = chroma_result["distances"]
        
        if "ids" in chroma_result:
            n8n_data["json"]["ids"] = chroma_result["ids"]
        
        return n8n_data
    
    def transform_from_n8n(
        self,
        n8n_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Transform n8n data for Chroma storage.
        
        Args:
            n8n_data: Data from n8n workflow
        
        Returns:
            Transformed data for Chroma
        """
        # Extract the json data from n8n format
        if "json" in n8n_data:
            return n8n_data["json"]
        return n8n_data
    
    def create_workflow_trigger(
        self,
        trigger_name: str,
        trigger_condition: Callable[[Dict[str, Any]], bool],
        action: Callable[[Dict[str, Any]], None]
    ):
        """Create a custom workflow trigger.
        
        Args:
            trigger_name: Name of the trigger
            trigger_condition: Function to evaluate if trigger should fire
            action: Action to execute when triggered
        """
        def webhook_handler(data: Dict[str, Any]) -> Dict[str, Any]:
            if trigger_condition(data):
                action(data)
                return {"status": "triggered", "trigger": trigger_name}
            return {"status": "not_triggered", "trigger": trigger_name}
        
        self.register_webhook(trigger_name, webhook_handler)
