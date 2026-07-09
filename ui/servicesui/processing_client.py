"""Thin HTTP client the Streamlit UI uses to trigger and inspect processing
runs. It never touches ClaimsProcessingPipeline directly - every run goes
through the same pipeline_singleton instance via the FastAPI routes in
routes/processing.py, so UI-triggered and SMS-triggered runs share one
history (WORKFLOW.md §2.2)."""

import os

import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


def ws_url() -> str:
    return API_BASE_URL.replace("http://", "ws://").replace("https://", "wss://") + "/ws"


def start_processing(sender_email: str | None = None, timeout: float = 5.0) -> dict:
    params = {"sender_email": sender_email} if sender_email else {}
    response = requests.post(f"{API_BASE_URL}/processing/start", params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_status(timeout: float = 5.0) -> dict:
    response = requests.get(f"{API_BASE_URL}/processing/status", timeout=timeout)
    response.raise_for_status()
    return response.json()


def get_history(limit: int = 50, timeout: float = 5.0) -> list[dict]:
    response = requests.get(f"{API_BASE_URL}/processing/history", params={"limit": limit}, timeout=timeout)
    response.raise_for_status()
    return response.json().get("history", [])


def get_result(agent_id: str, timeout: float = 5.0) -> dict | None:
    response = requests.get(f"{API_BASE_URL}/processing/result/{agent_id}", timeout=timeout)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def stop_agent(agent_id: str, timeout: float = 5.0) -> dict:
    response = requests.post(f"{API_BASE_URL}/processing/stop/{agent_id}", timeout=timeout)
    response.raise_for_status()
    return response.json()
