#!/usr/bin/env python3

"""
Automated Development System with Configurable Agents

Main entry point for the system. This script initializes and runs the system,
loading configuration, setting up agents, and starting the orchestrator.

Usage:
    python main.py [--config CONFIG_PATH] [--verbose]
"""

import os
import sys
import logging
import argparse
import asyncio
import json
from typing import Dict, List, Any, Optional

from core.agent import Agent
from core.orchestrator import TaskOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('automated_dev_agents.log')
    ]
)

logger = logging.getLogger("main")

class MockMTMAClient:
    """Mock implementation of MTMA client for development purposes.
    
    This class simulates the behavior of the MTMA client for testing
    and development when the actual MTMA system is not available.
    """
    
    def __init__(self):
        """Initialize the mock MTMA client."""
        self.short_term = {}
        self.long_term = {}
        self.world_state = {}
        self.logger = logging.getLogger("mock_mtma")
        
    def store_short_term(self, key: str, value: Any, ttl: int = 3600, lock: bool = False) -> None:
        """Store a value in short-term memory.
        
        Args:
            key: Key to store the value under
            value: Value to store
            ttl: Time-to-live in seconds (ignored in mock)
            lock: Whether to lock the value (ignored in mock)
        """
        self.short_term[key] = value
        self.logger.debug(f"Stored in short-term: {key}")
        
    def get_short_term(self, key: str) -> Optional[Any]:
        """Get a value from short-term memory.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Stored value or None if not found
        """
        return self.short_term.get(key)
        
    def store_long_term(self, key: str, value: Any) -> None:
        """Store a value in long-term memory.
        
        Args:
            key: Key to store the value under
            value: Value to store
        """
        self.long_term[key] = value
        self.logger.debug(f"Stored in long-term: {key}")
        
    def get_long_term(self, key: str) -> Optional[Any]:
        """Get a value from long-term memory.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Stored value or None if not found
        """
        return self.long_term.get(key)
        
    def update_world_state(self, key: str, value: Any) -> None:
        """Update a value in world state.
        
        Args:
            key: Key to update
            value: New value
        """
        self.world_state[key] = value
        self.logger.debug(f"Updated world state: {key}")
        
    def get_world_state(self, key: str) -> Optional[Any]:
        """Get a value from world state.
        
        Args:
            key: Key to retrieve
            
        Returns:
            Stored value or None if not found
        """
        return self.world_state.get(key)
        
    def search_short_term(self, query: str, limit: int = 10) -> List[Any]:
        """Search in short-term memory.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching values
        """
        # Very simplistic search implementation
        results = []
        for key, value in self.short_term.items():
            if isinstance(value, dict) and any(query.lower() in str(v).lower() for v in value.values()):
                results.append(value)
            elif isinstance(value, str) and query.lower() in value.lower():
                results.append({"key": key, "content": value})
                
            if len(results) >= limit:
                break
                
        return results
        
    def search_long_term(self, query: str, limit: int = 10) -> List[Any]:
        """Search in long-term memory.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching values
        """
        # Similar simplistic search implementation
        results = []
        for key, value in self.long_term.items():
            if isinstance(value, dict) and any(query.lower() in str(v).lower() for v in value.values()):
                results.append(value)
            elif isinstance(value, str) and query.lower() in value.lower():
                results.append({"key": key, "content": value})
                
            if len(results) >= limit:
                break
                
        return results

class MockLLMClient:
    """Mock implementation of LLM client for development purposes.
    
    This class simulates the behavior of an LLM API client for testing
    and development when the actual LLM API is not available.
    """
    
    def __init__(self):
        """Initialize the mock LLM client."""
        self.logger = logging.getLogger("mock_llm")
        
    async def generate(self, prompt: str) -> str:
        """Generate a response for the given prompt.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Generated response string
        """
        self.logger.info(f"Received prompt ({len(prompt)} chars)")
        
        # Return a simple mock response
        if "code" in prompt.lower():
            return "```python\ndef example_function(x, y):\n    \"\"\"Example function that adds two numbers.\"\"\"\n    return x + y\n```\n\nThis implementation provides a simple function that adds two numbers together. It demonstrates proper documentation with a docstring and clear parameter naming."
        elif "test" in prompt.lower():
            return "```python\nimport unittest\n\nclass TestExampleFunction(unittest.TestCase):\n    def test_positive_numbers(self):\n        self.assertEqual(example_function(2, 3), 5)\n    \n    def test_negative_numbers(self):\n        self.assertEqual(example_function(-1, -2), -3)\n    \n    def test_mixed_numbers(self):\n        self.assertEqual(example_function(-5, 10), 5)\n```\n\nThese tests cover the basic functionality of the example_function for positive, negative, and mixed number inputs."
        else:
            return "This is a placeholder response from the mock LLM client. In a real implementation, this would be a detailed and helpful response based on the prompt provided."

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {str(e)}")
        return {}

