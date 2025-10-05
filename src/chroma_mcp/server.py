from typing import Dict, List, TypedDict, Union, Optional, Any
from enum import Enum
import chromadb
from mcp.server.fastmcp import FastMCP
import os
from dotenv import load_dotenv
import argparse
from chromadb.config import Settings
import ssl
import uuid
import time
import json
from typing_extensions import TypedDict


from chromadb.api.collection_configuration import (
    CreateCollectionConfiguration
    )
from chromadb.api import EmbeddingFunction
from chromadb.utils.embedding_functions import (
    DefaultEmbeddingFunction,
    CohereEmbeddingFunction,
    OpenAIEmbeddingFunction,
    JinaEmbeddingFunction,
    VoyageAIEmbeddingFunction,
    RoboflowEmbeddingFunction,
)

# Import new modules
from .cache import get_memory_cache
from .health import get_health_monitor
from .maintenance import get_maintenance_scheduler, get_auto_scaler
from .security import get_encryption_manager
from .swarm import get_swarm_tracker, get_code_smell_monitor
from .entity_mapper import get_er_mapper

# Optional imports
try:
    from .umap_utils import get_umap_reducer
    UMAP_AVAILABLE = True
except ImportError:
    UMAP_AVAILABLE = False

try:
    from .interop import get_interop_manager
    INTEROP_AVAILABLE = True
except ImportError:
    INTEROP_AVAILABLE = False

# Initialize FastMCP server
mcp = FastMCP("chroma")

# Global variables
_chroma_client = None

def create_parser():
    """Create and return the argument parser."""
    parser = argparse.ArgumentParser(description='FastMCP server for Chroma DB')
    parser.add_argument('--client-type', 
                       choices=['http', 'cloud', 'persistent', 'ephemeral'],
                       default=os.getenv('CHROMA_CLIENT_TYPE', 'ephemeral'),
                       help='Type of Chroma client to use')
    parser.add_argument('--data-dir',
                       default=os.getenv('CHROMA_DATA_DIR'),
                       help='Directory for persistent client data (only used with persistent client)')
    parser.add_argument('--host', 
                       help='Chroma host (required for http client)', 
                       default=os.getenv('CHROMA_HOST'))
    parser.add_argument('--port', 
                       help='Chroma port (optional for http client)', 
                       default=os.getenv('CHROMA_PORT'))
    parser.add_argument('--custom-auth-credentials',
                       help='Custom auth credentials (optional for http client)', 
                       default=os.getenv('CHROMA_CUSTOM_AUTH_CREDENTIALS'))
    parser.add_argument('--tenant', 
                       help='Chroma tenant (optional for http client)', 
                       default=os.getenv('CHROMA_TENANT'))
    parser.add_argument('--database', 
                       help='Chroma database (required if tenant is provided)', 
                       default=os.getenv('CHROMA_DATABASE'))
    parser.add_argument('--api-key', 
                       help='Chroma API key (required if tenant is provided)', 
                       default=os.getenv('CHROMA_API_KEY'))
    parser.add_argument('--ssl', 
                       help='Use SSL (optional for http client)', 
                       type=lambda x: x.lower() in ['true', 'yes', '1', 't', 'y'],
                       default=os.getenv('CHROMA_SSL', 'true').lower() in ['true', 'yes', '1', 't', 'y'])
    parser.add_argument('--dotenv-path', 
                       help='Path to .env file', 
                       default=os.getenv('CHROMA_DOTENV_PATH', '.chroma_env'))
    return parser

