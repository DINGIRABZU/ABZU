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
        self._channel = grpc.insecure_channel(target)
        self._stub = vector_pb2_grpc.VectorServiceStub(self._channel)

    def init(self) -> vector_pb2.InitResponse:
        return self._stub.Init(vector_pb2.InitRequest())

    def search(self, text: str, top_n: int) -> vector_pb2.SearchResponse:
        req = vector_pb2.SearchRequest(text=text, top_n=top_n)
        return self._stub.Search(req)


__all__ = ["search", "VectorClient"]
