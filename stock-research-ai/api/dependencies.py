from services.report_service import ReportService
from services.research_service import ResearchService
from services.watchlist_service import WatchlistService


def get_research_service() -> ResearchService:
    return ResearchService()


def get_report_service() -> ReportService:
    return ReportService()


def get_watchlist_service() -> WatchlistService:
    return WatchlistService()