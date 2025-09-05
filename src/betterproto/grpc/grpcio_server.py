from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict


if TYPE_CHECKING:
    import grpc


class ServiceBase(ABC):

    @property
    @abstractmethod
    def __rpc_methods__(self) -> Dict[str, "grpc.RpcMethodHandler"]: ...

    @property
    @abstractmethod
    def __proto_path__(self) -> str: ...


def register_servicers(server: "grpc.aio.Server", *servicers: ServiceBase):
    from grpc import method_handlers_generic_handler

    server.add_generic_rpc_handlers(
        tuple(
            method_handlers_generic_handler(
                servicer.__proto_path__, servicer.__rpc_methods__
            )
            for servicer in servicers
        )
    )
