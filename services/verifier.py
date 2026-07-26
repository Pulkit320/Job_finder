import asyncio
import aiohttp
from typing import List, Tuple

try:
    from config import AppConfig
    from models.job import Job, LegitimacyType, VerificationStatus
    from utils.logger import get_logger
except ModuleNotFoundError:
    from job_finder.config import AppConfig
    from job_finder.models.job import Job, LegitimacyType, VerificationStatus
    from job_finder.utils.logger import get_logger

logger = get_logger()

class VerifierService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.semaphore = asyncio.Semaphore(config.max_concurrent_requests)

    async def verify_jobs(self, jobs: List[Job]) -> List[Job]:
        logger.info(f"Verifying legitimacy & URL health for {len(jobs)} jobs...")
        tasks = [self.verify_single_job(job) for job in jobs]
        verified_jobs = await asyncio.gather(*tasks)
        logger.info("Job verification phase complete.")
        return list(verified_jobs)

    async def verify_single_job(self, job: Job) -> Job:
        async with self.semaphore:
            url_ok, status_code = await self._check_url_status(job.application_url)

            if not url_ok:
                logger.warning(f"Verification failure: URL unreachable ({status_code}) for '{job.title}' at {job.company}")
                job.verification_status = VerificationStatus.FAILED.value
                job.legitimacy = LegitimacyType.SUSPICIOUS.value
                return job

            legitimacy = self._classify_legitimacy(job)
            job.legitimacy = legitimacy.value if isinstance(legitimacy, LegitimacyType) else legitimacy

            desc_len = len(job.description or "")
            suspicious_words = ["crypto scam", "whatsapp only", "send money", "telegram", "wire transfer"]
            is_suspicious_desc = any(sw in (job.description or "").lower() for sw in suspicious_words)

            if is_suspicious_desc:
                job.legitimacy = LegitimacyType.SUSPICIOUS.value
                job.verification_status = VerificationStatus.FAILED.value
            else:
                job.verification_status = VerificationStatus.VERIFIED.value

            return job

    async def _check_url_status(self, url: str) -> Tuple[bool, int]:
        if not url or not url.startswith("http"):
            return False, 0
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                try:
                    async with session.head(url, headers=headers, allow_redirects=True) as resp:
                        if resp.status < 400:
                            return True, resp.status
                except Exception:
                    pass
                async with session.get(url, headers=headers, allow_redirects=True) as resp:
                    return resp.status < 400, resp.status
        except Exception as e:
            logger.debug(f"URL check exception for {url}: {e}")
            return False, 0

    def _classify_legitimacy(self, job: Job) -> LegitimacyType:
        url_lower = job.application_url.lower()
        src_lower = job.source.lower()

        if "careers" in src_lower or "official" in src_lower:
            return LegitimacyType.OFFICIAL_CAREERS
        if any(domain in url_lower for domain in ["openai.com", "anthropic.com", "google.com", "microsoft.com", "apple.com", "meta.com", "nvidia.com"]):
            return LegitimacyType.OFFICIAL_CAREERS

        if any(ats in url_lower for ats in ["greenhouse.io", "lever.co", "myworkdayjobs.com", "workatastartup.com", "wellfound.com", "ashbyhq.com"]):
            return LegitimacyType.MAJOR_JOB_BOARD

        if any(agg in url_lower or agg in src_lower for agg in ["linkedin", "indeed", "naukri", "google search", "duckduckgo"]):
            return LegitimacyType.THIRD_PARTY_AGGREGATOR

        return LegitimacyType.THIRD_PARTY_AGGREGATOR
