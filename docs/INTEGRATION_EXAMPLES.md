# Integration Examples

This document provides detailed examples of how to use the various framework integrations in Chroma MCP.

## LangGraph Integration

### Overview
LangGraph integration enables stateful, multi-actor applications to persist their state in Chroma.

### Example: Building a Multi-Step Workflow

```python
from langgraph.graph import StateGraph
from chroma_mcp import get_chroma_client
from chroma_mcp.integrations import LangGraphAdapter

# Initialize the adapter
client = get_chroma_client()
adapter = LangGraphAdapter(client, collection_name="my_workflow_states")

# Define your graph state
class WorkflowState(TypedDict):
    current_step: str
    data: Dict[str, Any]
    completed_steps: List[str]

# Save state during workflow execution
def save_workflow_checkpoint(state: WorkflowState, graph_id: str):
    adapter.save_graph_state(graph_id, state, metadata={
        "timestamp": time.time(),
        "step_count": len(state["completed_steps"])
    })

# Resume workflow from saved state
def resume_workflow(graph_id: str) -> WorkflowState:
    return adapter.load_graph_state(graph_id)

# Query similar workflow states for learning
def find_similar_workflows(current_state: WorkflowState):
    similar = adapter.query_similar_states(current_state, n_results=5)
    return similar
```

### Using with MCP Tools

```python
# Via MCP tools
await langgraph_save_state(
    graph_id="user_onboarding_flow",
    state={
        "current_step": "email_verification",
        "user_id": "user123",
        "completed": ["registration", "profile_setup"]
    },
    metadata={"user_type": "premium"}
)

# Load saved state
state = await langgraph_load_state(graph_id="user_onboarding_flow")
```

## LlamaCodex Integration

### Overview
Store and search code snippets using semantic search for better code discovery and reuse.

### Example: Code Repository Management

```python
from chroma_mcp.integrations import LlamaCodexAdapter

# Initialize adapter
adapter = LlamaCodexAdapter(client, collection_name="my_code_repo")

# Store a code snippet
code = '''
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate discounted price."""
    return price * (1 - discount_percent / 100)
'''

adapter.store_code_snippet(
    code_id="discount_calculation",
    code=code,
    language="python",
    metadata={
        "file": "pricing.py",
        "author": "dev_team",
        "tags": ["pricing", "discount", "calculation"]
    }
)

# Search for code using natural language
results = adapter.search_code(
    query="function to calculate price with discount",
    language="python",
    n_results=5
)

for result in results:
    print(f"Code: {result['code']}")
    print(f"File: {result['metadata']['file']}")
    print(f"Relevance: {result['distance']}")

# Find similar code patterns
similar_code = adapter.find_similar_code(
    code="def apply_coupon(amount, coupon_code):\n    return amount * 0.9",
    n_results=3
)
```

### Using with MCP Tools

```python
# Store code via MCP
await llamacodex_store_code(
    code_id="auth_handler",
    code='''
def authenticate_user(username: str, password: str) -> bool:
    hashed = hash_password(password)
    return verify_credentials(username, hashed)
''',
    language="python",
    metadata={"module": "auth", "security_level": "critical"}
)

# Search code
results = await llamacodex_search_code(
    query="user authentication function",
    language="python",
    n_results=10
)
```

## CrewAI Integration

### Overview
Enable persistent memory for CrewAI agents, allowing them to learn from past experiences and share knowledge.

### Example: Multi-Agent Research Team

```python
from chroma_mcp.integrations import CrewAIAdapter

# Initialize adapter
adapter = CrewAIAdapter(client, collection_name="research_team_memory")

# Store agent experience
adapter.store_agent_memory(
    agent_id="researcher_001",
    memory_content="Found comprehensive documentation on transformer architectures in the Attention is All You Need paper",
    memory_type="knowledge",
    metadata={
        "source": "arxiv",
        "relevance": "high",
        "domain": "machine_learning"
    }
)

# Store conversation between agents
conversation_id = "research_meeting_20240115"
adapter.store_conversation(
    conversation_id=conversation_id,
    speaker_id="researcher_001",
    message="We should focus on the self-attention mechanism first"
)

adapter.store_conversation(
    conversation_id=conversation_id,
    speaker_id="reviewer_002",
    message="Agreed. I'll review the implementation details."
)

# Retrieve conversation history
history = adapter.get_conversation_history(conversation_id)

# Retrieve relevant memories for current task
memories = adapter.retrieve_agent_memories(
    agent_id="researcher_001",
    query="transformer architecture documentation",
    memory_type="knowledge",
    n_results=5
)

# Share knowledge across agents
adapter.share_knowledge(
    knowledge_id="transformer_best_practices",
    knowledge_content="Always use layer normalization before self-attention layers",
    source_agent_id="researcher_001",
    metadata={"verified": True}
)

# Query shared knowledge
shared_knowledge = adapter.query_shared_knowledge(
    query="best practices for transformers",
    n_results=10
)
```

