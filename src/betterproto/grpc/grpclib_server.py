from abc import ABC

import grpclib
import grpclib.server


class ServiceImplementation(ABC):
    """
    Base class for async gRPC servers.
    """

    __service_name__: str

    def __rpc_methods__(self):
        pass

    def __mapping__(self):
        mapping = {}
        for (
            method,
            proto_name,
            cardinality,
            request_type,
            response_type,
        ) in self.__rpc_methods__():
            mapping[f"/{self.__service_name__}/{proto_name}"] = grpclib.const.Handler(
                method, cardinality, request_type, response_type
            )
        return mapping
