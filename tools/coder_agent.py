#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import NotFoundError, OpenAI


DEFAULT_CONTEXT_FILES = [
    "README.md",
    "skills/agentic-pdf-ai/SKILL.md",
    "app/config.py",
    "app/database.py",
    "app/local_store.py",
    "app/schemas.py",
    "app/main.py",
    "app/routes/documents.py",
    "app/routes/reports.py",
    "app/routes/dashboard.py",
    "app/services/pdf_parser.py",
    "app/services/llm.py",
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repository-specific coding agent powered by gpt-oss-120B."
    )
    parser.add_argument("task", help="Coding task to plan or patch.")
    parser.add_argument(
        "--mode",
        choices=["plan", "patch"],
        default="patch",
        help="Generate a plan or a unified diff patch. Default: patch.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the generated patch with git apply after validation.",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run compile verification after applying a patch.",
    )
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        default=[],
        help="Additional repository-relative file to include in context.",
    )
    parser.add_argument(
        "--max-file-chars",
        type=int,
        default=12000,
        help="Maximum characters to include per context file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the generated plan or patch to this file.",
    )
    parser.add_argument(
        "--show-context-files",
        action="store_true",
        help="Print the repository files included in model context.",
    )
    parser.add_argument(
        "--debug-context",
        type=Path,
        help="Write the exact repository context sent to the model to this file.",
    )
    parser.add_argument(
        "--dry-context",
        action="store_true",
        help="Build/debug context and exit without calling the model.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Print OpenAI-compatible endpoint configuration and exit.",
    )
    args = parser.parse_args()

    repo = Path.cwd()
    load_dotenv(repo / ".env")

    if args.check_config:
        print_config()
        return 0

    context, context_files = build_context(repo, args.files, args.max_file_chars)
    if args.show_context_files:
        print("Context files:", file=sys.stderr)
        for relative in context_files:
            print(f"- {relative}", file=sys.stderr)

    if args.debug_context:
        args.debug_context.write_text(context, encoding="utf-8")
        print(f"Wrote debug context to {args.debug_context}", file=sys.stderr)

    prompt = load_prompt(repo, args.mode).replace("{{TASK}}", args.task)
    if args.dry_context:
        if not args.show_context_files and not args.debug_context:
            print(context)
        return 0

    client = make_client()

    result = call_model(client, context, prompt)
    if args.mode == "patch":
        result = extract_diff(result)

    if args.output:
        args.output.write_text(result, encoding="utf-8")
    else:
        print(result)

    if args.apply:
        if args.mode != "patch":
            print("--apply can only be used with --mode patch", file=sys.stderr)
            return 2
        apply_patch(repo, result)
        if args.verify:
            verify(repo)

    return 0


def make_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is required. Set it in .env or the environment.")

    kwargs = {"api_key": api_key}
    base_url = os.getenv("OPENAI_BASE_URL")
    if base_url:
        kwargs["base_url"] = base_url
    dep_ticket = os.getenv("OPENAI_DEP_TICKET")
    if dep_ticket:
        kwargs["default_headers"] = {"x-dep-ticket": dep_ticket}
    return OpenAI(**kwargs)


def print_config() -> None:
    base_url = os.getenv("OPENAI_BASE_URL")
    model = os.getenv("OPENAI_MODEL", "gpt-oss-120b")
    print(
        {
            "has_openai_api_key": bool(os.getenv("OPENAI_API_KEY")),
            "openai_base_url": base_url,
            "openai_model": model,
            "has_openai_dep_ticket": bool(os.getenv("OPENAI_DEP_TICKET")),
        }
    )
    if base_url and "127.0.0.1:8000" in base_url:
        print(
            "Warning: OPENAI_BASE_URL points to this FastAPI app, not a gpt-oss model server.",
            file=sys.stderr,
        )


