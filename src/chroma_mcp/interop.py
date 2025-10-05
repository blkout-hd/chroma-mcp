"""
Interoperability layer for external vector databases (Weaviate, Qdrant).
Provides seamless data exchange and offloading capabilities.
"""
from typing import Dict, List, Optional, Any
import os
from dotenv import load_dotenv

# Optional imports for interoperability
try:
    import weaviate
    from weaviate.classes.init import Auth
    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False


class InteropManager:
    """Manages interoperability with external vector databases."""
    
    def __init__(self):
        load_dotenv()
        self._weaviate_client = None
        self._qdrant_client = None
        
    def get_weaviate_client(self) -> Optional[Any]:
        """Get or create Weaviate client."""
        if not WEAVIATE_AVAILABLE:
            raise ImportError("Weaviate client not available. Install with: pip install weaviate-client")
        
        if self._weaviate_client is None:
            weaviate_url = os.getenv('WEAVIATE_URL', 'http://localhost:8080')
            weaviate_api_key = os.getenv('WEAVIATE_API_KEY')
            
            if weaviate_api_key:
                auth_config = Auth.api_key(weaviate_api_key)
                self._weaviate_client = weaviate.connect_to_wcs(
                    cluster_url=weaviate_url,
                    auth_credentials=auth_config
                )
            else:
                self._weaviate_client = weaviate.connect_to_local(host=weaviate_url)
                
        return self._weaviate_client
    
    def get_qdrant_client(self) -> Optional[Any]:
        """Get or create Qdrant client."""
        if not QDRANT_AVAILABLE:
            raise ImportError("Qdrant client not available. Install with: pip install qdrant-client")
        
        if self._qdrant_client is None:
            qdrant_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
            qdrant_api_key = os.getenv('QDRANT_API_KEY')
            
            self._qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key
            )
            
        return self._qdrant_client
    
    async def sync_to_weaviate(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> Dict:
        """Sync data from Chroma to Weaviate."""
        if not WEAVIATE_AVAILABLE:
            return {"error": "Weaviate not available"}
        
        client = self.get_weaviate_client()
        
        # Create collection if it doesn't exist
        try:
            collection = client.collections.get(collection_name)
        except:
            collection = client.collections.create(
                name=collection_name,
                properties=[
                    {"name": "content", "dataType": ["text"]},
                ]
            )
        
        # Add objects
        objects = []
        for i, (doc, emb) in enumerate(zip(documents, embeddings)):
            obj = {
                "content": doc,
                "vector": emb
            }
            if metadatas and i < len(metadatas):
                obj.update(metadatas[i])
            if ids and i < len(ids):
                obj["id"] = ids[i]
            objects.append(obj)
        
        # Batch insert
        with collection.batch.dynamic() as batch:
            for obj in objects:
                batch.add_object(properties=obj)
        
        return {"status": "success", "synced": len(objects)}
    
    async def sync_to_qdrant(
        self,
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict]] = None,
        ids: Optional[List[str]] = None
    ) -> Dict:
        """Sync data from Chroma to Qdrant."""
        if not QDRANT_AVAILABLE:
            return {"error": "Qdrant not available"}
        
        client = self.get_qdrant_client()
        
        # Create collection if it doesn't exist
        try:
            client.get_collection(collection_name)
        except:
            vector_size = len(embeddings[0]) if embeddings else 384
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
        
        # Prepare points
        points = []
        for i, (doc, emb) in enumerate(zip(documents, embeddings)):
            point_id = ids[i] if ids and i < len(ids) else i
            payload = {"content": doc}
            if metadatas and i < len(metadatas):
                payload.update(metadatas[i])
            
            points.append(
                PointStruct(
                    id=point_id,
                    vector=emb,
                    payload=payload
                )
            )
        
        # Upsert points
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return {"status": "success", "synced": len(points)}
    
    async def offload_to_qdrant(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5
    ) -> Dict:
        """Offload query to Qdrant for load balancing."""
        if not QDRANT_AVAILABLE:
            return {"error": "Qdrant not available"}
        
        client = self.get_qdrant_client()
        
        results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return {
            "results": [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]
        }


# Global interop manager instance
_interop_manager = None

def get_interop_manager() -> InteropManager:
    """Get or create the global interop manager."""
    global _interop_manager
    if _interop_manager is None:
        _interop_manager = InteropManager()
    return _interop_manager
