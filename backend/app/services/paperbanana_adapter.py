from __future__ import annotations

from pathlib import Path
import os
import subprocess
import sys
import tempfile

from app.config import Settings


def _paperbanana_python(settings: Settings) -> str:
    if settings.paperbanana_python:
        return settings.paperbanana_python
    candidate = Path(settings.paperbanana_root).expanduser().resolve() / ".venv" / "bin" / "python"
    if candidate.exists():
        return str(candidate)
    return sys.executable or "python3"


def generate_paperbanana_candidates(
    *,
    settings: Settings,
    content: str,
    caption: str,
    output_dir: Path,
    candidate_count: int | None = None,
) -> list[Path]:
    root = Path(settings.paperbanana_root).expanduser().resolve()
    runner = root / "skill" / "run.py"
    if not runner.exists():
        raise ValueError(f"PaperBanana runner not found at {runner}")

    output_dir.mkdir(parents=True, exist_ok=True)
    candidate_count = max(1, candidate_count or settings.paperbanana_candidates)
    output_path = output_dir / "paperbanana.png"

    env = os.environ.copy()
    if env.get("GEMINI_API_KEY") and not env.get("GOOGLE_API_KEY"):
        env["GOOGLE_API_KEY"] = env["GEMINI_API_KEY"]

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", dir=output_dir, delete=False) as handle:
        handle.write(content)
        content_path = Path(handle.name)

    command = [
        _paperbanana_python(settings),
        str(runner),
        "--content-file",
        str(content_path),
        "--caption",
        caption,
        "--output",
        str(output_path),
        "--num-candidates",
        str(candidate_count),
        "--task",
        "diagram",
        "--exp-mode",
        "demo_planner_critic",
    ]
    completed = subprocess.run(
        command,
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=1800,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise ValueError(stderr or "PaperBanana figure generation failed")

    candidates = [
        Path(line.strip())
        for line in completed.stdout.splitlines()
        if line.strip() and Path(line.strip()).exists()
    ]
    if not candidates:
        raise ValueError("PaperBanana completed without producing any figure files")
    return candidates
