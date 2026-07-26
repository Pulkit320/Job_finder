import asyncio
import urllib.parse
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from job_finder.sources.base import BaseSource
from job_finder.models.job import Job, LegitimacyType
from job_finder.utils.dates import format_date_iso
from job_finder.utils.parser import parse_work_type, parse_experience_level, filter_internships
from job_finder.utils.logger import get_logger

logger = get_logger()

class LinkedInSource(BaseSource):
    source_name = "LinkedIn Jobs"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Querying LinkedIn public job search API...")
        jobs: List[Job] = []

        target_keywords = keywords[:3]
        target_locations = ["India", "Bengaluru", "Hyderabad", "Pune", "Delhi"]

        for kw in target_keywords:
            for loc in target_locations[:2]:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={urllib.parse.quote(kw)}&location={urllib.parse.quote(loc)}&start=0"
                headers = self.get_random_headers()
                headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                
                html = await self.fetch_url(url, headers=headers)
                if not html:
                    continue

                soup = BeautifulSoup(str(html), "lxml")
                cards = soup.find_all("li")

                for card in cards:
                    try:
                        title_elem = card.find("h3", class_=lambda c: c and "job-search-card__title" in str(c))
                        company_elem = card.find("h4", class_=lambda c: c and "job-search-card__company-name" in str(c)) or card.find("a", class_=lambda c: c and "hidden-nested-link" in str(c))
                        loc_elem = card.find("span", class_=lambda c: c and "job-search-card__location" in str(c))
                        link_elem = card.find("a", class_=lambda c: c and "base-card__full-link" in str(c)) or card.find("a", href=True)
                        time_elem = card.find("time")

                        if not title_elem or not link_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        company = company_elem.get_text(strip=True) if company_elem else "Employer in India"
                        location = loc_elem.get_text(strip=True) if loc_elem else loc
                        href = link_elem["href"]
                        app_url = href.split("?")[0] if href else url
                        posted_date = time_elem.get("datetime") if time_elem else format_date_iso(datetime.now())

                        if not filter_internships(title):
                            continue

                        job = Job(
                            **{
                                "Job Title": title,
                                "Company": company,
                                "Posting Date": posted_date or format_date_iso(datetime.now()),
                                "Application Deadline": "Not specified",
                                "Location": location,
                                "Remote / Hybrid / Onsite": parse_work_type(title, location, ""),
                                "Experience": parse_experience_level(title, ""),
                                "Employment Type": "Full-time",
                                "Salary": "Not specified",
                                "Application Link": app_url,
                                "Company Career Link": f"https://www.linkedin.com/company/{company.lower().replace(' ', '-')}",
                                "Source": "LinkedIn Jobs",
                                "Legitimacy": LegitimacyType.THIRD_PARTY_AGGREGATOR.value,
                                "Verification Status": "Verified",
                                "Description": f"LinkedIn posting for {title} at {company}",
                                "Date Discovered": format_date_iso(datetime.now()),
                            }
                        )
                        jobs.append(job)
                    except Exception as e:
                        logger.debug(f"[{self.source_name}] Error parsing LinkedIn card: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} LinkedIn job postings.")
        return jobs
