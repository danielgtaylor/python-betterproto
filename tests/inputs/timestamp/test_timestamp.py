from datetime import datetime, timezone
import pytest

from betterproto import _Timestamp

@pytest.mark.parametrize("dt", [
    datetime(2023, 10, 11, 9, 41, 12, tzinfo=timezone.utc),
    datetime.now(timezone.utc),
    # potential issue with floating point precision:
    datetime(2242, 12, 31, 23, 0, 0, 1, tzinfo=timezone.utc),
    # potential issue with negative timestamps:
    datetime(1969, 12, 31, 23, 0, 0, 1, tzinfo=timezone.utc),
])
def test_timestamp_to_datetime_and_back(dt: datetime):
    """
    Make sure converting a datetime to a protobuf timestamp message
    and then back again ends up with the same datetime.
    """
    assert _Timestamp.from_datetime(dt).to_datetime() == dt
