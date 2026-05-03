import { Save } from "lucide-react";
import type { AgentLlmSettings, LlmProvider, LlmProviderInfo, ProjectLlmSettings } from "../../types/api";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";

type AgentKey = "pm" | "ba" | "architect";

type LlmSettingsPanelProps = {
  settings?: ProjectLlmSettings;
  providers: LlmProviderInfo[];
  busy: boolean;
  onChange: (agent: AgentKey, settings: AgentLlmSettings) => void;
  onSave: () => void;
};

const rows: Array<{ id: AgentKey; label: string }> = [
  { id: "pm", label: "PM" },
  { id: "ba", label: "BA" },
  { id: "architect", label: "Architect" },
];

export function LlmSettingsPanel({ settings, providers, busy, onChange, onSave }: LlmSettingsPanelProps) {
  if (!settings) {
    return null;
  }

  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-card">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-sm font-black text-slate-950">LLM Settings</h2>
        <Button variant="ghost" onClick={onSave} disabled={busy} icon={<Save className="h-4 w-4" />}>
          Save
        </Button>
      </div>
      <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
        {rows.map((row) => {
          const agentSettings = settings.agents[row.id];
          const providerInfo = providers.find((provider) => provider.provider === agentSettings.provider);
          const keyOk = agentSettings.provider === "stub" || Boolean(providerInfo?.apiKeyConfigured);
          return (
            <div key={row.id} className="rounded-md border border-slate-200 p-3">
              <div className="mb-2 flex items-center justify-between gap-2">
                <div className="text-xs font-black uppercase text-slate-500">{row.label}</div>
                <Badge tone={keyOk ? "success" : "warning"}>{keyOk ? "key ok" : "key missing"}</Badge>
              </div>
              <div className="space-y-2">
                <select
                  value={agentSettings.provider}
                  onChange={(event) => {
                    const provider = event.target.value as LlmProvider;
                    const nextProvider = providers.find((item) => item.provider === provider);
                    onChange(row.id, {
                      ...agentSettings,
                      provider,
                      model: nextProvider?.defaultModel ?? agentSettings.model,
                    });
                  }}
                  className="h-9 w-full rounded-md border border-slate-300 bg-white px-2 text-sm outline-none focus:border-primary focus:ring-2 focus:ring-blue-100"
                >
                  {providers.map((provider) => (
                    <option key={provider.provider} value={provider.provider}>
                      {provider.provider}
                    </option>
                  ))}
                </select>
                <Input
                  value={agentSettings.model}
                  onChange={(event) => onChange(row.id, { ...agentSettings, model: event.target.value })}
                  placeholder="Model"
                />
                <Input
                  type="number"
                  min={100}
                  max={200000}
                  value={agentSettings.tokenBudget}
                  onChange={(event) =>
                    onChange(row.id, {
                      ...agentSettings,
                      tokenBudget: Number(event.target.value),
                    })
                  }
                  placeholder="Token budget"
                />
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
