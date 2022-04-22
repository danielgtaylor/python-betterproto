from datetime import (
    datetime,
    timedelta,
)

from tests.output_betterproto.repeated_duration_timestamp import Test


def test_roundtrip():
    message = Test()
    message.times = [datetime.now(), datetime.now()]
    message.durations = [timedelta(), timedelta()]
