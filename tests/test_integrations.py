"""Tests for integration adapters."""
import pytest
from chroma_mcp.integrations import (
    LangGraphAdapter,
    LlamaCodexAdapter,
    CrewAIAdapter,
    N8NAdapter
)
import chromadb


@pytest.fixture
def chroma_client():
    """Create an ephemeral Chroma client for testing."""
    return chromadb.EphemeralClient()


class TestLangGraphAdapter:
    """Tests for LangGraph integration."""
    
    def test_save_and_load_state(self, chroma_client):
        """Test saving and loading graph state."""
        adapter = LangGraphAdapter(chroma_client, collection_name="test_langgraph")
        
        graph_id = "test_graph_1"
        state = {"current_node": "step_1", "data": {"count": 42}}
        metadata = {"user": "test_user"}
        
        # Save state
        result = adapter.save_graph_state(graph_id, state, metadata)
        assert result == graph_id
        
        # Load state
        loaded_state = adapter.load_graph_state(graph_id)
        assert loaded_state == state
    
    def test_load_nonexistent_state(self, chroma_client):
        """Test loading a state that doesn't exist."""
        adapter = LangGraphAdapter(chroma_client, collection_name="test_langgraph")
        
        loaded_state = adapter.load_graph_state("nonexistent_graph")
        assert loaded_state is None
    
    def test_save_checkpoint(self, chroma_client):
        """Test saving checkpoints."""
        adapter = LangGraphAdapter(chroma_client, collection_name="test_langgraph")
        
        graph_id = "test_graph_1"
        checkpoint_id = "checkpoint_1"
        checkpoint_data = {"step": 1, "status": "in_progress"}
        
        result = adapter.save_checkpoint(graph_id, checkpoint_id, checkpoint_data)
        assert checkpoint_id in result
    
    def test_list_checkpoints(self, chroma_client):
        """Test listing checkpoints for a graph."""
        adapter = LangGraphAdapter(chroma_client, collection_name="test_langgraph")
        
        graph_id = "test_graph_1"
        
        # Save multiple checkpoints
        adapter.save_checkpoint(graph_id, "checkpoint_1", {"step": 1})
        adapter.save_checkpoint(graph_id, "checkpoint_2", {"step": 2})
        
        # List checkpoints
        checkpoints = adapter.list_checkpoints(graph_id)
        assert len(checkpoints) >= 2


class TestLlamaCodexAdapter:
    """Tests for LlamaCodex integration."""
    
    def test_store_code_snippet(self, chroma_client):
        """Test storing a code snippet."""
        adapter = LlamaCodexAdapter(chroma_client, collection_name="test_code")
        
        code_id = "func_1"
        code = "def hello():\n    print('Hello, World!')"
        language = "python"
        metadata = {"file": "hello.py"}
        
        result = adapter.store_code_snippet(code_id, code, language, metadata)
        assert result == code_id
    
    def test_search_code(self, chroma_client):
        """Test searching for code."""
        adapter = LlamaCodexAdapter(chroma_client, collection_name="test_code")
        
        # Store some code
        adapter.store_code_snippet(
            "func_1",
            "def authenticate(user, password):\n    return verify(user, password)",
            "python"
        )
        adapter.store_code_snippet(
            "func_2",
            "def login(username, pwd):\n    return check_credentials(username, pwd)",
            "python"
        )
        
        # Search for code
        results = adapter.search_code("authentication", language="python", n_results=2)
        assert len(results) > 0
        assert "code" in results[0]
    
    def test_find_similar_code(self, chroma_client):
        """Test finding similar code snippets."""
        adapter = LlamaCodexAdapter(chroma_client, collection_name="test_code")
        
        code1 = "def add(a, b):\n    return a + b"
        code2 = "def sum_two(x, y):\n    return x + y"
        
        adapter.store_code_snippet("add_1", code1, "python")
        adapter.store_code_snippet("add_2", code2, "python")
        
        # Find similar code
        similar = adapter.find_similar_code(code1, n_results=2)
        assert len(similar) > 0
        assert "similarity_score" in similar[0]
    
    def test_get_code_by_language(self, chroma_client):
        """Test retrieving code by language."""
        adapter = LlamaCodexAdapter(chroma_client, collection_name="test_code")
        
        adapter.store_code_snippet("py_1", "print('Python')", "python")
        adapter.store_code_snippet("js_1", "console.log('JavaScript')", "javascript")
        
        python_code = adapter.get_code_by_language("python")
        assert len(python_code) >= 1


