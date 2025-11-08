## JSON Output

All commands support JSON output using the `--json` flag:

```bash
# Enqueue job with JSON output
python taskq.py --json enqueue "echo 'Hello World'"

# Get job details in JSON
python taskq.py --json get <job_id>

# List all jobs in JSON format
python taskq.py --json list

# Get system status in JSON
python taskq.py --json status

# Show configuration in JSON
python taskq.py --json config show