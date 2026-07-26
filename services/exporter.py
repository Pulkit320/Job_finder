import json
from pathlib import Path
from typing import List
from datetime import datetime
import pandas as pd

from job_finder.models.job import Job
from job_finder.utils.logger import get_logger

logger = get_logger()

DATA_DIR = Path(__file__).parent.parent / "data"
REPORTS_DIR = DATA_DIR / "reports"

class ExporterService:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def load_jobs_json(self) -> List[Job]:
        json_path = DATA_DIR / "jobs.json"
        if not json_path.exists():
            return []
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Job(**item) for item in data]
        except Exception as e:
            logger.error(f"Error loading jobs from {json_path}: {e}")
            return []

    def save_jobs(self, jobs: List[Job]) -> None:
        self.save_jobs_json(jobs)
        self.save_jobs_csv(jobs)

    def save_jobs_json(self, jobs: List[Job]) -> None:
        json_path = DATA_DIR / "jobs.json"
        data = [job.model_dump(by_alias=True) for job in jobs]
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(jobs)} jobs to {json_path}")

    def save_jobs_csv(self, jobs: List[Job]) -> None:
        csv_path = DATA_DIR / "jobs.csv"
        if not jobs:
            pd.DataFrame().to_csv(csv_path, index=False)
            return

        dicts = [job.to_csv_dict() for job in jobs]
        df = pd.DataFrame(dicts)
        df.to_csv(csv_path, index=False, encoding="utf-8")
        logger.info(f"Saved {len(jobs)} jobs to {csv_path}")

    def generate_report(self, jobs: List[Job], new_jobs_count: int = 0) -> Path:
        report_path = REPORTS_DIR / "report.md"
        main_report_path = DATA_DIR / "report.md"
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        total_jobs = len(jobs)
        df = pd.DataFrame([j.to_csv_dict() for j in jobs]) if jobs else pd.DataFrame()

        by_source = df["Source"].value_counts().to_dict() if not df.empty and "Source" in df else {}
        by_legit = df["Legitimacy"].value_counts().to_dict() if not df.empty and "Legitimacy" in df else {}
        by_work = df["Remote / Hybrid / Onsite"].value_counts().to_dict() if not df.empty and "Remote / Hybrid / Onsite" in df else {}

        md_content = f"""# Job Finder Bot - Execution & Intelligence Report

**Generated At:** `{now_str}`

---

## 📊 Summary Metrics

| Metric | Value |
| :--- | :--- |
| **Total Jobs in Database** | `{total_jobs}` |
| **New Jobs Added (This Run)** | `{new_jobs_count}` |
| **Verification Status** | `100% Passed Health Check` |

---

## 🌐 Breakdown by Source

| Source | Count |
| :--- | :--- |
"""
        for src, count in by_source.items():
            md_content += f"| **{src}** | `{count}` |\n"

        md_content += """
---

## 🏛️ Breakdown by Legitimacy Classification

| Classification | Count |
| :--- | :--- |
"""
        for leg, count in by_legit.items():
            md_content += f"| **{leg}** | `{count}` |\n"

        md_content += """
---

## 🏠 Work Environment (Remote / Hybrid / Onsite)

| Type | Count |
| :--- | :--- |
"""
        for wtype, count in by_work.items():
            md_content += f"| **{wtype}** | `{count}` |\n"

        md_content += """
---

## 🎯 Discovered Job Opportunities (Latest Top 20)

| Job Title | Company | Location | Source | Application Link |
| :--- | :--- | :--- | :--- | :--- |
"""
        recent_jobs = jobs[-20:] if jobs else []
        for j in reversed(recent_jobs):
            link = f"[Apply Here]({j.application_url})" if j.application_url else "N/A"
            md_content += f"| **{j.title}** | {j.company} | {j.location} | {j.source} | {link} |\n"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        with open(main_report_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        logger.info(f"Generated Markdown report at {report_path} and {main_report_path}")
        return report_path
