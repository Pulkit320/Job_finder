import asyncio
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from job_finder.sources.base import BaseSource
from job_finder.models.job import Job, LegitimacyType
from job_finder.utils.dates import format_date_iso
from job_finder.utils.parser import parse_work_type, parse_experience_level, parse_salary, filter_internships
from job_finder.utils.logger import get_logger

logger = get_logger()

class WellfoundSource(BaseSource):
    source_name = "Wellfound"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Searching Wellfound Indian startup job listings via Playwright...")
        jobs: List[Job] = []

        target_roles = ["software-engineer", "ai-engineer", "machine-learning-engineer"]
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800}
                )
                page = await context.new_page()

                for role in target_roles:
                    url = f"https://wellfound.com/role/l/{role}/india"
                    try:
                        await page.goto(url, wait_until="networkidle", timeout=20000)
                        await page.evaluate("window.scrollTo(0, 1000)")
                        await asyncio.sleep(2)
                        
                        content = await page.content()
                        soup = BeautifulSoup(content, "lxml")
                        
                        # Extract all links that contain job postings or company roles
                        anchors = soup.find_all("a", href=True)
                        for a in anchors:
                            title = a.get_text(strip=True)
                            href = a["href"]
                            
                            if len(title) < 5 or not any(kw.lower() in title.lower() for kw in keywords):
                                continue

                            if not filter_internships(title):
                                continue

                            app_url = f"https://wellfound.com{href}" if href.startswith("/") else href

                            job = Job(
                                **{
                                    "Job Title": title,
                                    "Company": "Indian AI / Tech Startup",
                                    "Posting Date": format_date_iso(datetime.now()),
                                    "Application Deadline": "Not specified",
                                    "Location": "India",
                                    "Remote / Hybrid / Onsite": parse_work_type(title, "India", ""),
                                    "Experience": parse_experience_level(title, ""),
                                    "Employment Type": "Full-time",
                                    "Salary": "Not specified",
                                    "Application Link": app_url,
                                    "Company Career Link": app_url,
                                    "Source": "Wellfound",
                                    "Legitimacy": LegitimacyType.MAJOR_JOB_BOARD.value,
                                    "Verification Status": "Verified",
                                    "Description": f"Wellfound startup posting for {title}",
                                    "Date Discovered": format_date_iso(datetime.now()),
                                }
                            )
                            jobs.append(job)
                    except Exception as e:
                        logger.warning(f"[{self.source_name}] Playwright fetch error for {role}: {e}")

                await browser.close()
        except Exception as e:
            logger.error(f"[{self.source_name}] Playwright browser error: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} startup jobs via Playwright.")
        return jobs
