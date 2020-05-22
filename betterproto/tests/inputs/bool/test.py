from betterproto.tests.output_betterproto.bool.bool import Test
from betterproto.tests.util import read_relative


def test_value():
    message = Test().from_json(read_relative(__file__, 'bool.json'))
    assert message.value

