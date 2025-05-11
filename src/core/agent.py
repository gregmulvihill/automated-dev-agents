import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

class Agent:
    """Base class for all agents in the system.
    
    Provides common functionality for task handling, memory operations,
    and progress reporting.
    """
    
    def __init__(self, name: str, capabilities: List[str], memory_client: Any):
        """Initialize a new agent.
        
        Args:
            name: Unique identifier for the agent
            capabilities: List of tasks this agent can perform
            memory_client: Client for MTMA operations
        """
        self.name = name
        self.id = f"{name.lower().replace(' ', '_')}_{uuid.uuid4().hex[:8]}"
        self.capabilities = capabilities
        self.memory_client = memory_client
        self.current_task = None
        self.status = "idle"
        self.logger = logging.getLogger(f"agent.{self.name}")
        
    async def assign_task(self, task: Dict[str, Any]) -> bool:
        """Assign a new task to this agent.
        
        Args:
            task: Task details including ID, description, and requirements
            
        Returns:
            bool: True if task was successfully assigned, False otherwise
        """
        # Check if agent is already busy
        if self.status != "idle":
            self.logger.warning(f"Cannot assign task {task['id']}: Agent is {self.status}")
            return False
            
        # Check if agent has required capabilities
        required_capabilities = task.get("required_capabilities", [])
        if required_capabilities and not all(cap in self.capabilities for cap in required_capabilities):
            self.logger.warning(f"Cannot assign task {task['id']}: Missing required capabilities")
            return False
        
        # Store task in agent's memory
        try:
            self.memory_client.store_short_term(f"task:{task['id']}", task)
            self.current_task = task
            self.status = "working"
            self.logger.info(f"Assigned task {task['id']} to agent {self.name}")
            
            # Update world state with assignment
            self.memory_client.update_world_state(
                f"task_assignment:{task['id']}",
                {
                    "agent": self.id,
                    "assigned_at": datetime.now().isoformat(),
                    "status": "assigned"
                }
            )
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to assign task {task['id']}: {str(e)}")
            return False
        
    async def execute(self) -> None:
        """Execute the current task.
        
        This method must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement execute method")
        
    async def report_progress(self, progress: Dict[str, Any]) -> None:
        """Report task progress to the orchestrator.
        
        Args:
            progress: Dictionary containing progress information
        """
        if not self.current_task:
            self.logger.warning("Cannot report progress: No task assigned")
            return
            
        try:
            # Add timestamp and agent info
            progress["reported_at"] = datetime.now().isoformat()
            progress["agent"] = self.id
            
            # Update task progress in world state
            self.memory_client.update_world_state(
                f"task_progress:{self.current_task['id']}", 
                progress
            )
            
            self.logger.info(f"Reported progress for task {self.current_task['id']}: {progress['status']}")
            
            # If task is completed or failed, update agent status
            if progress.get("status") in ["completed", "failed"]:
                self.status = "idle"
                self.current_task = None
                
        except Exception as e:
            self.logger.error(f"Failed to report progress: {str(e)}")
    
    async def get_context(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve context relevant to the current task.
        
        Args:
            query: Search query for finding relevant context
            limit: Maximum number of context items to retrieve
            
        Returns:
            List of context items
        """
        try:
            # Search in short-term memory first
            results = self.memory_client.search_short_term(query, limit=limit)
            
            # If not enough results, search in long-term memory
            if len(results) < limit:
                long_term_results = self.memory_client.search_long_term(
                    query, 
                    limit=limit - len(results)
                )
                results.extend(long_term_results)
                
            return results
        except Exception as e:
            self.logger.error(f"Failed to get context: {str(e)}")
            return []
