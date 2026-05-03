import type { SectionVersion } from "../../types/api";
import { Card } from "../ui/Card";

type SectionHistoryProps = {
  versions: SectionVersion[];
};

export function SectionHistory({ versions }: SectionHistoryProps) {
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-4 py-3 text-sm font-bold text-slate-900">History</div>
      <div className="max-h-44 overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-4 py-2">Version</th>
              <th className="px-4 py-2">Reason</th>
              <th className="px-4 py-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((version) => (
              <tr key={version.id} className="border-t border-slate-100">
                <td className="px-4 py-2 font-semibold">v{version.version}</td>
                <td className="px-4 py-2 text-slate-600">{version.changeReason ?? "initial"}</td>
                <td className="px-4 py-2 text-slate-500">{new Date(version.createdAt).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {versions.length === 0 ? <div className="p-4 text-sm text-slate-500">No versions yet.</div> : null}
      </div>
    </Card>
  );
}
