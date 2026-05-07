from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import requests
import streamlit as st


API_BASE_URL = os.getenv("AGENTIC_PDF_API_URL", "http://127.0.0.1:8000")
API_READ_TIMEOUT_SECONDS = int(os.getenv("AGENTIC_PDF_API_READ_TIMEOUT_SECONDS", "600"))
API_STATUS_TIMEOUT_SECONDS = int(os.getenv("AGENTIC_PDF_API_STATUS_TIMEOUT_SECONDS", "30"))
REPO_DIR = Path(__file__).resolve().parent
PYTHON_BIN = os.getenv("AGENTIC_PDF_PYTHON_BIN") or ""


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

    pdf_tab, data_tab, coding_tab = st.tabs(["PDF Chat", "Data Browser", "Coding Agent"])

    with pdf_tab:
        upload_col, topic_col = st.columns([0.42, 0.58], gap="large")
        with upload_col:
            render_upload()
        with topic_col:
            render_topics()

        st.divider()
        render_chat()

    with data_tab:
        render_data_browser()

    with coding_tab:
        render_coding_agent()


def init_state() -> None:
    st.session_state.setdefault("document_id", None)
    st.session_state.setdefault("document", None)
    st.session_state.setdefault("document_details", None)
    st.session_state.setdefault("topics", [])
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("ai_status", None)
    st.session_state.setdefault("dashboard", None)
    st.session_state.setdefault("documents_list", None)
    st.session_state.setdefault("reports_list", None)
    st.session_state.setdefault("coder_result", "")
    st.session_state.setdefault("coder_patch", "")
    st.session_state.setdefault("coder_context_files", "")
    st.session_state.setdefault("coder_apply_log", "")
    st.session_state.setdefault("coder_verify_log", "")
    st.session_state.setdefault("coder_direct_apply_log", "")

    if st.session_state.ai_status is None:
        safe_refresh_status()
    if st.session_state.dashboard is None:
        safe_refresh_dashboard()


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
    st.metric("Paragraphs", dashboard.get("paragraph_count", 0))

    recent_documents = dashboard.get("top_documents") or []
    if recent_documents:
        options = {
            f"{doc.get('filename')} · {doc.get('document_id')}": doc.get("document_id")
            for doc in recent_documents
            if doc.get("document_id")
        }
        selected = st.selectbox("Open recent document", [""] + list(options.keys()))
        if selected and st.button("Load selected document", use_container_width=True):
            load_document(options[selected])


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
                load_document(result["document_id"])
                refresh_status()
                refresh_dashboard()
                agent = result.get("agent", {})
                parsing_agent = agent.get("parsing", agent)
                topic_agent = agent.get("topics", {})
                if parsing_agent.get("agent_used") == "llm":
                    st.success(
                        "Uploaded with LLM parsing "
                        f"({parsing_agent.get('pages_enhanced', 0)} pages enhanced)."
                    )
                elif topic_agent.get("agent_used") == "llm":
                    st.success("Uploaded with LLM topic extraction.")
                else:
                    reason = parsing_agent.get("reason") or topic_agent.get("reason") or "unknown reason"
                    st.warning(f"Uploaded with fallback: {reason}")
            except requests.HTTPError as exc:
                st.error(api_error_message(exc))
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")

    document = st.session_state.document
    if document:
        st.info(f"Current document: {document['filename']}")
        st.code(document["document_id"])


def render_topics() -> None:
    st.subheader("Topic, keyword, and paragraph explorer")
    details = st.session_state.document_details
    topics = st.session_state.topics

    if not topics:
        st.write("Upload or load a PDF to inspect topics, keywords, and paragraphs.")
        return

    topic_options = {topic.get("topic", "Untitled"): topic for topic in topics}
    selected_topic_label = st.selectbox("Topic", list(topic_options.keys()))
    selected_topic = topic_options[selected_topic_label]

    st.markdown(f"### {extract_document_title(details)}")
    st.write(extract_document_summary(details, topics))
    st.divider()

    st.write(selected_topic.get("summary") or "No topic summary")
    st.caption(f"Topic ID: {selected_topic.get('topic_id')}")

    keywords = selected_topic.get("keywords") or []
    selected_keywords = st.multiselect(
        "Filter by keywords",
        keywords,
        default=[],
        help="Leave empty to show every paragraph in the selected topic.",
    )

    paragraphs = selected_topic.get("paragraphs") or []
    if not paragraphs and details:
        topic_chunk_ids = set(selected_topic.get("chunk_ids") or [])
        for chunk in details.get("chunks", []):
            if chunk.get("chunk_id") in topic_chunk_ids:
                paragraphs.extend(chunk.get("paragraphs") or [])

    body_paragraphs = visible_body_paragraphs(paragraphs)
    filtered = filter_paragraphs(body_paragraphs, selected_keywords)
    filter_label = "all paragraphs" if not selected_keywords else "keyword-matched paragraphs"
    st.caption(f"Showing {len(filtered)} of {len(body_paragraphs)} {filter_label}")

    for paragraph in filtered:
        label = f"Paragraph {paragraph.get('document_paragraph_index') or paragraph.get('paragraph_index')}"
        with st.expander(label, expanded=len(filtered) <= 3):
            st.write(paragraph.get("text") or "")


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


