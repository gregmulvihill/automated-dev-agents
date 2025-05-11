import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .agent import Agent
from .task import Task, TaskQueue

class TaskOrchestrator:
    """Central component responsible for managing tasks and agents.
    
    The orchestrator maintains the task queue, assigns tasks to appropriate
    agents, and monitors task execution.
    """
    
    def __init__(self, memory_client: Any):
        """Initialize the task orchestrator.
        
        Args:
            memory_client: Client for MTMA operations
        """
        self.memory_client = memory_client
        self.agents: Dict[str, Agent] = {}
        self.task_queue = TaskQueue()
        self.logger = logging.getLogger("orchestrator")
        
    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the orchestrator.
        
        Args:
            agent: Agent to register
        """
        self.agents[agent.id] = agent
        self.logger.info(f"Registered agent {agent.name} with ID {agent.id}")
        
    def create_task(
        self,
        description: str,
        requirements: List[str],
        required_capabilities: Optional[List[str]] = None,
        priority: int = 1,
        dependencies: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new task.
        
        Args:
            description: Clear description of what needs to be done
            requirements: List of specific requirements for the task
            required_capabilities: Capabilities needed to perform this task
            priority: Task priority (higher numbers = higher priority)
            dependencies: List of task IDs that must be completed first
            context: Additional context information for the task
            
        Returns:
            Task ID
        """
        task = Task(
            description=description,
            requirements=requirements,
            required_capabilities=required_capabilities,
            priority=priority,
            dependencies=dependencies,
            context=context
        )
        
        # Add to queue
        task_id = self.task_queue.add_task(task)
        
        # Store in memory
        self.memory_client.store_long_term(f"task:{task_id}", task.to_dict())
        
        self.logger.info(f"Created task {task_id}: {description}")
        return task_id
        
    async def assign_tasks(self) -> int:
        """Assign pending tasks to available agents.
        
        Returns:
            Number of tasks assigned
        """
        assigned_count = 0
        
        for agent in self.agents.values():
            if agent.status != "idle":
                continue
                
            # Find suitable task
            task = self.task_queue.get_next_task(agent.capabilities)
            if not task:
                continue
                
            # Assign task to agent
            success = await agent.assign_task(task.to_dict())
            if success:
                task.status = "assigned"
                task.assigned_to = agent.id
                self.task_queue.update_task(task.id, {
                    "status": "assigned",
                    "assigned_to": agent.id
                })
                assigned_count += 1
                
        return assigned_count
        
    async def monitor_progress(self) -> None:
        """Monitor progress of running tasks."""
        for agent_id, agent in self.agents.items():
            if agent.status != "working" or not agent.current_task:
                continue
                
            task_id = agent.current_task["id"]
            task_progress = self.memory_client.get_world_state(f"task_progress:{task_id}")
            
            if not task_progress:
                continue
                
            if task_progress.get("status") == "completed":
                # Task completed successfully
                self.handle_completed_task(task_id, task_progress)
                
            elif task_progress.get("status") == "failed":
                # Task failed
                self.handle_failed_task(task_id, task_progress)
                
    def handle_completed_task(self, task_id: str, result: Dict[str, Any]) -> None:
        """Handle a successfully completed task.
        
        Args:
            task_id: ID of the completed task
            result: Task result data
        """
        # Update task in queue
        self.task_queue.update_task(task_id, {
            "status": "completed",
            "result": result
        })
        
        # Update in long-term memory
        task_data = self.memory_client.get_long_term(f"task:{task_id}")
        if task_data:
            task_data["status"] = "completed"
            task_data["result"] = result
            task_data["completed_at"] = datetime.now().isoformat()
            self.memory_client.store_long_term(f"task:{task_id}", task_data)
            
        self.logger.info(f"Task {task_id} completed successfully")
        
    def handle_failed_task(self, task_id: str, error_data: Dict[str, Any]) -> None:
        """Handle a failed task.
        
        Args:
            task_id: ID of the failed task
            error_data: Error information
        """
        # Update task in queue
        self.task_queue.update_task(task_id, {
            "status": "failed",
            "result": error_data
        })
        
        # Update in long-term memory
        task_data = self.memory_client.get_long_term(f"task:{task_id}")
        if task_data:
            task_data["status"] = "failed"
            task_data["result"] = error_data
            task_data["failed_at"] = datetime.now().isoformat()
            self.memory_client.store_long_term(f"task:{task_id}", task_data)
            
        self.logger.error(f"Task {task_id} failed: {error_data.get('message', 'Unknown error')}")
        
    async def run(self, interval: float = 5.0) -> None:
        """Run the orchestrator in a continuous loop.
        
        Args:
            interval: Time between orchestration cycles in seconds
        """
        self.logger.info("Starting orchestrator")
        
        while True:
            try:
                # Assign available tasks
                assigned = await self.assign_tasks()
                if assigned > 0:
                    self.logger.info(f"Assigned {assigned} tasks")
                
                # Monitor task progress
                await self.monitor_progress()
                
                # Update world state
                self.update_system_state()
                
                # Wait before next cycle
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error in orchestrator cycle: {str(e)}")
                await asyncio.sleep(interval)
                
    def update_system_state(self) -> None:
        """Update the overall system state in world state."""
        # Count tasks by status
        task_counts = {
            "pending": 0,
            "assigned": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in self.task_queue.tasks.values():
            if task.status in task_counts:
                task_counts[task.status] += 1
                
        # Count agents by status
        agent_counts = {
            "idle": 0,
            "working": 0
        }
        
        for agent in self.agents.values():
            if agent.status in agent_counts:
                agent_counts[agent.status] += 1
                
        # Update world state
        self.memory_client.update_world_state("system:status", {
            "tasks": task_counts,
            "agents": agent_counts,
            "updated_at": datetime.now().isoformat()
        })