class TestCrewAIAdapter:
    """Tests for CrewAI integration."""
    
    def test_store_agent_memory(self, chroma_client):
        """Test storing agent memory."""
        adapter = CrewAIAdapter(chroma_client, collection_name="test_crewai")
        
        agent_id = "researcher_1"
        memory_content = "Found useful information about ML algorithms"
        memory_type = "knowledge"
        
        result = adapter.store_agent_memory(agent_id, memory_content, memory_type)
        assert agent_id in result
    
    def test_retrieve_agent_memories(self, chroma_client):
        """Test retrieving agent memories."""
        adapter = CrewAIAdapter(chroma_client, collection_name="test_crewai")
        
        agent_id = "researcher_1"
        
        # Store multiple memories
        adapter.store_agent_memory(agent_id, "Memory 1", "experience")
        adapter.store_agent_memory(agent_id, "Memory 2", "knowledge")
        
        # Retrieve memories
        memories = adapter.retrieve_agent_memories(agent_id, n_results=10)
        assert len(memories) >= 2
        assert "content" in memories[0]
    
    def test_retrieve_with_query(self, chroma_client):
        """Test retrieving memories with semantic query."""
        adapter = CrewAIAdapter(chroma_client, collection_name="test_crewai")
        
        agent_id = "researcher_1"
        adapter.store_agent_memory(agent_id, "Research about neural networks", "knowledge")
        
        # Query memories
        memories = adapter.retrieve_agent_memories(
            agent_id, 
            query="neural networks",
            n_results=5
        )
        assert len(memories) > 0
        assert "relevance" in memories[0]
    
    def test_store_task_result(self, chroma_client):
        """Test storing task results."""
        adapter = CrewAIAdapter(chroma_client, collection_name="test_crewai")
        
        task_id = "task_123"
        agent_id = "executor_1"
        result = "Task completed successfully"
        
        stored_id = adapter.store_task_result(task_id, agent_id, result)
        assert stored_id == task_id
    
    def test_conversation_storage(self, chroma_client):
        """Test storing and retrieving conversations."""
        adapter = CrewAIAdapter(chroma_client, collection_name="test_crewai")
        
        conversation_id = "conv_1"
        
        # Store messages
        adapter.store_conversation(conversation_id, "agent_1", "Hello")
        adapter.store_conversation(conversation_id, "agent_2", "Hi there!")
        
        # Get history
        history = adapter.get_conversation_history(conversation_id)
        assert len(history) >= 2
        assert "message" in history[0]
    
    def test_share_knowledge(self, chroma_client):
        """Test knowledge sharing."""
        adapter = CrewAIAdapter(chroma_client, collection_name="test_crewai")
        
        knowledge_id = "knowledge_1"
        knowledge_content = "Best practices for API design"
        source_agent = "expert_agent"
        
        result = adapter.share_knowledge(knowledge_id, knowledge_content, source_agent)
        assert result == knowledge_id
        
        # Query shared knowledge
        results = adapter.query_shared_knowledge("API design", n_results=5)
        assert len(results) > 0


class TestN8NAdapter:
    """Tests for n8n integration."""
    
    def test_store_and_load_workflow_state(self, chroma_client):
        """Test storing and loading workflow state."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        workflow_id = "workflow_1"
        state = {"step": 3, "processed_items": 150}
        
        # Store state
        result = adapter.store_workflow_state(workflow_id, state)
        assert result == workflow_id
        
        # Load state
        loaded_state = adapter.load_workflow_state(workflow_id)
        assert loaded_state == state
    
    def test_load_nonexistent_workflow(self, chroma_client):
        """Test loading workflow that doesn't exist."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        loaded_state = adapter.load_workflow_state("nonexistent_workflow")
        assert loaded_state is None
    
    def test_store_workflow_data(self, chroma_client):
        """Test storing workflow data."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        data_id = "data_1"
        data = "Customer email: test@example.com"
        workflow_id = "workflow_1"
        node_name = "email_parser"
        
        result = adapter.store_workflow_data(data_id, data, workflow_id, node_name)
        assert result == data_id
    
    def test_query_workflow_data(self, chroma_client):
        """Test querying workflow data."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        # Store some data
        adapter.store_workflow_data(
            "data_1",
            "Customer information: John Doe",
            "workflow_1"
        )
        adapter.store_workflow_data(
            "data_2",
            "Customer information: Jane Smith",
            "workflow_1"
        )
        
        # Query data
        results = adapter.query_workflow_data("customer", workflow_id="workflow_1")
        assert len(results) >= 2
        assert "data" in results[0]
    
    def test_transform_for_n8n(self, chroma_client):
        """Test transforming Chroma results for n8n."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        chroma_result = {
            "documents": [["doc1", "doc2"]],
            "metadatas": [[{"key": "value"}]],
            "distances": [[0.1, 0.2]]
        }
        
        n8n_data = adapter.transform_for_n8n(chroma_result)
        assert "json" in n8n_data
        assert "documents" in n8n_data["json"]
    
    def test_transform_from_n8n(self, chroma_client):
        """Test transforming n8n data for Chroma."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        n8n_data = {
            "json": {"field1": "value1", "field2": "value2"}
        }
        
        chroma_data = adapter.transform_from_n8n(n8n_data)
        assert chroma_data == n8n_data["json"]
    
    def test_webhook_registration(self, chroma_client):
        """Test webhook registration and triggering."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        def test_handler(data):
            return {"processed": True, "input": data}
        
        webhook_name = "test_webhook"
        adapter.register_webhook(webhook_name, test_handler)
        
        # Trigger webhook
        result = adapter.trigger_webhook(webhook_name, {"test": "data"})
        assert result["processed"] is True
    
    def test_webhook_not_found(self, chroma_client):
        """Test triggering non-existent webhook."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        with pytest.raises(ValueError, match="Webhook .* not registered"):
            adapter.trigger_webhook("nonexistent", {})
    
    def test_create_workflow_trigger(self, chroma_client):
        """Test creating a custom workflow trigger."""
        adapter = N8NAdapter(chroma_client, collection_name="test_n8n")
        
        triggered = []
        
        def condition(data):
            return data.get("status") == "ready"
        
        def action(data):
            triggered.append(data)
        
        adapter.create_workflow_trigger("custom_trigger", condition, action)
        
        # Trigger with matching condition
        result = adapter.trigger_webhook("custom_trigger", {"status": "ready"})
        assert result["status"] == "triggered"
        assert len(triggered) == 1
        
        # Trigger with non-matching condition
        result = adapter.trigger_webhook("custom_trigger", {"status": "pending"})
        assert result["status"] == "not_triggered"
