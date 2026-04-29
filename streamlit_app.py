from __future__ import annotations

import os
import subprocess
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("AGENTIC_PDF_API_URL", "http://127.0.0.1:8000")
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_BIN = os.path.join(REPO_DIR, ".venv", "bin", "python")


st.set_page_config(
    page_title="Agentic PDF AI",
    page_icon="📄",
    layout="wide",
)


def main() -> None:
    init_state()

    st.title("Agentic PDF AI")
    st.caption("PDF upload, topic extraction, and report chat powered by the FastAPI backend.")

    with st.sidebar:
        st.subheader("Backend")
        st.code(API_BASE_URL)
        if st.button("Refresh status", use_container_width=True):
            refresh_status()
            refresh_dashboard()

        render_ai_status()
        render_dashboard()

    pdf_tab, coding_tab = st.tabs(["PDF Chat", "Coding Agent"])

    with pdf_tab:
        upload_col, topic_col = st.columns([0.42, 0.58], gap="large")
        with upload_col:
            render_upload()
        with topic_col:
            render_topics()

        st.divider()
        render_chat()

    with coding_tab:
        render_coding_agent()


def init_state() -> None:
    st.session_state.setdefault("document_id", None)
    st.session_state.setdefault("document", None)
    st.session_state.setdefault("topics", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("ai_status", None)
    st.session_state.setdefault("dashboard", None)
    st.session_state.setdefault("coder_result", "")
    st.session_state.setdefault("coder_patch", "")
    st.session_state.setdefault("coder_context_files", "")
    st.session_state.setdefault("coder_apply_log", "")
    st.session_state.setdefault("coder_verify_log", "")

    if st.session_state.ai_status is None:
        refresh_status()
    if st.session_state.dashboard is None:
        refresh_dashboard()


def render_ai_status() -> None:
    status = st.session_state.ai_status or {}
    configured = status.get("configured", False)
    st.metric("AI", "Configured" if configured else "Fallback")
    st.write(f"Model: `{status.get('model') or '-'}`")
    st.write(f"Endpoint: `{status.get('base_url') or 'not configured'}`")

    last_call = status.get("last_call")
    if last_call:
        st.write(f"Last call: `{last_call.get('task')} / {last_call.get('mode')}`")
        if last_call.get("error"):
            st.warning(last_call["error"])


def render_dashboard() -> None:
    dashboard = st.session_state.dashboard or {}
    st.subheader("Dashboard")
    st.metric("Documents", dashboard.get("document_count", 0))
    st.metric("Topics", dashboard.get("topic_count", 0))
    st.metric("Chunks", dashboard.get("chunk_count", 0))


def render_upload() -> None:
    st.subheader("Upload PDF")
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

    if st.button("Upload and parse", type="primary", use_container_width=True, disabled=uploaded_file is None):
        if uploaded_file is None:
            return
        with st.spinner("Uploading, parsing, and storing the PDF..."):
            try:
                result = upload_document(uploaded_file.name, uploaded_file.getvalue())
                st.session_state.document = result
                st.session_state.document_id = result["document_id"]
                load_topics(result["document_id"])
                refresh_status()
                refresh_dashboard()
                agent = result.get("agent", {})
                if agent.get("agent_used") == "llm":
                    st.success("Uploaded and parsed with LLM.")
                else:
                    st.warning(f"Uploaded with fallback: {agent.get('reason') or 'unknown reason'}")
            except requests.HTTPError as exc:
                st.error(api_error_message(exc))
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")

    document = st.session_state.document
    if document:
        st.info(f"Current document: {document['filename']}")
        st.code(document["document_id"])


def render_topics() -> None:
    st.subheader("Topics")
    topics = st.session_state.topics

    if not topics:
        st.write("Upload a PDF to inspect extracted topics.")
        return

    for topic in topics:
        title = f"{topic.get('topic', 'Untitled')} · pages {topic.get('page_start')}-{topic.get('page_end')}"
        with st.expander(title, expanded=True):
            st.write(topic.get("summary") or "No summary")
            keywords = topic.get("keywords") or []
            if keywords:
                st.caption("Keywords")
                st.write(", ".join(f"`{keyword}`" for keyword in keywords))
            st.caption(f"Topic ID: {topic.get('topic_id')}")


def render_chat() -> None:
    st.subheader("Report chat")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message.get("sources"):
                render_sources(message["sources"])

    prompt = st.chat_input("Ask from stored PDF chunks")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Generating report..."):
            try:
                report = create_report(prompt)
                st.write(report["answer"])
                render_sources(report.get("source_chunks", []))
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": report["answer"],
                        "sources": report.get("source_chunks", []),
                    }
                )
                refresh_status()
            except requests.HTTPError as exc:
                message = api_error_message(exc)
                st.error(message)
                st.session_state.messages.append({"role": "assistant", "content": message})
            except requests.RequestException as exc:
                message = f"Backend request failed: {exc}"
                st.error(message)
                st.session_state.messages.append({"role": "assistant", "content": message})


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        return
    st.caption("Sources")
    for source in sources:
        topic = source.get("topic") or source.get("metadata", {}).get("topic") or "No topic"
        st.write(
            f"- `{topic}` · `{source.get('document_id')}` · "
            f"pages {source.get('page_start')}-{source.get('page_end')}"
        )


