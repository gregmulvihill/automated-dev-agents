#!/usr/bin/env python3

"""
Example usage of the Automated Development System with Configurable Agents.

This example demonstrates how to create custom tasks, configure agents,
and use the system for automated development.

Usage:
    python example_usage.py
"""

import asyncio
import logging
from typing import Dict, List, Any

# Import ADCA core components
from src.core.orchestrator import TaskOrchestrator
from src.core.agent import Agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Mock memory client for demonstration
class MockMemoryClient:
    def __init__(self):
        self.short_term = {}
        self.long_term = {}
        self.world_state = {}
        
    def store_short_term(self, key, value, ttl=3600, lock=False):
        self.short_term[key] = value
        print(f"[MEMORY] Stored in short-term: {key}")
        
    def get_short_term(self, key):
        return self.short_term.get(key)
        
    def store_long_term(self, key, value):
        self.long_term[key] = value
        print(f"[MEMORY] Stored in long-term: {key}")
        
    def get_long_term(self, key):
        return self.long_term.get(key)
        
    def update_world_state(self, key, value):
        self.world_state[key] = value
        print(f"[MEMORY] Updated world state: {key}")
        
    def get_world_state(self, key):
        return self.world_state.get(key)
        
    def search_short_term(self, query, limit=10):
        print(f"[MEMORY] Searching short-term for: {query}")
        return []
        
    def search_long_term(self, query, limit=10):
        print(f"[MEMORY] Searching long-term for: {query}")
        return []

# Example custom agent
class SimpleCodeAgent(Agent):
    def __init__(self, name, memory_client):
        super().__init__(
            name=name,
            capabilities=["code_generation"],
            memory_client=memory_client
        )
        
    async def execute(self):
        """Execute the current task."""
        if not self.current_task:
            print(f"[{self.name}] No task assigned")
            return
            
        print(f"[{self.name}] Executing task: {self.current_task['description']}")
        
        # Simulate work with a delay
        await asyncio.sleep(2)
        
        # Generate example code
        if "code_generation" in self.capabilities:
            code = f"""
def example_function():
    \"\"\"
    This is an example function generated for task: {self.current_task['description']}
    \"\"\"
    print("Hello from generated code!")
    return True
            """
            
            # Report completion
            await self.report_progress({
                "status": "completed",
                "output": code,
                "message": "Code generation successful"
            })
            
            print(f"[{self.name}] Task completed successfully")
        else:
            # Report failure for unsupported task
            await self.report_progress({
                "status": "failed",
                "message": f"Agent {self.name} cannot handle this task type"
            })
            
            print(f"[{self.name}] Task failed: Unsupported task type")

async def run_example():
    """Run an example usage of the system."""
    print("Starting Automated Development System with Configurable Agents example")
    
    # Initialize memory client
    memory_client = MockMemoryClient()
    
    # Initialize orchestrator
    orchestrator = TaskOrchestrator(memory_client)
    
    # Create and register agent
    agent = SimpleCodeAgent("ExampleCodeAgent", memory_client)
    orchestrator.register_agent(agent)
    
    print("\nCreating example tasks...")
    
    # Create a simple task
    task_id = orchestrator.create_task(
        description="Implement a simple Hello World function",
        requirements=[
            "Function should print 'Hello World!'",
            "Function should return True",
            "Function should be well documented"
        ],
        required_capabilities=["code_generation"],
        priority=2
    )
    
    print(f"Created task: {task_id}")
    
    # Run a few assignment cycles
    print("\nRunning task assignment cycles...")
    for i in range(3):
        print(f"\nCycle {i+1}:")
        assigned = await orchestrator.assign_tasks()
        print(f"Assigned {assigned} tasks")
        
        # Monitor progress
        await orchestrator.monitor_progress()
        
        # Wait to simulate time passing
        await asyncio.sleep(1)
    
    print("\nExample completed. In a real scenario, the system would continue running.")

if __name__ == "__main__":
    asyncio.run(run_example())
