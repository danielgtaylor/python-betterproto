import pytest
from pydantic.error_wrappers import ValidationError

from tests.output_betterproto_pydantic.mapmessage import Test as Fail
from tests.output_betterproto_pydantic_optionals.mapmessage import Test as Success


def test_mapmessage_optional():
    with pytest.raises(ValidationError):
        message = Fail()
    # TODO: Actually make this succeed
    message = Success()
