from uuid import uuid4
from psycopg2.extensions import connection
from schemas.report import ReportCreate, ReportOut

class ReportRepository:
    def __init__(self, db: connection):
        self.db = db

    def create(self, report: ReportCreate) -> ReportOut:
        report_id = str(uuid4()) 
        with self.db.cursor() as cur:
            cur.execute(
                """
                insert into reports(
                    id,
                    user_id,
                    symbol,
                    content,
                    recommendation,
                    confidence_score
                )
                Values(%s, %s, %s, %s, %s, %s)
                Returning id , user_id , symbol , content , recommendation , confidence_score , created_at
                """,
                (
                    report_id,
                    report.user_id,
                    report.symbol.upper(),
                    report.content,
                    report.recommendation,
                    report.confidence_score,
                ),
            )
            row = cur.fetchone()

        self.db.commit()
        return ReportOut(**row)
    
    
    def get_by_id(self, report_id: str) -> ReportOut | None:
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, symbol, content, recommendation, confidence_score, created_at
                FROM reports
                WHERE id = %s
                """
                (report_id,),
            )
            row = cur.fetchone()
        return ReportOut(**row) if row else None
    
    def list_by_user(self, user_id:str)->list[ReportOut]:
        with self.db.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, symbol, content, recommendation, confidence_score, created_at
                FROM reports
                WHERE user_id = %s
                order by created_at desc
                """,
                (user_id,),
            )
            rows = cur.fetchall()
        return [ReportOut(**row) for row in rows]
