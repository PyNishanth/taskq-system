#!/usr/bin/env python3

import subprocess
import json
import time

def test_json_output():
    """Test the JSON output functionality"""
    print("=== Testing JSON Output ===\n")
    
    # Test 1: Enqueue job with JSON output
    print("1. Enqueue job with JSON output:")
    result = subprocess.run([
        'python', 'taskq.py', '--json', 'enqueue', 
        'echo "Hello JSON World"'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        job_data = json.loads(result.stdout)
        print("✅ Job enqueued with JSON output:")
        print(json.dumps(job_data, indent=2))
        job_id = job_data['id']
    else:
        print("❌ Failed to enqueue job")
        return
    
    # Test 2: Get job details with JSON
    print(f"\n2. Get job details for {job_id}:")
    result = subprocess.run([
        'python', 'taskq.py', '--json', 'get', job_id
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ Job details:")
        print(json.dumps(json.loads(result.stdout), indent=2))
    
    # Test 3: List all jobs with JSON
    print("\n3. List all jobs with JSON output:")
    result = subprocess.run([
        'python', 'taskq.py', '--json', 'list'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        jobs = json.loads(result.stdout)
        print(f"✅ Found {len(jobs)} jobs")
        print(json.dumps(jobs, indent=2))
    
    # Test 4: Get status with JSON
    print("\n4. Get system status with JSON:")
    result = subprocess.run([
        'python', 'taskq.py', '--json', 'status'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        status = json.loads(result.stdout)
        print("✅ System status:")
        print(json.dumps(status, indent=2))
    
    # Test 5: Show config with JSON
    print("\n5. Show configuration with JSON:")
    result = subprocess.run([
        'python', 'taskq.py', '--json', 'config', 'show'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        config = json.loads(result.stdout)
        print("✅ Configuration:")
        print(json.dumps(config, indent=2))
    
    print("\n=== JSON Test Complete ===")

if __name__ == '__main__':
    test_json_output()