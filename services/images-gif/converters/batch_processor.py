"""
배치 GIF 변환 처리 모듈
대량 파일 처리를 위한 큐 기반 병렬 처리 시스템
"""

import os
import uuid
import threading
import queue
import time
import zipfile
import io
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .image_to_gif import image_to_gif, _is_supported_image


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class FileTask:
    """개별 파일 변환 작업"""
    file_path: str
    original_name: str
    output_path: str
    status: JobStatus = JobStatus.PENDING
    error_message: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


@dataclass
class BatchJob:
    """배치 변환 작업"""
    job_id: str
    total_files: int
    completed_files: int = 0
    failed_files: int = 0
    status: JobStatus = JobStatus.PENDING
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    output_dir: str = ""
    zip_path: Optional[str] = None
    tasks: List[FileTask] = None
    quality: str = "medium"
    resize_factor: float = 1.0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.tasks is None:
            self.tasks = []
    
    @property
    def progress_percentage(self) -> float:
        """진행률 계산 (0-100)"""
        if self.total_files == 0:
            return 0.0
        return (self.completed_files + self.failed_files) / self.total_files * 100
    
    @property
    def is_finished(self) -> bool:
        """작업 완료 여부"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
    
    def to_dict(self) -> dict:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        data = asdict(self)
        data['status'] = self.status.value
        for task in data['tasks']:
            task['status'] = task['status'].value
        return data


class BatchProcessor:
    """배치 GIF 변환 처리기"""
    
    def __init__(self, max_workers: int = 4, max_queue_size: int = 1000):
        self.max_workers = max_workers
        self.max_queue_size = max_queue_size
        self.jobs: Dict[str, BatchJob] = {}
        self.task_queue = queue.Queue(maxsize=max_queue_size)
        self.workers = []
        self.running = False
        self.lock = threading.Lock()
        
        # 워커 스레드 시작
        self._start_workers()
    
    def _start_workers(self):
        """워커 스레드들을 시작"""
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, name=f"BatchWorker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """워커 스레드 메인 루프"""
        while self.running:
            try:
                # 작업 가져오기 (타임아웃 1초)
                task_data = self.task_queue.get(timeout=1.0)
                if task_data is None:  # 종료 신호
                    break
                
                job_id, task_index = task_data
                
                with self.lock:
                    if job_id not in self.jobs:
                        continue
                    
                    job = self.jobs[job_id]
                    if job.status == JobStatus.CANCELLED:
                        continue
                    
                    if task_index >= len(job.tasks):
                        continue
                    
                    task = job.tasks[task_index]
                    if task.status != JobStatus.PENDING:
                        continue
                    
                    # 작업 시작 표시
                    task.status = JobStatus.PROCESSING
                    task.start_time = time.time()
                    
                    if job.status == JobStatus.PENDING:
                        job.status = JobStatus.PROCESSING
                        job.started_at = time.time()
                
                # 실제 변환 작업 수행
                try:
                    success, message = image_to_gif(
                        task.file_path,
                        task.output_path,
                        quality=job.quality,
                        resize_factor=job.resize_factor
                    )
                    
                    with self.lock:
                        task.end_time = time.time()
                        if success:
                            task.status = JobStatus.COMPLETED
                            job.completed_files += 1
                        else:
                            task.status = JobStatus.FAILED
                            task.error_message = message
                            job.failed_files += 1
                        
                        # 작업 완료 확인
                        if job.completed_files + job.failed_files >= job.total_files:
                            job.completed_at = time.time()
                            if job.failed_files == 0:
                                job.status = JobStatus.COMPLETED
                                # ZIP 파일 생성
                                self._create_zip_file(job)
                            else:
                                job.status = JobStatus.FAILED
                
                except Exception as e:
                    with self.lock:
                        task.end_time = time.time()
                        task.status = JobStatus.FAILED
                        task.error_message = str(e)
                        job.failed_files += 1
                        
                        if job.completed_files + job.failed_files >= job.total_files:
                            job.completed_at = time.time()
                            job.status = JobStatus.FAILED
                
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker error: {e}")
                continue
    
    def _create_zip_file(self, job: BatchJob):
        """완료된 작업의 결과 파일들을 ZIP으로 압축"""
        try:
            zip_filename = f"{job.job_id}_results.zip"
            zip_path = os.path.join(job.output_dir, zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for task in job.tasks:
                    if task.status == JobStatus.COMPLETED and os.path.exists(task.output_path):
                        # ZIP 내에서의 파일명은 원본 파일명 기반으로 생성
                        base_name = os.path.splitext(task.original_name)[0]
                        zip_filename = f"{base_name}.gif"
                        zipf.write(task.output_path, zip_filename)
            
            job.zip_path = zip_path
            
        except Exception as e:
            print(f"ZIP 생성 실패: {e}")
    
    def create_batch_job(
        self,
        file_paths: List[str],
        original_names: List[str],
        output_dir: str,
        quality: str = "medium",
        resize_factor: float = 1.0
    ) -> str:
        """
        배치 변환 작업 생성
        
        Args:
            file_paths: 입력 파일 경로 리스트
            original_names: 원본 파일명 리스트
            output_dir: 출력 디렉토리
            quality: 품질 설정
            resize_factor: 크기 조정 비율
        
        Returns:
            작업 ID
        """
        job_id = str(uuid.uuid4())
        
        # 출력 디렉토리 생성
        os.makedirs(output_dir, exist_ok=True)
        
        # 작업 생성
        tasks = []
        valid_files = []
        valid_names = []
        
        for file_path, original_name in zip(file_paths, original_names):
            if _is_supported_image(file_path):
                # 출력 파일명 생성
                base_name = os.path.splitext(original_name)[0]
                output_filename = f"{base_name}.gif"
                output_path = os.path.join(output_dir, f"{job_id}_{output_filename}")
                
                task = FileTask(
                    file_path=file_path,
                    original_name=original_name,
                    output_path=output_path
                )
                tasks.append(task)
                valid_files.append(file_path)
                valid_names.append(original_name)
        
        if not tasks:
            raise ValueError("변환 가능한 이미지 파일이 없습니다.")
        
        # 배치 작업 생성
        job = BatchJob(
            job_id=job_id,
            total_files=len(tasks),
            output_dir=output_dir,
            tasks=tasks,
            quality=quality,
            resize_factor=resize_factor
        )
        
        with self.lock:
            self.jobs[job_id] = job
        
        # 작업을 큐에 추가
        for i in range(len(tasks)):
            self.task_queue.put((job_id, i))
        
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """작업 상태 조회"""
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            return job.to_dict()
    
    def get_job_zip_path(self, job_id: str) -> Optional[str]:
        """작업 결과 ZIP 파일 경로 반환"""
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            if job.status == JobStatus.COMPLETED and job.zip_path:
                if os.path.exists(job.zip_path):
                    return job.zip_path
            
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """작업 취소"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.is_finished:
                return False
            
            job.status = JobStatus.CANCELLED
            job.completed_at = time.time()
            
            # 대기 중인 작업들을 취소 상태로 변경
            for task in job.tasks:
                if task.status == JobStatus.PENDING:
                    task.status = JobStatus.CANCELLED
            
            return True
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """오래된 작업 정리"""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        with self.lock:
            jobs_to_remove = []
            
            for job_id, job in self.jobs.items():
                if job.is_finished:
                    age = current_time - job.created_at
                    if age > max_age_seconds:
                        # 관련 파일들 삭제
                        try:
                            for task in job.tasks:
                                if os.path.exists(task.output_path):
                                    os.remove(task.output_path)
                            
                            if job.zip_path and os.path.exists(job.zip_path):
                                os.remove(job.zip_path)
                        except Exception as e:
                            print(f"파일 삭제 실패: {e}")
                        
                        jobs_to_remove.append(job_id)
            
            for job_id in jobs_to_remove:
                del self.jobs[job_id]
    
    def shutdown(self):
        """배치 처리기 종료"""
        self.running = False
        
        # 모든 워커에게 종료 신호 전송
        for _ in self.workers:
            self.task_queue.put(None)
        
        # 워커 스레드들이 종료될 때까지 대기
        for worker in self.workers:
            worker.join(timeout=5.0)


# 전역 배치 처리기 인스턴스
_batch_processor = None

def get_batch_processor() -> BatchProcessor:
    """전역 배치 처리기 인스턴스 반환"""
    global _batch_processor
    if _batch_processor is None:
        _batch_processor = BatchProcessor()
    return _batch_processor