import { create } from "zustand";
import { laneForAgentId, rootAgentId, type Lane } from "../ws/stageTaxonomy";
import type { AgentUpdate, MasterResult } from "../api/types";

export type RunView = "idle" | "running" | "completed" | "failed";

interface RunStore {
  started: boolean;
  rootAgentId: string | null;
  senderEmail: string | null;
  laneUpdates: Partial<Record<Lane, AgentUpdate>>;
  finalResult: MasterResult | null;
  resultFetched: boolean;
  error: string | null;
  message: string | null;

  view: () => RunView;
  startNewRun: (senderEmail?: string) => void;
  applyUpdate: (update: AgentUpdate) => void;
  setFinalResult: (result: MasterResult) => void;
}

export const useRunStore = create<RunStore>((set, get) => ({
  started: false,
  rootAgentId: null,
  senderEmail: null,
  laneUpdates: {},
  finalResult: null,
  resultFetched: false,
  error: null,
  message: null,

  view: () => {
    const master = get().laneUpdates.master;
    if (!master) return get().started ? "running" : "idle";
    if (master.status === "failed" || master.status === "paused") return "failed";
    if (master.status === "completed") return "completed";
    return "running";
  },

  startNewRun: (senderEmail) =>
    set({
      started: true,
      senderEmail: senderEmail ?? null,
      rootAgentId: null,
      laneUpdates: {},
      finalResult: null,
      resultFetched: false,
      error: null,
      message: null,
    }),

  applyUpdate: (update) => {
    const lane = laneForAgentId(update.agent_id);
    const incomingRoot = rootAgentId(update.agent_id);
    const state = get();

    const isNewRunStart =
      lane === "master" &&
      incomingRoot !== state.rootAgentId &&
      update.status !== "completed" &&
      update.status !== "failed";

    if (isNewRunStart) {
      set({
        rootAgentId: incomingRoot,
        laneUpdates: {},
        finalResult: null,
        resultFetched: false,
        error: null,
      });
    }

    if (get().rootAgentId !== null && incomingRoot !== get().rootAgentId) {
      return; // stale broadcast from a run this client isn't tracking
    }

    set((s) => ({
      laneUpdates: { ...s.laneUpdates, [lane]: update },
      ...(lane === "master"
        ? {
            message: update.message,
            error: update.status === "failed" ? update.error : s.error,
          }
        : {}),
    }));
  },

  setFinalResult: (result) => set({ finalResult: result, resultFetched: true }),
}));
