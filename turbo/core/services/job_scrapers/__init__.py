"""Job scraper modules for different job boards."""

from turbo.core.services.job_scrapers.base_scraper import BaseScraper, ScrapedJob
from turbo.core.services.job_scrapers.indeed_scraper import IndeedScraper
from turbo.core.services.job_scrapers.adzuna_scraper import AdzunaScraper
from turbo.core.services.job_scrapers.jsearch_scraper import JSearchScraper
from turbo.core.services.job_scrapers.remotive_scraper import RemotiveScraper
from turbo.core.services.job_scrapers.themuse_scraper import TheMuseScraper
from turbo.core.services.job_scrapers.arbeitnow_scraper import ArbeitnowScraper
from turbo.core.services.job_scrapers.reed_scraper import ReedScraper
from turbo.core.services.job_scrapers.usajobs_scraper import USAJobsScraper
from turbo.core.services.job_scrapers.weworkremotely_scraper import WeWorkRemotelyScraper

__all__ = [
    "BaseScraper",
    "IndeedScraper",
    "AdzunaScraper",
    "JSearchScraper",
    "RemotiveScraper",
    "TheMuseScraper",
    "ArbeitnowScraper",
    "ReedScraper",
    "USAJobsScraper",
    "WeWorkRemotelyScraper",
    "ScrapedJob",
]
