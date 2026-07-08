"""Scrapers package for the InternIntel application."""

from __future__ import annotations

from app.scrapers.greenhouse import GreenhouseScraper
from app.scrapers.lever import LeverScraper
from app.scrapers.workday import WorkdayScraper
from app.scrapers.ashby import AshbyScraper
from app.scrapers.smartrecruiters import SmartRecruitersScraper
from app.scrapers.icims import IcimsScraper
from app.scrapers.oracle import OracleScraper
from app.scrapers.successfactors import SuccessFactorsScraper

__all__ = [
    "GreenhouseScraper",
    "LeverScraper",
    "WorkdayScraper",
    "AshbyScraper",
    "SmartRecruitersScraper",
    "IcimsScraper",
    "OracleScraper",
    "SuccessFactorsScraper",
]
