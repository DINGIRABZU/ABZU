import grpc
from urllib.parse import urlparse
from . import vector_pb2, vector_pb2_grpc


class VectorClient:
    """Simple gRPC client for the NeoABZU vector service."""

    def __init__(self, target: str) -> None:
        parsed = urlparse(target)
        self._target = parsed.netloc or parsed.path
        self._channel: grpc.Channel | None = None
        self._stub: vector_pb2_grpc.VectorServiceStub | None = None

    def __enter__(self) -> "VectorClient":
        self._channel = grpc.insecure_channel(
            self._target, options=(("grpc.enable_http_proxy", 0),)
        )
        self._stub = vector_pb2_grpc.VectorServiceStub(self._channel)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._channel is not None:
            self._channel.close()

    def init(self) -> vector_pb2.InitResponse:
        if self._stub is None:
            raise RuntimeError("client not initialized")
        return self._stub.Init(vector_pb2.InitRequest())

    def search(self, text: str, top_n: int) -> vector_pb2.SearchResponse:
        if self._stub is None:
            raise RuntimeError("client not initialized")
        req = vector_pb2.SearchRequest(text=text, top_n=top_n)
        return self._stub.Search(req)


__all__ = ["VectorClient"]
