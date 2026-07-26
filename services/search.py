import asyncio
import time
from typing import List
from job_finder.config import AppConfig
from job_finder.models.job import Job
from job_finder.sources import SOURCES_MAP
from job_finder.utils.dates import is_within_days
from job_finder.utils.parser import filter_internships, is_india_location, is_entry_level
from job_finder.utils.logger import get_logger

logger = get_logger()

class SearchService:
    def __init__(self, config: AppConfig):
        self.config = config

    async def execute_search(self) -> List[Job]:
        start_time = time.time()
        logger.info("Starting concurrent multi-source job search...")

        enabled_sources = [
            src_cls(self.config)
            for src_name, src_cls in SOURCES_MAP.items()
            if src_name in self.config.enabled_sources
        ]

        if not enabled_sources:
            logger.warning("No job sources enabled in configuration!")
            return []

        tasks = [src.search(self.config.keywords, self.config.locations) for src in enabled_sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_jobs: List[Job] = []
        for src, res in zip(enabled_sources, results):
            if isinstance(res, Exception):
                logger.error(f"Source {src.source_name} failed with error: {res}")
            elif isinstance(res, list):
                logger.info(f"Source {src.source_name} yielded {len(res)} candidate jobs.")
                raw_jobs.extend(res)

        pass_date = 0
        pass_intern = 0
        pass_india = 0
        pass_entry = 0

        filtered_jobs: List[Job] = []
        for job in raw_jobs:
            # Rule 1: Posted within posting_age_days (default <= 3 days)
            if not is_within_days(job.posting_date, max_days=self.config.posting_age_days):
                continue
            pass_date += 1

            # Rule 2: Internship title filter
            if not filter_internships(job.title):
                continue
            pass_intern += 1

            # Rule 3: India location filter
            if getattr(self.config, "india_only", True):
                if not is_india_location(job.location, job.description):
                    continue
            pass_india += 1

            # Rule 4: Entry level filter
            if getattr(self.config, "entry_level_only", True):
                if not is_entry_level(job.title, job.description):
                    continue
            pass_entry += 1

            filtered_jobs.append(job)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"Search Funnel Filter Breakdown: Raw={len(raw_jobs)} -> Age<=3d={pass_date} -> InternshipRule={pass_intern} -> IndiaLoc={pass_india} -> EntryLevel={pass_entry}.")
        return filtered_jobs
