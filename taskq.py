#!/usr/bin/env python3

import click
import json
from job_manager import JobManager

@click.group()
@click.pass_context
@click.option('--json', 'json_output', is_flag=True, help='Output in JSON format')
def cli(ctx, json_output):
    """TaskQ - CLI-based background job queue system"""
    ctx.obj = JobManager()
    ctx.obj.json_output = json_output

def format_output(data, json_output=False):
    """Format output as JSON or pretty text"""
    if json_output:
        return json.dumps(data, indent=2, default=str)
    return data

@cli.command()
@click.argument('command')
@click.option('--max-retries', '-r', type=int, help='Maximum number of retries')
@click.pass_obj
def enqueue(job_manager, command, max_retries):
    """Add a new job to the queue"""
    job = job_manager.enqueue_job(command, max_retries)
    if job_manager.json_output:
        click.echo(json.dumps(job, indent=2, default=str))
    else:
        click.echo(f"Enqueued job {job['id']}: {job['command']}")

@cli.group()
def worker():
    """Worker management commands"""
    pass

@worker.command()
@click.option('--count', '-c', default=1, help='Number of workers to start')
@click.pass_obj
def start(job_manager, count):
    """Start workers"""
    result = job_manager.start_workers(count)
    if job_manager.json_output:
        click.echo(json.dumps({"message": f"Started {count} worker(s)", "workers": count}, indent=2))

@worker.command()
@click.pass_obj
def stop(job_manager):
    """Stop all workers gracefully"""
    worker_count = len(job_manager.workers)
    job_manager.stop_workers()
    if job_manager.json_output:
        click.echo(json.dumps({"message": f"Stopped {worker_count} worker(s)", "workers_stopped": worker_count}, indent=2))

@cli.command()
@click.pass_obj
def status(job_manager):
    """Show summary of all job states & active workers"""
    status = job_manager.get_status()
    if job_manager.json_output:
        click.echo(json.dumps(status, indent=2))
    else:
        click.echo("Task Queue Status:")
        click.echo(f"  Pending: {status['pending']}")
        click.echo(f"  Processing: {status['processing']}")
        click.echo(f"  Completed: {status['completed']}")
        click.echo(f"  Failed: {status['failed']}")
        click.echo(f"  Dead: {status['dead']}")
        click.echo(f"  Active Workers: {status['workers']}")

@cli.command()
@click.option('--state', help='Filter by state (pending, processing, completed, failed, dead)')
@click.pass_obj
def list(job_manager, state):
    """List jobs by state"""
    jobs = job_manager.list_jobs(state)
    
    if job_manager.json_output:
        click.echo(json.dumps(jobs, indent=2, default=str))
    else:
        if not jobs:
            click.echo("No jobs found")
            return
        
        for job in jobs:
            click.echo(f"{job['id']}: {job['command']} [{job['state']}] (attempts: {job['attempts']}/{job['max_retries']})")

@cli.group()
def dlq():
    """Dead Letter Queue commands"""
    pass

@dlq.command()
@click.pass_obj
def list(job_manager):
    """List jobs in Dead Letter Queue"""
    jobs = job_manager.list_dlq()
    
    if job_manager.json_output:
        click.echo(json.dumps(jobs, indent=2, default=str))
    else:
        if not jobs:
            click.echo("DLQ is empty")
            return
        
        click.echo("Dead Letter Queue:")
        for job in jobs:
            click.echo(f"  {job['id']}: {job['command']} (failed after {job['attempts']} attempts)")

@dlq.command()
@click.argument('job_id')
@click.pass_obj
def retry(job_manager, job_id):
    """Retry a job from DLQ"""
    try:
        job = job_manager.retry_dlq_job(job_id)
        if job_manager.json_output:
            click.echo(json.dumps({"message": f"Job {job_id} moved back to pending state", "job": job}, indent=2, default=str))
        else:
            click.echo(f"Job {job_id} moved back to pending state")
    except ValueError as e:
        if job_manager.json_output:
            click.echo(json.dumps({"error": str(e)}, indent=2))
        else:
            click.echo(f"Error: {e}")

@cli.group()
def config():
    """Configuration management"""
    pass

@config.command()
@click.argument('key')
@click.argument('value')
@click.pass_obj
def set(job_manager, key, value):
    """Set configuration value"""
    job_manager.set_config(key, value)
    if job_manager.json_output:
        config = job_manager.get_config()
        click.echo(json.dumps({"message": f"Config updated: {key} = {value}", "config": config}, indent=2))

@config.command()
@click.pass_obj
def show(job_manager):
    """Show current configuration"""
    config = job_manager.get_config()
    if job_manager.json_output:
        click.echo(json.dumps(config, indent=2))
    else:
        click.echo("Current Configuration:")
        for key, value in config.items():
            click.echo(f"  {key}: {value}")

@cli.command()
@click.argument('job_id')
@click.pass_obj
def get(job_manager, job_id):
    """Get detailed information about a specific job"""
    jobs = job_manager.list_jobs()
    job = next((j for j in jobs if j['id'] == job_id), None)
    
    if job:
        if job_manager.json_output:
            click.echo(json.dumps(job, indent=2, default=str))
        else:
            click.echo(f"Job ID: {job['id']}")
            click.echo(f"Command: {job['command']}")
            click.echo(f"State: {job['state']}")
            click.echo(f"Attempts: {job['attempts']}/{job['max_retries']}")
            click.echo(f"Created: {job['created_at']}")
            click.echo(f"Updated: {job['updated_at']}")
            if job['next_retry_at']:
                click.echo(f"Next Retry: {job['next_retry_at']}")
    else:
        if job_manager.json_output:
            click.echo(json.dumps({"error": f"Job {job_id} not found"}, indent=2))
        else:
            click.echo(f"Job {job_id} not found")

if __name__ == '__main__':
    cli()