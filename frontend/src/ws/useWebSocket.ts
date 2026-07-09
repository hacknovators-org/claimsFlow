import { useEffect, useRef, useState } from "react";
import { wsUrl } from "../api/client";
import type { AgentUpdate } from "../api/types";

export type ConnectionState = "connecting" | "open" | "reconnecting" | "closed";

export function useWebSocket(onMessage: (update: AgentUpdate) => void) {
  const [state, setState] = useState<ConnectionState>("connecting");
  const stopped = useRef(false);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  useEffect(() => {
    stopped.current = false;
    let socket: WebSocket | null = null;
    let retryDelay = 1000;
    let retryTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (stopped.current) return;
      setState((prev) => (prev === "connecting" ? "connecting" : "reconnecting"));
      socket = new WebSocket(wsUrl());

      socket.onopen = () => {
        retryDelay = 1000;
        setState("open");
      };
      socket.onmessage = (event) => {
        try {
          onMessageRef.current(JSON.parse(event.data));
        } catch {
          console.warn("Dropped malformed WS message", event.data);
        }
      };
      socket.onclose = () => {
        if (stopped.current) return;
        setState("reconnecting");
        retryTimer = setTimeout(connect, retryDelay);
        retryDelay = Math.min(retryDelay * 2, 15000);
      };
      socket.onerror = () => socket?.close();
    }

    connect();
    return () => {
      stopped.current = true;
      setState("closed");
      if (retryTimer) clearTimeout(retryTimer);
      socket?.close();
    };
  }, []);

  return state;
}