def create_agents(config: Dict[str, Any], memory_client: Any, llm_client: Any) -> List[Agent]:
    """Create agents based on configuration.
    
    Args:
        config: Configuration dictionary
        memory_client: MTMA client instance
        llm_client: LLM client instance
        
    Returns:
        List of agent instances
    """
    agents = []
    
    # Import agent classes here to avoid circular imports
    from agents.code_generator import CodeGeneratorAgent
    from agents.test_writer import TestWriterAgent
    from agents.claude_integration import ClaudeIntegrationAgent
    
    # Create agents based on configuration
    agent_configs = config.get("agents", {})
    
    # Create code generator agents
    for agent_config in agent_configs.get("code_generators", []):
        agent = CodeGeneratorAgent(
            name=agent_config["name"],
            memory_client=memory_client,
            llm_client=llm_client
        )
        agents.append(agent)
        logger.info(f"Created code generator agent: {agent.name}")
        
    # Create test writer agents
    for agent_config in agent_configs.get("test_writers", []):
        agent = TestWriterAgent(
            name=agent_config["name"],
            memory_client=memory_client,
            llm_client=llm_client
        )
        agents.append(agent)
        logger.info(f"Created test writer agent: {agent.name}")
        
    # Create Claude integration agents
    for agent_config in agent_configs.get("claude_integration", []):
        agent = ClaudeIntegrationAgent(
            name=agent_config["name"],
            memory_client=memory_client,
            claude_api_key=agent_config.get("api_key", "dummy_key"),
            model=agent_config.get("model", "claude-3-7-sonnet")
        )
        agents.append(agent)
        logger.info(f"Created Claude integration agent: {agent.name}")
        
    return agents

async def setup_demo_tasks(orchestrator: TaskOrchestrator) -> None:
    """Set up demonstration tasks for testing.
    
    Args:
        orchestrator: Task orchestrator instance
    """
    # Create a simple task for code generation
    code_task_id = orchestrator.create_task(
        description="Implement a function to calculate Fibonacci numbers",
        requirements=[
            "The function should calculate the nth Fibonacci number",
            "It should handle inputs up to n=100 efficiently",
            "It should include proper error handling for invalid inputs",
            "It should be well-documented with examples"
        ],
        required_capabilities=["code_generation"],
        priority=2
    )
    
    # Create a task for writing tests for the code
    test_task_id = orchestrator.create_task(
        description="Write tests for the Fibonacci function",
        requirements=[
            "Test basic functionality with known Fibonacci numbers",
            "Test error handling for invalid inputs",
            "Test edge cases (0, 1, large numbers)",
            "Ensure all tests are clear and well-documented"
        ],
        required_capabilities=["test_writing"],
        dependencies=[code_task_id],
        priority=1
    )
    
    logger.info(f"Created demo tasks: code_task_id={code_task_id}, test_task_id={test_task_id}")

async def main() -> None:
    """Main entry point for the system."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Automated Development System with Configurable Agents")
    parser.add_argument("--config", default="config/default.json", help="Path to configuration file")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Set logging level based on verbosity
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Load configuration
    config = load_config(args.config)
    
    # Initialize clients
    if config.get("use_mock_clients", True):
        memory_client = MockMTMAClient()
        llm_client = MockLLMClient()
        logger.info("Using mock clients for development")
    else:
        # Initialize real clients here
        # This would be replaced with actual client initialization code
        logger.error("Real clients not implemented yet, falling back to mock clients")
        memory_client = MockMTMAClient()
        llm_client = MockLLMClient()
        
    # Initialize orchestrator
    orchestrator = TaskOrchestrator(memory_client)
    
    # Create agents
    agents = create_agents(config, memory_client, llm_client)
    
    # Register agents with orchestrator
    for agent in agents:
        orchestrator.register_agent(agent)
        
    # Set up demo tasks if enabled
    if config.get("setup_demo_tasks", True):
        await setup_demo_tasks(orchestrator)
        
    # Start orchestrator
    try:
        logger.info("Starting orchestrator")
        await orchestrator.run(interval=config.get("orchestrator_interval", 5.0))
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully")
    except Exception as e:
        logger.error(f"Error in main loop: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(main())