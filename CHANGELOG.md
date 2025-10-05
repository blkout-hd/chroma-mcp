# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - TBD

### Added

- **LangGraph Integration**: Support for stateful multi-actor applications
  - `langgraph_save_state` tool for persistent state storage
  - `langgraph_load_state` tool for state retrieval
  - State management with checkpoint support
  
- **LlamaCodex Integration**: Code-related LLM tools
  - `llamacodex_store_code` tool for code snippet storage
  - `llamacodex_search_code` tool for semantic code search
  - Language-specific filtering and metadata support
  
- **CrewAI Integration**: Multi-agent coordination and memory
  - `crewai_store_agent_memory` tool for agent memory persistence
  - `crewai_retrieve_agent_memories` tool for memory retrieval
  - Support for different memory types (experience, knowledge, conversation)
  
- **n8n Integration**: Workflow automation extensibility
  - `n8n_store_workflow_state` tool for workflow state persistence
  - `n8n_load_workflow_state` tool for state retrieval
  - `n8n_query_workflow_data` tool for semantic workflow data search
  - Data transformation utilities for n8n compatibility

- Integration adapters module (`chroma_mcp.integrations`) with specialized classes:
  - `LangGraphAdapter` for graph state management
  - `LlamaCodexAdapter` for code storage and retrieval
  - `CrewAIAdapter` for agent memory and coordination
  - `N8NAdapter` for workflow automation support

### Changed

- Enhanced documentation with integration examples and use cases
- Improved server architecture to support extensibility

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