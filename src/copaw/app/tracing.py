# -*- coding: utf-8 -*-
"""CoPaw OpenTelemetry tracing setup.

Supported backends (auto-detected from environment variables):

1. **Langfuse** (preferred when Langfuse keys are present)
   Required env vars:
     COPAW_LANGFUSE_PUBLIC_KEY   – Langfuse project public key
     COPAW_LANGFUSE_SECRET_KEY   – Langfuse project secret key
   Optional:
     COPAW_TRACING_ENDPOINT      – Langfuse host; defaults to
                                   https://cloud.langfuse.com
                                   (set to your self-hosted URL if needed)

2. **Generic OTLP** (Jaeger, Grafana Tempo, self-hosted OpenTelemetry Collector, …)
   Required env vars:
     COPAW_TRACING_ENDPOINT      – full trace endpoint URL,
                                   e.g. http://localhost:4318/v1/traces
   Optional:
     COPAW_OTLP_HEADERS          – comma-separated "Key=Value" pairs for
                                   request headers, e.g.
                                   "X-Tenant-ID=myorg,Authorization=Bearer t"

If none of the above are configured, tracing is silently skipped.
"""

import base64
import logging

logger = logging.getLogger(__name__)


def _parse_headers(raw: str) -> dict[str, str]:
    """Parse a comma-separated ``Key=Value`` header string into a dict."""
    headers: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair:
            continue
        if "=" not in pair:
            logger.warning("COPAW_OTLP_HEADERS: ignoring malformed entry %r", pair)
            continue
        k, v = pair.split("=", 1)
        headers[k.strip()] = v.strip()
    return headers


def _setup_otlp(endpoint: str, headers: dict[str, str] | None = None) -> None:
    """Configure an OTLPSpanExporter with optional headers.

    This mirrors AgentScope's ``setup_tracing`` but adds header support that
    backends requiring authentication (e.g. Langfuse) need.
    """
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
        OTLPSpanExporter,
    )

    exporter_kwargs: dict = {"endpoint": endpoint}
    if headers:
        exporter_kwargs["headers"] = headers

    exporter = OTLPSpanExporter(**exporter_kwargs)
    span_processor = BatchSpanProcessor(exporter)

    tracer_provider = trace.get_tracer_provider()
    if isinstance(tracer_provider, TracerProvider):
        tracer_provider.add_span_processor(span_processor)
    else:
        tracer_provider = TracerProvider()
        tracer_provider.add_span_processor(span_processor)
        trace.set_tracer_provider(tracer_provider)


def _setup_langfuse(host: str, public_key: str, secret_key: str) -> None:
    """Configure OTLP export pointed at a Langfuse instance."""
    endpoint = f"{host}/api/public/otel/v1/traces"
    token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    headers = {"Authorization": f"Basic {token}"}
    logger.info("Tracing: Langfuse backend → %s", endpoint)
    _setup_otlp(endpoint, headers)


def setup_copaw_tracing() -> None:
    """Initialise OpenTelemetry tracing based on environment configuration.

    Detection order:
    1. Langfuse  – when ``COPAW_LANGFUSE_PUBLIC_KEY`` and
                   ``COPAW_LANGFUSE_SECRET_KEY`` are both non-empty.
    2. Generic OTLP – when ``COPAW_OTLP_ENDPOINT`` is non-empty.
    3. No-op     – tracing is skipped silently.

    Env vars are read directly from ``os.environ`` at call-time (not from
    cached module-level constants) so that values written by
    ``load_envs_into_environ()`` are visible here.
    """
    import os

    # --- Langfuse -----------------------------------------------------------
    public_key = os.environ.get("COPAW_LANGFUSE_PUBLIC_KEY", "").strip()
    secret_key = os.environ.get("COPAW_LANGFUSE_SECRET_KEY", "").strip()
    if public_key and secret_key:
        host = os.environ.get(
            "COPAW_TRACING_ENDPOINT", "https://cloud.langfuse.com"
        ).rstrip("/")
        try:
            _setup_langfuse(host, public_key, secret_key)
        except Exception:
            logger.exception("Failed to set up Langfuse tracing")
        return

    # --- Generic OTLP -------------------------------------------------------
    endpoint = os.environ.get("COPAW_TRACING_ENDPOINT", "").strip()
    if endpoint:
        raw_headers = os.environ.get("COPAW_OTLP_HEADERS", "").strip()
        headers = _parse_headers(raw_headers) if raw_headers else None
        try:
            _setup_otlp(endpoint, headers)
            logger.info("Tracing: generic OTLP backend → %s", endpoint)
        except Exception:
            logger.exception("Failed to set up OTLP tracing")
        return

    logger.debug("Tracing: no backend configured, skipping")
