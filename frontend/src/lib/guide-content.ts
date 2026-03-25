export type GuideLanguage = "en" | "ko";

type GuideContent = {
  title: string;
  intro: string;
  quickStartTitle: string;
  quickStartSteps: string[];
  uploadTitle: string;
  uploadItems: string[];
  nextTitle: string;
  nextItems: string[];
  mistakesTitle: string;
  mistakesItems: string[];
};

export const GUIDE_CONTENT: Record<GuideLanguage, GuideContent> = {
  en: {
    title: "Usage Guide",
    intro: "Use this workflow when you want to turn project files into a review-ready manuscript with grounded citations, quality checks, figure handoff text for PaperBanana, and gated exports.",
    quickStartTitle: "Quick Start",
    quickStartSteps: [
      "Upload Selected Files",
      "Run All",
      "Review Quality Summary",
      "Review Figure Review",
      "Draft Export",
      "Final Export",
    ],
    uploadTitle: "What To Upload",
    uploadItems: [
      "Upload internal project materials such as README files, usage docs, CSV tables, JSON outputs, notes, and prior draft text.",
      "Choose a role for each file at upload time: Narrative brief, Supporting doc, Results table, or Background / reference.",
      "Reference papers are optional at upload time. Run Evidence searches external literature later.",
      "Upload is for your source material, not only for final reference PDFs.",
    ],
    nextTitle: "What Happens Next",
    nextItems: [
      "Run All sequences ingest, plan, draft, evidence, quality audit, and figure handoff preparation automatically.",
      "Quality Summary shows critical issues, warnings, and recommended actions.",
      "Figure Review prepares copyable method-section content and captions for PaperBanana.",
      "Draft Export always creates a working manuscript bundle.",
      "Final Export unlocks only after the latest quality report has no critical issues.",
      "If uploaded files change, run Run Ingest again to refresh the project profile.",
      "If you change an uploaded file role after upload, rerun ingest so the manuscript context is rebuilt correctly.",
    ],
    mistakesTitle: "Common Mistakes",
    mistakesItems: [
      "Uploading only literature PDFs and expecting a manuscript draft immediately.",
      "Ignoring Quality Summary and assuming a draft export is submission-ready.",
      "Skipping Figure Review when the manuscript still needs PaperBanana-ready figure handoff text.",
      "Forgetting to rerun ingest after adding or deleting uploaded files.",
    ],
  },
  ko: {
    title: "사용 가이드",
    intro: "이 워크플로우는 프로젝트 파일을 업로드한 뒤 초안 작성, 문헌 grounding, 품질 점검, PaperBanana용 그림 handoff 텍스트 준비, gated export까지 순서대로 진행할 때 사용합니다.",
    quickStartTitle: "빠른 시작",
    quickStartSteps: [
      "Upload Selected Files",
      "Run All",
      "Quality Summary 검토",
      "Figure Review 검토",
      "Draft Export",
      "Final Export",
    ],
    uploadTitle: "무엇을 업로드하나요?",
    uploadItems: [
      "README, 사용 문서, CSV 표, JSON 결과, 메모, 기존 초안 같은 내부 프로젝트 자료를 업로드하세요.",
      "업로드할 때 각 파일 역할을 Narrative brief, Supporting doc, Results table, Background / reference 중에서 고르세요.",
      "참고 논문은 업로드 단계에서 필수가 아닙니다. Run Evidence가 이후 외부 문헌을 검색합니다.",
      "Upload는 참고문헌 PDF 전용이 아니라, 논문 초안의 근거가 되는 내부 자료용입니다.",
    ],
    nextTitle: "그 다음에는 무엇을 하나요?",
    nextItems: [
      "Run All은 ingest, plan, draft, evidence, quality audit, figure handoff preparation을 자동으로 순서대로 실행합니다.",
      "Quality Summary는 critical issue, warning, recommended action을 보여줍니다.",
      "Figure Review는 PaperBanana에 붙여 넣을 method section content와 caption을 준비해 줍니다.",
      "Draft Export는 작업용 초안을 항상 내보냅니다.",
      "Final Export는 최신 quality report에 critical issue가 없을 때만 활성화됩니다.",
      "업로드한 파일이 바뀌면 Run Ingest를 다시 실행하세요.",
      "업로드 후 파일 역할을 바꿨다면 manuscript context를 다시 만들기 위해 ingest를 다시 실행하세요.",
    ],
    mistakesTitle: "자주 하는 실수",
    mistakesItems: [
      "참고 논문 PDF만 올리고 바로 초안이 나오길 기대하는 것.",
      "Quality Summary를 보지 않고 Draft Export를 제출본처럼 사용하는 것.",
      "Figure Review를 건너뛰고 PaperBanana에 넣을 그림 handoff 텍스트를 준비하지 않는 것.",
      "파일을 추가하거나 삭제한 뒤 ingest를 다시 실행하지 않는 것.",
    ],
  },
};
