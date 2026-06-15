from datetime import datetime
from uuid import uuid4

from schemas.report import ReportCreate, ReportOut


class ReportService:
    def __init__(self):
        self._reports: dict[str, ReportOut] = {}

    async def create_report(self, report: ReportCreate) -> ReportOut:
        report_out = ReportOut(
            id=str(uuid4()),
            user_id=report.user_id,
            symbol=report.symbol.upper(),
            content=report.content,
            recommendation=report.recommendation,
            confidence_score=report.confidence_score,
            created_at=datetime.utcnow(),
        )
        self._reports[report_out.id] = report_out
        return report_out

    async def get_report(self, report_id: str) -> ReportOut | None:
        return self._reports.get(report_id)