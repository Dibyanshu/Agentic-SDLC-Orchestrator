import { useEffect, useMemo, useState } from "react";
import { AlertCircle, Rocket } from "lucide-react";
import { AgentsPanel } from "../components/domain/AgentsPanel";
import { HITLPanel } from "../components/domain/HITLPanel";
import { LlmSettingsPanel } from "../components/domain/LlmSettingsPanel";
import { LogsTable } from "../components/domain/LogsTable";
import { SectionEditor } from "../components/domain/SectionEditor";
import { SectionHistory } from "../components/domain/SectionHistory";
import { SectionTabs } from "../components/domain/SectionTabs";
import { Sidebar } from "../components/domain/Sidebar";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Textarea } from "../components/ui/Textarea";
import { AppLayout } from "../layouts/AppLayout";
import {
  createProject,
  deleteRagSource,
  getLlmProviders,
  getLogs,
  getMetrics,
  getProjectLlmSettings,
  getRagSources,
  getSectionVersions,
  getSections,
  getWorkflowStatus,
  hitlAction,
  resumeWorkflow,
  startWorkflow,
  updateSection,
  updateProjectLlmSettings,
  uploadRagSource,
} from "../services/api";
import { useAppStore } from "../store/useAppStore";
import type { AgentLlmSettings, ArtifactType, LlmProviderInfo, ProjectLlmSettings, RagSource, SectionVersion } from "../types/api";

