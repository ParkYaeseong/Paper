export type User = {
  sub: string;
  username: string;
  email: string;
  name: string;
  role: string;
};

export type AuthConfig = {
  ok: boolean;
  enabled: boolean;
  issuer?: string;
  client_id?: string;
  scopes?: string;
  provider_name?: string;
  authorization_endpoint?: string;
  end_session_endpoint?: string;
  account_url?: string;
};

export type Project = {
  id: string;
  title: string;
  objective: string;
  status: string;
  owner_sub: string;
  owner_username: string;
  created_at: string;
  updated_at: string;
};

export type ProjectListResponse = {
  items: Project[];
};

export type DatasetProfile = {
  id: string;
  version: number;
  summary_json: Record<string, unknown>;
} | null;

export type Outline = {
  id: string;
  version: number;
  manuscript_type: string;
  title_candidates_json: string[];
  outline_json: {
    sections: Array<{
      key: string;
      heading: string;
      claims?: string[];
    }>;
  };
} | null;

export type DraftSection = {
  id: string;
  section_key: string;
  heading: string;
  version: number;
  content: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type CitationSlot = {
  id: string;
  section_key: string;
  slot_key: string;
  claim_text: string;
  context_text: string;
  ordinal: number;
  status: string;
};

export type ReferenceRecord = {
  id: string;
  source: string;
  external_id: string;
  title: string;
  abstract: string;
  authors_json: string[];
  venue: string;
  year: number | null;
  doi: string;
  url: string;
};

export type EvidenceMatch = {
  id: string;
  citation_slot_id: string;
  queries_json: string[];
  candidate_reference_ids_json: string[];
  selected_reference_ids_json: string[];
  support_score: number;
  status: string;
  notes: string;
};

export type ExportBundle = {
  id: string;
  status: string;
  manifest_json: Record<string, string>;
  download_urls: Record<string, string>;
} | null;

export type JobRun = {
  id: string;
  stage: string;
  status: string;
  payload_json: Record<string, unknown> | null;
  result_json: Record<string, unknown> | null;
  log_text: string;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Workspace = {
  project: Project;
  dataset_profile: DatasetProfile;
  outline: Outline;
  draft_sections: DraftSection[];
  citation_slots: CitationSlot[];
  reference_records: ReferenceRecord[];
  evidence_matches: EvidenceMatch[];
  export_bundle: ExportBundle;
  jobs: JobRun[];
};
