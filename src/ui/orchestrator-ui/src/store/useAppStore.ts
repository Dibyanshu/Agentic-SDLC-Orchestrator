import { create } from "zustand";
import type { ArtifactType, LlmLog, Project, Section, WorkflowMetrics, WorkflowResponse } from "../types/api";

type AppState = {
  project?: Project;
  workflow?: WorkflowResponse;
  selectedArtifact: ArtifactType;
  selectedSection: string;
  sections: Section[];
  logs: LlmLog[];
  metrics?: WorkflowMetrics;
  busy: boolean;
  message?: string;
  setProject: (project: Project) => void;
  setWorkflow: (workflow: WorkflowResponse) => void;
  setSections: (sections: Section[]) => void;
  setSelectedArtifact: (artifact: ArtifactType) => void;
  setSelectedSection: (section: string) => void;
  setLogs: (logs: LlmLog[]) => void;
  setMetrics: (metrics: WorkflowMetrics) => void;
  setBusy: (busy: boolean) => void;
  setMessage: (message?: string) => void;
};

export const useAppStore = create<AppState>((set) => ({
  selectedArtifact: "PRD",
  selectedSection: "Overview",
  sections: [],
  logs: [],
  busy: false,
  setProject: (project) => set({ project }),
  setWorkflow: (workflow) => set({ workflow }),
  setSections: (sections) => set({ sections }),
  setSelectedArtifact: (selectedArtifact) => set({ selectedArtifact }),
  setSelectedSection: (selectedSection) => set({ selectedSection }),
  setLogs: (logs) => set({ logs }),
  setMetrics: (metrics) => set({ metrics }),
  setBusy: (busy) => set({ busy }),
  setMessage: (message) => set({ message }),
}));
