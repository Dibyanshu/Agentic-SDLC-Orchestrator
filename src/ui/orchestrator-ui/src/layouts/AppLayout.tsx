import type { ReactNode } from "react";

type AppLayoutProps = {
  sidebar: ReactNode;
  main: ReactNode;
  actionPanel: ReactNode;
};

export function AppLayout({ sidebar, main, actionPanel }: AppLayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-100">
      {sidebar}
      <main className="min-w-0 flex-1 overflow-auto">{main}</main>
      {actionPanel}
    </div>
  );
}
