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
    intro: "Use this workflow when you want to turn project files into a draft manuscript with grounded citations and export-ready outputs.",
    quickStartTitle: "Quick Start",
    quickStartSteps: [
      "Upload Selected Files",
      "Run Ingest",
      "Run Plan",
      "Run Draft",
      "Run Retrieve",
      "Run Ground",
      "Review evidence and draft text",
      "Run Export",
    ],
    uploadTitle: "What To Upload",
    uploadItems: [
      "Upload internal project materials such as README files, usage docs, CSV tables, JSON outputs, notes, and prior draft text.",
      "Reference papers are optional at upload time. Run Retrieve searches external literature later.",
      "Upload is for your source material, not only for final reference PDFs.",
    ],
    nextTitle: "What Happens Next",
    nextItems: [
      "Run Ingest builds the project profile from your uploaded files.",
      "Run Plan creates the manuscript outline and citation slots.",
      "Run Draft writes section drafts from the structured project profile.",
      "Run Retrieve and Run Ground connect claim slots to supporting papers.",
      "If uploaded files change, run Run Ingest again to refresh the project profile.",
    ],
    mistakesTitle: "Common Mistakes",
    mistakesItems: [
      "Uploading only literature PDFs and expecting a manuscript draft immediately.",
      "Skipping ingest and running plan or draft before the project profile exists.",
      "Expecting supported citations before retrieve and ground have run.",
      "Forgetting to rerun ingest after adding or deleting uploaded files.",
    ],
  },
  ko: {
    title: "사용 가이드",
    intro: "이 워크플로우는 프로젝트 파일을 업로드한 뒤 초안 작성, 문헌 검색, citation grounding, export까지 순서대로 진행할 때 사용합니다.",
    quickStartTitle: "빠른 시작",
    quickStartSteps: [
      "Upload Selected Files",
      "Run Ingest",
      "Run Plan",
      "Run Draft",
      "Run Retrieve",
      "Run Ground",
      "Evidence Review에서 검토",
      "Run Export",
    ],
    uploadTitle: "무엇을 업로드하나요?",
    uploadItems: [
      "README, 사용 문서, CSV 표, JSON 결과, 메모, 기존 초안 같은 내부 프로젝트 자료를 업로드하세요.",
      "참고 논문은 업로드 단계에서 필수가 아닙니다. Run Retrieve가 이후 외부 문헌을 검색합니다.",
      "Upload는 참고문헌 PDF 전용이 아니라, 논문 초안의 근거가 되는 내부 자료용입니다.",
    ],
    nextTitle: "그 다음에는 무엇을 하나요?",
    nextItems: [
      "Run Ingest는 업로드된 파일을 읽어 프로젝트 프로필과 요약을 만듭니다.",
      "Run Plan은 논문 아웃라인과 citation slot을 생성합니다.",
      "Run Draft는 구조화된 프로젝트 정보를 바탕으로 섹션 초안을 작성합니다.",
      "Run Retrieve와 Run Ground는 문장과 근거 논문을 연결합니다.",
      "업로드한 파일이 바뀌면 Run Ingest를 다시 실행하세요.",
    ],
    mistakesTitle: "자주 하는 실수",
    mistakesItems: [
      "참고 논문 PDF만 올리고 바로 초안이 나오길 기대하는 것.",
      "ingest 없이 plan이나 draft를 먼저 실행하는 것.",
      "retrieve와 ground 전에 citation이 자동 검토되길 기대하는 것.",
      "파일을 추가하거나 삭제한 뒤 ingest를 다시 실행하지 않는 것.",
    ],
  },
};
