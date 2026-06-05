"""Local OpenTelemetry wiring for the autonomic loops.

The trail remains the durable evidence store. This module emits the same
operational slice as OTEL spans when a collector/exporter is configured, so
latency, token usage, model/provider, and dispatch failures can be consumed by
standard observability tooling without making OTEL part of the trust ledger.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Mapping
from contextlib import contextmanager, suppress
from typing import Any, cast

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.util.types import AttributeValue

from practice_theory_implementation.trail import UsageRecord

_CONFIGURED = False
_TRACER_NAME = "practice_theory_implementation"


def _truthy(value: str | None) -> bool:
    return value is not None and value.strip().lower() in {"1", "true", "yes", "on"}


def configure_otel() -> dict[str, object]:
    """Configure OTEL once and return a small status summary.

    Export is enabled when either:
    - `PRACTICE_OTEL_ENABLED` is truthy,
    - an `OTEL_EXPORTER_OTLP_ENDPOINT` is present, or
    - `PRACTICE_OTEL_CONSOLE` is truthy.

    Without one of those, spans are no-ops. This keeps local service logs quiet
    while still letting a local collector be attached by environment alone.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return otel_status()

    enabled = (
        _truthy(os.environ.get("PRACTICE_OTEL_ENABLED"))
        or bool(os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT"))
        or _truthy(os.environ.get("PRACTICE_OTEL_CONSOLE"))
    )
    if not enabled:
        _CONFIGURED = True
        return otel_status()

    service_name = os.environ.get(
        "OTEL_SERVICE_NAME",
        os.environ.get("PRACTICE_OTEL_SERVICE_NAME", "practice-theory-implementation"),
    )
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    if _truthy(os.environ.get("PRACTICE_OTEL_CONSOLE")):
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    with suppress(Exception):
        trace.set_tracer_provider(provider)
    _CONFIGURED = True
    return otel_status()


def otel_status() -> dict[str, object]:
    """Return local OTEL configuration status without exposing secrets."""
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    headers = os.environ.get("OTEL_EXPORTER_OTLP_HEADERS")
    return {
        "configured": _CONFIGURED,
        "export_requested": (
            _truthy(os.environ.get("PRACTICE_OTEL_ENABLED"))
            or bool(endpoint)
            or _truthy(os.environ.get("PRACTICE_OTEL_CONSOLE"))
        ),
        "console_exporter": _truthy(os.environ.get("PRACTICE_OTEL_CONSOLE")),
        "otlp_endpoint": endpoint,
        "otlp_headers_present": bool(headers),
        "service_name": os.environ.get(
            "OTEL_SERVICE_NAME",
            os.environ.get("PRACTICE_OTEL_SERVICE_NAME", "practice-theory-implementation"),
        ),
    }


def _is_attribute_value(value: object) -> bool:
    return isinstance(value, str | bool | int | float)


def _attrs(raw: Mapping[str, object | None]) -> dict[str, AttributeValue]:
    return {
        key: cast(AttributeValue, value)
        for key, value in raw.items()
        if value is not None and _is_attribute_value(value)
    }


@contextmanager
def autonomic_dispatch_span(
    *,
    role: str,
    bundle_id: str,
    primary_id: object,
    worker_id: str,
    metadata: Mapping[str, Any] | None = None,
) -> Iterator[Span]:
    """Start an OTEL span for one autonomic dispatch."""
    configure_otel()
    tracer = trace.get_tracer(_TRACER_NAME)
    attrs: dict[str, object | None] = {
        "practice.loop.role": role,
        "practice.bundle_id": bundle_id,
        "practice.dispatch.primary_id": str(primary_id),
        "practice.dispatch.worker_id": worker_id,
    }
    for key, value in (metadata or {}).items():
        if _is_attribute_value(value):
            attrs[f"practice.dispatch.{key}"] = value
    with tracer.start_as_current_span(
        "autonomic.dispatch",
        attributes=_attrs(attrs),
    ) as span:
        try:
            yield span
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def emit_autonomic_event(
    *,
    name: str,
    notification: str,
    attributes: Mapping[str, object | None] | None = None,
) -> None:
    """Emit a deterministic autonomic event as a short OTEL span.

    Used for machine-decided occurrences that need no intelligent explanation —
    a quota halt, a repeated-error halt, a triage-decision summary. The
    `notification` is a fixed, templated human-readable string built from
    structured fields (never model-authored), surfaced both as a span event and
    the `practice.notification` attribute so a collector or alert can show it
    verbatim. A no-op when OTEL export is not configured.
    """
    configure_otel()
    tracer = trace.get_tracer(_TRACER_NAME)
    attrs: dict[str, object | None] = {"practice.notification": notification}
    if attributes:
        attrs.update(attributes)
    with tracer.start_as_current_span(name, attributes=_attrs(attrs)) as span:
        span.add_event(notification, attributes=_attrs(attrs))


def annotate_dispatch_result(
    span: Span,
    *,
    status: str,
    consumer_id: str | None = None,
    usage: UsageRecord | None = None,
    dispatch_ms: int | None = None,
    error: str | None = None,
    error_kind: str | None = None,
) -> None:
    """Attach outcome attributes to a dispatch span."""
    attrs: dict[str, object | None] = {
        "practice.dispatch.status": status,
        "practice.enactment_id": consumer_id,
        "practice.dispatch.duration_ms": dispatch_ms,
    }
    if usage is not None:
        attrs.update(
            {
                "llm.provider": usage.provider,
                "llm.model": usage.model,
                "llm.input_tokens": usage.input_tokens,
                "llm.output_tokens": usage.output_tokens,
                "llm.cache_read_tokens": usage.cache_read_tokens,
                "llm.cache_creation_tokens": usage.cache_creation_tokens,
                "llm.cost_usd": usage.cost_usd,
                "llm.num_turns": usage.num_turns,
            }
        )
    for key, value in _attrs(attrs).items():
        span.set_attribute(key, value)
    if error:
        span.set_attribute("practice.dispatch.error", error)
        if error_kind:
            span.set_attribute("practice.dispatch.error_kind", error_kind)
        span.set_status(Status(StatusCode.ERROR, error))
    elif status == "ok":
        span.set_status(Status(StatusCode.OK))
