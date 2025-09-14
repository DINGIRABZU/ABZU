"""Helpers for the Rust-based vector search module and gRPC service."""

import grpc

from neoabzu_vector import search as rust_search

from . import vector_pb2, vector_pb2_grpc


def search(text: str, top_n: int):
    """Invoke the embedded Rust search function."""
    return rust_search(text, top_n)


class VectorClient:
    """Simple gRPC client for the VectorService."""

    def __init__(self, target: str):
        if target.startswith("http://"):
            target = target[7:]
        elif target.startswith("https://"):
            target = target[8:]
        self._channel = grpc.insecure_channel(target)
        self._stub = vector_pb2_grpc.VectorServiceStub(self._channel)

    def init(self) -> vector_pb2.InitResponse:
        return self._stub.Init(vector_pb2.InitRequest())

    def search(self, text: str, top_n: int) -> vector_pb2.SearchResponse:
        req = vector_pb2.SearchRequest(text=text, top_n=top_n)
        return self._stub.Search(req)

    def close(self) -> None:
        self._channel.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


__all__ = ["search", "VectorClient"]
