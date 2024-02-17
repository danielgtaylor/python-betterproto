import pytest


def test_payloads_import_is_generated():
    try:
        from tests.output_betterproto.service_complex_structure.service import _payloads__
        assert hasattr(_payloads__, 'Test')
    except ImportError:
        pytest.fail("Required import for type annotations is not generated!")


def test_payloads_import_is_generated_pydantic():
    try:
        from tests.output_betterproto_pydantic.service_complex_structure.service import _payloads__
        assert hasattr(_payloads__, 'Test')
    except ImportError:
        pytest.fail("Required import for type annotations is not generated in pydantic output!")
