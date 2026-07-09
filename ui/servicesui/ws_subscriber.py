"""Background WebSocket subscriber.

Runs in its own thread (started once per Streamlit session), holds a
persistent connection to the FastAPI /ws broadcast endpoint, and appends
every incoming AgentUpdate JSON message onto a thread-safe queue. The main
Streamlit render loop drains that queue on each rerun - it never talks to
the socket directly, since Streamlit's script-rerun model can't hold a
long-lived async connection on the render thread itself (WORKFLOW.md §9).
"""

import asyncio
import json
import logging
import queue
import threading

import websockets

logger = logging.getLogger(__name__)


class WebSocketSubscriber:
    def __init__(self, url: str):
        self.url = url
        self.messages: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def drain(self) -> list[dict]:
        drained = []
        while True:
            try:
                drained.append(self.messages.get_nowait())
            except queue.Empty:
                break
        return drained

    def _run(self):
        asyncio.run(self._listen())

    async def _listen(self):
        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self.url, ping_interval=20, ping_timeout=20) as ws:
                    while not self._stop_event.is_set():
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        except asyncio.TimeoutError:
                            continue
                        try:
                            self.messages.put(json.loads(message))
                        except json.JSONDecodeError:
                            logger.warning("Dropped malformed WS message: %r", message)
            except Exception as e:
                if self._stop_event.is_set():
                    break
                logger.warning(f"WS connection lost ({e}); retrying in 2s")
                await asyncio.sleep(2)


def get_or_create_subscriber(session_state, url: str) -> WebSocketSubscriber:
    """Guarded singleton: only starts one background thread per session,
    even across Streamlit's full-script reruns."""
    subscriber = session_state.get("ws_subscriber")
    if subscriber is None:
        subscriber = WebSocketSubscriber(url)
        subscriber.start()
        session_state["ws_subscriber"] = subscriber
    return subscriber
