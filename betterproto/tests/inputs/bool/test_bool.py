from betterproto.tests.output_betterproto.bool import Test


def test_value():
    message = Test()
    assert not message.value, "Boolean is False by default"
