import asyncio
from typing import List
from datetime import datetime

try:
    from sources.base import BaseSource
    from models.job import Job, LegitimacyType
    from utils.dates import format_date_iso
    from utils.parser import parse_work_type, parse_experience_level, filter_internships
    from utils.logger import get_logger
except ModuleNotFoundError:
    from job_finder.sources.base import BaseSource
    from job_finder.models.job import Job, LegitimacyType
    from job_finder.utils.dates import format_date_iso
    from job_finder.utils.parser import parse_work_type, parse_experience_level, filter_internships
    from job_finder.utils.logger import get_logger

logger = get_logger()

LEVER_COMPANIES = [
    "palantir", "spotify", "postman", "retool", "linear", "supabase",
    "modal", "langchain", "anyscale", "n8n", "sourcegraph", "hex",
    "weightsandbiases", "vanta", "brex", "ramp", "notion"
]

class LeverSource(BaseSource):
    source_name = "Lever"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Searching Lever postings across {len(LEVER_COMPANIES)} companies...")
        jobs: List[Job] = []

        tasks = [self._fetch_lever_jobs(company, keywords, locations) for company in LEVER_COMPANIES]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for res in results:
            if isinstance(res, list):
                jobs.extend(res)
            elif isinstance(res, Exception):
                logger.warning(f"[{self.source_name}] Lever error: {res}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} total jobs.")
        return jobs

    async def _fetch_lever_jobs(self, company: str, keywords: List[str], locations: List[str]) -> List[Job]:
        url = f"https://api.lever.co/v0/postings/{company}?mode=json"
        data = await self.fetch_url(url, json=True)
        if not data or not isinstance(data, list):
            return []

        company_name = company.capitalize()
        matched_jobs: List[Job] = []

        for item in data:
            title = item.get("text", "")
            categories = item.get("categories", {})
            location_name = categories.get("location", "Not specified")
            commitment = categories.get("commitment", "Full-time")
            app_url = item.get("hostedUrl", "")
            created_at = item.get("createdAt", None)

            title_match = any(kw.lower() in title.lower() for kw in keywords)
            if not title_match:
                continue

            if not filter_internships(title):
                continue

            post_date = format_date_iso(datetime.now())
            if created_at:
                post_date = datetime.fromtimestamp(created_at / 1000.0).strftime("%Y-%m-%d")

            description_plain = item.get("descriptionPlain", "")

            job = Job(
                **{
                    "Job Title": title,
                    "Company": company_name,
                    "Posting Date": post_date,
                    "Application Deadline": "Not specified",
                    "Location": location_name,
                    "Remote / Hybrid / Onsite": parse_work_type(title, location_name, description_plain),
                    "Experience": parse_experience_level(title, description_plain),
                    "Employment Type": commitment or "Full-time",
                    "Salary": "Not specified",
                    "Application Link": app_url,
                    "Company Career Link": f"https://jobs.lever.co/{company}",
                    "Source": "Lever",
                    "Legitimacy": LegitimacyType.MAJOR_JOB_BOARD.value,
                    "Verification Status": "Verified",
                    "Description": description_plain[:2000] if description_plain else f"Lever posting for {title}",
                    "Date Discovered": format_date_iso(datetime.now()),
                }
            )
            matched_jobs.append(job)

        return matched_jobs
