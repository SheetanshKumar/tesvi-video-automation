"""Extractor service entrypoint.

Consumes source.ingested Pub/Sub messages, calls Claude Sonnet 5 with a
structured-output tool schema, writes validated questions to Postgres,
and publishes questions.extracted.

This scaffold only exposes /healthz and /readyz — real handlers land
with the Anthropic SDK and Postgres client wiring.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

SERVICE_NAME = "extractor"

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(SERVICE_NAME)

app = FastAPI(title=SERVICE_NAME)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    return {"status": "ok", "service": SERVICE_NAME}
