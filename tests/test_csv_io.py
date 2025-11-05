from datetime import date
import csv
import os
import uuid
import pytest

from ledger.models import Record, RecordType

# 如果你还没实现 utils/csv_io.py，这组测试会自动跳过
csv_io = None
try:
    from ledger.utils import csv_io as _csv_io

    csv_io = _csv_io
except Exception:
    pass


@pytest.mark.skipif(csv_io is None, reason="csv_io not implemented yet")
def test_csv_roundtrip(tmp_path):
    path = tmp_path / f"r_{uuid.uuid4().hex}.csv"
    recs = [
        Record(None, 1, RecordType.INCOME, "salary", 1000.0, date(2025, 1, 1), "Jan"),
        Record(None, 1, RecordType.EXPENSE, "food", 120.0, date(2025, 1, 5), "noodles"),
    ]
    csv_io.save_records_to_csv(str(path), recs)
    assert path.exists() and path.stat().st_size > 0

    loaded = csv_io.load_records_from_csv(str(path))
    assert len(loaded) == 2
    assert loaded[0].rtype == RecordType.INCOME
    assert loaded[1].category == "food"
