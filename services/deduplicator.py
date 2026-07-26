from typing import List, Tuple
from rapidfuzz import fuzz

try:
    from config import AppConfig
    from models.job import Job, LegitimacyType
    from utils.logger import get_logger
except ModuleNotFoundError:
    from job_finder.config import AppConfig
    from job_finder.models.job import Job, LegitimacyType
    from job_finder.utils.logger import get_logger

logger = get_logger()

SOURCE_PRIORITY = {
    LegitimacyType.OFFICIAL_CAREERS.value: 100,
    LegitimacyType.MAJOR_JOB_BOARD.value: 80,
    LegitimacyType.THIRD_PARTY_AGGREGATOR.value: 50,
    LegitimacyType.SUSPICIOUS.value: 10,
}

class DeduplicatorService:
    def __init__(self, config: AppConfig):
        self.config = config

    def deduplicate(self, existing_jobs: List[Job], new_jobs: List[Job]) -> Tuple[List[Job], int]:
        logger.info(f"Deduplicating {len(new_jobs)} newly found jobs against {len(existing_jobs)} existing stored jobs...")
        
        duplicates_removed = 0
        pool: List[Job] = list(existing_jobs)
        existing_ids = {j.id for j in existing_jobs}
        existing_urls = {j.application_url.strip().lower() for j in existing_jobs if j.application_url}

        newly_added_jobs: List[Job] = []

        for candidate in new_jobs:
            cand_url = candidate.application_url.strip().lower()
            
            if candidate.id in existing_ids or cand_url in existing_urls:
                duplicates_removed += 1
                logger.debug(f"Exact match duplicate skipped: {candidate.title} at {candidate.company}")
                continue

            is_dup = False
            for idx, existing in enumerate(pool):
                if self._is_duplicate(candidate, existing):
                    is_dup = True
                    duplicates_removed += 1
                    logger.debug(f"Fuzzy duplicate detected (>={self.config.fuzzy_threshold}%): '{candidate.title}' at '{candidate.company}' vs stored '{existing.title}' at '{existing.company}'")
                    
                    if self._get_priority(candidate) > self._get_priority(existing):
                        logger.info(f"Replacing duplicate with higher priority source: {candidate.source} over {existing.source}")
                        pool[idx] = candidate
                    break

            if not is_dup:
                pool.append(candidate)
                newly_added_jobs.append(candidate)
                existing_ids.add(candidate.id)
                existing_urls.add(cand_url)

        logger.info(f"Deduplication complete. {duplicates_removed} duplicates skipped/merged. {len(newly_added_jobs)} genuinely NEW jobs added.")
        return pool, len(newly_added_jobs)

    def _is_duplicate(self, job1: Job, job2: Job) -> bool:
        comp1 = job1.company.lower().strip()
        comp2 = job2.company.lower().strip()
        
        comp_sim = fuzz.ratio(comp1, comp2)
        if comp_sim < 85:
            return False

        title1 = job1.title.lower().strip()
        title2 = job2.title.lower().strip()
        title_sim = fuzz.ratio(title1, title2)

        if title_sim >= self.config.fuzzy_threshold:
            return True

        comb1 = f"{comp1} {title1}"
        comb2 = f"{comp2} {title2}"
        comb_sim = fuzz.ratio(comb1, comb2)

        return comb_sim >= self.config.fuzzy_threshold

    def _get_priority(self, job: Job) -> int:
        return SOURCE_PRIORITY.get(job.legitimacy, 30)
