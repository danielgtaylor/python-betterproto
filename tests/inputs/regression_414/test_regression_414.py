from tests.output_bananaproto.regression_414 import Test


def test_full_cycle():
    body = bytes([0, 1])
    auth = bytes([2, 3])
    sig = [b""]

    obj = Test(body=body, auth=auth, signatures=sig)

    decoded = Test().parse(bytes(obj))
    assert decoded == obj
    assert decoded.body == body
    assert decoded.auth == auth
    assert decoded.signatures == sig