### Using with MCP Tools

```python
# Store agent memory via MCP
await crewai_store_agent_memory(
    agent_id="data_analyst_agent",
    memory_content="Successfully analyzed customer churn patterns using logistic regression",
    memory_type="experience",
    metadata={"project": "churn_prediction", "accuracy": 0.92}
)

# Retrieve memories
memories = await crewai_retrieve_agent_memories(
    agent_id="data_analyst_agent",
    query="customer churn analysis",
    n_results=10
)
```

## n8n Integration

### Overview
Integrate Chroma with n8n workflows for persistent state management and semantic data search.

### Example: Customer Support Workflow

```python
from chroma_mcp.integrations import N8NAdapter

# Initialize adapter
adapter = N8NAdapter(client, collection_name="support_workflows")

# Store workflow state
workflow_state = {
    "ticket_id": "TICKET-12345",
    "current_stage": "analysis",
    "assigned_agent": "agent_42",
    "priority": "high",
    "customer_info": {
        "id": "CUST-789",
        "tier": "premium"
    }
}

adapter.store_workflow_state(
    workflow_id="support_ticket_12345",
    state=workflow_state,
    metadata={"department": "technical_support"}
)

# Store data from workflow nodes
adapter.store_workflow_data(
    data_id="ticket_12345_resolution",
    data="Customer issue resolved by restarting the service",
    workflow_id="support_ticket_12345",
    node_name="resolution_logger"
)

# Query workflow data for similar issues
similar_issues = adapter.query_workflow_data(
    query="service restart resolved issue",
    workflow_id=None,  # Search across all workflows
    n_results=5
)

# Register a custom webhook
def on_high_priority_ticket(data):
    ticket_id = data.get("ticket_id")
    priority = data.get("priority")
    
    if priority == "critical":
        # Store for immediate escalation
        adapter.store_workflow_data(
            data_id=f"escalation_{ticket_id}",
            data=f"Critical ticket {ticket_id} requires immediate attention",
            workflow_id="escalation_workflow"
        )
        return {"status": "escalated", "ticket_id": ticket_id}
    
    return {"status": "queued", "ticket_id": ticket_id}

adapter.register_webhook("ticket_priority_handler", on_high_priority_ticket)

# Trigger the webhook
result = adapter.trigger_webhook(
    "ticket_priority_handler",
    {"ticket_id": "TICKET-999", "priority": "critical"}
)

# Transform data for n8n consumption
chroma_results = {
    "documents": [["doc1", "doc2"]],
    "metadatas": [[{"key": "value"}]],
    "distances": [[0.1, 0.2]]
}
n8n_formatted = adapter.transform_for_n8n(chroma_results)
# Use in n8n workflow nodes
```

### Using with MCP Tools

```python
# Store workflow state via MCP
await n8n_store_workflow_state(
    workflow_id="email_automation_flow",
    state={
        "step": 3,
        "emails_sent": 150,
        "remaining": 50
    },
    metadata={"campaign": "spring_sale_2024"}
)

# Load workflow state
state = await n8n_load_workflow_state(workflow_id="email_automation_flow")

# Query workflow data
results = await n8n_query_workflow_data(
    query="customer email responses",
    workflow_id="email_automation_flow",
    n_results=20
)
```

## Best Practices

### General Guidelines

1. **Use meaningful IDs**: Always use descriptive, unique identifiers for your data
2. **Add rich metadata**: Include relevant metadata to enable better filtering and search
3. **Consistent naming**: Use consistent naming conventions across your integrations
4. **Error handling**: Wrap integration calls in try-except blocks
5. **State cleanup**: Regularly clean up old states and checkpoints

### Performance Tips

1. **Batch operations**: When storing multiple items, consider batching for better performance
2. **Optimize queries**: Use metadata filters to narrow down search space
3. **Cache frequently accessed data**: Consider caching frequently loaded states
4. **Collection design**: Create separate collections for different types of data

### Security Considerations

1. **Sensitive data**: Be cautious about storing sensitive information in metadata
2. **Access control**: Implement proper access control for your Chroma collections
3. **Data retention**: Implement data retention policies for compliance
4. **Encryption**: Use encrypted connections when using HTTP/cloud clients

## Troubleshooting

### Common Issues

1. **Collection not found**: Ensure the collection exists before querying
2. **Import errors**: Verify all dependencies are installed
3. **Connection issues**: Check your Chroma client configuration
4. **Serialization errors**: Ensure your state objects are JSON-serializable

### Debug Mode

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- Explore the [API documentation](../README.md) for detailed tool descriptions
- Check out the [test suite](../tests/test_integrations.py) for more examples
- Join the community to share your integration patterns
