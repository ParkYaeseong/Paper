import type { AuthConfig } from "../lib/types";


type LoginGateProps = {
  authConfig: AuthConfig | null;
  onLogin: () => void;
  error: string | null;
};


export default function LoginGate({ authConfig, onLogin, error }: LoginGateProps) {
  return (
    <div className="login-gate">
      <div className="hero-card">
        <p className="eyebrow">Evidence-grounded manuscript generation</p>
        <h1>Paper Authoring Studio</h1>
        <p className="hero-copy">
          Upload internal data, generate a structured manuscript draft, retrieve supporting literature, ground citation slots,
          and review the result before export.
        </p>
        <div className="hero-meta">
          <span>{authConfig?.provider_name || "KBF SSO"}</span>
          <span>GPT + Gemini</span>
          <span>Review-first workflow</span>
        </div>
        {error ? <p className="error-text">{error}</p> : null}
        <button className="primary-button" onClick={onLogin} type="button">
          Sign in with KBF SSO
        </button>
      </div>
    </div>
  );
}
