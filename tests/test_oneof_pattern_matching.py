import sys

import pytest


@pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="pattern matching is only supported in python3.10+",
)
def test_oneof_pattern_matching():
    from tests.oneof_pattern_matching import test_oneof_pattern_matching

    test_oneof_pattern_matching()
