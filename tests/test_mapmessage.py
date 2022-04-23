from tests.output_betterproto.mapmessage import (
    Test,
    Nested,
)

def test_mapmessage():
    message = Test(
        items={
            "test": Nested(
                count=1,
            )
        }
    )

    message.to_json()

    assert isinstance(message.items["test"], Nested), "Wrong nested type after to_json"
