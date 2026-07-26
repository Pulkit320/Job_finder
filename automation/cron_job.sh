#!/usr/bin/env bash
# ==============================================================================
# Job Finder Bot - Linux Cron Script (Runs every 2 days)
# ==============================================================================
# Add to crontab via `crontab -e`:
# 0 8 */2 * * /bin/bash /home/pulkit/applications/job_finder/automation/cron_job.sh >> /home/pulkit/applications/job_finder/logs/cron.log 2>&1

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=================================================="
echo "Starting Scheduled Job Finder Run: $(date)"
echo "=================================================="

# Activate virtual environment if present
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run Job Finder Search
python3 main.py search

echo "Job Finder Run Finished: $(date)"
