import { Fragment, useState } from "react";
import type { LlmLog } from "../../types/api";
import { Badge } from "../ui/Badge";
import { Card } from "../ui/Card";

type LogsTableProps = {
  logs: LlmLog[];
};

export function LogsTable({ logs }: LogsTableProps) {
  const [openId, setOpenId] = useState<number | null>(null);
  return (
    <Card className="overflow-hidden">
      <div className="border-b border-slate-200 px-4 py-3 text-sm font-bold text-slate-900">LLM Logs</div>
      <div className="max-h-72 overflow-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs text-slate-500">
            <tr>
              <th className="px-4 py-2">Node</th>
              <th className="px-4 py-2">Model</th>
              <th className="px-4 py-2">Tokens</th>
              <th className="px-4 py-2">Latency</th>
              <th className="px-4 py-2">Status</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <Fragment key={log.id}>
                <tr key={log.id} onClick={() => setOpenId(openId === log.id ? null : log.id)} className="cursor-pointer border-t border-slate-100 hover:bg-slate-50">
                  <td className="px-4 py-2 font-semibold">{log.nodeName}</td>
                  <td className="px-4 py-2">{log.modelName}</td>
                  <td className="px-4 py-2">{log.totalTokens}</td>
                  <td className="px-4 py-2">{log.latencyMs}ms</td>
                  <td className="px-4 py-2"><Badge tone={log.status === "success" ? "success" : "danger"}>{log.status}</Badge></td>
                </tr>
                {openId === log.id ? (
                  <tr key={`${log.id}-detail`} className="border-t border-slate-100 bg-slate-50">
                    <td colSpan={5} className="space-y-2 px-4 py-3 text-xs text-slate-600">
                      <div className="font-semibold text-slate-800">Prompt</div>
                      <pre className="whitespace-pre-wrap rounded bg-white p-3">{log.userPrompt}</pre>
                      <div className="font-semibold text-slate-800">Response</div>
                      <pre className="whitespace-pre-wrap rounded bg-white p-3">{log.responseText}</pre>
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            ))}
          </tbody>
        </table>
        {logs.length === 0 ? <div className="p-4 text-sm text-slate-500">No logs yet.</div> : null}
      </div>
    </Card>
  );
}
