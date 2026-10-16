#!/usr/bin/env python3
"""Install the reading skill; optionally back up an old version and add a Codex router."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
START = '<!-- paper-reader:auto:start -->'
END = '<!-- paper-reader:auto:end -->'
IGNORES = shutil.ignore_patterns('.venv', '__pycache__', '*.pyc', '.git')


def exists(path: Path) -> bool:
    """Include dangling symlinks in overwrite checks."""
    return path.exists() or path.is_symlink()


def unique_label() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid4().hex[:8]


def install(destination_root: Path, source: Path | None = None, *, update: bool = False) -> Path:
    """Install through a staging directory. Explicit updates retain the entire old tree."""
    source = (source or ROOT / 'skills' / 'paper-reader').expanduser().resolve()
    if not (source / 'SKILL.md').is_file():
        raise ValueError(f'Missing SKILL.md in {source}')
    destination_root = destination_root.expanduser().resolve()
    target = destination_root / 'paper-reader'
    if target == source or source in target.parents or target in source.parents:
        raise ValueError('Source and destination skill directories must not overlap.')
    if target.is_symlink():
        raise ValueError(f'Refusing to replace a symlinked skill: {target}')
    if exists(target) and not update:
        raise FileExistsError(f'Refusing to overwrite existing skill: {target}; use --update to back it up.')
    if exists(target) and (not target.is_dir() or not (target / 'SKILL.md').is_file()):
        raise ValueError(f'Existing target is not a recognizable skill: {target}')
    for folder, dirs, files in os.walk(source):
        dirs[:] = [d for d in dirs if d not in {'.venv', '__pycache__', '.git'}]
        for name in dirs + files:
            item = Path(folder) / name
            if item.is_symlink():
                raise ValueError(f'Refusing to copy a symlink: {item}')
    destination_root.mkdir(parents=True, exist_ok=True)
    stage_parent = Path(tempfile.mkdtemp(prefix='.paper-reader-stage-', dir=destination_root))
    stage = stage_parent / 'content'
    backup: Path | None = None
    try:
        shutil.copytree(source, stage, ignore=IGNORES)
        if exists(target):
            # Keep backups OUTSIDE the skills discovery directory, avoiding duplicate skills.
            backup_root = destination_root.parent / 'paper-reader-backups'
            backup_root.mkdir(parents=True, exist_ok=True)
            backup = backup_root / ('paper-reader-' + unique_label())
            target.rename(backup)
        try:
            stage.rename(target)
        except OSError:
            if backup is not None and not exists(target):
                backup.rename(target)
            raise
    finally:
        # Only remove the staging directory created by this invocation.
        shutil.rmtree(stage_parent, ignore_errors=True)
    if backup is not None:
        print(f'Previous skill backed up to: {backup}')
        if (backup / '.venv').exists():
            print('Previous .venv is preserved in the backup; recreate dependencies if you use the PDF helper.')
    return target


def merge_router(original: str, block: str) -> str:
    """Replace only this skill's managed block; preserve all other text exactly."""
    starts, ends = original.count(START), original.count(END)
    if starts == ends == 0:
        return original + ('\n\n' if original else '') + block.strip() + '\n'
    if starts != 1 or ends != 1:
        raise ValueError('Ambiguous router markers; leaving existing instructions unchanged.')
    start, end = original.index(START), original.index(END)
    if end < start:
        raise ValueError('Router markers are reversed; leaving existing instructions unchanged.')
    return original[:start] + block.strip() + original[end + len(END):]


def active_agents_file(codex_home: Path) -> Path:
    """Follow the documented non-empty global override precedence."""
    codex_home = codex_home.expanduser().resolve()
    override = codex_home / 'AGENTS.override.md'
    if exists(override):
        if override.is_symlink() or not override.is_file():
            raise ValueError(f'Refusing an unsafe AGENTS override: {override}')
        if override.read_text(encoding='utf-8-sig').strip():
            return override
    return codex_home / 'AGENTS.md'


def configure_router(skill: Path, codex_home: Path) -> Path:
    """Opt-in only: back up existing instructions, then atomically update our block."""
    skill_file = skill.resolve() / 'SKILL.md'
    if not skill_file.is_file():
        raise ValueError(f'Install the skill before routing to it: {skill_file}')
    if any(c in str(skill_file) for c in ('\n', '\r', '`')):
        raise ValueError('Skill path contains unsupported characters for the Markdown router.')
    target = active_agents_file(codex_home)
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError(f'Refusing to replace non-regular instructions: {target}')
    existed = target.exists()
    before = target.read_bytes() if existed else b''
    original = before.decode('utf-8')  # UTF-8 BOM, if any, is preserved in surrounding text.
    template = (ROOT / 'docs' / 'AGENTS-snippet.md').read_text(encoding='utf-8')
    block = template.replace('{{SKILL_FILE}}', skill_file.as_posix())
    after = merge_router(original, block).encode('utf-8')
    if len(after) > 32 * 1024:
        raise ValueError('Global instructions would exceed the default 32 KiB guidance limit; merge manually.')
    if after == before:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    if existed:
        backup = target.with_name(target.name + '.paper-reader-backup-' + unique_label())
        with backup.open('xb') as handle:
            handle.write(before)
        print(f'Previous instructions backed up to: {backup}')
    fd, temporary = tempfile.mkstemp(prefix='.paper-reader-agents-', dir=target.parent)
    tmp = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(after)
            handle.flush()
            os.fsync(handle.fileno())
        if existed:
            os.chmod(tmp, stat.S_IMODE(target.stat().st_mode))
        # Detect ordinary concurrent changes; this is not a global cross-process lock.
        if existed != target.exists() or (target.exists() and target.read_bytes() != before):
            raise RuntimeError('Instructions changed during installation; retry after reviewing them.')
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', type=Path, default=Path.home() / '.agents' / 'skills',
                        help='Parent skills directory (default: ~/.agents/skills).')
    parser.add_argument('--update', action='store_true',
                        help='Back up an existing skill outside discovery paths before replacing it.')
    parser.add_argument('--with-router', action='store_true',
                        help='Add keyword routing to the active global AGENTS file, with backup.')
    parser.add_argument('--codex-home', type=Path,
                        default=Path(os.environ.get('CODEX_HOME') or Path.home() / '.codex'),
                        help='Codex profile directory for --with-router; respects CODEX_HOME.')
    args = parser.parse_args()
    try:
        target = install(args.dest, update=args.update)
    except (OSError, ValueError, shutil.Error) as exc:
        print(f'Skill installation failed: {exc}', file=sys.stderr)
        return 1
    print(f'Installed: {target}')
    if args.with_router:
        try:
            instructions = configure_router(target, args.codex_home)
        except (OSError, ValueError, RuntimeError) as exc:
            print(f'Skill is installed, but router was NOT installed: {exc}', file=sys.stderr)
            print('Review docs/AGENTS-snippet.md for manual merging. Existing guidance is retained.', file=sys.stderr)
            return 2
        print(f'Keyword guidance installed in: {instructions}')
    print('No packages were installed; no network requests were made.')
    print('Start a new Codex session, attach a paper, and say: 阅读这篇论文')
    print('Routing is model instruction, not a deterministic prompt interception hook.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
