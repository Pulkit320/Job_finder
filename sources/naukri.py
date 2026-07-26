import asyncio
import urllib.parse
from typing import List
from datetime import datetime

try:
    from sources.base import BaseSource
    from models.job import Job, LegitimacyType
    from utils.dates import format_date_iso
    from utils.parser import parse_work_type, parse_experience_level, parse_salary, filter_internships
    from utils.logger import get_logger
except ModuleNotFoundError:
    from job_finder.sources.base import BaseSource
    from job_finder.models.job import Job, LegitimacyType
    from job_finder.utils.dates import format_date_iso
    from job_finder.utils.parser import parse_work_type, parse_experience_level, parse_salary, filter_internships
    from job_finder.utils.logger import get_logger

logger = get_logger()

class NaukriSource(BaseSource):
    source_name = "Naukri"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Querying Naukri API / web endpoints...")
        jobs: List[Job] = []

        headers = self.get_random_headers()
        headers["appid"] = "109"
        headers["systemid"] = "Naukri"

        for kw in keywords[:2]:
            url = f"https://www.naukri.com/jobapi/v3/search?noOfResults=20&urlType=search_by_keyword&searchType=adv&keyword={urllib.parse.quote(kw)}&seoKey={urllib.parse.quote(kw.lower().replace(' ', '-'))}-jobs&pageNo=1"
            data = await self.fetch_url(url, headers=headers, json=True)
            if not data or not isinstance(data, dict) or "jobDetails" not in data:
                continue

            for item in data.get("jobDetails", []):
                try:
                    title = item.get("title", "")
                    company = item.get("companyName", "Tech Employer")
                    location = item.get("placeholders", [{}])[0].get("label", "India") if item.get("placeholders") else "India"
                    post_str = item.get("footerPlaceholder", "")
                    jd_url = item.get("jdURL", "")
                    app_url = f"https://www.naukri.com{jd_url}" if jd_url.startswith("/") else jd_url or "https://www.naukri.com"
                    desc = item.get("jobDescription", "")

                    if not filter_internships(title):
                        continue

                    job = Job(
                        **{
                            "Job Title": title,
                            "Company": company,
                            "Posting Date": format_date_iso(datetime.now()),
                            "Application Deadline": "Not specified",
                            "Location": location,
                            "Remote / Hybrid / Onsite": parse_work_type(title, location, desc),
                            "Experience": item.get("experienceText", parse_experience_level(title, desc)),
                            "Employment Type": "Full-time",
                            "Salary": parse_salary(item.get("salary", "")),
                            "Application Link": app_url,
                            "Company Career Link": app_url,
                            "Source": "Naukri",
                            "Legitimacy": LegitimacyType.THIRD_PARTY_AGGREGATOR.value,
                            "Verification Status": "Verified",
                            "Description": desc[:1500] if desc else f"Naukri posting for {title} at {company}",
                            "Date Discovered": format_date_iso(datetime.now()),
                        }
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.debug(f"[{self.source_name}] Error parsing Naukri record: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} Naukri jobs.")
        return jobs
