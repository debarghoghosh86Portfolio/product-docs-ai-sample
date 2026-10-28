"""Web UI for both features.  Run with:   streamlit run app.py

LESSON: Streamlit turns a Python script into a web app. Every time you
click something, the script re-runs top to bottom; `st.session_state`
remembers values (like chat history) between runs.
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))  # so `import docai` works without installing

from docai.config import load_settings  # noqa: E402
from docai.generator import DocsGenerator  # noqa: E402
from docai.rag import DocsAssistant, ingest  # noqa: E402

st.set_page_config(page_title="Product Docs AI", page_icon="📘", layout="wide")
settings = load_settings()

st.sidebar.title("📘 Product Docs AI")
st.sidebar.caption(f"LLM: **{settings.llm_provider}** · Embeddings: **{settings.embedding_provider}**")
st.sidebar.caption("Change these in your `.env` file, then restart.")
docs_folder = st.sidebar.text_input("Docs folder", "sample_product/docs")
if st.sidebar.button("Re-index docs"):
    store = ingest(docs_folder, settings)
    st.cache_resource.clear()
    st.sidebar.success(f"Indexed {len(store.chunks)} chunks")


@st.cache_resource
def get_assistant():
    if not Path(settings.index_path).exists():
        ingest(docs_folder, settings)
    return DocsAssistant(settings)


tab_qa, tab_gen = st.tabs(["💬 Ask the docs", "✍️ Generate docs"])

with tab_qa:
    if "history" not in st.session_state:
        st.session_state.history = []
    for role, text in st.session_state.history:
        st.chat_message(role).markdown(text)

    question = st.chat_input("e.g. How do I reset my password?")
    if question:
        st.chat_message("user").markdown(question)
        answer = get_assistant().ask(question)
        sources = "\n".join(
            f"- [{i}] `{r.chunk.source}` › {r.chunk.heading} (score {r.score:.2f})"
            for i, r in enumerate(answer.sources, 1)
        )
        reply = answer.text + (f"\n\n**Sources**\n{sources}" if sources else "")
        st.chat_message("assistant").markdown(reply)
        st.session_state.history += [("user", question), ("assistant", reply)]

with tab_gen:
    kind = st.radio("What should the AI write?", ["API reference", "Release notes", "How-to guide"], horizontal=True)
    gen = DocsGenerator(settings)

    if kind == "API reference":
        path = st.text_input("Python file", "sample_product/code/tasks.py")
        if st.button("Generate"):
            with st.spinner("Writing..."):
                st.session_state.draft = gen.api_reference(path)
    elif kind == "Release notes":
        path = st.text_input("Changelog file", "sample_product/CHANGELOG.md")
        version = st.text_input("Version", "2.4.0")
        if st.button("Generate"):
            with st.spinner("Writing..."):
                st.session_state.draft = gen.release_notes(path, version, "TaskFlow")
    else:
        title = st.text_input("Title", "Set up webhooks")
        notes = st.text_area("Rough notes", Path("sample_product/notes/webhook-notes.txt").read_text(), height=220)
        if st.button("Generate"):
            with st.spinner("Writing..."):
                st.session_state.draft = gen.how_to(title, notes, "TaskFlow", "developers")

    if st.session_state.get("draft"):
        st.markdown("---")
        st.markdown(st.session_state.draft)
        st.download_button("Download .md", st.session_state.draft, file_name="generated.md")
