import { Check, GitBranch, PenLine, Play, RotateCw } from "lucide-react";
import type { Section, WorkflowResponse } from "../../types/api";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Textarea } from "../ui/Textarea";

type HITLPanelProps = {
  workflow?: WorkflowResponse;
  section?: Section;
  mode: "single" | "cascade";
  content: string;
  onModeChange: (mode: "single" | "cascade") => void;
  onContentChange: (value: string) => void;
  onApprove: () => void;
  onEdit: () => void;
  onRegenerate: () => void;
  onResume: () => void;
  busy: boolean;
};

export function HITLPanel({
  workflow,
  section,
  mode,
  content,
  onModeChange,
  onContentChange,
  onApprove,
  onEdit,
  onRegenerate,
  onResume,
  busy,
}: HITLPanelProps) {
  const qualified = section ? `${section.artifactType}.${section.sectionName}` : "";
  return (
    <aside className="flex h-full w-80 flex-none flex-col gap-3 border-l border-slate-200 bg-slate-50 p-4">
      <Card className="p-4">
        <div className="mb-3 text-sm font-bold text-slate-900">HITL</div>
        <div className="mb-3 text-xs text-slate-500">Current node: {workflow?.currentNode ?? "idle"}</div>
        <div className="grid grid-cols-2 gap-2">
          <Button onClick={onApprove} disabled={busy || !workflow} icon={<Check className="h-4 w-4" />}>
            Approve
          </Button>
          <Button variant="ghost" onClick={onResume} disabled={busy || !workflow} icon={<Play className="h-4 w-4" />}>
            Resume
          </Button>
          <Button variant="secondary" onClick={onEdit} disabled={busy || !section} icon={<PenLine className="h-4 w-4" />}>
            Edit
          </Button>
          <Button variant="ghost" onClick={onRegenerate} disabled={busy || !section} icon={<RotateCw className="h-4 w-4" />}>
            Regen
          </Button>
        </div>
      </Card>
      <Card className="p-4">
        <div className="mb-2 text-sm font-bold text-slate-900">Mode</div>
        <div className="grid grid-cols-2 rounded-md bg-slate-100 p-1">
          {(["single", "cascade"] as const).map((item) => (
            <button
              key={item}
              onClick={() => onModeChange(item)}
              className={`h-8 rounded text-sm font-semibold ${mode === item ? "bg-white text-primary shadow-sm" : "text-slate-600"}`}
            >
              {item}
            </button>
          ))}
        </div>
      </Card>
      <Card className="flex min-h-0 flex-1 flex-col p-4">
        <div className="mb-2 text-sm font-bold text-slate-900">Input</div>
        <Textarea value={content} onChange={(event) => onContentChange(event.target.value)} className="min-h-40 flex-1" />
      </Card>
      <Card className="p-4">
        <div className="mb-2 flex items-center gap-2 text-sm font-bold text-slate-900">
          <GitBranch className="h-4 w-4" />
          Impact
        </div>
        <div className="text-sm text-slate-600">{qualified || "No section selected"}</div>
        <div className="mt-1 text-xs text-slate-500">{mode === "cascade" ? "Downstream sections may be regenerated." : "Only the owning node is rerun."}</div>
      </Card>
    </aside>
  );
}
