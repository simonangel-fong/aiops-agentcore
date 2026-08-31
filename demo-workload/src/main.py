"""
FastAPI app that leaks memory until the container is OOMKilled (exit 137).
Env vars: LEAK_ENABLED, LEAK_START_SECONDS, LEAK_MB_PER_TICK, LEAK_INTERVAL_SECONDS
"""

import asyncio
import json
import os
import sys
import time
from contextlib import asynccontextmanager

import psutil
from fastapi import FastAPI

# get env var
ENABLED = os.getenv("LEAK_ENABLED", "true").lower() != "false"
START_SECONDS = int(os.getenv("LEAK_START_SECONDS", "180"))
MB_PER_TICK = int(os.getenv("LEAK_MB_PER_TICK", "16"))
INTERVAL = int(os.getenv("LEAK_INTERVAL_SECONDS", "1"))

MB = 1024 * 1024
blocks = []
started = time.monotonic()


def rss_mb():
    return psutil.Process().memory_info().rss // MB


def log(event, **extra):
    """One JSON line per event."""
    print(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "level": "INFO",
        "event": event,
        "allocated_mb": len(blocks) * MB_PER_TICK,
        "rss_mb": rss_mb(),
        **extra,
    }), flush=True)


def allocate():
    """Allocate one block and touch every page so RSS actually grows."""
    block = bytearray(MB_PER_TICK * MB)
    for offset in range(0, len(block), 4096):
        block[offset] = 1
    blocks.append(block)


async def leak():
    await asyncio.sleep(START_SECONDS)
    log("leak_started", mb_per_tick=MB_PER_TICK)
    while True:
        allocate()
        log("leak_progress")
        await asyncio.sleep(INTERVAL)


@asynccontextmanager
async def lifespan(app):
    log("app_started", leak_enabled=ENABLED, leak_start_seconds=START_SECONDS)
    task = asyncio.create_task(leak()) if ENABLED else None
    yield
    if task:
        task.cancel()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    return {"service": "aiops-agentcore-workload", "status": "ok"}


@app.get("/healthz")
async def healthz():
    return {"status": "healthy"}


@app.get("/status")
async def status():
    return {
        "allocated_mb": len(blocks) * MB_PER_TICK,
        "rss_mb": rss_mb(),
        "uptime_seconds": round(time.monotonic() - started, 1),
        "leaking": bool(blocks),
    }
