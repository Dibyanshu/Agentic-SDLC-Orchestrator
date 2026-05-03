import { Activity, FileText, ListChecks, Network, ScrollText } from "lucide-react";
import type { ArtifactType, Project, WorkflowMetrics } from "../../types/api";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type SidebarProps = {
  project?: Project;
  metrics?: WorkflowMetrics;
  selectedArtifact: ArtifactType;
  onArtifactChange: (artifact: ArtifactType) => void;
  projectName: string;
  projectGoal: string;
  onProjectNameChange: (value: string) => void;
  onProjectGoalChange: (value: string) => void;
  onCreate: () => void;
  busy: boolean;
};

const items: Array<{ id: ArtifactType; label: string; icon: typeof FileText }> = [
  { id: "PRD", label: "PRD", icon: FileText },
  { id: "BA", label: "BA", icon: ListChecks },
  { id: "ARCH", label: "Architecture", icon: Network },
];

export function Sidebar({
  project,
  metrics,
  selectedArtifact,
  onArtifactChange,
  projectName,
  projectGoal,
  onProjectNameChange,
  onProjectGoalChange,
  onCreate,
  busy,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-64 flex-none flex-col border-r border-slate-200 bg-white">
      <div className="border-b border-slate-200 p-4">
        <div className="text-base font-black text-slate-950">Agentic SDLC</div>
        <div className="mt-1 text-xs text-slate-500">Workflow console</div>
      </div>
      <div className="space-y-2 border-b border-slate-200 p-4">
        <Input value={projectName} onChange={(event) => onProjectNameChange(event.target.value)} placeholder="Project name" />
        <Input value={projectGoal} onChange={(event) => onProjectGoalChange(event.target.value)} placeholder="Project goal" />
        <Button onClick={onCreate} disabled={busy} className="w-full" icon={<Activity className="h-4 w-4" />}>
          Create
        </Button>
        {project ? <div className="truncate text-xs text-slate-500">{project.id}</div> : null}
      </div>
      <nav className="space-y-1 p-3">
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              onClick={() => onArtifactChange(item.id)}
              className={`flex h-10 w-full items-center gap-2 rounded-md px-3 text-sm font-semibold ${
                selectedArtifact === item.id ? "bg-blue-50 text-primary" : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </button>
          );
        })}
      </nav>
      <div className="mt-auto border-t border-slate-200 p-4 text-xs text-slate-500">
        <div className="mb-2 flex items-center gap-2 font-bold text-slate-700">
          <ScrollText className="h-4 w-4" />
          Metrics
        </div>
        <div>LLM calls: {metrics?.llmCallCount ?? 0}</div>
        <div>Tokens: {metrics?.totalTokens ?? 0}</div>
        <div>Refinements: {metrics?.refinementCount ?? 0}</div>
      </div>
    </aside>
  );
}
