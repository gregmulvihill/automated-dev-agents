# ADCA Integration Guide

This document explains how to integrate Automated Development System with Configurable Agents (ADCA) with the other components of the ecosystem: Orchestrate-AI and Multi-Tiered Memory Architecture (MTMA).

## Ecosystem Overview

The complete AI-driven development platform consists of three key repositories that work together:

```
┌─────────────────────────────────────────────────┐
│ ORCHESTRATE-AI                                  │
│ (Strategic Orchestration & Business Logic)      │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│ AUTOMATED-DEV-AGENTS (ADCA)                     │
│ (Tactical Task Execution & Agent Management)    │
└────────────────────────┬────────────────────────┘
                         │
┌────────────────────────▼────────────────────────┐
│ MULTI-TIERED MEMORY ARCHITECTURE (MTMA)         │
│ (Persistence, Context Preservation, Knowledge)  │
└─────────────────────────────────────────────────┘
```

Each system has a distinct responsibility:

1. **Orchestrate-AI**: High-level orchestration, workflow management, and business strategy
2. **ADCA**: Task execution, agent coordination, and development artifact generation
3. **MTMA**: Memory persistence, knowledge management, and context preservation

## Integration with Orchestrate-AI

### API Integration

ADCA exposes a RESTful API that Orchestrate-AI can call to:

- Create new development tasks
- Get updates on task status
- Retrieve generated artifacts
- Provide feedback for learning

### Configuration

1. Set the `ORCHESTRATE_API_URL` in your `.env` file to point to your Orchestrate-AI instance:

```
ORCHESTRATE_API_URL=http://orchestrate-ai-service:8080/api
ORCHESTRATE_API_KEY=your_api_key_here
```

2. Enable the Orchestrate-AI integration in `config/default.json`:

```json
{
  "integrations": {
    "orchestrate": {
      "enabled": true,
      "webhook_enabled": true,
      "webhook_url": "http://adca-service:8000/api/webhooks/orchestrate"
    }
  }
}
```

### Data Flow

1. **From Orchestrate-AI to ADCA**:
   - Task definitions with requirements
   - Priority information for scheduling
   - User feedback on generated artifacts
   - Business context for development tasks

2. **From ADCA to Orchestrate-AI**:
   - Task completion updates
   - Generated artifacts (code, tests, documentation)
   - Resource utilization metrics
   - Error reports and blockers

## Integration with MTMA

### Memory Client

ADCA uses MTMA as its memory persistence layer through a dedicated client:

```python
from mtma_client import MTMAClient

mtma_client = MTMAClient(
    controller_url="http://mtma-service:8000",
    api_key="your_mtma_api_key",
    namespace="adca"
)
```

### Configuration

1. Set the MTMA connection details in your `.env` file:

```
MTMA_CONTROLLER_URL=http://mtma-service:8000
MTMA_API_KEY=your_api_key_here
MTMA_NAMESPACE=adca
```

2. Enable the MTMA integration in `config/default.json`:

```json
{
  "use_mock_clients": false,
  "mtma": {
    "controller_url": "http://mtma-service:8000",
    "namespace": "adca"
  }
}
```

### Memory Operations

ADCA uses different memory tiers for different purposes:

1. **Short-term Memory**:
   - Active task context
   - Temporary agent state
   - Recent interactions and results
   - Working data for current tasks

2. **Long-term Memory**:
   - Completed tasks and results
   - Generated artifacts (code, tests, documentation)
   - Historical performance metrics
   - Learned patterns and optimizations

3. **World State**:
   - Current system status
   - Shared context between agents
   - Active task inventory
   - Resource availability

### Implementation

Replace the mock memory client with the actual MTMA client implementation:

```python
# Before (development with mock):
from src.main import MockMTMAClient
memory_client = MockMTMAClient()

# After (production with real MTMA):
from mtma_client import MTMAClient
memory_client = MTMAClient(
    controller_url=config["mtma"]["controller_url"],
    api_key=os.environ.get("MTMA_API_KEY"),
    namespace=config["mtma"]["namespace"]
)
```

## Docker Compose Integration

For local development with all three components, use this docker-compose configuration:

```yaml
version: '3.8'

services:
  orchestrate-ai:
    image: gregmulvihill/orchestrate-ai:latest
    ports:
      - "8080:8080"
    environment:
      - NODE_ENV=development
      - ADCA_API_URL=http://adca:8000/api
      - MTMA_CONTROLLER_URL=http://mtma:8000
    networks:
      - dev-network

  adca:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app
      - ORCHESTRATE_API_URL=http://orchestrate-ai:8080/api
      - MTMA_CONTROLLER_URL=http://mtma:8000
    networks:
      - dev-network
    depends_on:
      - mtma

  mtma:
    image: gregmulvihill/mtma:latest
    ports:
      - "8001:8000"
    environment:
      - REDIS_URI=redis://redis:6379/0
      - MONGODB_URI=mongodb://mtma:password@mongodb:27017/mtma
    networks:
      - dev-network
    depends_on:
      - redis
      - mongodb

  redis:
    image: redis:7.0-alpine
    networks:
      - dev-network

  mongodb:
    image: mongo:6.0
    environment:
      - MONGO_INITDB_ROOT_USERNAME=mtma
      - MONGO_INITDB_ROOT_PASSWORD=password
    networks:
      - dev-network

networks:
  dev-network:
    driver: bridge
```

## Testing the Integration

A simple test to verify that all three systems are communicating properly:

```python
async def test_integration():
    # 1. Create a task in Orchestrate-AI
    orchestrate_client = OrchestateClient(api_url=ORCHESTRATE_API_URL, api_key=ORCHESTRATE_API_KEY)
    task_id = await orchestrate_client.create_task(
        description="Test integration task",
        requirements=["Simple test to verify integration"]
    )
    
    # 2. Wait for ADCA to process the task
    timeout = 30  # seconds
    start_time = time.time()
    status = "pending"
    
    while status not in ["completed", "failed"] and time.time() - start_time < timeout:
        response = await orchestrate_client.get_task_status(task_id)
        status = response["status"]
        await asyncio.sleep(1)
    
    assert status == "completed", f"Task failed to complete within {timeout} seconds"
    
    # 3. Verify that results are in MTMA
    mtma_client = MTMAClient(
        controller_url=MTMA_CONTROLLER_URL,
        api_key=MTMA_API_KEY
    )
    
    task_result = mtma_client.get_long_term(f"task:{task_id}")
    assert task_result is not None, "Task result not found in MTMA"
    assert task_result["status"] == "completed"
```

## Troubleshooting

Common integration issues and their solutions:

1. **Connection Refused Errors**
   - Ensure all services are running
   - Check that service names in URLs match your docker-compose configuration
   - Verify network configuration allows the services to communicate

2. **Authentication Failures**
   - Verify API keys are correctly set in environment variables
   - Check that the keys have appropriate permissions

3. **Data Not Being Stored in MTMA**
   - Ensure the MTMA client is properly initialized
   - Verify the namespace is set correctly
   - Check that Redis and MongoDB are running and accessible to MTMA

4. **Tasks Not Being Processed by ADCA**
   - Verify the webhook URL is correctly configured in Orchestrate-AI
   - Check that ADCA is listening on the expected port
   - Ensure there are agents registered with the required capabilities
