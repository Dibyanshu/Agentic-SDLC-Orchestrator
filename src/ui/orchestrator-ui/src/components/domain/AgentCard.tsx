import { Badge } from "../ui/Badge";

type AgentCardProps = {
  name: string;
  role: string;
  status: "complete" | "active" | "waiting";
  progress: number;
};

const tone = {
  complete: "success",
  active: "info",
  waiting: "neutral",
} as const;

export function AgentCard({ name, role, status, progress }: AgentCardProps) {
  return (
    <div className={`min-w-44 flex-1 rounded-lg border p-3 ${status === "active" ? "border-primary bg-blue-50" : "border-slate-200 bg-white"}`}>
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="text-sm font-bold text-slate-900">{name}</div>
          <div className="text-xs text-slate-500">{role}</div>
        </div>
        <Badge tone={tone[status]}>{status}</Badge>
      </div>
      <div className="mt-3 h-2 rounded-full bg-slate-100">
        <div className="h-2 rounded-full bg-primary" style={{ width: `${progress}%` }} />
      </div>
    </div>
  );
}
