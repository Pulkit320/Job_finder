import asyncio
import urllib.parse
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from job_finder.sources.base import BaseSource
from job_finder.models.job import Job, LegitimacyType
from job_finder.utils.dates import format_date_iso
from job_finder.utils.parser import parse_work_type, parse_experience_level, parse_salary, filter_internships
from job_finder.utils.logger import get_logger

logger = get_logger()

class IndeedSource(BaseSource):
    source_name = "Indeed"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Querying Indeed public listings...")
        jobs: List[Job] = []

        for kw in keywords[:2]:
            url = f"https://www.indeed.com/jobs?q={urllib.parse.quote(kw)}&fromage=3"  # last 3 days
            html = await self.fetch_url(url)
            if not html:
                logger.warning(f"[{self.source_name}] Request blocked or un-parseable by anti-bot. Failing gracefully.")
                continue

            soup = BeautifulSoup(str(html), "lxml")
            cards = soup.find_all("div", class_=lambda c: c and "job_seen_beacon" in str(c))

            for card in cards:
                try:
                    title_elem = card.find("h2", class_=lambda c: c and "jobTitle" in str(c))
                    company_elem = card.find("span", class_=lambda c: c and "companyName" in str(c)) or card.find("span", {"data-testid": "company-name"})
                    loc_elem = card.find("div", class_=lambda c: c and "companyLocation" in str(c))
                    link_elem = card.find("a", href=True)

                    if not title_elem:
                        continue

                    title = title_elem.get_text(strip=True)
                    company = company_elem.get_text(strip=True) if company_elem else "Employer"
                    location = loc_elem.get_text(strip=True) if loc_elem else "United States"
                    href = link_elem["href"] if link_elem else ""
                    app_url = f"https://www.indeed.com{href}" if href.startswith("/") else href or url

                    if not filter_internships(title):
                        continue

                    card_text = card.get_text()

                    job = Job(
                        **{
                            "Job Title": title,
                            "Company": company,
                            "Posting Date": format_date_iso(datetime.now()),
                            "Application Deadline": "Not specified",
                            "Location": location,
                            "Remote / Hybrid / Onsite": parse_work_type(title, location, card_text),
                            "Experience": parse_experience_level(title, card_text),
                            "Employment Type": "Full-time",
                            "Salary": parse_salary(card_text),
                            "Application Link": app_url,
                            "Company Career Link": app_url,
                            "Source": "Indeed",
                            "Legitimacy": LegitimacyType.THIRD_PARTY_AGGREGATOR.value,
                            "Verification Status": "Verified",
                            "Description": f"Indeed posting for {title} at {company}",
                            "Date Discovered": format_date_iso(datetime.now()),
                        }
                    )
                    jobs.append(job)
                except Exception as e:
                    logger.debug(f"[{self.source_name}] Error parsing Indeed card: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} Indeed jobs.")
        return jobs
