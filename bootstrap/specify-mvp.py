#!/usr/bin/env python3
"""Global bootstrap for Greenfield MVP Governance on Spec Kit.

One-time setup:
    python3 bootstrap/specify-mvp.py install-global \
      --repo https://github.com/<owner>/speckit-greenfield-mvp-governance.git

Then initialize any new project with:
    specify-mvp init --here --integration codex --force

The wrapper syncs the governance source from GitHub, delegates project
initialization to the installed `specify` CLI, installs the MVP Complexity Guard
during init when the CLI supports `--extension`, installs the MVP Simplicity
preset, and verifies the resulting project.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

APP_ID = "speckit-greenfield-mvp-governance"
PRESET_ID = "greenfield-mvp-simplicity"
EXTENSION_ID = "mvp-complexity-guard"
DEFAULT_PRIORITY = 10
CONFIG_DIR = Path(os.environ.get("SPECKIT_MVP_GOVERNANCE_HOME", Path.home() / ".config" / APP_ID)).expanduser()
CONFIG_FILE = CONFIG_DIR / "config.json"
SOURCE_DIR = CONFIG_DIR / "source"
LAUNCHER = Path.home() / ".local" / "bin" / "specify-mvp"

VALUE_OPTIONS = {
    "--script",
    "--preset",
    "--integration",
    "--integration-options",
    "--extension",
    "--github-token",
}


def die(message: str, code: int = 1) -> "NoReturn":
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(
    args: list[str],
    *,
    cwd: Path | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    kwargs = {
        "cwd": str(cwd) if cwd else None,
        "text": True,
        "check": False,
    }
    if capture:
        kwargs.update(stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = subprocess.run(args, **kwargs)
    if check and result.returncode != 0:
        if capture and result.stdout:
            print(result.stdout, file=sys.stderr, end="" if result.stdout.endswith("\n") else "\n")
        raise SystemExit(result.returncode)
    return result


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        die(f"required tool '{name}' is not on PATH")
    return path


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        die(
            f"global bootstrap is not configured ({CONFIG_FILE} missing). "
            "Run 'python3 bootstrap/specify-mvp.py install-global --repo <github-repo-url>' first."
        )
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        die(f"cannot read {CONFIG_FILE}: {exc}")
    if not isinstance(data, dict) or not data.get("repo"):
        die(f"invalid bootstrap config in {CONFIG_FILE}: 'repo' is required")
    data.setdefault("ref", "main")
    data.setdefault("priority", DEFAULT_PRIORITY)
    return data


def save_config(repo: str, ref: str, priority: int) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps({"repo": repo, "ref": ref, "priority": priority}, indent=2) + "\n",
        encoding="utf-8",
    )


def validate_source(source: Path = SOURCE_DIR) -> None:
    required = [
        source / "preset" / "preset.yml",
        source / "extension" / "extension.yml",
        source / "bootstrap" / "specify-mvp.py",
    ]
    missing = [str(p) for p in required if not p.is_file()]
    if missing:
        die("governance source is incomplete; missing: " + ", ".join(missing))


def sync_source(config: dict | None = None) -> None:
    require_tool("git")
    config = config or load_config()
    repo = str(config["repo"])
    ref = str(config.get("ref", "main"))
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not (SOURCE_DIR / ".git").is_dir():
        if SOURCE_DIR.exists():
            shutil.rmtree(SOURCE_DIR)
        print(f"Cloning governance source: {repo} [{ref}]")
        run(["git", "clone", "--origin", "origin", repo, str(SOURCE_DIR)])
    else:
        run(["git", "-C", str(SOURCE_DIR), "remote", "set-url", "origin", repo])

    print(f"Syncing governance source: {ref}")
    run(["git", "-C", str(SOURCE_DIR), "fetch", "--prune", "--tags", "origin"])

    remote_ref = run(
        ["git", "-C", str(SOURCE_DIR), "rev-parse", "--verify", f"origin/{ref}"],
        capture=True,
        check=False,
    )
    if remote_ref.returncode == 0:
        run(["git", "-C", str(SOURCE_DIR), "checkout", "-B", ref, f"origin/{ref}"])
        run(["git", "-C", str(SOURCE_DIR), "reset", "--hard", f"origin/{ref}"])
    else:
        local_ref = run(
            ["git", "-C", str(SOURCE_DIR), "rev-parse", "--verify", ref],
            capture=True,
            check=False,
        )
        if local_ref.returncode != 0:
            die(f"Git ref '{ref}' does not exist in {repo}")
        run(["git", "-C", str(SOURCE_DIR), "checkout", "--detach", ref])
        run(["git", "-C", str(SOURCE_DIR), "reset", "--hard", ref])

    validate_source()


def write_launcher() -> None:
    LAUNCHER.parent.mkdir(parents=True, exist_ok=True)
    script = f'''#!/usr/bin/env bash
set -euo pipefail
exec python3 "{SOURCE_DIR / 'bootstrap' / 'specify-mvp.py'}" "$@"
'''
    LAUNCHER.write_text(script, encoding="utf-8")
    LAUNCHER.chmod(0o755)


def init_supports_extension() -> bool:
    result = run(["specify", "init", "--help"], capture=True, check=False)
    return result.returncode == 0 and "--extension" in (result.stdout or "")


def _option_present(args: Iterable[str], option: str) -> bool:
    return any(a == option or a.startswith(option + "=") for a in args)


def infer_project_root(init_args: list[str], cwd: Path) -> Path:
    if "--here" in init_args or "." in init_args:
        return cwd.resolve()

    skip_next = False
    for token in init_args:
        if skip_next:
            skip_next = False
            continue
        if token in VALUE_OPTIONS:
            skip_next = True
            continue
        if any(token.startswith(opt + "=") for opt in VALUE_OPTIONS):
            continue
        if token.startswith("-"):
            continue
        return (cwd / token).resolve()
    die("cannot determine project directory from 'specify init' arguments; use --here or provide a project name")


def project_has_component(project_root: Path, kind: str, component_id: str) -> bool:
    result = run(["specify", kind, "list"], cwd=project_root, capture=True, check=False)
    return result.returncode == 0 and component_id in (result.stdout or "")


def install_missing_components(project_root: Path, priority: int, extension_was_in_init: bool) -> None:
    if not project_has_component(project_root, "preset", PRESET_ID):
        print(f"Installing preset: {PRESET_ID}")
        run(
            [
                "specify",
                "preset",
                "add",
                "--dev",
                str(SOURCE_DIR / "preset"),
                "--priority",
                str(priority),
            ],
            cwd=project_root,
        )
    else:
        print(f"Preset already installed: {PRESET_ID}")

    if not project_has_component(project_root, "extension", EXTENSION_ID):
        print(f"Installing extension: {EXTENSION_ID}")
        # On Spec Kit releases without init --extension support this is the fallback.
        run(
            [
                "specify",
                "extension",
                "add",
                "--dev",
                str(SOURCE_DIR / "extension"),
                "--priority",
                str(priority),
            ],
            cwd=project_root,
        )
    elif extension_was_in_init:
        print(f"Extension installed during init: {EXTENSION_ID}")
    else:
        print(f"Extension already installed: {EXTENSION_ID}")


def ensure_fresh_constitution_addendum(project_root: Path) -> None:
    """Guarantee the MVP policy is present for a freshly initialized project.

    Spec Kit 0.16.x normally reconciles a generated constitution when a preset is
    installed. This explicit check keeps the bootstrap deterministic if that
    behavior changes in a later compatible release. It is intentionally called
    only for projects that did not have `.specify/` before this bootstrap run.
    """
    constitution = project_root / ".specify" / "memory" / "constitution.md"
    addendum = SOURCE_DIR / "preset" / "templates" / "constitution-addendum.md"
    marker = "## MVP Simplicity and Evidence-Driven Architecture"
    if not constitution.is_file() or not addendum.is_file():
        die("fresh project is missing constitution or MVP addendum")
    text = constitution.read_text(encoding="utf-8")
    if marker in text:
        print("Constitution contains MVP simplicity policy")
        return
    addition = addendum.read_text(encoding="utf-8").strip()
    constitution.write_text(text.rstrip() + "\n\n" + addition + "\n", encoding="utf-8")
    print("Added MVP simplicity policy to fresh project constitution")


def verify_project(project_root: Path) -> None:
    problems: list[str] = []
    if not (project_root / ".specify").is_dir():
        problems.append(".specify/ is missing")
    if not project_has_component(project_root, "preset", PRESET_ID):
        problems.append(f"preset {PRESET_ID} is not installed")
    if not project_has_component(project_root, "extension", EXTENSION_ID):
        problems.append(f"extension {EXTENSION_ID} is not installed")
    constitution = project_root / ".specify" / "memory" / "constitution.md"
    if constitution.is_file():
        if "## MVP Simplicity and Evidence-Driven Architecture" not in constitution.read_text(encoding="utf-8"):
            problems.append("constitution does not contain the MVP simplicity addendum")
    else:
        problems.append("constitution.md is missing")

    if problems:
        print("Governance verification FAILED:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        raise SystemExit(2)
    print("Governance verification OK")


def cmd_install_global(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="specify-mvp install-global")
    parser.add_argument("--repo", required=True, help="Git repository URL containing this package")
    parser.add_argument("--ref", default="main", help="Git branch/tag/commit to track (default: main)")
    parser.add_argument("--priority", type=int, default=DEFAULT_PRIORITY)
    args = parser.parse_args(argv)
    if args.priority < 1:
        die("priority must be >= 1")
    save_config(args.repo, args.ref, args.priority)
    sync_source(load_config())
    write_launcher()
    print(f"Installed launcher: {LAUNCHER}")
    if str(LAUNCHER.parent) not in os.environ.get("PATH", "").split(os.pathsep):
        print(f"warning: {LAUNCHER.parent} is not on PATH")
    cmd_doctor([])


def cmd_sync(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="specify-mvp sync")
    parser.parse_args(argv)
    sync_source()


def cmd_doctor(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="specify-mvp doctor")
    parser.parse_args(argv)
    checks: list[tuple[str, bool, str]] = []
    checks.append(("python3", bool(shutil.which("python3")), shutil.which("python3") or "missing"))
    checks.append(("git", bool(shutil.which("git")), shutil.which("git") or "missing"))
    checks.append(("specify", bool(shutil.which("specify")), shutil.which("specify") or "missing"))
    checks.append(("config", CONFIG_FILE.is_file(), str(CONFIG_FILE)))
    checks.append(("source", (SOURCE_DIR / "preset" / "preset.yml").is_file(), str(SOURCE_DIR)))
    checks.append(("launcher", LAUNCHER.is_file(), str(LAUNCHER)))
    if shutil.which("specify"):
        result = run(["specify", "version"], capture=True, check=False)
        details = (result.stdout or "").strip() or f"exit {result.returncode}"
        checks.append(("specify-version", result.returncode == 0, details))
        native_extension = init_supports_extension()
        checks.append((
            "extension install",
            True,
            "native init --extension" if native_extension else "post-init fallback (init --extension unavailable)",
        ))
    width = max(len(name) for name, _, _ in checks)
    failed = False
    for name, ok, details in checks:
        failed = failed or not ok
        print(f"{name.ljust(width)}  {'OK' if ok else 'FAIL'}  {details}")
    if failed:
        raise SystemExit(2)


def cmd_ensure_project(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="specify-mvp ensure-project")
    parser.add_argument("project", nargs="?", default=".")
    parser.add_argument("--no-sync", action="store_true")
    args = parser.parse_args(argv)
    require_tool("specify")
    config = load_config()
    if not args.no_sync:
        sync_source(config)
    else:
        validate_source()
    project_root = Path(args.project).expanduser().resolve()
    if not (project_root / ".specify").is_dir():
        die(f"{project_root} is not an initialized Spec Kit project")
    install_missing_components(project_root, int(config.get("priority", DEFAULT_PRIORITY)), False)
    verify_project(project_root)


def cmd_init(argv: list[str]) -> None:
    require_tool("specify")
    config = load_config()
    sync_source(config)
    cwd = Path.cwd()
    project_root = infer_project_root(argv, cwd)
    had_specify_before = (project_root / ".specify").is_dir()

    init_args = list(argv)
    extension_was_in_init = False
    if init_supports_extension():
        # A local path passed to init is installed by Spec Kit's normal installer,
        # avoiding a second extension-add step on the fresh project.
        init_args.extend(["--extension", str(SOURCE_DIR / "extension")])
        extension_was_in_init = True

    print("Running Spec Kit initialization with MVP governance...")
    run(["specify", "init", *init_args], cwd=cwd)

    if not (project_root / ".specify").is_dir():
        die(f"Spec Kit init completed but {project_root}/.specify was not found")

    install_missing_components(
        project_root,
        int(config.get("priority", DEFAULT_PRIORITY)),
        extension_was_in_init,
    )
    if not had_specify_before:
        ensure_fresh_constitution_addendum(project_root)
    verify_project(project_root)
    print(f"Project ready with Greenfield MVP Governance: {project_root}")


def usage() -> None:
    print(
        """Usage:
  specify-mvp install-global --repo <github-repo-url> [--ref main]
  specify-mvp sync
  specify-mvp doctor
  specify-mvp ensure-project [PROJECT] [--no-sync]
  specify-mvp init <normal specify init arguments...>

Examples:
  specify-mvp init my-app --integration codex
  specify-mvp init --here --force --integration codex
"""
    )


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] in {"-h", "--help", "help"}:
        usage()
        return
    command, argv = sys.argv[1], sys.argv[2:]
    commands = {
        "install-global": cmd_install_global,
        "sync": cmd_sync,
        "doctor": cmd_doctor,
        "ensure-project": cmd_ensure_project,
        "init": cmd_init,
    }
    fn = commands.get(command)
    if not fn:
        die(f"unknown command '{command}' (use --help)", 2)
    fn(argv)


if __name__ == "__main__":
    main()
