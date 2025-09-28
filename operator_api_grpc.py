"""gRPC service exposing operator_api parity endpoints."""

from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Any, Mapping

import grpc
from grpc import aio
from opentelemetry import trace

try:  # pragma: no cover - optional status shim
    from opentelemetry.trace import Status, StatusCode
except ImportError:  # pragma: no cover - fallback for repo stub

    class StatusCode(Enum):
        OK = "OK"
        ERROR = "ERROR"

    class Status:  # type: ignore[override]
        def __init__(self, status_code: StatusCode, description: str | None = None):
            self.status_code = status_code
            self.description = description


from operator_api import (
    CommandDispatchError,
    CommandValidationError,
    MCPHandshakeError,
    execute_command_for_transport,
    execute_handover_for_transport,
    execute_memory_query_for_transport,
)

logger = logging.getLogger(__name__)
_tracer = trace.get_tracer(__name__)


def _decode_request(data: bytes) -> Mapping[str, Any]:
    if not data:
        return {}
    text = data.decode("utf-8")
    return json.loads(text)


def _encode_response(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


class OperatorApiGrpcService(grpc.GenericRpcHandler):
    """Generic gRPC handler that mirrors key operator_api endpoints."""

    def __init__(self, *, enable_rest_fallback: bool = True) -> None:
        self._enable_rest_fallback = enable_rest_fallback

    async def _dispatch_command(
        self, request: Mapping[str, Any], context: aio.ServicerContext
    ) -> Mapping[str, Any]:
        span_attributes = {"transport": "grpc"}
        with _tracer.start_as_current_span(
            "operator_api.grpc.dispatch_command", attributes=span_attributes
        ) as span:
            try:
                response = await execute_command_for_transport(
                    request, transport="grpc"
                )
                span.set_status(Status(StatusCode.OK))
                return response
            except CommandValidationError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            except PermissionError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))
            except MCPHandshakeError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, exc.detail))
                await context.abort(grpc.StatusCode.UNAVAILABLE, exc.detail)
            except CommandDispatchError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                if self._enable_rest_fallback:
                    span.add_event("rest-fallback-engaged")
                    logger.warning(
                        "operator_api grpc dispatch failed, invoking REST fallback"
                    )
                    response = await execute_command_for_transport(
                        request, transport="grpc", fallback=True
                    )
                    context.set_trailing_metadata((("abzu-fallback", "rest"),))
                    span.set_status(Status(StatusCode.OK))
                    return response
                await context.abort(grpc.StatusCode.INTERNAL, str(exc))
            except json.JSONDecodeError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            except Exception as exc:  # pragma: no cover - defensive guard
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INTERNAL, "unexpected error")
        raise AssertionError("context.abort should terminate the RPC")

    async def _memory_query(
        self, request: Mapping[str, Any], context: aio.ServicerContext
    ) -> Mapping[str, Any]:
        span_attributes = {"transport": "grpc"}
        with _tracer.start_as_current_span(
            "operator_api.grpc.memory_query", attributes=span_attributes
        ) as span:
            try:
                query = str(request.get("query", ""))
                response = execute_memory_query_for_transport(query, transport="grpc")
                span.set_status(Status(StatusCode.OK))
                return response
            except json.JSONDecodeError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            except Exception as exc:  # pragma: no cover - defensive guard
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INTERNAL, "unexpected error")
        raise AssertionError("context.abort should terminate the RPC")

    async def _handover(
        self, request: Mapping[str, Any], context: aio.ServicerContext
    ) -> Mapping[str, Any]:
        span_attributes = {"transport": "grpc"}
        with _tracer.start_as_current_span(
            "operator_api.grpc.handover", attributes=span_attributes
        ) as span:
            try:
                response = execute_handover_for_transport(request, transport="grpc")
                span.set_status(Status(StatusCode.OK))
                return response
            except json.JSONDecodeError as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            except Exception as exc:  # pragma: no cover - defensive guard
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                await context.abort(grpc.StatusCode.INTERNAL, "unexpected error")
        raise AssertionError("context.abort should terminate the RPC")

    def service(self, handler_call_details: grpc.HandlerCallDetails):
        method = handler_call_details.method
        if method == "/abzu.operator.OperatorApi/DispatchCommand":

            async def _handler(
                data: bytes, context: aio.ServicerContext
            ) -> Mapping[str, Any]:
                try:
                    payload = _decode_request(data)
                except json.JSONDecodeError as exc:
                    await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
                return await self._dispatch_command(payload, context)

            return aio.unary_unary_rpc_method_handler(
                _handler,
                response_serializer=_encode_response,
            )
        if method == "/abzu.operator.OperatorApi/MemoryQuery":

            async def _memory_handler(
                data: bytes, context: aio.ServicerContext
            ) -> Mapping[str, Any]:
                try:
                    payload = _decode_request(data)
                except json.JSONDecodeError as exc:
                    await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
                return await self._memory_query(payload, context)

            return aio.unary_unary_rpc_method_handler(
                _memory_handler,
                response_serializer=_encode_response,
            )
        if method == "/abzu.operator.OperatorApi/Handover":

            async def _handover_handler(
                data: bytes, context: aio.ServicerContext
            ) -> Mapping[str, Any]:
                try:
                    payload = _decode_request(data)
                except json.JSONDecodeError as exc:
                    await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
                return await self._handover(payload, context)

            return aio.unary_unary_rpc_method_handler(
                _handover_handler,
                response_serializer=_encode_response,
            )
        return None


async def serve(
    address: str = "0.0.0.0:9000",
    *,
    enable_rest_fallback: bool = True,
    **kwargs: Any,
) -> aio.Server:
    """Create and start a gRPC server bound to ``address``."""

    server = aio.server(**kwargs)
    server.add_generic_rpc_handlers(
        (OperatorApiGrpcService(enable_rest_fallback=enable_rest_fallback),)
    )
    server.add_insecure_port(address)
    await server.start()
    return server


__all__ = [
    "OperatorApiGrpcService",
    "serve",
]