def render_data_browser() -> None:
    st.subheader("Existing data")
    document_section, report_section = st.columns(2, gap="large")

    with document_section:
        st.markdown("#### Documents")
        document_search = st.text_input("Search documents", key="document_search")
        if st.button("Load documents", type="primary", use_container_width=True):
            try:
                st.session_state.documents_list = list_documents(document_search)
            except requests.HTTPError as exc:
                st.error(api_error_message(exc))
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")

        documents_data = st.session_state.documents_list
        if documents_data:
            documents = documents_data.get("documents", [])
            st.caption(f"{len(documents)} of {documents_data.get('total', 0)} documents")
            st.dataframe(document_rows(documents), use_container_width=True, hide_index=True)
            document_options = {
                f"{document.get('filename')} · {document.get('document_id')}": document.get("document_id")
                for document in documents
                if document.get("document_id")
            }
            selected_document = st.selectbox("Open document", [""] + list(document_options.keys()))
            if selected_document and st.button("Load document into PDF Chat", use_container_width=True):
                load_document(document_options[selected_document])
                st.success("Document loaded. Open the PDF Chat tab to inspect topics and paragraphs.")

    with report_section:
        st.markdown("#### Reports")
        report_search = st.text_input("Search reports", key="report_search")
        if st.button("Load reports", type="primary", use_container_width=True):
            try:
                st.session_state.reports_list = list_reports(report_search)
            except requests.HTTPError as exc:
                st.error(api_error_message(exc))
            except requests.RequestException as exc:
                st.error(f"Backend request failed: {exc}")

        reports_data = st.session_state.reports_list
        if reports_data:
            reports = reports_data.get("reports", [])
            st.caption(f"{len(reports)} of {reports_data.get('total', 0)} reports")
            st.dataframe(report_rows(reports), use_container_width=True, hide_index=True)
            report_options = {
                f"{report.get('created_at')} · {report.get('query', '')[:60]}": report
                for report in reports
            }
            selected_report = st.selectbox("Open report", [""] + list(report_options.keys()))
            if selected_report:
                report = report_options[selected_report]
                st.write(report.get("answer") or "")
                render_sources(report.get("source_chunks", []))


def render_coding_agent() -> None:
    st.subheader("Coding Agent")
    st.caption("Generate plans, review patches, or let tools/coder_agent.py apply and verify a patch.")
    st.caption(f"Python: `{resolve_python_bin()}`")

    config = run_command([resolve_python_bin(), "tools/coder_agent.py", "test", "--check-config"])
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

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        plan_clicked = st.button("Generate plan", use_container_width=True)
    with col2:
        patch_clicked = st.button("Generate patch", type="primary", use_container_width=True)
    with col3:
        context_clicked = st.button("Show context files", use_container_width=True)
    with col4:
        direct_apply_clicked = st.button("Generate, apply, verify", use_container_width=True)

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

    if direct_apply_clicked:
        st.warning("This will modify repository files by running coder_agent.py with --apply --verify.")
        with st.spinner("Generating, applying, and verifying patch..."):
            result = run_coder_agent(task, "patch", extra_files, ["--apply", "--verify"])
            st.session_state.coder_direct_apply_log = command_output(result)
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

    if st.session_state.coder_direct_apply_log:
        st.subheader("Direct apply log")
        st.code(st.session_state.coder_direct_apply_log, language="text")


def refresh_status() -> None:
    st.session_state.ai_status = get_json("/v1/ai/status")


def safe_refresh_status() -> None:
    try:
        refresh_status()
    except requests.RequestException as exc:
        st.session_state.ai_status = {
            "configured": False,
            "model": None,
            "base_url": None,
            "last_call": {
                "task": "status",
                "mode": "unavailable",
                "error": f"Backend unavailable: {exc}",
            },
        }


def refresh_dashboard() -> None:
    st.session_state.dashboard = post_json("/v1/dashboard/refresh")


def safe_refresh_dashboard() -> None:
    try:
        refresh_dashboard()
    except requests.RequestException:
        st.session_state.dashboard = {
            "document_count": 0,
            "topic_count": 0,
            "chunk_count": 0,
            "paragraph_count": 0,
            "top_documents": [],
        }


def upload_document(filename: str, content: bytes) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/v1/documents",
        files={"file": (filename, content, "application/pdf")},
        timeout=API_READ_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def load_topics(document_id: str) -> None:
    data = get_json(f"/v1/documents/{document_id}/topics")
    st.session_state.topics = data.get("topics", [])


def load_document(document_id: str) -> None:
    data = get_json(f"/v1/documents/{document_id}")
    st.session_state.document_details = data
    st.session_state.document = data.get("document")
    st.session_state.document_id = document_id
    st.session_state.topics = data.get("topics", [])


