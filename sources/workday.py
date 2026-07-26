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

WORKDAY_ENDPOINTS = [
    {
        "company": "NVIDIA",
        "url": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
        "base_link": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite",
    },
    {
        "company": "Adobe",
        "url": "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs",
        "base_link": "https://adobe.wd5.myworkdayjobs.com/external_experienced",
    },
    {
        "company": "Salesforce",
        "url": "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs",
        "base_link": "https://salesforce.wd12.myworkdayjobs.com/External_Career_Site",
    },
]

class WorkdaySource(BaseSource):
    source_name = "Workday"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Querying Workday endpoints for India jobs...")
        jobs: List[Job] = []

        for site in WORKDAY_ENDPOINTS:
            try:
                for kw in keywords[:2]:
                    payload = {
                        "appliedFacets": {},
                        "limit": 20,
                        "offset": 0,
                        "searchText": f"{kw} India",
                    }
                    data = await self.fetch_post(site["url"], payload)
                    if not data or "jobPostings" not in data:
                        continue

                    for item in data.get("jobPostings", []):
                        title = item.get("title", "")
                        external_path = item.get("externalPath", "")
                        location_name = item.get("location", "India")
                        posted_on = item.get("postedOn", "")

                        if not any(k.lower() in title.lower() for kw in keywords):
                            continue

                        if not filter_internships(title):
                            continue

                        app_url = f"{site['base_link']}{external_path}" if external_path else site["base_link"]

                        job = Job(
                            **{
                                "Job Title": title,
                                "Company": site["company"],
                                "Posting Date": format_date_iso(datetime.now()),
                                "Application Deadline": "Not specified",
                                "Location": location_name if "India" in location_name or "Bengaluru" in location_name or "Hyderabad" in location_name else f"{location_name}, India",
                                "Remote / Hybrid / Onsite": parse_work_type(title, location_name, ""),
                                "Experience": parse_experience_level(title, ""),
                                "Employment Type": "Full-time",
                                "Salary": "Not specified",
                                "Application Link": app_url,
                                "Company Career Link": site["base_link"],
                                "Source": "Workday",
                                "Legitimacy": LegitimacyType.MAJOR_JOB_BOARD.value,
                                "Verification Status": "Verified",
                                "Description": f"Workday listing for {title} at {site['company']}",
                                "Date Discovered": format_date_iso(datetime.now()),
                            }
                        )
                        jobs.append(job)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Workday fetch error for {site['company']}: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} total jobs.")
        return jobs
