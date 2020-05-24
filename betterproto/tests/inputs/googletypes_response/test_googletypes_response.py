from typing import Optional

import pytest

from betterproto.tests.output_betterproto.googletypes_response.googletypes_response import (
    TestStub
)


class TestStubChild(TestStub):
    async def _unary_unary(self, route, request, response_type, **kwargs):
        self.response_type = response_type


@pytest.mark.asyncio
async def test():
    pytest.skip("todo")
    stub = TestStubChild(None)
    await stub.get_int64()
    assert stub.response_type != Optional[int]