def list_documents(search: str | None = None) -> dict[str, Any]:
    params = {"limit": 100}
    if search:
        params["search"] = search
    response = requests.get(f"{API_BASE_URL}/v1/documents", params=params, timeout=API_STATUS_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def list_reports(search: str | None = None) -> dict[str, Any]:
    params = {"limit": 100}
    if search:
        params["search"] = search
    response = requests.get(f"{API_BASE_URL}/v1/reports", params=params, timeout=API_STATUS_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def create_report(query: str) -> dict[str, Any]:
    return post_json("/v1/reports", {"query": query, "limit": 8})


def get_json(path: str) -> dict[str, Any]:
    response = requests.get(f"{API_BASE_URL}{path}", timeout=API_STATUS_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def post_json(path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}{path}", json=body, timeout=API_READ_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def api_error_message(exc: requests.HTTPError) -> str:
    response = exc.response
    try:
        detail = response.json().get("detail")
    except ValueError:
        detail = response.text
    return f"{response.status_code}: {detail}"


def filter_paragraphs(paragraphs: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    if not keywords:
        return paragraphs
    lowered = [keyword.lower() for keyword in keywords]
    return [
        paragraph
        for paragraph in paragraphs
        if any(keyword in str(paragraph.get("text", "")).lower() for keyword in lowered)
    ]


def visible_body_paragraphs(paragraphs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hidden_kinds = {"title", "artifact", "footer", "table"}
    return [
        paragraph
        for paragraph in paragraphs
        if str(paragraph.get("kind") or "paragraph").lower() not in hidden_kinds
    ]


def extract_document_title(details: dict[str, Any] | None) -> str:
    details = details or {}
    document = details.get("document") or {}
    topics = details.get("topics") or []
    metadata_title = document.get("metadata", {}).get("title")

    for topic in topics:
        for paragraph in topic.get("paragraphs") or []:
            if str(paragraph.get("kind", "")).lower() == "title":
                return str(paragraph.get("text", "")).strip()

    return str(metadata_title or document.get("filename") or "Untitled document")


def extract_document_summary(details: dict[str, Any] | None, topics: list[dict[str, Any]]) -> str:
    summaries = []
    for topic in topics:
        summary = str(topic.get("summary") or "").strip()
        if summary and summary not in summaries:
            summaries.append(summary)
    if summaries:
        return " ".join(summaries[:3])[:900]

    details = details or {}
    for topic in details.get("topics") or []:
        for paragraph in visible_body_paragraphs(topic.get("paragraphs") or []):
            text = str(paragraph.get("text") or "").strip()
            if text:
                return text[:900]
    return "No document summary available yet."


def document_rows(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "filename": document.get("filename"),
            "document_id": document.get("document_id"),
            "pages": document.get("metadata", {}).get("page_count"),
            "topics": document.get("topic_count", 0),
            "chunks": document.get("chunk_count", 0),
            "paragraphs": document.get("paragraph_count", 0),
            "uploaded_at": document.get("metadata", {}).get("uploaded_at"),
        }
        for document in documents
    ]


def report_rows(reports: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "report_id": report.get("report_id"),
            "query": report.get("query"),
            "sources": len(report.get("source_chunks", [])),
            "created_at": report.get("created_at"),
        }
        for report in reports
    ]


def parse_extra_files(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def resolve_python_bin() -> str:
    if PYTHON_BIN:
        return PYTHON_BIN

    candidates = [
        REPO_DIR / ".venv" / "bin" / "python",
        REPO_DIR / ".venv" / "bin" / "python3",
        REPO_DIR / ".venv" / "Scripts" / "python.exe",
        REPO_DIR / ".venv" / "Scripts" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return sys.executable


def run_coder_agent(
    task: str,
    mode: str,
    extra_files: list[str],
    extra_args: list[str],
) -> subprocess.CompletedProcess[str]:
    command = [resolve_python_bin(), "tools/coder_agent.py", task, "--mode", mode]
    for file_path in extra_files:
        command.extend(["--file", file_path])
    command.extend(extra_args)
    return run_command(command, timeout=180)


def run_command(
    command: list[str],
    timeout: int = 60,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=str(REPO_DIR),
            input=input_text,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(
            command,
            127,
            "",
            f"Command file not found: {exc.filename}. Set AGENTIC_PDF_PYTHON_BIN if needed.",
        )
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(
            command,
            124,
            exc.stdout or "",
            exc.stderr or f"Command timed out after {timeout} seconds.",
        )


def apply_patch_text(patch: str) -> subprocess.CompletedProcess[str]:
    check = run_command(["git", "apply", "--check", "-"], timeout=30, input_text=patch)
    if check.returncode != 0:
        return check
    return run_command(["git", "apply", "-"], timeout=30, input_text=patch)


def verify_code() -> subprocess.CompletedProcess[str]:
    return run_command([resolve_python_bin(), "-m", "compileall", "app"], timeout=60)


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
