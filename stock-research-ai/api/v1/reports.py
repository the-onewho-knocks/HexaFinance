from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import get_report_service
from schemas.report import ReportCreate, ReportOut
from services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportOut)
async def create_report(
    report: ReportCreate,
    service: ReportService = Depends(get_report_service),
) -> ReportOut:
    return await service.create_report(report)


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: str,
    service: ReportService = Depends(get_report_service),
) -> ReportOut:
    report = await service.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report