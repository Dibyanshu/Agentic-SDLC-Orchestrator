import { RefreshCcw, Save } from "lucide-react";
import type { Section } from "../../types/api";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";

type SectionEditorProps = {
  section?: Section;
  draft: string;
  onDraftChange: (value: string) => void;
  onSave: () => void;
  onRegenerate: () => void;
  busy: boolean;
};

export function SectionEditor({ section, draft, onDraftChange, onSave, onRegenerate, busy }: SectionEditorProps) {
  return (
    <section className="flex min-h-0 flex-1 flex-col rounded-lg border border-slate-200 bg-white shadow-card">
      <div className="flex items-center justify-between border-b border-slate-200 p-4">
        <div>
          <h2 className="text-sm font-bold text-slate-900">{section?.sectionName ?? "No section"}</h2>
          <div className="mt-1 flex gap-2">
            <Badge tone="neutral">{section?.artifactType ?? "Artifact"}</Badge>
            <Badge tone="info">{`v${section?.version ?? 0}`}</Badge>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={onRegenerate} disabled={busy || !section} icon={<RefreshCcw className="h-4 w-4" />}>
            Regenerate
          </Button>
          <Button onClick={onSave} disabled={busy || !section} icon={<Save className="h-4 w-4" />}>
            Save
          </Button>
        </div>
      </div>
      <Textarea
        value={draft}
        onChange={(event) => onDraftChange(event.target.value)}
        className="m-4 min-h-72 flex-1"
        placeholder="Generated section content appears here."
      />
    </section>
  );
}
