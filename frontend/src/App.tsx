import { BrowserRouter, Route, Routes } from "react-router-dom";
import { WebSocketProvider, useConnectionState } from "./ws/WebSocketProvider";
import { Header } from "./components/Header";
import { Dashboard } from "./pages/Dashboard";
import { History } from "./pages/History";

function AppShell() {
  const connectionState = useConnectionState();
  return (
    <div className="flex min-h-screen flex-col">
      <Header connectionState={connectionState} />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/history" element={<History />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <WebSocketProvider>
        <AppShell />
      </WebSocketProvider>
    </BrowserRouter>
  );
}

export default App;
