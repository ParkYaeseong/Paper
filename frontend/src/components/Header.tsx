import type { User } from "../lib/types";


type HeaderProps = {
  user: User;
  onLogout: () => void;
};


export default function Header({ user, onLogout }: HeaderProps) {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">K-BioFoundry</p>
        <h1>Paper Authoring Studio</h1>
      </div>
      <div className="header-actions">
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
