import { createContext, useContext, type ReactNode } from "react";
import { useWebSocket, type ConnectionState } from "./useWebSocket";
import { useRunStore } from "../store/runStore";

const ConnectionStateContext = createContext<ConnectionState>("connecting");

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const applyUpdate = useRunStore((s) => s.applyUpdate);
  const connectionState = useWebSocket(applyUpdate);

  return (
    <ConnectionStateContext.Provider value={connectionState}>{children}</ConnectionStateContext.Provider>
  );
}

export function useConnectionState() {
  return useContext(ConnectionStateContext);
}
