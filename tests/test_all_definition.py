def test_all_definition():
    """
    Check that a compiled module defines __all__ with the right value.

    These modules have been chosen since they contain messages, services and enums.
    """
    import tests.output_betterproto.enum as enum
    import tests.output_betterproto.service as service

    assert service.__all__ == (
        "ThingType",
        "DoThingRequest",
        "DoThingResponse",
        "GetThingRequest",
        "GetThingResponse",
        "TestStub",
        "TestSyncStub",
        "TestBase",
    )
    assert enum.__all__ == ("Choice", "ArithmeticOperator", "Test")
