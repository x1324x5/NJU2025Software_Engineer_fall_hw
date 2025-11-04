from datetime import date
from ledger.models import Record, RecordType
from ledger.services.statistics_service import StatisticsService

def test_monthly_summary():
    svc = StatisticsService()
    records = [
        Record(None, 1, RecordType.INCOME, "salary", 1000.0, date(2025, 1, 1)),
        Record(None, 1, RecordType.EXPENSE, "food", 200.0, date(2025, 1, 2)),
    ]
    out = svc.monthly_summary(records)
    assert out["income"] == 1000.0
    assert out["expense"] == 200.0
    assert out["balance"] == 800.0
