"""
Batch processing module for handling multiple image conversions
"""

import os
import threading
import time
import uuid
import zipfile
import tempfile
import shutil
from enum import Enum
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from .multi_format_converter import MultiFormatConverter

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
    output_format: str = 'webp'
    quality: str = 'medium'
    resize_factor: float = 1.0
    preserve_transparency: bool = False
    result_zip_path: Optional[str] = None

class BatchProcessor:
    def __init__(self):
        self.jobs: Dict[str, BatchJob] = {}
        self.lock = threading.Lock()
        self.converter = MultiFormatConverter()
        self.temp_dir = tempfile.mkdtemp(prefix='batch_convert_')
    
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

    def start_batch_job(self, files, output_format='webp', quality='medium', resize_factor=1.0, preserve_transparency=False):
        """Start a new batch conversion job"""
        # Save uploaded files to temp directory
        temp_files = []
        job_temp_dir = os.path.join(self.temp_dir, str(uuid.uuid4()))
        os.makedirs(job_temp_dir, exist_ok=True)
        
        for file in files:
            temp_path = os.path.join(job_temp_dir, file.filename)
            file.save(temp_path)
            temp_files.append(temp_path)
        
        # Create job
        job_id = str(uuid.uuid4())
        job = BatchJob(
            job_id=job_id,
            files=temp_files,
            total_files=len(temp_files),
            output_format=output_format,
            quality=quality,
            resize_factor=resize_factor,
            preserve_transparency=preserve_transparency
        )
        
        with self.lock:
            self.jobs[job_id] = job
        
        # Start processing in background thread
        thread = threading.Thread(target=self._process_batch_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return job_id
    
    def _process_batch_job(self, job_id):
        """Process batch job in background"""
        job = self.get_job(job_id)
        if not job:
            return
        
        self.start_job(job_id)
        
        # Create output directory for this job
        output_dir = os.path.join(self.temp_dir, f'output_{job_id}')
        os.makedirs(output_dir, exist_ok=True)
        
        converted_files = []
        
        for file_path in job.files:
            try:
                # Convert file
                output_path = self.converter.convert_image(
                    input_path=file_path,
                    output_format=job.output_format,
                    quality=job.quality,
                    resize_factor=job.resize_factor,
                    preserve_transparency=job.preserve_transparency,
                    output_dir=output_dir
                )
                
                if output_path and os.path.exists(output_path):
                    converted_files.append(output_path)
                    self.update_job_progress(job_id, completed_file=os.path.basename(file_path))
                else:
                    self.update_job_progress(job_id, failed_file=os.path.basename(file_path), error="변환 실패")
                    
            except Exception as e:
                self.update_job_progress(job_id, failed_file=os.path.basename(file_path), error=str(e))
        
        # Create ZIP file with converted images
        if converted_files:
            zip_path = os.path.join(self.temp_dir, f'batch_result_{job_id}.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in converted_files:
                    zipf.write(file_path, os.path.basename(file_path))
            
            # Update job with zip path
            with self.lock:
                if job_id in self.jobs:
                    self.jobs[job_id].result_zip_path = zip_path
    
    def get_job_status(self, job_id):
        """Get job status for API response"""
        job = self.get_job(job_id)
        if not job:
            return {'error': '작업을 찾을 수 없습니다.'}
        
        progress_percentage = (job.progress / job.total_files * 100) if job.total_files > 0 else 0
        
        return {
            'job_id': job_id,
            'status': job.status.value,
            'progress': progress_percentage,
            'total_files': job.total_files,
            'completed_files': len(job.completed_files),
            'failed_files': len(job.failed_files),
            'error_message': job.error_message
        }
    
    def get_result_zip(self, job_id):
        """Get the result ZIP file path for a completed job"""
        job = self.get_job(job_id)
        if not job or job.status != JobStatus.COMPLETED:
            return None
        
        return job.result_zip_path

# Global batch processor instance
_batch_processor = None

def get_batch_processor() -> BatchProcessor:
    """Get the global batch processor instance"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor