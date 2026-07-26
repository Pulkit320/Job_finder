# 🤖 Job Finder Bot CLI

> An autonomous, high-performance Python CLI tool designed to search, verify, deduplicate, and report NEW software and AI engineering job postings published across 10+ sources within the last 3 days.

---

## 🌟 Key Features

- **🎯 Target Role Focus**:
  - Core: `Software Engineer`, `AI Engineer`, `Prompt Engineer`
  - Related: `Machine Learning Engineer`, `Applied AI Engineer`, `LLM Engineer`, `Generative AI Engineer`, `AI Developer`, `Prompt Developer`
- **🌐 10 Integrated Job Sources**:
  1. **Official Company Career Pages** (OpenAI, Anthropic, Google, Microsoft, Meta)
  2. **Greenhouse API & Scraper** (Stripe, Databricks, Figma, Scale, Vercel, etc.)
  3. **Lever API & Scraper** (Palantir, Spotify, Retool, Supabase, Notion, etc.)
  4. **Workday Jobs** (NVIDIA, Adobe, Salesforce)
  5. **Wellfound** (AngelList Startup Postings)
  6. **Y Combinator Jobs** (Work at a Startup)
  7. **Google Search Index**
  8. **LinkedIn Jobs** (Public Guest API)
  9. **Indeed** (Public search with anti-bot fallback)
  10. **Naukri** (Public Search API)
- **⏱️ 3-Day Posting Age Limit**: Ignores stale postings older than 3 days.
- **🎓 Smart Internship Filter**: Ignores unrelated internships; keeps internships *only* if the title contains *Software Engineer*, *AI Engineer*, or *Prompt Engineer*.
- **🛡️ Automated Verification**: Validates HTTP application link reachability, checks description quality, and classifies listing legitimacy (`Official Company Careers`, `Major Job Board`, `Third-party Aggregator`, `Suspicious`).
- **⚡ RapidFuzz Deduplication**: Combines exact link matching, title+company normalization, and RapidFuzz fuzzy string similarity (>95%) while preserving highest priority sources.
- **🎨 Rich Terminal UI**: Interactive progress spinners, formatted tables, panels, and colored metrics.
- **🤖 Complete Automation**: Pre-configured GitHub Actions, Linux Cron, and Windows Task Scheduler scripts for running every 2 days.

---

## 🛠️ Tech Stack

- **Python 3.12+**
- **Typer**: Modern CLI command parsing
- **Rich**: Terminal formatting, tables, spinners, and progress indicators
- **aiohttp / asyncio / requests**: High-throughput concurrent asynchronous web scraping
- **Playwright**: Dynamic JavaScript rendering fallback
- **BeautifulSoup4 & lxml**: Robust HTML parsing
- **RapidFuzz**: High-performance string fuzzy similarity calculation
- **Pydantic v2**: Data validation and type-safe schemas
- **Loguru**: Rotated file logging and stderr output
- **Pandas**: Structured dataset exports to CSV and JSON

---

## 📦 Installation & Setup

### 1. Clone & Enter Directory
```bash
cd /home/pulkit/applications/job_finder
```

### 2. Create Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Install Playwright Browsers
```bash
playwright install chromium
```

---

## 🚀 CLI Usage & Commands

Run all commands using `python main.py <command>`:

### 1. Perform Full Search (`search`)
Searches all 10 sources concurrently, filters, verifies, deduplicates, and saves output to `data/jobs.csv`, `data/jobs.json`, and `data/reports/report.md`.
```bash
python main.py search
```

### 2. View Database Statistics (`stats`)
Displays formatted Rich tables showing open positions by company, source platform, and geographical location.
```bash
python main.py stats
```

### 3. Re-Verify Stored Listings (`verify`)
Re-checks link accessibility and legitimacy status for all jobs currently stored in the local database.
```bash
python main.py verify
```

### 4. Export Datasets & Markdown Report (`export`)
Manually triggers export of database records to CSV, JSON, and Markdown format.
```bash
python main.py export
```

### 5. Clean Database (`clean`)
Removes duplicates and expired listings older than 3 days.
```bash
python main.py clean
```

### 6. View or Edit Configuration (`config`)
View current settings or update configuration without altering code.
```bash
# View configuration
python main.py config --show

# Change keywords
python main.py config --keywords "AI Engineer, Software Engineer, LLM Engineer"

# Change posting age limit
python main.py config --posting-age 3

# Filter remote-only
python main.py config --remote-only true
```

---

## ⚙️ Configuration File (`data/config.json`)

All operational settings can be customized in `data/config.json`:
```json
{
  "keywords": [
    "Software Engineer",
    "AI Engineer",
    "Prompt Engineer",
    "Machine Learning Engineer",
    "Applied AI Engineer",
    "LLM Engineer",
    "Generative AI Engineer",
    "AI Developer",
    "Prompt Developer"
  ],
  "locations": [
    "Remote",
    "United States",
    "India",
    "San Francisco, CA"
  ],
  "remote_only": false,
  "posting_age_days": 3,
  "max_concurrent_requests": 10,
  "enabled_sources": [
    "greenhouse",
    "lever",
    "workday",
    "wellfound",
    "yc",
    "careers",
    "google",
    "linkedin",
    "indeed",
    "naukri"
  ],
  "fuzzy_threshold": 95.0
}
```

---

## ➕ Adding a New Job Source

To extend **Job Finder Bot** with a custom source:

1. Create a new file in `sources/` (e.g., `sources/my_board.py`).
2. Inherit from `BaseSource`:
```python
from typing import List
from job_finder.sources.base import BaseSource
from job_finder.models.job import Job

class MyBoardSource(BaseSource):
    source_name = "My Custom Board"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        # Implement fetching & parsing logic
        return []
```
3. Register the new source in `sources/__init__.py` inside `SOURCES_MAP`.

---

## ⏰ Automation & Schedules (Every 2 Days)

### GitHub Actions
A complete workflow is provided at `automation/.github/workflows/job_finder.yml`. It runs automatically every 2 days (`cron: '0 0 */2 * *'`) and commits fresh job data back to the repository.

### Linux Cron Job
Add `automation/cron_job.sh` to your crontab:
```bash
crontab -e
# Add line:
0 8 */2 * * /bin/bash /home/pulkit/applications/job_finder/automation/cron_job.sh >> /home/pulkit/applications/job_finder/logs/cron.log 2>&1
```

### Windows Task Scheduler
Run the PowerShell script located at `automation/windows_task.ps1` as Administrator to register a recurring 2-day task.

---

## 🐛 Troubleshooting & FAQ

- **Source returns 0 results / Blocked by Anti-Bot**: The scraper will catch the error, log a warning, and continue execution without crashing.
- **Log Files**: Check detailed logs in `logs/job_finder.log`.
- **Playwright missing browsers error**: Run `playwright install chromium`.
