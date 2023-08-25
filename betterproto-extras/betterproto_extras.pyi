def deserialize(msg, data: bytes):
    """
    Parses the binary encoded Protobuf `data` with respect to the metadata
    given by the betterproto message `msg`, and merges the result into `msg`.
    """

def serialize(msg) -> bytes:
    """
    Get the binary encoded Protobuf representation of this message instance.
    """