def get_chroma_client(args=None):
    """Get or create the global Chroma client instance."""
    global _chroma_client
    if _chroma_client is None:
        if args is None:
            # Create parser and parse args if not provided
            parser = create_parser()
            args = parser.parse_args()
        
        # Load environment variables from .env file if it exists
        load_dotenv(dotenv_path=args.dotenv_path)
        if args.client_type == 'http':
            if not args.host:
                raise ValueError("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
            
            settings = Settings()
            if args.custom_auth_credentials:
                settings = Settings(
                    chroma_client_auth_provider="chromadb.auth.basic_authn.BasicAuthClientProvider",
                    chroma_client_auth_credentials=args.custom_auth_credentials
                )
            
            # Handle SSL configuration
            try:
                _chroma_client = chromadb.HttpClient(
                    host=args.host,
                    port=args.port if args.port else None,
                    ssl=args.ssl,
                    settings=settings
                )
            except ssl.SSLError as e:
                print(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                print(f"Error connecting to HTTP client: {str(e)}")
                raise
            
        elif args.client_type == 'cloud':
            if not args.tenant:
                raise ValueError("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
            if not args.database:
                raise ValueError("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
            if not args.api_key:
                raise ValueError("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
            
            try:
                _chroma_client = chromadb.HttpClient(
                    host="api.trychroma.com",
                    ssl=True,  # Always use SSL for cloud
                    tenant=args.tenant,
                    database=args.database,
                    headers={
                        'x-chroma-token': args.api_key
                    }
                )
            except ssl.SSLError as e:
                print(f"SSL connection failed: {str(e)}")
                raise
            except Exception as e:
                print(f"Error connecting to cloud client: {str(e)}")
                raise
                
        elif args.client_type == 'persistent':
            if not args.data_dir:
                raise ValueError("Data directory must be provided via --data-dir flag when using persistent client")
            _chroma_client = chromadb.PersistentClient(path=args.data_dir)
        else:  # ephemeral
            _chroma_client = chromadb.EphemeralClient()
            
    return _chroma_client

##### Collection Tools #####

@mcp.tool()
async def chroma_list_collections(
    limit: int | None = None,
    offset: int | None = None
) -> List[str]:
    """List all collection names in the Chroma database with pagination support.
    
    Args:
        limit: Optional maximum number of collections to return
        offset: Optional number of collections to skip before returning results
    
    Returns:
        List of collection names or ["__NO_COLLECTIONS_FOUND__"] if database is empty
    """
    client = get_chroma_client()
    try:
        colls = client.list_collections(limit=limit, offset=offset)
        # Safe handling: If colls is None or empty, return a special marker
        if not colls:
            return ["__NO_COLLECTIONS_FOUND__"]
        # Otherwise iterate to get collection names
        return [coll.name for coll in colls]

    except Exception as e:
        raise Exception(f"Failed to list collections: {str(e)}") from e

mcp_known_embedding_functions: Dict[str, EmbeddingFunction] = {
    "default": DefaultEmbeddingFunction,
    "cohere": CohereEmbeddingFunction,
    "openai": OpenAIEmbeddingFunction,
    "jina": JinaEmbeddingFunction,
    "voyageai": VoyageAIEmbeddingFunction,
    "roboflow": RoboflowEmbeddingFunction,
}
@mcp.tool()
async def chroma_create_collection(
    collection_name: str,
    embedding_function_name: str = "default",
    metadata: Dict | None = None,
) -> str:
    """Create a new Chroma collection with configurable HNSW parameters.
    
    Args:
        collection_name: Name of the collection to create
        embedding_function_name: Name of the embedding function to use. Options: 'default', 'cohere', 'openai', 'jina', 'voyageai', 'ollama', 'roboflow'
        metadata: Optional metadata dict to add to the collection
    """
    client = get_chroma_client()
    
    embedding_function = mcp_known_embedding_functions[embedding_function_name]
    
    configuration=CreateCollectionConfiguration(
        embedding_function=embedding_function()
    )
    
    try:
        client.create_collection(
            name=collection_name,
            configuration=configuration,
            metadata=metadata
        )
        config_msg = f" with configuration: {configuration}"
        return f"Successfully created collection {collection_name}{config_msg}"
    except Exception as e:
        raise Exception(f"Failed to create collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_peek_collection(
    collection_name: str,
    limit: int = 5
) -> Dict:
    """Peek at documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to peek into
        limit: Number of documents to peek at
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        results = collection.peek(limit=limit)
        return results
    except Exception as e:
        raise Exception(f"Failed to peek collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_get_collection_info(collection_name: str) -> Dict:
    """Get information about a Chroma collection.
    
    Args:
        collection_name: Name of the collection to get info about
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        
        # Get collection count
        count = collection.count()
        
        # Peek at a few documents
        peek_results = collection.peek(limit=3)
        
        return {
            "name": collection_name,
            "count": count,
            "sample_documents": peek_results
        }
    except Exception as e:
        raise Exception(f"Failed to get collection info for '{collection_name}': {str(e)}") from e
    
@mcp.tool()
async def chroma_get_collection_count(collection_name: str) -> int:
    """Get the number of documents in a Chroma collection.
    
    Args:
        collection_name: Name of the collection to count
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.count()
    except Exception as e:
        raise Exception(f"Failed to get collection count for '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_modify_collection(
    collection_name: str,
    new_name: str | None = None,
    new_metadata: Dict | None = None,
) -> str:
    """Modify a Chroma collection's name or metadata.
    
    Args:
        collection_name: Name of the collection to modify
        new_name: Optional new name for the collection
        new_metadata: Optional new metadata for the collection
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        collection.modify(name=new_name, metadata=new_metadata)
        
        modified_aspects = []
        if new_name:
            modified_aspects.append("name")
        if new_metadata:
            modified_aspects.append("metadata")
        
        return f"Successfully modified collection {collection_name}: updated {' and '.join(modified_aspects)}"
    except Exception as e:
        raise Exception(f"Failed to modify collection '{collection_name}': {str(e)}") from e
    
@mcp.tool()
async def chroma_fork_collection(
    collection_name: str,
    new_collection_name: str,
) -> str:
    """Fork a Chroma collection.
    
    Args:
        collection_name: Name of the collection to fork
        new_collection_name: Name of the new collection to create
        metadata: Optional metadata dict to add to the new collection
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        collection.fork(new_collection_name)
        return f"Successfully forked collection {collection_name} to {new_collection_name}"
    except Exception as e:
        raise Exception(f"Failed to fork collection '{collection_name}': {str(e)}") from e
    
@mcp.tool()
async def chroma_delete_collection(collection_name: str) -> str:
    """Delete a Chroma collection.
    
    Args:
        collection_name: Name of the collection to delete
    """
    client = get_chroma_client()
    try:
        client.delete_collection(collection_name)
        return f"Successfully deleted collection {collection_name}"
    except Exception as e:
        raise Exception(f"Failed to delete collection '{collection_name}': {str(e)}") from e

##### Document Tools #####
@mcp.tool()
async def chroma_add_documents(
    collection_name: str,
    documents: List[str],
    ids: List[str],
    metadatas: List[Dict] | None = None
) -> str:
    """Add documents to a Chroma collection.
    
    Args:
        collection_name: Name of the collection to add documents to
        documents: List of text documents to add
        ids: List of IDs for the documents (required)
        metadatas: Optional list of metadata dictionaries for each document
    """
    if not documents:
        raise ValueError("The 'documents' list cannot be empty.")
    
    if not ids:
        raise ValueError("The 'ids' list is required and cannot be empty.")
    
    # Check if there are empty strings in the ids list
    if any(not id.strip() for id in ids):
        raise ValueError("IDs cannot be empty strings.")
    
    if len(ids) != len(documents):
        raise ValueError(f"Number of ids ({len(ids)}) must match number of documents ({len(documents)}).")

    # Track operation with health monitor
    monitor = get_health_monitor()
    monitor.record_insert(collection_name)
    
    # Track with swarm
    tracker = get_swarm_tracker()
    tracker.track_operation("add", collection_name)
    
    # Check for code smells
    smell_monitor = get_code_smell_monitor()
    smell_monitor.analyze_operation("add", collection_name, {"documents": documents})

    client = get_chroma_client()
    try:
        collection = client.get_or_create_collection(collection_name)
        
        # Check for duplicate IDs
        existing_ids = collection.get(include=[])["ids"]
        duplicate_ids = [id for id in ids if id in existing_ids]
        
        if duplicate_ids:
            raise ValueError(
                f"The following IDs already exist in collection '{collection_name}': {duplicate_ids}. "
                f"Use 'chroma_update_documents' to update existing documents."
            )
        
        result = collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        # Check the return value
        if result and isinstance(result, dict):
            # If the return value is a dictionary, it may contain success information
            if 'success' in result and not result['success']:
                raise Exception(f"Failed to add documents: {result.get('error', 'Unknown error')}")
            
            # If the return value contains the actual number added
            if 'count' in result:
                return f"Successfully added {result['count']} documents to collection {collection_name}"
        
        # Default return
        return f"Successfully added {len(documents)} documents to collection {collection_name}, result is {result}"
    except Exception as e:
        monitor.record_error(str(e))
        raise Exception(f"Failed to add documents to collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_query_documents(
    collection_name: str,
    query_texts: List[str],
    n_results: int = 5,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas", "distances"]
) -> Dict:
    """Query documents from a Chroma collection with advanced filtering.
    
    Args:
        collection_name: Name of the collection to query
        query_texts: List of query texts to search for
        n_results: Number of results to return per query
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
               Examples:
               - Contains: {"$contains": "value"}
               - Not contains: {"$not_contains": "value"}
               - Regex: {"$regex": "[a-z]+"}
               - Not regex: {"$not_regex": "[a-z]+"}
               - Logical AND: {"$and": [{"$contains": "value1"}, {"$not_regex": "[a-z]+"}]}
               - Logical OR: {"$or": [{"$regex": "[a-z]+"}, {"$not_contains": "value2"}]}
        include: List of what to include in response. By default, this will include documents, metadatas, and distances.
    """
    if not query_texts:
        raise ValueError("The 'query_texts' list cannot be empty.")

    # Track operation with swarm and health monitor
    monitor = get_health_monitor()
    monitor.record_query(collection_name)
    
    tracker = get_swarm_tracker()
    tracker.track_operation("query", collection_name, str(query_texts))
    
    # Check for code smells
    smell_monitor = get_code_smell_monitor()
    smell_monitor.analyze_operation("query", collection_name, {"n_results": n_results})

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.query(
            query_texts=query_texts,
            n_results=n_results,
            where=where,
            where_document=where_document,
            include=include
        )
    except Exception as e:
        monitor.record_error(str(e))
        raise Exception(f"Failed to query documents from collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_get_documents(
    collection_name: str,
    ids: List[str] | None = None,
    where: Dict | None = None,
    where_document: Dict | None = None,
    include: List[str] = ["documents", "metadatas"],
    limit: int | None = None,
    offset: int | None = None
) -> Dict:
    """Get documents from a Chroma collection with optional filtering.
    
    Args:
        collection_name: Name of the collection to get documents from
        ids: Optional list of document IDs to retrieve
        where: Optional metadata filters using Chroma's query operators
               Examples:
               - Simple equality: {"metadata_field": "value"}
               - Comparison: {"metadata_field": {"$gt": 5}}
               - Logical AND: {"$and": [{"field1": {"$eq": "value1"}}, {"field2": {"$gt": 5}}]}
               - Logical OR: {"$or": [{"field1": {"$eq": "value1"}}, {"field1": {"$eq": "value2"}}]}
        where_document: Optional document content filters
               Examples:
               - Contains: {"$contains": "value"}
               - Not contains: {"$not_contains": "value"}
               - Regex: {"$regex": "[a-z]+"}
               - Not regex: {"$not_regex": "[a-z]+"}
               - Logical AND: {"$and": [{"$contains": "value1"}, {"$not_regex": "[a-z]+"}]}
               - Logical OR: {"$or": [{"$regex": "[a-z]+"}, {"$not_contains": "value2"}]}
        include: List of what to include in response. By default, this will include documents, and metadatas.
        limit: Optional maximum number of documents to return
        offset: Optional number of documents to skip before returning results
    
    Returns:
        Dictionary containing the matching documents, their IDs, and requested includes
    """
    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
        return collection.get(
            ids=ids,
            where=where,
            where_document=where_document,
            include=include,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise Exception(f"Failed to get documents from collection '{collection_name}': {str(e)}") from e

@mcp.tool()
async def chroma_update_documents(
    collection_name: str,
    ids: List[str],
    embeddings: List[List[float]] | None = None,
    metadatas: List[Dict] | None = None,
    documents: List[str] | None = None
) -> str:
    """Update documents in a Chroma collection.

    Args:
        collection_name: Name of the collection to update documents in
        ids: List of document IDs to update (required)
        embeddings: Optional list of new embeddings for the documents.
                    Must match length of ids if provided.
        metadatas: Optional list of new metadata dictionaries for the documents.
                   Must match length of ids if provided.
        documents: Optional list of new text documents.
                   Must match length of ids if provided.

    Returns:
        A confirmation message indicating the number of documents updated.

    Raises:
        ValueError: If 'ids' is empty or if none of 'embeddings', 'metadatas',
                    or 'documents' are provided, or if the length of provided
                    update lists does not match the length of 'ids'.
        Exception: If the collection does not exist or if the update operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    if embeddings is None and metadatas is None and documents is None:
        raise ValueError(
            "At least one of 'embeddings', 'metadatas', or 'documents' "
            "must be provided for update."
        )

    # Ensure provided lists match the length of ids if they are not None
    if embeddings is not None and len(embeddings) != len(ids):
        raise ValueError("Length of 'embeddings' list must match length of 'ids' list.")
    if metadatas is not None and len(metadatas) != len(ids):
        raise ValueError("Length of 'metadatas' list must match length of 'ids' list.")
    if documents is not None and len(documents) != len(ids):
        raise ValueError("Length of 'documents' list must match length of 'ids' list.")


    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(
            f"Failed to get collection '{collection_name}': {str(e)}"
        ) from e

    # Prepare arguments for update, excluding None values at the top level
    update_args = {
        "ids": ids,
        "embeddings": embeddings,
        "metadatas": metadatas,
        "documents": documents,
    }
    kwargs = {k: v for k, v in update_args.items() if v is not None}

    try:
        collection.update(**kwargs)
        return (
            f"Successfully processed update request for {len(ids)} documents in "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to update documents in collection '{collection_name}': {str(e)}"
        ) from e

@mcp.tool()
async def chroma_delete_documents(
    collection_name: str,
    ids: List[str]
) -> str:
    """Delete documents from a Chroma collection.

    Args:
        collection_name: Name of the collection to delete documents from
        ids: List of document IDs to delete

    Returns:
        A confirmation message indicating the number of documents deleted.

    Raises:
        ValueError: If 'ids' is empty
        Exception: If the collection does not exist or if the delete operation fails.
    """
    if not ids:
        raise ValueError("The 'ids' list cannot be empty.")

    client = get_chroma_client()
    try:
        collection = client.get_collection(collection_name)
    except Exception as e:
        raise Exception(
            f"Failed to get collection '{collection_name}': {str(e)}"
        ) from e

    try:
        collection.delete(ids=ids)
        return (
            f"Successfully deleted {len(ids)} documents from "
            f"collection '{collection_name}'. Note: Non-existent IDs are ignored by ChromaDB."
        )
    except Exception as e:
        raise Exception(
            f"Failed to delete documents from collection '{collection_name}': {str(e)}"
        ) from e

def validate_thought_data(input_data: Dict) -> Dict:
    """Validate thought data structure."""
    if not input_data.get("sessionId"):
        raise ValueError("Invalid sessionId: must be provided")
    if not input_data.get("thought") or not isinstance(input_data.get("thought"), str):
        raise ValueError("Invalid thought: must be a string")
    if not input_data.get("thoughtNumber") or not isinstance(input_data.get("thoughtNumber"), int):
            raise ValueError("Invalid thoughtNumber: must be a number")
    if not input_data.get("totalThoughts") or not isinstance(input_data.get("totalThoughts"), int):
        raise ValueError("Invalid totalThoughts: must be a number")
    if not isinstance(input_data.get("nextThoughtNeeded"), bool):
        raise ValueError("Invalid nextThoughtNeeded: must be a boolean")
        
    return {
        "sessionId": input_data.get("sessionId"),
        "thought": input_data.get("thought"),
        "thoughtNumber": input_data.get("thoughtNumber"),
        "totalThoughts": input_data.get("totalThoughts"),
        "nextThoughtNeeded": input_data.get("nextThoughtNeeded"),
        "isRevision": input_data.get("isRevision"),
        "revisesThought": input_data.get("revisesThought"),
        "branchFromThought": input_data.get("branchFromThought"),
        "branchId": input_data.get("branchId"),
        "needsMoreThoughts": input_data.get("needsMoreThoughts"),
    }

##### Advanced Features Tools #####

@mcp.tool()
async def chroma_cache_query(
    collection_name: str,
    query: str,
    project_id: str | None = None,
    ttl: int | None = None
) -> str:
    """
    Cache a query for passive short-term memory.
    
    Args:
        collection_name: Collection name
        query: Query string to cache
        project_id: Optional project ID for isolated caching
        ttl: Time to live in seconds (default: 3600)
    """
    cache = get_memory_cache()
    result = {"cached": True, "timestamp": time.time()}
    key = cache.cache_query_result(query, result, collection_name, project_id, ttl)
    return f"Query cached with key: {key}"

@mcp.tool()
async def chroma_get_cache_stats(project_id: str | None = None) -> Dict:
    """
    Get cache statistics.
    
    Args:
        project_id: Optional project ID
    """
    cache = get_memory_cache()
    return cache.get_stats(project_id)

@mcp.tool()
async def chroma_health_check() -> Dict:
    """Get comprehensive health status of the Chroma MCP server."""
    monitor = get_health_monitor()
    return monitor.get_health_status()

@mcp.tool()
async def chroma_get_scaling_recommendation() -> Dict:
    """Get intelligent scaling recommendations based on current metrics."""
    monitor = get_health_monitor()
    scaler = get_auto_scaler()
    metrics = monitor.get_system_metrics()
    return scaler.analyze_and_scale(metrics)

@mcp.tool()
async def chroma_get_hot_trails(min_strength: float = 0.5, limit: int = 10) -> List[Dict]:
    """
    Get hot pheromone trails (frequently accessed patterns).
    
    Args:
        min_strength: Minimum trail strength (0.0-1.0)
        limit: Maximum number of trails to return
    """
    tracker = get_swarm_tracker()
    return tracker.get_hot_trails(min_strength, limit)

@mcp.tool()
async def chroma_get_code_smells() -> Dict:
    """Get report of detected code smells and anti-patterns."""
    monitor = get_code_smell_monitor()
    return monitor.get_smell_report()

@mcp.tool()
async def chroma_encrypt_documents(
    documents: List[str],
    metadatas: List[Dict] | None = None,
    project_id: str | None = None
) -> Dict:
    """
    Selectively encrypt documents based on sensitive information detection.
    
    Args:
        documents: List of documents to potentially encrypt
        metadatas: Optional list of metadata dicts
        project_id: Optional project ID
    """
    encryption_mgr = get_encryption_manager()
    return encryption_mgr.batch_selective_encrypt(documents, metadatas, project_id)

@mcp.tool()
async def chroma_add_entity(
    entity_id: str,
    entity_type: str,
    properties: Dict | None = None
) -> Dict:
    """
    Add an entity to the relationship graph.
    
    Args:
        entity_id: Unique entity ID
        entity_type: Type of entity
        properties: Optional entity properties
    """
    mapper = get_er_mapper()
    entity = mapper.add_entity(entity_id, entity_type, properties)
    return entity.to_dict()

@mcp.tool()
async def chroma_add_relationship(
    relationship_id: str,
    source_id: str,
    target_id: str,
    relationship_type: str,
    properties: Dict | None = None
) -> Dict:
    """
    Add a relationship between entities.
    
    Args:
        relationship_id: Unique relationship ID
        source_id: Source entity ID
        target_id: Target entity ID
        relationship_type: Type of relationship
        properties: Optional relationship properties
    """
    mapper = get_er_mapper()
    rel = mapper.add_relationship(relationship_id, source_id, target_id, relationship_type, properties)
    if rel:
        return rel.to_dict()
    return {"error": "Failed to create relationship. Entities may not exist."}

@mcp.tool()
async def chroma_get_graph_stats() -> Dict:
    """Get entity relationship graph statistics."""
    mapper = get_er_mapper()
    return mapper.get_statistics()

@mcp.tool()
async def chroma_find_entity_path(
    source_id: str,
    target_id: str,
    max_depth: int = 5
) -> Dict:
    """
    Find path between two entities.
    
    Args:
        source_id: Source entity ID
        target_id: Target entity ID
        max_depth: Maximum path depth
    """
    mapper = get_er_mapper()
    path = mapper.find_path(source_id, target_id, max_depth)
    if path:
        return {"found": True, "path": path, "length": len(path)}
    return {"found": False, "path": None}

if INTEROP_AVAILABLE:
    @mcp.tool()
    async def chroma_sync_to_qdrant(
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict] | None = None,
        ids: List[str] | None = None
    ) -> Dict:
        """
        Sync data from Chroma to Qdrant for offloading.
        
        Args:
            collection_name: Collection name
            documents: List of documents
            embeddings: List of embeddings
            metadatas: Optional metadata
            ids: Optional IDs
        """
        interop = get_interop_manager()
        return await interop.sync_to_qdrant(collection_name, documents, embeddings, metadatas, ids)
    
    @mcp.tool()
    async def chroma_sync_to_weaviate(
        collection_name: str,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict] | None = None,
        ids: List[str] | None = None
    ) -> Dict:
        """
        Sync data from Chroma to Weaviate.
        
        Args:
            collection_name: Collection name
            documents: List of documents
            embeddings: List of embeddings
            metadatas: Optional metadata
            ids: Optional IDs
        """
        interop = get_interop_manager()
        return await interop.sync_to_weaviate(collection_name, documents, embeddings, metadatas, ids)

if UMAP_AVAILABLE:
    @mcp.tool()
    async def chroma_reduce_embeddings(
        embeddings: List[List[float]],
        n_components: int = 2,
        labels: List[str] | None = None
    ) -> Dict:
        """
        Reduce embeddings dimensionality using UMAP for visualization.
        
        Args:
            embeddings: List of embedding vectors
            n_components: Number of dimensions (2 or 3 for visualization)
            labels: Optional labels for each embedding
        """
        reducer = get_umap_reducer()
        reducer.n_components = n_components
        return reducer.visualize_embeddings(embeddings, labels)

def main():
    """Entry point for the Chroma MCP server."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.dotenv_path:
        load_dotenv(dotenv_path=args.dotenv_path)
        # re-parse args to read the updated environment variables
        parser = create_parser()
        args = parser.parse_args()
    
    # Validate required arguments based on client type
    if args.client_type == 'http':
        if not args.host:
            parser.error("Host must be provided via --host flag or CHROMA_HOST environment variable when using HTTP client")
    
    elif args.client_type == 'cloud':
        if not args.tenant:
            parser.error("Tenant must be provided via --tenant flag or CHROMA_TENANT environment variable when using cloud client")
        if not args.database:
            parser.error("Database must be provided via --database flag or CHROMA_DATABASE environment variable when using cloud client")
        if not args.api_key:
            parser.error("API key must be provided via --api-key flag or CHROMA_API_KEY environment variable when using cloud client")
    
    # Initialize client with parsed args
    try:
        get_chroma_client(args)
        print("Successfully initialized Chroma client")
    except Exception as e:
        print(f"Failed to initialize Chroma client: {str(e)}")
        raise
    
    # Initialize advanced features
    print("Initializing advanced features...")
    
    # Start maintenance scheduler
    scheduler = get_maintenance_scheduler()
    scheduler.start()
    print("Started maintenance scheduler")
    
    # Initialize health monitor
    monitor = get_health_monitor()
    print("Initialized health monitor")
    
    # Initialize cache
    cache = get_memory_cache()
    print("Initialized memory cache")
    
    print(f"Advanced features ready: Cache, Health Monitoring, Auto-scaling, Swarm Tracking, Entity Mapping")
    
    # Initialize and run the server
    print("Starting MCP server")
    mcp.run(transport='stdio')
    
if __name__ == "__main__":
    main()
