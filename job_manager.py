import json
import uuid
import subprocess
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

class JobManager:
    def __init__(self):
        self.data_dir = Path("data")
        self.jobs_file = self.data_dir / "jobs.json"
        self.config_file = self.data_dir / "config.json"
        self.workers = {}
        self._lock = threading.Lock()
        self.init()
    
    def init(self):
        """Initialize data directory and files"""
        self.data_dir.mkdir(exist_ok=True)
        
        if not self.jobs_file.exists():
            self.save_jobs([])
        
        if not self.config_file.exists():
            default_config = {
                "max_retries": 3,
                "backoff_base": 2,
                "worker_count": 1
            }
            self.save_config(default_config)
    
    def get_jobs(self):
        """Load jobs from file"""
        try:
            with open(self.jobs_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def save_jobs(self, jobs):
        """Save jobs to file"""
        with open(self.jobs_file, 'w') as f:
            json.dump(jobs, f, indent=2, default=str)
    
    def get_config(self):
        """Load configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"max_retries": 3, "backoff_base": 2, "worker_count": 1}
    
    def save_config(self, config):
        """Save configuration"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def enqueue_job(self, command, max_retries=None):
        """Add a new job to the queue"""
        with self._lock:
            jobs = self.get_jobs()
            config = self.get_config()
            
            job = {
                "id": str(uuid.uuid4()),
                "command": command,
                "state": "pending",
                "attempts": 0,
                "max_retries": max_retries or config["max_retries"],
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "next_retry_at": None
            }
            
            jobs.append(job)
            self.save_jobs(jobs)
            return job
    
    def list_jobs(self, state=None):
        """List jobs, optionally filtered by state"""
        jobs = self.get_jobs()
        if state:
            return [job for job in jobs if job["state"] == state]
        return jobs
    
    def list_dlq(self):
        """List jobs in Dead Letter Queue"""
        return self.list_jobs("dead")
    
    def retry_dlq_job(self, job_id):
        """Retry a job from DLQ"""
        with self._lock:
            jobs = self.get_jobs()
            job_index = next((i for i, job in enumerate(jobs) 
                            if job["id"] == job_id and job["state"] == "dead"), None)
            
            if job_index is None:
                raise ValueError(f"Job {job_id} not found in DLQ")
            
            jobs[job_index]["state"] = "pending"
            jobs[job_index]["attempts"] = 0
            jobs[job_index]["updated_at"] = datetime.now().isoformat()
            jobs[job_index]["next_retry_at"] = None
            
            self.save_jobs(jobs)
            return jobs[job_index]
    
    def execute_command(self, command):
        """Execute a shell command"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            if result.returncode == 0:
                return {"success": True, "stdout": result.stdout, "stderr": result.stderr}
            else:
                return {"success": False, "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def process_job(self, worker_id):
        """Process a single job"""
        with self._lock:
            jobs = self.get_jobs()
            config = self.get_config()
            
            now = datetime.now()
            
            # Find a job to process
            job_index = None
            for i, job in enumerate(jobs):
                if job["state"] == "pending":
                    job_index = i
                    break
                elif (job["state"] == "failed" and 
                      job["next_retry_at"] and 
                      datetime.fromisoformat(job["next_retry_at"]) <= now):
                    job_index = i
                    break
            
            if job_index is None:
                return None
            
            job = jobs[job_index]
            
            # Lock the job
            job["state"] = "processing"
            job["updated_at"] = datetime.now().isoformat()
            self.save_jobs(jobs)
        
        # Process the job (outside lock to allow other operations)
        try:
            print(f"[Worker {worker_id}] Processing job {job['id']}: {job['command']}")
            
            result = self.execute_command(job["command"])
            
            with self._lock:
                jobs = self.get_jobs()
                job_index = next((i for i, j in enumerate(jobs) if j["id"] == job["id"]), None)
                
                if job_index is not None:
                    if result["success"]:
                        jobs[job_index]["state"] = "completed"
                        print(f"[Worker {worker_id}] Job {job['id']} completed successfully")
                    else:
                        jobs[job_index]["attempts"] += 1
                        
                        if jobs[job_index]["attempts"] >= jobs[job_index]["max_retries"]:
                            jobs[job_index]["state"] = "dead"
                            print(f"[Worker {worker_id}] Job {job['id']} moved to DLQ after {jobs[job_index]['attempts']} attempts")
                        else:
                            jobs[job_index]["state"] = "failed"
                            delay = config["backoff_base"] ** jobs[job_index]["attempts"]
                            next_retry = datetime.now() + timedelta(seconds=delay)
                            jobs[job_index]["next_retry_at"] = next_retry.isoformat()
                            print(f"[Worker {worker_id}] Job {job['id']} failed (attempt {jobs[job_index]['attempts']}/{jobs[job_index]['max_retries']}), retrying in {delay}s")
                    
                    jobs[job_index]["updated_at"] = datetime.now().isoformat()
                    self.save_jobs(jobs)
                    
        except Exception as e:
            print(f"[Worker {worker_id}] Error processing job {job['id']}: {e}")
        
        return job
    
    def worker_loop(self, worker_id, stop_event):
        """Main worker loop"""
        print(f"[Worker {worker_id}] Started")
        
        while not stop_event.is_set():
            job = self.process_job(worker_id)
            if not job:
                time.sleep(1)  # No jobs available, wait before checking again
    
    def start_worker(self, worker_id):
        """Start a worker thread"""
        stop_event = threading.Event()
        worker_thread = threading.Thread(
            target=self.worker_loop, 
            args=(worker_id, stop_event)
        )
        worker_thread.daemon = True
        worker_thread.start()
        
        self.workers[worker_id] = {
            "stop_event": stop_event,
            "thread": worker_thread
        }
    
    def start_workers(self, count=1):
        """Start multiple workers"""
        for i in range(1, count + 1):
            worker_id = f"worker-{i}"
            self.start_worker(worker_id)
        print(f"Started {count} worker(s)")
    
    def stop_workers(self):
        """Stop all workers gracefully"""
        worker_count = len(self.workers)
        for worker_id, worker_info in self.workers.items():
            worker_info["stop_event"].set()
            print(f"[Worker {worker_id}] Stopped")
        self.workers.clear()
        print(f"Stopped {worker_count} worker(s)")
    
    def get_status(self):
        """Get system status"""
        jobs = self.get_jobs()
        status = {
            "pending": len([j for j in jobs if j["state"] == "pending"]),
            "processing": len([j for j in jobs if j["state"] == "processing"]),
            "completed": len([j for j in jobs if j["state"] == "completed"]),
            "failed": len([j for j in jobs if j["state"] == "failed"]),
            "dead": len([j for j in jobs if j["state"] == "dead"]),
            "workers": len(self.workers)
        }
        return status
    
    def set_config(self, key, value):
        """Update configuration"""
        config = self.get_config()
        
        # Convert value to appropriate type
        if key in ["max_retries", "worker_count"]:
            value = int(value)
        elif key == "backoff_base":
            value = float(value)
        
        config[key] = value
        self.save_config(config)
        print(f"Config updated: {key} = {value}")