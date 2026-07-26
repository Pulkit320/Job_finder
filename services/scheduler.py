import asyncio

try:
    from config import AppConfig
    from services.search import SearchService
    from services.verifier import VerifierService
    from services.deduplicator import DeduplicatorService
    from services.exporter import ExporterService
    from utils.logger import get_logger
except ModuleNotFoundError:
    from job_finder.config import AppConfig
    from job_finder.services.search import SearchService
    from job_finder.services.verifier import VerifierService
    from job_finder.services.deduplicator import DeduplicatorService
    from job_finder.services.exporter import ExporterService
    from job_finder.utils.logger import get_logger

logger = get_logger()

class SchedulerService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.search_service = SearchService(config)
        self.verifier_service = VerifierService(config)
        self.deduplicator_service = DeduplicatorService(config)
        self.exporter_service = ExporterService()

    async def run_pipeline(self) -> dict:
        logger.info("Initializing full Job Finder Bot pipeline execution...")
        
        existing_jobs = self.exporter_service.load_jobs_json()
        scraped_jobs = await self.search_service.execute_search()
        verified_jobs = await self.verifier_service.verify_jobs(scraped_jobs)
        merged_jobs, new_count = self.deduplicator_service.deduplicate(existing_jobs, verified_jobs)
        
        self.exporter_service.save_jobs(merged_jobs)
        self.exporter_service.generate_report(merged_jobs, new_count)

        summary = {
            "total_jobs": len(merged_jobs),
            "new_jobs": new_count,
            "scraped_count": len(scraped_jobs),
        }
        logger.info(f"Pipeline finished successfully: {summary}")
        return summary
