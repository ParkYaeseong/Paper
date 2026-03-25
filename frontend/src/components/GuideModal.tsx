import { useEffect } from "react";

import { GUIDE_CONTENT, type GuideLanguage } from "../lib/guide-content";


type GuideModalProps = {
  language: GuideLanguage;
  onClose: () => void;
  onLanguageChange: (language: GuideLanguage) => void;
  open: boolean;
};


export default function GuideModal({ language, onClose, onLanguageChange, open }: GuideModalProps) {
  useEffect(() => {
    if (!open) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, open]);

  if (!open) {
    return null;
  }

  const content = GUIDE_CONTENT[language];

  return (
    <div className="guide-overlay" onClick={onClose} role="presentation">
      <div
        aria-label={content.title}
        aria-modal="true"
        className="guide-modal"
        onClick={(event) => event.stopPropagation()}
        role="dialog"
      >
        <div className="guide-modal-header">
          <div>
            <p className="eyebrow">Help</p>
            <h2>{content.title}</h2>
          </div>
          <button aria-label="Close guide" className="ghost-button" onClick={onClose} type="button">
            Close
          </button>
        </div>

        <div className="guide-tab-row" role="tablist">
          <button
            aria-selected={language === "en"}
            className={language === "en" ? "guide-tab active" : "guide-tab"}
            onClick={() => onLanguageChange("en")}
            role="tab"
            type="button"
          >
            English
          </button>
          <button
            aria-selected={language === "ko"}
            className={language === "ko" ? "guide-tab active" : "guide-tab"}
            onClick={() => onLanguageChange("ko")}
            role="tab"
            type="button"
          >
            한국어
          </button>
        </div>

        <div className="guide-body">
          <p className="guide-intro">{content.intro}</p>

          <section className="guide-section">
            <h3>{content.quickStartTitle}</h3>
            <ol className="guide-steps">
              {content.quickStartSteps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          </section>

          <section className="guide-section">
            <h3>{content.uploadTitle}</h3>
            <ul>
              {content.uploadItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="guide-section">
            <h3>{content.nextTitle}</h3>
            <ul>
              {content.nextItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>

          <section className="guide-section">
            <h3>{content.mistakesTitle}</h3>
            <ul>
              {content.mistakesItems.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
