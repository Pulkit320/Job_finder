import asyncio
from typing import List
from datetime import datetime
from job_finder.sources.base import BaseSource
from job_finder.models.job import Job, LegitimacyType
from job_finder.utils.dates import format_date_iso
from job_finder.utils.parser import parse_work_type, parse_experience_level, filter_internships
from job_finder.utils.logger import get_logger

logger = get_logger()

# Popular tech companies with active India engineering offices using Greenhouse
GREENHOUSE_BOARDS = [
    "razorpay", "swiggy", "meesho", "groww", "browserstack", "cred",
    "thoughtworks", "inmobi", "chargebee", "postman", "sprinklr",
    "stripe", "databricks", "cloudflare", "datadog", "cohere",
    "huggingface", "replit", "pinecone", "perplexity", "scaleai", "anthropic"
]

class GreenhouseSource(BaseSource):
    source_name = "Greenhouse"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Searching across {len(GREENHOUSE_BOARDS)} Greenhouse company boards...")
        jobs: List[Job] = []

        tasks = [self._fetch_board_jobs(board, keywords, locations) for board in GREENHOUSE_BOARDS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                jobs.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"[{self.source_name}] Board error: {res}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} total jobs matching criteria.")
        return jobs

    async def _fetch_board_jobs(self, board: str, keywords: List[str], locations: List[str]) -> List[Job]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
        data = await self.fetch_url(url, json=True)
        if not data or not isinstance(data, dict) or "jobs" not in data:
            return []

        company_name = board.capitalize()
        matched_jobs: List[Job] = []

        for item in data.get("jobs", []):
            title = item.get("title", "")
            location_name = item.get("location", {}).get("name", "Not specified")
            app_url = item.get("absolute_url", "")
            updated_at = item.get("updated_at", "")
            
            # Check title against keywords
            title_match = any(kw.lower() in title.lower() for kw in keywords)
            if not title_match:
                continue

            if not filter_internships(title):
                continue

            content = item.get("content", "")
            post_date = format_date_iso(datetime.now())
            if updated_at:
                post_date = updated_at[:10]

            job = Job(
                **{
                    "Job Title": title,
                    "Company": company_name,
                    "Posting Date": post_date,
                    "Application Deadline": "Not specified",
                    "Location": location_name,
                    "Remote / Hybrid / Onsite": parse_work_type(title, location_name, content),
                    "Experience": parse_experience_level(title, content),
                    "Employment Type": "Full-time",
                    "Salary": "Not specified",
                    "Application Link": app_url,
                    "Company Career Link": f"https://boards.greenhouse.io/{board}",
                    "Source": "Greenhouse",
                    "Legitimacy": LegitimacyType.MAJOR_JOB_BOARD.value,
                    "Verification Status": "Verified",
                    "Description": content[:2000] if content else f"Greenhouse posting for {title} at {company_name}",
                    "Date Discovered": format_date_iso(datetime.now()),
                }
            )
            matched_jobs.append(job)

        return matched_jobs
