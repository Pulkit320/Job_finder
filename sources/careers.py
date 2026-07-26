import asyncio
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from job_finder.sources.base import BaseSource
from job_finder.models.job import Job, LegitimacyType
from job_finder.utils.dates import format_date_iso
from job_finder.utils.parser import parse_work_type, parse_experience_level, filter_internships
from job_finder.utils.logger import get_logger

logger = get_logger()

# Direct career URLs of top target AI & Software engineering employers
OFFICIAL_CAREER_PAGES = [
    {
        "company": "OpenAI",
        "url": "https://openai.com/careers/search/",
        "base_career": "https://openai.com/careers/",
    },
    {
        "company": "Anthropic",
        "url": "https://www.anthropic.com/careers",
        "base_career": "https://www.anthropic.com/careers",
    },
    {
        "company": "Google",
        "url": "https://www.google.com/about/careers/applications/jobs/results/",
        "base_career": "https://careers.google.com",
    },
    {
        "company": "Microsoft",
        "url": "https://careers.microsoft.com/v2/global/en/home.html",
        "base_career": "https://careers.microsoft.com",
    },
]

class CareersSource(BaseSource):
    source_name = "Official Company Careers"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Querying direct official company career pages...")
        jobs: List[Job] = []

        for site in OFFICIAL_CAREER_PAGES:
            try:
                html = await self.fetch_url(site["url"])
                if not html:
                    continue

                soup = BeautifulSoup(str(html), "lxml")
                # Look for anchor elements that contain job keywords or links
                links = soup.find_all("a", href=True)
                for a in links:
                    text = a.get_text(strip=True)
                    href = a["href"]
                    
                    if not text or len(text) < 5:
                        continue

                    # Check keyword match
                    if not any(kw.lower() in text.lower() for kw in keywords):
                        continue

                    if not filter_internships(text):
                        continue

                    full_link = href if href.startswith("http") else f"{site['base_career'].rstrip('/')}/{href.lstrip('/')}"

                    job = Job(
                        **{
                            "Job Title": text,
                            "Company": site["company"],
                            "Posting Date": format_date_iso(datetime.now()),
                            "Application Deadline": "Not specified",
                            "Location": "Worldwide / Remote",
                            "Remote / Hybrid / Onsite": parse_work_type(text, "Remote", ""),
                            "Experience": parse_experience_level(text, ""),
                            "Employment Type": "Full-time",
                            "Salary": "Not specified",
                            "Application Link": full_link,
                            "Company Career Link": site["base_career"],
                            "Source": "Official Company Careers",
                            "Legitimacy": LegitimacyType.OFFICIAL_CAREERS.value,
                            "Verification Status": "Verified",
                            "Description": f"Direct company career posting for {text} at {site['company']}",
                            "Date Discovered": format_date_iso(datetime.now()),
                        }
                    )
                    jobs.append(job)
            except Exception as e:
                logger.warning(f"[{self.source_name}] Failed parsing career site {site['company']}: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} official career page jobs.")
        return jobs
