# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **UMAP Integration**: Dimensionality reduction and visualization capabilities for embeddings
- **Weaviate Interoperability**: Seamless data synchronization with Weaviate vector database
- **Qdrant Interoperability**: Data offloading and load balancing with Qdrant
- **Passive Memory Cache**: Short-term memory cache layer for operations without explicit commit to database
- **Autonomous Maintenance**: Scheduled maintenance tasks and cron job support
- **Health Checking**: Comprehensive health monitoring and system metrics
- **Entity Relationship Mapping**: Graph-based entity and relationship tracking
- **Intelligent Auto-scaling**: Adaptive scaling recommendations based on ecosystem metrics
- **Swarm Pheromone Tracking**: Pattern tracking for frequently accessed operations
- **Code Smell Monitoring**: Detection of anti-patterns and inefficient operations
- **Selective Encryption**: Algorithmic detection and encryption of sensitive information
- **Watchdog Service**: Auto-restart capabilities for cloud database connections

### Tools Added

- `chroma_cache_query` - Cache queries for passive short-term memory
- `chroma_get_cache_stats` - Get cache statistics
- `chroma_health_check` - Get comprehensive health status
- `chroma_get_scaling_recommendation` - Get intelligent scaling recommendations
- `chroma_get_hot_trails` - Get frequently accessed operation patterns
- `chroma_get_code_smells` - Get code smell detection report
- `chroma_encrypt_documents` - Selectively encrypt documents based on sensitive data detection
- `chroma_add_entity` - Add entity to relationship graph
- `chroma_add_relationship` - Add relationship between entities
- `chroma_get_graph_stats` - Get entity relationship graph statistics
- `chroma_find_entity_path` - Find path between entities
- `chroma_sync_to_qdrant` - Sync data to Qdrant for offloading
- `chroma_sync_to_weaviate` - Sync data to Weaviate
- `chroma_reduce_embeddings` - Reduce embeddings dimensionality with UMAP
- `chroma_schedule_health_check` - Schedule periodic health checks
- `chroma_schedule_cache_cleanup` - Schedule periodic cache cleanup
- `chroma_get_scheduled_jobs` - Get list of scheduled maintenance jobs

### Changed

- Enhanced query and add operations with health monitoring and swarm tracking
- Updated dependencies to include new features (umap-learn, weaviate-client, qdrant-client, watchdog, schedule, cryptography, psutil)
- Main server now starts with default scheduled maintenance tasks
- Watchdog service auto-starts for persistent clients

## [0.2.6] - 08/14/2025

- Update chromadb to 1.0.16
- Add tool prompts for regex support
- Add new `chroma_fork_collection` tool support

## [0.2.5] - 06/18/2025

- Update chromadb to 1.0.13
- Simplify configuration instantiation
- Clarify list_collection success with no collections
- Remove Optional parameters, replace with | None

## [0.2.4] - 05/21/2025

### Changed

- Update chromadb to v1.0.10

## [0.2.2] - 04/08/2025

### Changed

- Update chromadb to v1.0.3
- Fix include on query and get to match chromadb Python client


## [0.2.1] - 04/03/2025

### Added

- The ability to select embedding functions when creating collections (default, cohere, openai, jina, voyageai, roboflow)

### Changed
- Upgraded to v1.0.0 of Chroma
- Fix dotenv path support during argparse

## [0.2.0] - 04/02/2025

### Added
- New `delete_document` tool for removing documents from collections
- New `chroma_update_documents` tool for updating existing documents
- Docker deployment support with Dockerfile
- Smithery configuration for deployment
- Environment variable support in Smithery config

### Changed
- Improved error handling across tools
- Removed sequential thinking in favor of more direct operations
- SSL parsing improvements and fixes

### Security
- Enhanced SSL handling and security configurations

## [0.1.11] - 02/21/2025

### Changed
- Version bump

## [0.1.10] - 02/21/2024

### Added
- Initial release
- Support for ephemeral, persistent, HTTP, and cloud Chroma clients
- Collection management tools
- Document operations (add, query, get)
- Claude Desktop integration
- Environment variable support
- Dotenv file support

### Security
- SSL support for HTTP and cloud clients
- Authentication support for HTTP clients
- API key management for cloud deployments 