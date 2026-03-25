export const ARTIFACT_ROLE_OPTIONS = [
  { value: "narrative_brief", label: "Narrative brief" },
  { value: "supporting_doc", label: "Supporting doc" },
  { value: "results_table", label: "Results table" },
  { value: "background_reference", label: "Background / reference" },
] as const;

export type ArtifactRole = (typeof ARTIFACT_ROLE_OPTIONS)[number]["value"];

export function artifactRoleLabel(role: string) {
  return ARTIFACT_ROLE_OPTIONS.find((option) => option.value === role)?.label || "Supporting doc";
}

export function defaultArtifactRoleForFilename(filename: string): ArtifactRole {
  const suffix = filename.toLowerCase().split(".").pop() || "";
  if (["csv", "tsv", "xlsx", "xls"].includes(suffix)) {
    return "results_table";
  }
  if (["md", "txt", "doc", "docx"].includes(suffix)) {
    return "supporting_doc";
  }
  return "supporting_doc";
}
