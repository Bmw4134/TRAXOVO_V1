"""
TRAXOVO Background Task System
Async processing for GAUGE API sync cycles and resource-intensive operations
"""

import asyncio
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Any
import requests
import os
from dataclasses import dataclass
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class BackgroundTask:
    id: str
    name: str
    function: Callable
    args: tuple
    kwargs: dict
    status: TaskStatus
    created_at: datetime
    started_at: datetime = None
    completed_at: datetime = None
    error: str = None
    retry_count: int = 0
    max_retries: int = 3
    result: Any = None

class TaskManager:
    """Enterprise-grade background task management for TRAXOVO"""
    
    def __init__(self):
        self.tasks: Dict[str, BackgroundTask] = {}
        self.worker_thread = None
        self.running = False
        self.logger = self._setup_logger()
        
    def _setup_logger(self):
        """Setup optimized logging for background tasks"""
        logger = logging.getLogger('traxovo.background')
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers to prevent duplicates
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            
        # Add single handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - BACKGROUND - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def start_worker(self):
        """Start the background task worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            self.logger.info("Background task worker started")
    
    def stop_worker(self):
        """Stop the background task worker"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        self.logger.info("Background task worker stopped")
    
    def add_task(self, name: str, function: Callable, *args, **kwargs) -> str:
        """Add a new background task"""
        task_id = f"{name}_{int(time.time())}"
        task = BackgroundTask(
            id=task_id,
            name=name,
            function=function,
            args=args,
            kwargs=kwargs,
            status=TaskStatus.PENDING,
            created_at=datetime.now()
        )
        self.tasks[task_id] = task
        self.logger.info(f"Task added: {name} ({task_id})")
        return task_id
    
    def get_task_status(self, task_id: str) -> Dict:
        """Get task status and details"""
        if task_id not in self.tasks:
            return {"error": "Task not found"}
        
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "name": task.name,
            "status": task.status.value,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "error": task.error,
            "retry_count": task.retry_count,
            "result": task.result
        }
    
    def _worker_loop(self):
        """Main worker loop for processing tasks"""
        while self.running:
            try:
                # Find pending tasks
                pending_tasks = [task for task in self.tasks.values() 
                               if task.status == TaskStatus.PENDING]
                
                for task in pending_tasks:
                    if not self.running:
                        break
                    
                    self._execute_task(task)
                
                # Clean up old completed tasks (keep for 1 hour)
                self._cleanup_old_tasks()
                
                time.sleep(1)  # Check for new tasks every second
                
            except Exception as e:
                self.logger.error(f"Worker loop error: {e}")
                time.sleep(5)
    
    def _execute_task(self, task: BackgroundTask):
        """Execute a single background task"""
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            self.logger.info(f"Executing task: {task.name}")
            
            # Execute the task function
            result = task.function(*task.args, **task.kwargs)
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
            self.logger.info(f"Task completed: {task.name}")
            
        except Exception as e:
            self.logger.error(f"Task failed: {task.name} - {str(e)}")
            task.error = str(e)
            
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                self.logger.info(f"Retrying task: {task.name} (attempt {task.retry_count})")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
    
    def _cleanup_old_tasks(self):
        """Remove completed tasks older than 1 hour"""
        cutoff = datetime.now() - timedelta(hours=1)
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and 
                task.completed_at and task.completed_at < cutoff):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]

# Global task manager instance
task_manager = TaskManager()

class GaugeAPISync:
    """Optimized GAUGE API synchronization with background processing"""
    
    def __init__(self):
        self.api_url = os.environ.get('GAUGE_API_URL')
        self.api_key = os.environ.get('GAUGE_API_KEY')
        self.last_sync = None
        self.sync_interval = 300  # 5 minutes
        
    def schedule_sync(self) -> str:
        """Schedule a GAUGE API sync in the background"""
        return task_manager.add_task("gauge_api_sync", self._perform_sync)
    
    def _perform_sync(self) -> Dict:
        """Perform the actual GAUGE API synchronization"""
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
            
            response = requests.get(
                f"{self.api_url}/AssetList/28dcba94c01e453fa8e9215a068f30e4",
                headers=headers,
                timeout=30,
                verify=False
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Process asset data
                total_assets = len(data)
                active_assets = sum(1 for asset in data if asset.get('Active', False))
                categories = len(set(asset.get('AssetCategory', 'Unknown') for asset in data))
                
                self.last_sync = datetime.now()
                
                result = {
                    "status": "success",
                    "timestamp": self.last_sync.isoformat(),
                    "total_assets": total_assets,
                    "active_assets": active_assets,
                    "categories": categories,
                    "sync_duration": "optimized_background"
                }
                
                logging.info(f"GAUGE sync completed: {active_assets} active assets")
                return result
                
            else:
                raise Exception(f"API error: {response.status_code}")
                
        except Exception as e:
            logging.error(f"GAUGE sync failed: {e}")
            raise

def start_background_services():
    """Initialize all background services for TRAXOVO"""
    task_manager.start_worker()
    
    # Schedule initial GAUGE sync
    gauge_sync = GaugeAPISync()
    gauge_sync.schedule_sync()
    
    logging.info("TRAXOVO background services started")

def stop_background_services():
    """Stop all background services"""
    task_manager.stop_worker()
    logging.info("TRAXOVO background services stopped")

def get_system_status() -> Dict:
    """Get comprehensive system status"""
    return {
        "background_worker": "running" if task_manager.running else "stopped",
        "active_tasks": len([t for t in task_manager.tasks.values() 
                           if t.status == TaskStatus.RUNNING]),
        "pending_tasks": len([t for t in task_manager.tasks.values() 
                            if t.status == TaskStatus.PENDING]),
        "total_tasks": len(task_manager.tasks),
        "uptime": datetime.now().isoformat()
    }