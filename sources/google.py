import asyncio
import urllib.parse
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup

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

class GoogleSource(BaseSource):
    source_name = "Google Search"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Querying Search index for Indian startups & career postings...")
        jobs: List[Job] = []

        query = '("Software Engineer" OR "AI Engineer" OR "Prompt Engineer" OR "SDE 1") ("India" OR "Bengaluru" OR "Bangalore" OR "Hyderabad" OR "Gurugram" OR "Pune") (site:greenhouse.io OR site:lever.co OR site:jobs.ashbyhq.com OR site:wellfound.com)'
        encoded_query = urllib.parse.quote(query)
        search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

        headers = self.get_random_headers()
        headers["Referer"] = "https://html.duckduckgo.com/"

        html = await self.fetch_url(search_url, headers=headers)
        if not html:
            logger.warning(f"[{self.source_name}] Search query returned empty.")
            return jobs

        soup = BeautifulSoup(str(html), "lxml")
        results = soup.find_all("div", class_="result")

        for res in results:
            try:
                title_elem = res.find("a", class_="result__a")
                snippet_elem = res.find("a", class_="result__snippet")
                if not title_elem:
                    continue

                raw_title = title_elem.get_text(strip=True)
                raw_url = title_elem.get("href", "")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                if "/l/?" in raw_url and "uddg=" in raw_url:
                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(raw_url).query)
                    if "uddg" in parsed:
                        raw_url = parsed["uddg"][0]

                company_name = "AI / Tech Startup"
                if "greenhouse.io/" in raw_url:
                    parts = raw_url.split("greenhouse.io/")[-1].split("/")
                    if parts and parts[0]:
                        company_name = parts[0].capitalize()
                elif "lever.co/" in raw_url:
                    parts = raw_url.split("lever.co/")[-1].split("/")
                    if parts and parts[0]:
                        company_name = parts[0].capitalize()
                elif "ashbyhq.com/" in raw_url:
                    parts = raw_url.split("ashbyhq.com/")[-1].split("/")
                    if parts and parts[0]:
                        company_name = parts[0].capitalize()

                if not filter_internships(raw_title):
                    continue

                job = Job(
                    **{
                        "Job Title": raw_title,
                        "Company": company_name,
                        "Posting Date": format_date_iso(datetime.now()),
                        "Application Deadline": "Not specified",
                        "Location": "India",
                        "Remote / Hybrid / Onsite": parse_work_type(raw_title, snippet, ""),
                        "Experience": parse_experience_level(raw_title, snippet),
                        "Employment Type": "Full-time",
                        "Salary": "Not specified",
                        "Application Link": raw_url,
                        "Company Career Link": raw_url,
                        "Source": "Google Search",
                        "Legitimacy": LegitimacyType.THIRD_PARTY_AGGREGATOR.value,
                        "Verification Status": "Verified",
                        "Description": snippet or f"Discovered startup job: {raw_title}",
                        "Date Discovered": format_date_iso(datetime.now()),
                    }
                )
                jobs.append(job)
            except Exception as e:
                logger.debug(f"[{self.source_name}] Error parsing result: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} jobs via Search.")
        return jobs
