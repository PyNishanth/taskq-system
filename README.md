# TaskQ - Background Job Queue System

A production-grade CLI-based background job queue system with worker processes, exponential backoff retry mechanism, and Dead Letter Queue (DLQ).

## 🚀 Features

- ✅ **Job Management** - Enqueue, list, and track background jobs
- ✅ **Worker Processes** - Multiple concurrent workers with graceful shutdown
- ✅ **Retry Mechanism** - Exponential backoff with configurable retries
- ✅ **Dead Letter Queue** - Automatic movement of failed jobs to DLQ
- ✅ **Persistent Storage** - Job data survives restarts
- ✅ **JSON Support** - Machine-readable output with `--json` flag
- ✅ **CLI Interface** - Intuitive command-line interface
- ✅ **Thread-Safe** - Proper locking for concurrent operations

## Output
  
  [Demo Video](https://drive.google.com/file/d/10EHFDwPbWuUmInzmEy-om-jv43CEBGe3/view?usp=sharing)

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/PyNishanth/taskq-system.git
cd taskq-system

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install click==8.1.7
