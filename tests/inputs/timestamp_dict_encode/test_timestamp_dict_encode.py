from datetime import datetime, timedelta, timezone
from tests.output_betterproto.timestamp_dict_encode import Test
import pytest

# Current World Timezone range (UTC-12 to UTC+14)
MIN_UTC_OFFSET_MIN = -12 * 60
MAX_UTC_OFFSET_MIN = 14 * 60

# Generate all timezones in range in 15 min increments
timezones = [
    timezone(timedelta(minutes=x))
    for x in range(MIN_UTC_OFFSET_MIN, MAX_UTC_OFFSET_MIN + 1, 15)
]


@pytest.mark.parametrize("tz", timezones)
def test_timezone_aware_datetime_dict_encode(tz: timezone):
    original_time = datetime.now(tz=tz)
    original_message = Test()
    original_message.ts = original_time
    encoded = original_message.to_dict()
    decoded_message = Test()
    decoded_message.from_dict(encoded)

    # check that the timestamps are equal after decoding from dict
    assert original_message.ts.tzinfo is not None
    assert decoded_message.ts.tzinfo is not None
    assert original_message.ts == decoded_message.ts


def test_naive_datetime_dict_encode():
    # make suer naive datetime objects are still treated as utc
    original_time = datetime.now()
    assert original_time.tzinfo is None
    original_message = Test()
    original_message.ts = original_time
    original_time_utc = original_time.replace(tzinfo=timezone.utc)
    encoded = original_message.to_dict()
    decoded_message = Test()
    decoded_message.from_dict(encoded)

    # check that the timestamps are equal after decoding from dict
    assert decoded_message.ts.tzinfo is not None
    assert original_time_utc == decoded_message.ts


@pytest.mark.parametrize("tz", timezones)
def test_timezone_aware_json_serialize(tz: timezone):
    original_time = datetime.now(tz=tz)
    original_message = Test()
    original_message.ts = original_time
    json_serialized = original_message.to_json()
    decoded_message = Test()
    decoded_message.from_json(json_serialized)

    # check that the timestamps are equal after decoding from dict
    assert original_message.ts.tzinfo is not None
    assert decoded_message.ts.tzinfo is not None
    assert original_message.ts == decoded_message.ts


def test_naive_datetime_json_serialize():
    # make suer naive datetime objects are still treated as utc
    original_time = datetime.now()
    assert original_time.tzinfo is None
    original_message = Test()
    original_message.ts = original_time
    original_time_utc = original_time.replace(tzinfo=timezone.utc)
    json_serialized = original_message.to_json()
    decoded_message = Test()
    decoded_message.from_json(json_serialized)

    # check that the timestamps are equal after decoding from dict
    assert decoded_message.ts.tzinfo is not None
    assert original_time_utc == decoded_message.ts