def build_context(
    repo: Path,
    extra_files: list[str],
    max_file_chars: int,
) -> tuple[str, list[str]]:
    files = list(dict.fromkeys(DEFAULT_CONTEXT_FILES + extra_files))
    sections = [file_tree(repo)]
    included_files = []

    for relative in files:
        path = repo / relative
        if not path.exists() or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_file_chars:
            text = text[:max_file_chars] + "\n...[truncated]\n"
        sections.append(f"--- FILE: {relative} ---\n{text}")
        included_files.append(relative)

    return "\n\n".join(sections), included_files


def file_tree(repo: Path) -> str:
    ignored = {".git", ".venv", "__pycache__", ".storage"}
    paths = []
    for path in sorted(repo.rglob("*")):
        relative = path.relative_to(repo)
        if any(part in ignored for part in relative.parts):
            continue
        if path.is_file():
            paths.append(str(relative))
    return "--- REPOSITORY FILES ---\n" + "\n".join(paths[:250])


def load_prompt(repo: Path, mode: str) -> str:
    prompt_file = repo / "prompts" / ("plan.md" if mode == "plan" else "patch_generation.md")
    return prompt_file.read_text(encoding="utf-8")


def call_model(client: OpenAI, context: str, prompt: str) -> str:
    system = Path("prompts/coding_system.md").read_text(encoding="utf-8")
    model = os.getenv("OPENAI_MODEL", "gpt-oss-120b")
    messages = [
        {"role": "system", "content": system},
        {
            "role": "user",
            "content": (
                "Repository context follows. Use it as the source of truth.\n\n"
                f"{context}\n\n"
                f"{prompt}"
            ),
        },
    ]
    try:
        response = client.responses.create(model=model, input=messages)
        return response.output_text.strip()
    except NotFoundError as responses_exc:
        try:
            response = client.chat.completions.create(model=model, messages=messages)
            return (response.choices[0].message.content or "").strip()
        except NotFoundError as chat_exc:
            raise SystemExit(endpoint_not_found_message(responses_exc, chat_exc)) from chat_exc
    except Exception:
        response = client.chat.completions.create(model=model, messages=messages)
        return (response.choices[0].message.content or "").strip()


def endpoint_not_found_message(responses_exc: Exception, chat_exc: Exception) -> str:
    base_url = os.getenv("OPENAI_BASE_URL")
    return (
        "The configured OpenAI-compatible endpoint returned 404 for both "
        "/responses and /chat/completions.\n"
        f"OPENAI_BASE_URL={base_url!r}\n"
        "Check that OPENAI_BASE_URL points to your gpt-oss model server, not this "
        "FastAPI app at http://127.0.0.1:8000/v1.\n"
        f"Responses error: {responses_exc}\n"
        f"Chat Completions error: {chat_exc}"
    )


def extract_diff(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()

    markers = ["diff --git ", "--- "]
    starts = [stripped.find(marker) for marker in markers if stripped.find(marker) >= 0]
    if starts:
        stripped = stripped[min(starts) :].strip()

    if "diff --git " not in stripped and "\n--- " not in f"\n{stripped}":
        raise SystemExit("Model did not return a recognizable unified diff.")
    return stripped + "\n"


def apply_patch(repo: Path, patch: str) -> None:
    check = subprocess.run(
        ["git", "apply", "--check", "-"],
        input=patch,
        text=True,
        cwd=repo,
        capture_output=True,
    )
    if check.returncode != 0:
        print(check.stderr, file=sys.stderr)
        raise SystemExit("Patch validation failed.")

    applied = subprocess.run(
        ["git", "apply", "-"],
        input=patch,
        text=True,
        cwd=repo,
        capture_output=True,
    )
    if applied.returncode != 0:
        print(applied.stderr, file=sys.stderr)
        raise SystemExit("Patch apply failed.")
    print("Patch applied.")


def verify(repo: Path) -> None:
    result = subprocess.run(
        [".venv/bin/python", "-m", "compileall", "app"],
        cwd=repo,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit("Verification failed.")


if __name__ == "__main__":
    raise SystemExit(main())