def render_coding_agent() -> None:
    st.subheader("Coding Agent")
    st.caption("Generate plans or patches with tools/coder_agent.py. Apply only after reviewing the patch.")

    config = run_command([PYTHON_BIN, "tools/coder_agent.py", "test", "--check-config"])
    if config.returncode == 0:
        st.code(config.stdout.strip() or "No config output", language="text")
    else:
        st.warning(config.stderr.strip() or config.stdout.strip())

    task = st.text_area(
        "Task",
        value=(
            "app/services/llm.py의 topic extraction 품질 평가를 추가해줘. "
            "allowed_topics, keyword grounding, summary quality scoring, fallback replacement를 넣어줘."
        ),
        height=110,
    )
    extra_files_text = st.text_input(
        "Extra context files",
        value="app/services/llm.py",
        help="Comma-separated repository-relative paths.",
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        plan_clicked = st.button("Generate plan", use_container_width=True)
    with col2:
        patch_clicked = st.button("Generate patch", type="primary", use_container_width=True)
    with col3:
        context_clicked = st.button("Show context files", use_container_width=True)

    extra_files = parse_extra_files(extra_files_text)

    if context_clicked:
        result = run_coder_agent(task, "plan", extra_files, ["--show-context-files", "--dry-context"])
        st.session_state.coder_context_files = result.stderr.strip() or result.stdout.strip()

    if plan_clicked:
        with st.spinner("Generating plan..."):
            result = run_coder_agent(task, "plan", extra_files, [])
            st.session_state.coder_result = command_output(result)
            st.session_state.coder_patch = ""

    if patch_clicked:
        with st.spinner("Generating patch..."):
            result = run_coder_agent(task, "patch", extra_files, [])
            st.session_state.coder_result = command_output(result)
            st.session_state.coder_patch = result.stdout if result.returncode == 0 else ""

    if st.session_state.coder_context_files:
        with st.expander("Context files", expanded=False):
            st.code(st.session_state.coder_context_files, language="text")

    if st.session_state.coder_result:
        st.subheader("Agent output")
        st.code(st.session_state.coder_result, language="diff" if st.session_state.coder_patch else "text")

    if st.session_state.coder_patch:
        st.warning("Review the patch before applying. This will modify local files in the repository.")
        apply_col, verify_col = st.columns(2)
        with apply_col:
            if st.button("Apply displayed patch", use_container_width=True):
                result = apply_patch_text(st.session_state.coder_patch)
                st.session_state.coder_apply_log = command_output(result)
        with verify_col:
            if st.button("Run compile verification", use_container_width=True):
                result = verify_code()
                st.session_state.coder_verify_log = command_output(result)

    if st.session_state.coder_apply_log:
        st.subheader("Apply log")
        st.code(st.session_state.coder_apply_log, language="text")

    if st.session_state.coder_verify_log:
        st.subheader("Verification log")
        st.code(st.session_state.coder_verify_log, language="text")


def refresh_status() -> None:
    st.session_state.ai_status = get_json("/v1/ai/status")


def refresh_dashboard() -> None:
    st.session_state.dashboard = post_json("/v1/dashboard/refresh")


def upload_document(filename: str, content: bytes) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/v1/documents",
        files={"file": (filename, content, "application/pdf")},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def load_topics(document_id: str) -> None:
    data = get_json(f"/v1/documents/{document_id}/topics")
    st.session_state.topics = data.get("topics", [])


def create_report(query: str) -> dict[str, Any]:
    return post_json("/v1/reports", {"query": query, "limit": 8})


def get_json(path: str) -> dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}{path}", timeout=30)
    response.raise_for_status()
    return response.json()


def post_json(path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}{path}", json=body, timeout=120)
    response.raise_for_status()
    return response.json()


def api_error_message(exc: requests.HTTPError) -> str:
    response = exc.response
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text
    return f"{response.status_code}: {detail}"


def parse_extra_files(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def run_coder_agent(
    task: str,
    mode: str,
    extra_files: list[str],
    extra_args: list[str],
) -> subprocess.CompletedProcess[str]:
    command = [PYTHON_BIN, "tools/coder_agent.py", task, "--mode", mode]
    for file_path in extra_files:
        command.extend(["--file", file_path])
    command.extend(extra_args)
    return run_command(command, timeout=180)


def run_command(
    command: list[str],
    timeout: int = 60,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_DIR,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def apply_patch_text(patch: str) -> subprocess.CompletedProcess[str]:
    check = run_command(["git", "apply", "--check", "-"], timeout=30, input_text=patch)
    if check.returncode != 0:
        return check
    return run_command(["git", "apply", "-"], timeout=30, input_text=patch)


def verify_code() -> subprocess.CompletedProcess[str]:
    return run_command([PYTHON_BIN, "-m", "compileall", "app"], timeout=60)


def command_output(result: subprocess.CompletedProcess[str]) -> str:
    output = []
    output.append(f"exit_code={result.returncode}")
    if result.stdout:
        output.append("\nSTDOUT:\n" + result.stdout)
    if result.stderr:
        output.append("\nSTDERR:\n" + result.stderr)
    return "\n".join(output)


if __name__ == "__main__":
    main()
