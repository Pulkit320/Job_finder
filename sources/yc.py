import asyncio
from typing import List
from datetime import datetime
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

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

class YCSource(BaseSource):
    source_name = "Y Combinator Jobs"

    async def search(self, keywords: List[str], locations: List[str]) -> List[Job]:
        logger.info(f"[{self.source_name}] Searching Y Combinator Work at a Startup jobs via Playwright...")
        jobs: List[Job] = []

        url = "https://www.workatastartup.com/jobs"
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                page = await context.new_page()

                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    await page.evaluate("window.scrollTo(0, 1500)")
                    await asyncio.sleep(3)

                    content = await page.content()
                    soup = BeautifulSoup(content, "lxml")

                    job_elements = soup.find_all("a", href=True)
                    for a in job_elements:
                        title = a.get_text(strip=True)
                        href = a["href"]

                        if len(title) < 5 or not any(kw.lower() in title.lower() for kw in keywords):
                            continue

                        if not filter_internships(title):
                            continue

                        app_url = f"https://www.workatastartup.com{href}" if href.startswith("/") else href

                        job = Job(
                            **{
                                "Job Title": title,
                                "Company": "YC Startup",
                                "Posting Date": format_date_iso(datetime.now()),
                                "Application Deadline": "Not specified",
                                "Location": "India / Remote",
                                "Remote / Hybrid / Onsite": parse_work_type(title, "Remote", ""),
                                "Experience": parse_experience_level(title, ""),
                                "Employment Type": "Full-time",
                                "Salary": "Not specified",
                                "Application Link": app_url,
                                "Company Career Link": "https://www.ycombinator.com/companies",
                                "Source": "Y Combinator Jobs",
                                "Legitimacy": LegitimacyType.MAJOR_JOB_BOARD.value,
                                "Verification Status": "Verified",
                                "Description": f"Y Combinator startup job: {title}",
                                "Date Discovered": format_date_iso(datetime.now()),
                            }
                        )
                        jobs.append(job)
                except Exception as e:
                    logger.warning(f"[{self.source_name}] YC Playwright page error: {e}")

                await browser.close()
        except Exception as e:
            logger.error(f"[{self.source_name}] YC Playwright browser error: {e}")

        logger.info(f"[{self.source_name}] Found {len(jobs)} YC startup jobs via Playwright.")
        return jobs
