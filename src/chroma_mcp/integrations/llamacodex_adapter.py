"""LlamaCodex integration adapter for Chroma MCP.

This module provides integration for code-related LLM tools, enabling
code embedding, search, and analysis with Chroma vector database.
"""

from typing import Dict, List, Any, Optional
import json


class LlamaCodexAdapter:
    """Adapter for integrating code analysis and storage with Chroma MCP.
    
    This adapter enables:
    - Code snippet storage and retrieval
    - Semantic code search
    - Code documentation embedding
    - Code similarity analysis
    """
    
    def __init__(self, chroma_client, collection_name: str = "code_repository"):
        """Initialize the LlamaCodex adapter.
        
        Args:
            chroma_client: Chroma client instance
            collection_name: Name of the collection to store code
        """
        self.client = chroma_client
        self.collection_name = collection_name
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure the collection exists for storing code."""
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            # Create collection if it doesn't exist
            self.collection = self.client.create_collection(self.collection_name)
    
    def store_code_snippet(
        self,
        code_id: str,
        code: str,
        language: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a code snippet in Chroma.
        
        Args:
            code_id: Unique identifier for the code snippet
            code: The code content
            language: Programming language
            metadata: Optional metadata (file path, author, etc.)
        
        Returns:
            The ID of the stored code
        """
        meta = metadata or {}
        meta.update({
            "language": language,
            "type": "code_snippet"
        })
        
        self.collection.upsert(
            ids=[code_id],
            documents=[code],
            metadatas=[meta]
        )
        return code_id
    
    def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for code snippets using semantic search.
        
        Args:
            query: Natural language or code query
            language: Optional language filter
            n_results: Number of results to return
        
        Returns:
            List of matching code snippets with metadata
        """
        where_filter = {"type": "code_snippet"}
        if language:
            where_filter["language"] = language
        
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_filter
        )
        
        code_results = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            code_results.append({
                "code": doc,
                "metadata": results.get("metadatas", [[]])[0][i],
                "distance": results.get("distances", [[]])[0][i]
            })
        
        return code_results
    
    def store_code_documentation(
        self,
        doc_id: str,
        documentation: str,
        associated_code_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store code documentation.
        
        Args:
            doc_id: Unique identifier for the documentation
            documentation: The documentation content
            associated_code_id: Optional ID of associated code snippet
            metadata: Optional metadata
        
        Returns:
            The ID of the stored documentation
        """
        meta = metadata or {}
        meta.update({
            "type": "code_documentation"
        })
        if associated_code_id:
            meta["associated_code_id"] = associated_code_id
        
        self.collection.upsert(
            ids=[doc_id],
            documents=[documentation],
            metadatas=[meta]
        )
        return doc_id
    
    def find_similar_code(
        self,
        code: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar code snippets.
        
        Args:
            code: The code to find similar snippets for
            n_results: Number of similar snippets to return
        
        Returns:
            List of similar code snippets
        """
        results = self.collection.query(
            query_texts=[code],
            n_results=n_results,
            where={"type": "code_snippet"}
        )
        
        similar_code = []
        for i, doc in enumerate(results.get("documents", [[]])[0]):
            similar_code.append({
                "code": doc,
                "metadata": results.get("metadatas", [[]])[0][i],
                "similarity_score": 1 - results.get("distances", [[]])[0][i]
            })
        
        return similar_code
    
    def get_code_by_language(self, language: str) -> List[Dict[str, Any]]:
        """Get all code snippets for a specific language.
        
        Args:
            language: Programming language
        
        Returns:
            List of code snippets
        """
        try:
            results = self.collection.get(
                where={
                    "$and": [
                        {"type": "code_snippet"},
                        {"language": language}
                    ]
                },
                include=["documents", "metadatas"]
            )
            
            code_snippets = []
            for i, doc in enumerate(results.get("documents", [])):
                code_snippets.append({
                    "code": doc,
                    "metadata": results.get("metadatas", [])[i]
                })
            
            return code_snippets
        except Exception:
            return []
