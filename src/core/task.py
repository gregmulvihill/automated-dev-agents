import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

class Task:
    """Represents a discrete unit of work in the system.
    
    Tasks are the fundamental unit of work assignment and tracking
    in the automated development system.
    """
    
    def __init__(
        self,
        description: str,
        requirements: List[str],
        required_capabilities: Optional[List[str]] = None,
        priority: int = 1,
        dependencies: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize a new task.
        
        Args:
            description: Clear description of what needs to be done
            requirements: List of specific requirements for the task
            required_capabilities: Capabilities needed to perform this task
            priority: Task priority (higher numbers = higher priority)
            dependencies: List of task IDs that must be completed first
            context: Additional context information for the task
        """
        self.id = str(uuid.uuid4())
        self.description = description
        self.requirements = requirements
        self.required_capabilities = required_capabilities or []
        self.priority = priority
        self.dependencies = dependencies or []
        self.context = context or {}
        self.status = "pending"
        self.created_at = datetime.now().isoformat()
        self.assigned_to = None
        self.result = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for storage.
        
        Returns:
            Dictionary representation of the task
        """
        return {
            "id": self.id,
            "description": self.description,
            "requirements": self.requirements,
            "required_capabilities": self.required_capabilities,
            "priority": self.priority,
            "dependencies": self.dependencies,
            "context": self.context,
            "status": self.status,
            "created_at": self.created_at,
            "assigned_to": self.assigned_to,
            "result": self.result
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a task from a dictionary.
        
        Args:
            data: Dictionary containing task data
            
        Returns:
            Task instance
        """
        task = cls(
            description=data["description"],
            requirements=data["requirements"],
            required_capabilities=data.get("required_capabilities"),
            priority=data.get("priority", 1),
            dependencies=data.get("dependencies"),
            context=data.get("context")
        )
        
        # Override auto-generated fields
        task.id = data["id"]
        task.status = data["status"]
        task.created_at = data["created_at"]
        task.assigned_to = data.get("assigned_to")
        task.result = data.get("result")
        
        return task


class TaskQueue:
    """Manages a collection of tasks with prioritization and dependency tracking."""
    
    def __init__(self):
        """Initialize a new task queue."""
        self.tasks: Dict[str, Task] = {}
        
    def add_task(self, task: Task) -> str:
        """Add a task to the queue.
        
        Args:
            task: Task to add
            
        Returns:
            Task ID
        """
        self.tasks[task.id] = task
        return task.id
        
    def get_next_task(self, agent_capabilities: List[str]) -> Optional[Task]:
        """Get the next appropriate task for an agent with given capabilities.
        
        Args:
            agent_capabilities: List of agent capabilities
            
        Returns:
            Next suitable task or None if no suitable task exists
        """
        available_tasks = []
        
        for task in self.tasks.values():
            # Skip tasks that aren't pending
            if task.status != "pending":
                continue
                
            # Skip tasks with unmet dependencies
            if any(self.tasks.get(dep, Task("", [])).status != "completed" 
                   for dep in task.dependencies):
                continue
                
            # Skip tasks requiring capabilities the agent doesn't have
            if not all(cap in agent_capabilities for cap in task.required_capabilities):
                continue
                
            available_tasks.append(task)
            
        if not available_tasks:
            return None
            
        # Return highest priority task
        return sorted(available_tasks, key=lambda t: t.priority, reverse=True)[0]
        
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing task.
        
        Args:
            task_id: ID of task to update
            updates: Dictionary of fields to update
            
        Returns:
            True if update was successful, False otherwise
        """
        if task_id not in self.tasks:
            return False
            
        for key, value in updates.items():
            if hasattr(self.tasks[task_id], key):
                setattr(self.tasks[task_id], key, value)
                
        return True