export function Dashboard() {
  const {
    project,
    workflow,
    sections,
    logs,
    metrics,
    selectedArtifact,
    selectedSection,
    busy,
    message,
    setProject,
    setWorkflow,
    setSections,
    setSelectedArtifact,
    setSelectedSection,
    setLogs,
    setMetrics,
    setBusy,
    setMessage,
  } = useAppStore();
  const [projectName, setProjectName] = useState("Demo");
  const [projectGoal, setProjectGoal] = useState("Generate early SDLC artifacts");
  const [workflowInput, setWorkflowInput] = useState("Build an agentic SDLC orchestrator with HITL controls");
  const [draft, setDraft] = useState("");
  const [hitlInput, setHitlInput] = useState("");
  const [mode, setMode] = useState<"single" | "cascade">("single");
  const [versions, setVersions] = useState<SectionVersion[]>([]);
  const [sources, setSources] = useState<RagSource[]>([]);
  const [providers, setProviders] = useState<LlmProviderInfo[]>([]);
  const [llmSettings, setLlmSettings] = useState<ProjectLlmSettings>();

  const artifactSections = useMemo(
    () => sections.filter((section) => section.artifactType === selectedArtifact),
    [sections, selectedArtifact],
  );
  const currentSection = artifactSections.find((section) => section.sectionName === selectedSection);

  useEffect(() => {
    const first = artifactSections[0]?.sectionName;
    if (first && !artifactSections.some((section) => section.sectionName === selectedSection)) {
      setSelectedSection(first);
    }
  }, [artifactSections, selectedSection, setSelectedSection]);

  useEffect(() => {
    setDraft(String(currentSection?.content ?? ""));
    setHitlInput(String(currentSection?.content ?? ""));
  }, [currentSection]);

  useEffect(() => {
    getLlmProviders()
      .then(setProviders)
      .catch(() => setProviders([]));
  }, []);

  useEffect(() => {
    if (!project || !currentSection) {
      setVersions([]);
      return;
    }
    getSectionVersions(project.id, currentSection.artifactType, currentSection.sectionName)
      .then(setVersions)
      .catch(() => setVersions([]));
  }, [project, currentSection]);

  async function refresh(projectId = project?.id) {
    if (!projectId) {
      return;
    }
    const [nextSections, nextLogs, nextMetrics, nextWorkflow] = await Promise.all([
      getSections(projectId),
      getLogs(projectId),
      getMetrics(projectId),
      getWorkflowStatus(projectId),
    ]);
    setSections(nextSections);
    setLogs(nextLogs);
    setMetrics(nextMetrics);
    setWorkflow(nextWorkflow);
    setSources(await getRagSources(projectId));
    setLlmSettings(await getProjectLlmSettings(projectId));
  }

  async function runAction(action: () => Promise<void>, success: string) {
    setBusy(true);
    setMessage(undefined);
    try {
      await action();
      setMessage(success);
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Request failed";
      setMessage(detail);
    } finally {
      setBusy(false);
    }
  }

  async function handleCreate() {
    await runAction(async () => {
      const nextProject = await createProject(projectName, projectGoal);
      setProject(nextProject);
      setSections([]);
      setLogs([]);
      setVersions([]);
      setSources(await getRagSources(nextProject.id));
      setLlmSettings(await getProjectLlmSettings(nextProject.id));
    }, "Project created");
  }

  async function handleSourceUpload(file: File) {
    if (!project) return;
    await runAction(async () => {
      const sourceType = getSourceType(file);
      if (!sourceType) {
        throw new Error("Only TXT, PDF, and DOCX context sources are supported.");
      }
      const content = sourceType === "txt" ? await file.text() : await readFileAsBase64(file);
      await uploadRagSource(project.id, file.name, content, sourceType);
      setSources(await getRagSources(project.id));
    }, "Context source indexed");
  }

  async function handleSourceDelete(sourceId: string) {
    if (!project) return;
    await runAction(async () => {
      await deleteRagSource(sourceId);
      setSources(await getRagSources(project.id));
    }, "Context source deleted");
  }

  async function handleStart() {
    if (!project) return;
    const missingKey = findMissingProviderKey();
    if (missingKey) {
      setMessage(`${missingKey} API key is not configured in .env`);
      return;
    }
    await runAction(async () => {
      const nextWorkflow = await startWorkflow(project.id, workflowInput);
      setWorkflow(nextWorkflow);
      await refresh(project.id);
    }, "Workflow started");
  }

  async function handleLlmSettingsSave() {
    if (!project || !llmSettings) return;
    await runAction(async () => {
      setLlmSettings(await updateProjectLlmSettings(project.id, llmSettings));
    }, "LLM settings saved");
  }

  function handleLlmSettingsChange(agent: "pm" | "ba" | "architect", settings: AgentLlmSettings) {
    if (!llmSettings) return;
    setLlmSettings({
      ...llmSettings,
      agents: {
        ...llmSettings.agents,
        [agent]: settings,
      },
    });
  }

  function findMissingProviderKey() {
    if (!llmSettings) return undefined;
    for (const settings of Object.values(llmSettings.agents)) {
      if (settings.provider === "stub") continue;
      const provider = providers.find((item) => item.provider === settings.provider);
      if (!provider?.apiKeyConfigured) {
        return settings.provider;
      }
    }

    return undefined;
  }

  async function handleSave() {
    if (!project || !currentSection) return;
    await runAction(async () => {
      await updateSection(project.id, currentSection.artifactType, currentSection.sectionName, draft);
      await refresh(project.id);
    }, "Section saved");
  }

  async function handleHitl(action: "approve" | "edit" | "regenerate") {
    if (!project) return;
    await runAction(async () => {
      const section = currentSection ? `${currentSection.artifactType}.${currentSection.sectionName}` : undefined;
      const nextWorkflow = await hitlAction({
        projectId: project.id,
        action,
        section,
        content: action === "edit" ? hitlInput : undefined,
        mode: action === "regenerate" ? mode : undefined,
      });
      setWorkflow(nextWorkflow);
      await refresh(project.id);
    }, `${action} sent`);
  }

  async function handleResume() {
    if (!project) return;
    await runAction(async () => {
      const nextWorkflow = await resumeWorkflow(project.id);
      setWorkflow(nextWorkflow);
      await refresh(project.id);
    }, "Workflow resumed");
  }

  const main = (
    <div className="flex min-h-full flex-col gap-4 p-4">
      <header className="rounded-lg border border-slate-200 bg-white p-4 shadow-card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-black text-slate-950">{project?.name ?? "No project selected"}</h1>
              <Badge tone={workflow?.status === "completed" ? "success" : workflow ? "info" : "neutral"}>
                {workflow?.status ?? "idle"}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-slate-500">{project?.goal ?? "Create a project to begin."}</p>
          </div>
          <div className="flex min-w-80 flex-1 gap-2">
            <Textarea value={workflowInput} onChange={(event) => setWorkflowInput(event.target.value)} className="h-20 flex-1" />
            <Button onClick={handleStart} disabled={busy || !project} icon={<Rocket className="h-4 w-4" />}>
              Start
            </Button>
          </div>
        </div>
        {message ? (
          <div className="mt-3 flex items-center gap-2 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
            <AlertCircle className="h-4 w-4" />
            {message}
          </div>
        ) : null}
      </header>
      <AgentsPanel workflow={workflow} />
      <LlmSettingsPanel
        settings={llmSettings}
        providers={providers}
        busy={busy || !project}
        onChange={handleLlmSettingsChange}
        onSave={handleLlmSettingsSave}
      />
      <div className="rounded-lg border border-slate-200 bg-white px-4 shadow-card">
        <SectionTabs
          artifact={selectedArtifact}
          sections={artifactSections}
          selected={selectedSection}
          onSelect={setSelectedSection}
        />
      </div>
      <SectionEditor
        section={currentSection}
        draft={draft}
        onDraftChange={setDraft}
        onSave={handleSave}
        onRegenerate={() => handleHitl("regenerate")}
        busy={busy}
      />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <SectionHistory versions={versions} />
        <LogsTable logs={logs} />
      </div>
    </div>
  );

  return (
    <AppLayout
      sidebar={
        <Sidebar
          project={project}
          metrics={metrics}
          selectedArtifact={selectedArtifact}
          onArtifactChange={(artifact: ArtifactType) => {
            setSelectedArtifact(artifact);
            const first = sections.find((section) => section.artifactType === artifact)?.sectionName;
            setSelectedSection(first ?? (artifact === "ARCH" ? "APIs" : artifact === "BA" ? "UserStories" : "Overview"));
          }}
          projectName={projectName}
          projectGoal={projectGoal}
          onProjectNameChange={setProjectName}
          onProjectGoalChange={setProjectGoal}
          onCreate={handleCreate}
          onSourceUpload={handleSourceUpload}
          onSourceDelete={handleSourceDelete}
          sources={sources}
          busy={busy}
        />
      }
      main={main}
      actionPanel={
        <HITLPanel
          workflow={workflow}
          section={currentSection}
          mode={mode}
          content={hitlInput}
          onModeChange={setMode}
          onContentChange={setHitlInput}
          onApprove={() => handleHitl("approve")}
          onEdit={() => handleHitl("edit")}
          onRegenerate={() => handleHitl("regenerate")}
          onResume={handleResume}
          busy={busy}
        />
      }
    />
  );
}

function getSourceType(file: File): RagSource["sourceType"] | undefined {
  const extension = file.name.split(".").pop()?.toLowerCase();
  if (extension === "txt" || file.type === "text/plain") return "txt";
  if (extension === "pdf" || file.type === "application/pdf") return "pdf";
  if (
    extension === "docx" ||
    file.type === "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
  ) {
    return "docx";
  }

  return undefined;
}

function readFileAsBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Could not read context source."));
    reader.onload = () => {
      const result = typeof reader.result === "string" ? reader.result : "";
      resolve(result.split(",", 2)[1] ?? "");
    };
    reader.readAsDataURL(file);
  });
}
