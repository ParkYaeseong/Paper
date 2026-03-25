import type { User } from "../lib/types";


type HeaderProps = {
  onOpenGuide: () => void;
  user: User;
  onLogout: () => void;
};


export default function Header({ onOpenGuide, user, onLogout }: HeaderProps) {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">K-BioFoundry</p>
        <h1>Paper Authoring Studio</h1>
      </div>
      <div className="header-actions">
        <button className="ghost-button" onClick={onOpenGuide} type="button">
          Help / 사용법
        </button>
        <div className="identity-chip">
          <strong>{user.name}</strong>
          <span>{user.role}</span>
        </div>
        <button className="ghost-button" onClick={onLogout} type="button">
          Log out
        </button>
      </div>
    </header>
  );
}
