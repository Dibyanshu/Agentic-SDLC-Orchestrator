import type { ArtifactType, Section } from "../../types/api";
import { Tabs } from "../ui/Tabs";

type SectionTabsProps = {
  artifact: ArtifactType;
  sections: Section[];
  selected: string;
  onSelect: (section: string) => void;
};

const fallback = {
  PRD: ["Overview", "Features", "UserFlow"],
  BA: ["UserStories", "AcceptanceCriteria"],
  ARCH: ["APIs", "DBSchema", "HLD", "LLD"],
};

export function SectionTabs({ artifact, sections, selected, onSelect }: SectionTabsProps) {
  const names = sections.length > 0 ? sections.map((section) => section.sectionName) : fallback[artifact];
  return <Tabs tabs={names.map((name) => ({ id: name, label: name }))} activeId={selected} onChange={onSelect} />;
}
