"""
Wrapper for evaluation commands from project root.
Detects the correct python-tracker script, converts root-relative paths to tracker-relative paths,
and runs the script inside python-tracker/ while preserving exit code.
"""

import sys
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
TRACKER_DIR = ROOT_DIR / 'python-tracker'

EVALUATE_PIPELINE = 'evaluate_pipeline.py'
EVALUATION_UTILS = 'evaluation_utils.py'
KNOWN_COMMANDS = {
    'validate-annotations',
    'validate-videos',
    'create-template',
    'video-info'
}

PIPELINE_PATH_FLAGS = {'--annotations', '--videos', '--output'}


def is_absolute_or_url(value: str) -> bool:
    return Path(value).is_absolute() or value.startswith(('http://', 'https://'))


def convert_path_value(value: str) -> str:
    if is_absolute_or_url(value):
        return value
    if value.startswith('..'):
        return value
    if value.startswith('./') or value.startswith('.\\'):
        value = value[2:]
    return str(Path('..') / Path(value))


def normalize_paths(command: str, raw_args: list[str]) -> list[str]:
    normalized = []

    if command == EVALUATE_PIPELINE:
        i = 0
        while i < len(raw_args):
            arg = raw_args[i]
            normalized.append(arg)
            if arg in PIPELINE_PATH_FLAGS and i + 1 < len(raw_args):
                normalized.append(convert_path_value(raw_args[i + 1]))
                i += 2
                continue
            i += 1
        return normalized

    if command == EVALUATION_UTILS and raw_args:
        subcommand = raw_args[0]
        normalized.append(subcommand)

        if subcommand == 'validate-annotations' and len(raw_args) > 2:
            normalized.append(convert_path_value(raw_args[1]))
            normalized.append(convert_path_value(raw_args[2]))
            normalized.extend(raw_args[3:])
            return normalized

        if subcommand == 'validate-videos' and len(raw_args) > 1:
            normalized.append(convert_path_value(raw_args[1]))
            normalized.extend(raw_args[2:])
            return normalized

        if subcommand in {'create-template', 'video-info'} and len(raw_args) > 1:
            normalized.append(convert_path_value(raw_args[1]))
            normalized.extend(raw_args[2:])
            return normalized

        normalized.extend(raw_args[1:])
        return normalized

    return raw_args


def select_script(raw_args: list[str]) -> tuple[str, list[str]]:
    if not raw_args:
        return EVALUATE_PIPELINE, []

    first = raw_args[0]

    if first == 'validate-annotations':
        return EVALUATION_UTILS, raw_args

    if first in KNOWN_COMMANDS:
        return EVALUATION_UTILS, raw_args

    if '--generate-sample' in raw_args:
        return EVALUATE_PIPELINE, raw_args

    if '--annotations' in raw_args:
        return EVALUATE_PIPELINE, raw_args

    if first.endswith('.py'):
        return first, raw_args[1:]

    if first.startswith('--'):
        return EVALUATE_PIPELINE, raw_args

    return EVALUATE_PIPELINE, raw_args


def format_command(script_name: str, script_args: list[str]) -> str:
    quoted = [script_name] + [f'"{arg}"' if ' ' in arg else arg for arg in script_args]
    return 'python ' + ' '.join(quoted)


def main() -> int:
    print(f"🔄 Working directory: {ROOT_DIR}")

    if not TRACKER_DIR.exists():
        print(f"❌ Error: python-tracker directory not found at {TRACKER_DIR}")
        return 1

    raw_args = sys.argv[1:]
    script_name, script_args = select_script(raw_args)

    resolved_script = TRACKER_DIR / script_name
    if not resolved_script.exists():
        print(f"❌ Error: script not found: {resolved_script}")
        return 2

    normalized_args = normalize_paths(script_name, script_args)
    print(f"🔄 Switching to: {TRACKER_DIR}")
    print(f"🚀 Executing: {format_command(script_name, normalized_args)}")

    completed = subprocess.run([sys.executable, str(resolved_script)] + normalized_args, cwd=TRACKER_DIR)
    exit_code = completed.returncode

    print(f"\n✅ Script finished (exit code: {exit_code})")
    print(f"🔄 Returning to: {ROOT_DIR}")
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
