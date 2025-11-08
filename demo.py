#!/usr/bin/env python3

import time
from job_manager import JobManager

def test_demo():
    """Demo script to test the queue system"""
    print("=== TaskQ Demo ===\n")
    
    job_manager = JobManager()
    
    # Enqueue some test jobs
    print("1. Enqueuing test jobs...")
    job1 = job_manager.enqueue_job("echo 'Hello World'")
    job2 = job_manager.enqueue_job("timeout 2")
    job3 = job_manager.enqueue_job("invalid_command_123")  # This will fail
    job4 = job_manager.enqueue_job("dir", max_retries=2)  # Custom retries
    
    print(f"Enqueued job: {job1['id']} - {job1['command']}")
    print(f"Enqueued job: {job2['id']} - {job2['command']}")
    print(f"Enqueued job: {job3['id']} - {job3['command']}")
    print(f"Enqueued job: {job4['id']} - {job4['command']}")
    
    # Start workers
    print("\n2. Starting workers...")
    job_manager.start_workers(2)
    
    # Show status
    print("\n3. Initial status:")
    status = job_manager.get_status()
    print(f"   Pending: {status['pending']}, Workers: {status['workers']}")
    
    # Let workers process for a bit
    print("\n4. Letting workers process jobs for 10 seconds...")
    time.sleep(10)
    
    # Show final status
    print("\n5. Final status:")
    status = job_manager.get_status()
    print(f"   Pending: {status['pending']}")
    print(f"   Processing: {status['processing']}")
    print(f"   Completed: {status['completed']}")
    print(f"   Failed: {status['failed']}")
    print(f"   Dead: {status['dead']}")
    
    # Show DLQ
    print("\n6. Dead Letter Queue:")
    dlq_jobs = job_manager.list_dlq()
    for job in dlq_jobs:
        print(f"   {job['id']}: {job['command']}")
    
    # Stop workers
    print("\n7. Stopping workers...")
    job_manager.stop_workers()
    
    print("\n=== Demo Complete ===")

if __name__ == '__main__':
    test_demo()