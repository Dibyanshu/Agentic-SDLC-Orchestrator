import { ArrowRight } from "lucide-react";
import type { WorkflowResponse } from "../../types/api";
import { AgentCard } from "./AgentCard";

type AgentsPanelProps = {
  workflow?: WorkflowResponse;
};

export function AgentsPanel({ workflow }: AgentsPanelProps) {
  const artifacts = workflow?.artifacts ?? {};
  const currentNode = workflow?.currentNode ?? "manager_node";
  const agents = [
    { key: "PRD", node: "pm_node", name: "PM", role: "Product requirements" },
    { key: "BA", node: "ba_node", name: "BA", role: "Stories and criteria" },
    { key: "ARCH", node: "architect_node", name: "Architect", role: "HLD, LLD, APIs, schema" },
  ];

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-card">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-sm font-bold text-slate-900">Agents</h2>
        <span className="text-xs font-medium text-slate-500">{workflow?.status ?? "idle"}</span>
      </div>
      <div className="flex items-center gap-2 overflow-x-auto">
        {agents.map((agent, index) => {
          const complete = Boolean(artifacts[agent.key]);
          const status = currentNode === agent.node ? "active" : complete ? "complete" : "waiting";
          return (
            <div key={agent.key} className="flex flex-1 items-center gap-2">
              <AgentCard
                name={agent.name}
                role={agent.role}
                status={status}
                progress={status === "complete" ? 100 : status === "active" ? 65 : 0}
              />
              {index < agents.length - 1 ? <ArrowRight className="h-4 w-4 flex-none text-slate-400" /> : null}
            </div>
          );
        })}
      </div>
    </section>
  );
}
