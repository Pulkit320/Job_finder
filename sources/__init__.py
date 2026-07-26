from .base import BaseSource
from .greenhouse import GreenhouseSource
from .lever import LeverSource
from .workday import WorkdaySource
from .wellfound import WellfoundSource
from .yc import YCSource
from .careers import CareersSource
from .google import GoogleSource
from .linkedin import LinkedInSource
from .indeed import IndeedSource
from .naukri import NaukriSource

SOURCES_MAP = {
    "greenhouse": GreenhouseSource,
    "lever": LeverSource,
    "workday": WorkdaySource,
    "wellfound": WellfoundSource,
    "yc": YCSource,
    "careers": CareersSource,
    "google": GoogleSource,
    "linkedin": LinkedInSource,
    "indeed": IndeedSource,
    "naukri": NaukriSource,
}

__all__ = [
    "BaseSource",
    "GreenhouseSource",
    "LeverSource",
    "WorkdaySource",
    "WellfoundSource",
    "YCSource",
    "CareersSource",
    "GoogleSource",
    "LinkedInSource",
    "IndeedSource",
    "NaukriSource",
    "SOURCES_MAP",
]
