# Chroma MCP Integrations - Quick Reference

## Available Integration Tools

### LangGraph Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `langgraph_save_state` | Save graph state for persistence | `graph_id`, `state`, `metadata?` |
| `langgraph_load_state` | Load saved graph state | `graph_id` |

### LlamaCodex Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `llamacodex_store_code` | Store code snippet with indexing | `code_id`, `code`, `language`, `metadata?` |
| `llamacodex_search_code` | Search code semantically | `query`, `language?`, `n_results=5` |

### CrewAI Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `crewai_store_agent_memory` | Store agent memory/experience | `agent_id`, `memory_content`, `memory_type="experience"`, `metadata?` |
| `crewai_retrieve_agent_memories` | Retrieve agent memories | `agent_id`, `query?`, `memory_type?`, `n_results=10` |

### n8n Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `n8n_store_workflow_state` | Store workflow execution state | `workflow_id`, `state`, `metadata?` |
| `n8n_load_workflow_state` | Load workflow state | `workflow_id` |
| `n8n_query_workflow_data` | Query workflow data semantically | `query`, `workflow_id?`, `n_results=10` |

## Quick Examples

### LangGraph: Save and Resume Workflow

```python
# Save state
await langgraph_save_state(
    graph_id="my_workflow",
    state={"step": 2, "data": {...}},
    metadata={"user": "alice"}
)

# Resume later
state = await langgraph_load_state(graph_id="my_workflow")
```

### LlamaCodex: Code Search

```python
# Store code
await llamacodex_store_code(
    code_id="auth_func",
    code="def authenticate(user, pwd):\n    return verify(user, pwd)",
    language="python",
    metadata={"module": "auth"}
)

# Search code
results = await llamacodex_search_code(
    query="user authentication",
    language="python"
)
```

### CrewAI: Agent Memory

```python
# Store memory
await crewai_store_agent_memory(
    agent_id="researcher_1",
    memory_content="Found API docs at...",
    memory_type="knowledge"
)

# Recall memories
memories = await crewai_retrieve_agent_memories(
    agent_id="researcher_1",
    query="API documentation"
)
```

### n8n: Workflow State

```python
# Store workflow state
await n8n_store_workflow_state(
    workflow_id="email_flow",
    state={"step": 3, "sent": 100}
)

# Query workflow data
results = await n8n_query_workflow_data(
    query="email responses",
    workflow_id="email_flow"
)
```

## Adapter Classes

For direct Python usage (not through MCP):

```python
from chroma_mcp import get_chroma_client
from chroma_mcp.integrations import (
    LangGraphAdapter,
    LlamaCodexAdapter,
    CrewAIAdapter,
    N8NAdapter
)

client = get_chroma_client()

# Use adapters directly
langgraph = LangGraphAdapter(client, collection_name="graphs")
llamacodex = LlamaCodexAdapter(client, collection_name="code")
crewai = CrewAIAdapter(client, collection_name="agents")
n8n = N8NAdapter(client, collection_name="workflows")
```

## Memory Types (CrewAI)

- `"experience"` - Past actions and outcomes
- `"knowledge"` - Learned information
- `"conversation"` - Dialog history
- `"task_result"` - Completed task outcomes

## Best Practices

1. **Use descriptive IDs**: Make IDs meaningful for easier debugging
2. **Add metadata**: Rich metadata enables better filtering
3. **Error handling**: Always wrap calls in try-except blocks
4. **State cleanup**: Implement retention policies for old states
5. **Batch operations**: Consider batching for performance

## Common Patterns

### Checkpoint Pattern (LangGraph)
```python
# Save checkpoint after each major step
await langgraph_save_state(
    graph_id=f"workflow_{id}",
    state=current_state,
    metadata={"checkpoint": step_number}
)
```

### Knowledge Sharing (CrewAI)
```python
# Store knowledge accessible by all agents
await crewai_store_agent_memory(
    agent_id="knowledge_base",
    memory_content="Best practice: ...",
    memory_type="knowledge"
)
```

### State Machine (n8n)
```python
# Track workflow progression
await n8n_store_workflow_state(
    workflow_id=f"process_{id}",
    state={"stage": "processing", "items": processed}
)
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Collection not found | Adapters auto-create collections |
| Import errors | Check dependencies installed |
| Serialization errors | Ensure JSON-serializable data |
| Connection issues | Verify Chroma client config |

## Resources

- [Full Documentation](../README.md)
- [Integration Examples](./INTEGRATION_EXAMPLES.md)
- [Test Suite](../tests/test_integrations.py)
- [Chroma Documentation](https://docs.trychroma.com/)

## Support

For issues or questions:
1. Check the [Integration Examples](./INTEGRATION_EXAMPLES.md)
2. Review test cases in `tests/test_integrations.py`
3. Open an issue on GitHub
