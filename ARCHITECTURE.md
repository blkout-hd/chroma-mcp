# Chroma MCP Advanced Features Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Chroma MCP Server                           │
│                         (server.py)                                 │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        │ Initializes & Manages
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Chroma DB  │ │   FastMCP    │ │  Advanced    │
│   Client     │ │   Tools      │ │  Features    │
└──────────────┘ └──────────────┘ └───────┬──────┘
                                           │
        ┌──────────────────────────────────┼─────────────────────┐
        │                                  │                     │
        ▼                                  ▼                     ▼
┌──────────────┐                    ┌──────────────┐     ┌──────────────┐
│   Memory     │                    │   Health &   │     │  Security &  │
│   Cache      │                    │  Monitoring  │     │  Encryption  │
│              │                    │              │     │              │
│ • LRU Cache  │                    │ • Metrics    │     │ • Detection  │
│ • TTL        │                    │ • Status     │     │ • Encryption │
│ • Projects   │                    │ • Resources  │     │ • Privacy    │
└──────────────┘                    └──────────────┘     └──────────────┘
        │                                  │                     │
        ▼                                  ▼                     ▼
┌──────────────┐                    ┌──────────────┐     ┌──────────────┐
│   Swarm      │                    │ Maintenance  │     │   Entity     │
│   Tracking   │                    │ & Scheduling │     │  Mapping     │
│              │                    │              │     │              │
│ • Trails     │                    │ • Cron Jobs  │     │ • Graph      │
│ • Patterns   │                    │ • Watchdog   │     │ • Relations  │
│ • Smells     │                    │ • Autoscale  │     │ • Pathfind   │
└──────────────┘                    └──────────────┘     └──────────────┘
        │                                  │                     │
        └──────────────┬───────────────────┴─────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Interoperability Layer     │
        │                              │
        │ • UMAP Reduction             │
        │ • Weaviate Sync              │
        │ • Qdrant Offload             │
        └──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐
│   Weaviate   │ │  Qdrant  │ │   UMAP   │
│   (Optional) │ │(Optional)│ │(Optional)│
└──────────────┘ └──────────┘ └──────────┘
```

## Data Flow

### Query Operation
```
User Request
    │
    ▼
MCP Tool (chroma_query_documents)
    │
    ├──► Health Monitor (record query)
    ├──► Swarm Tracker (track pattern)
    ├──► Code Smell Monitor (check efficiency)
    │
    ▼
Check Cache
    │
    ├──► Cache Hit → Return cached result
    │
    └──► Cache Miss
            │
            ▼
        Query Chroma DB
            │
            ▼
        Cache Result
            │
            ▼
        Return to User
```

### Add Documents Operation
```
User Request
    │
    ▼
MCP Tool (chroma_add_documents)
    │
    ├──► Health Monitor (record insert)
    ├──► Swarm Tracker (track pattern)
    ├──► Security Module (detect sensitive data)
    │        │
    │        └──► Encrypt if needed
    │
    ▼
Add to Chroma DB
    │
    ▼
Optional: Sync to External DBs
    │
    ├──► Weaviate
    └──► Qdrant
```

### Maintenance Loop
```
Server Start
    │
    ▼
Initialize Scheduler
    │
    ├──► Schedule Health Check (every 5 min)
    ├──► Schedule Cache Cleanup (hourly)
    └──► Start Watchdog (if persistent)
    │
    ▼
Background Thread Loop
    │
    ├──► Check scheduled tasks
    ├──► Execute due tasks
    ├──► Monitor file system (watchdog)
    └──► Sleep 1 second
```

## Component Interactions

### Automatic Features (No User Action Required)
- Health monitoring on every operation
- Swarm trail reinforcement on queries/inserts
- Code smell detection on operations
- Scheduled maintenance tasks
- Watchdog monitoring (persistent mode)

### Manual Features (Requires Tool Call)
- UMAP dimensionality reduction
- External DB synchronization
- Entity relationship operations
- Cache querying (explicit)
- Manual encryption
- Scheduling custom tasks

## Thread Model

```
Main Thread
    │
    ├──► FastMCP Server (stdio transport)
    │
    └──► Background Threads
            │
            ├──► Maintenance Scheduler Thread
            │       └──► Executes cron jobs
            │
            └──► Watchdog Observer Thread
                    └──► Monitors file system
```

## State Management

All components use singleton pattern:
```python
# Global instances
_memory_cache = None
_health_monitor = None
_maintenance_scheduler = None
_auto_scaler = None
_swarm_tracker = None
_code_smell_monitor = None
_er_mapper = None
_interop_manager = None
_umap_reducer = None
_encryption_manager = None

# Accessed via getter functions
get_memory_cache()
get_health_monitor()
# etc.
```

## Security Architecture

```
Document Input
    │
    ▼
Sensitive Data Detector
    │
    ├──► Pattern Matching
    │       ├──► Email
    │       ├──► SSN
    │       ├──► Credit Card
    │       ├──► API Keys
    │       └──► Passwords
    │
    ▼
Calculate Sensitivity Score
    │
    ▼
Score >= 0.5?
    │
    ├──► Yes → Encrypt with Fernet
    │            │
    │            └──► Add metadata flag
    │
    └──► No  → Store as plaintext
```

## Performance Characteristics

| Feature | Time Complexity | Space Complexity | Notes |
|---------|----------------|------------------|-------|
| Cache Set | O(1) | O(n) | LRU eviction |
| Cache Get | O(1) | O(1) | Hash lookup |
| Swarm Track | O(1) | O(m) | Trail reinforcement |
| Health Check | O(1) | O(1) | Metric aggregation |
| Encrypt | O(n) | O(n) | Per document |
| Entity Add | O(1) | O(e) | Graph node |
| Path Find | O(e+v) | O(v) | BFS algorithm |
| UMAP | O(n²) | O(n*d) | Dimensionality reduction |

Where:
- n = number of documents
- m = number of unique trails
- e = number of edges
- v = number of vertices
- d = embedding dimensions
