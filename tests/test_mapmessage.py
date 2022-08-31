from tests.output_betterproto.mapmessage import (
    Nested,
    Test,
)


def test_mapmessage_to_dict_preserves_message():
    message = Test(
        items={
            "test": Nested(
                count=1,
            )
        }
    )

    message.to_dict()

    assert isinstance(message.items["test"], Nested), "Wrong nested type after to_dict"
