from tests.output_bananaproto.regression_387 import (
    ParentElement,
    Test,
)


def test_regression_387():
    el = ParentElement(name="test", elems=[Test(id=0), Test(id=42)])
    binary = bytes(el)
    decoded = ParentElement().parse(binary)
    assert decoded == el
    assert decoded.elems == [Test(id=0), Test(id=42)]
