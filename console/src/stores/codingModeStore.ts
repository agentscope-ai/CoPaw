import { create } from "zustand";
import { persist } from "zustand/middleware";
import { useAgentStore } from "./agentStore";

export interface TodoItem {
  id: string;
  content: string;
  status: "pending" | "in_progress" | "done" | "cancelled";
}

interface CodingModeState {
  /** Whether Coding Mode is active per agentId */
  codingModeByAgent: Record<string, boolean>;
  /** Live TODO list, keyed by agentId */
  todosByAgent: Record<string, TodoItem[]>;

  setCodingMode: (agentId: string, enabled: boolean) => void;
  setTodos: (agentId: string, todos: TodoItem[]) => void;
}

export const useCodingModeStore = create<CodingModeState>()(
  persist<CodingModeState>(
    (set) => ({
      codingModeByAgent: {},
      todosByAgent: {},

      setCodingMode: (agentId: string, enabled: boolean) =>
        set((state: CodingModeState) => ({
          codingModeByAgent: { ...state.codingModeByAgent, [agentId]: enabled },
        })),

      setTodos: (agentId: string, todos: TodoItem[]) =>
        set((state: CodingModeState) => ({
          todosByAgent: { ...state.todosByAgent, [agentId]: todos },
        })),
    }),
    {
      name: "qwenpaw-coding-mode",
    },
  ),
);

/** Convenience hook: coding mode status for the currently selected agent */
export function useCodingMode(): {
  codingMode: boolean;
  setCodingMode: (enabled: boolean) => void;
} {
  const { selectedAgent } = useAgentStore();
  const { codingModeByAgent, setCodingMode } = useCodingModeStore();
  return {
    codingMode: codingModeByAgent[selectedAgent] ?? false,
    setCodingMode: (enabled: boolean) => setCodingMode(selectedAgent, enabled),
  };
}

/** Convenience hook: todos for the currently selected agent */
export function useCurrentTodos(): TodoItem[] {
  const { selectedAgent } = useAgentStore();
  const { todosByAgent } = useCodingModeStore();
  return todosByAgent[selectedAgent] ?? [];
}
