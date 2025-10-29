"""
Batch processing module for handling multiple image conversions
"""

import os
import threading
import time
import uuid
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class BatchJob:
    job_id: str
    files: List[str] = field(default_factory=list)
    status: JobStatus = JobStatus.PENDING
    progress: int = 0
    total_files: int = 0
    completed_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

class BatchProcessor:
    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}
        self.lock = threading.Lock()
    
    def create_job(self, files: List[str]) -> str:
        """Create a new batch job"""
        job_id = str(uuid.uuid4())
        job = BatchJob(
            job_id=job_id,
            files=files,
            total_files=len(files)
        )
        
        with self.lock:
            self.jobs[job_id] = job
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get job by ID"""
        with self.lock:
            return self.jobs.get(job_id)
    
    def update_job_progress(self, job_id: str, completed_file: str = None, failed_file: str = None, error: str = None):
        """Update job progress"""
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return
            
            if completed_file:
                job.completed_files.append(completed_file)
            
            if failed_file:
                job.failed_files.append(failed_file)
                if error:
                    job.error_message = error
            
            job.progress = len(job.completed_files) + len(job.failed_files)
            job.updated_at = time.time()
            
            # Update status
            if job.progress >= job.total_files:
                if len(job.failed_files) == 0:
                    job.status = JobStatus.COMPLETED
                elif len(job.completed_files) == 0:
                    job.status = JobStatus.FAILED
                else:
                    job.status = JobStatus.COMPLETED  # Partial success
            elif job.progress > 0:
                job.status = JobStatus.PROCESSING
    
    def start_job(self, job_id: str):
        """Mark job as started"""
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job.status = JobStatus.PROCESSING
                job.updated_at = time.time()
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """Clean up old jobs"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.lock:
            jobs_to_remove = []
            for job_id, job in self.jobs.items():
                if current_time - job.created_at > max_age_seconds:
                    jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]

# Global batch processor instance
_batch_processor = None

def get_batch_processor() -> BatchProcessor:
    """Get the global batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor