# 🎓 Learning Guide: Build GenAI for Product Documentation

This guide teaches you, step by step, how the code in this repo works and *why* it is built this way. Each lesson points to a file, explains the idea in plain English, and ends with a small exercise.

Suggested pace: one or two lessons a day. Do the exercises; that's where the learning happens.

| # | Lesson | File |
|---|---|---|
| 0 | Setup and first run | `README.md` |
| 1 | What an LLM is, and how to call one | `llm.py` |
| 2 | Prompt engineering | `prompts.py` |
| 3 | Why we need RAG | `rag.py` |
| 4 | Chunking | `chunking.py` |
| 5 | Embeddings | `embeddings.py` |
| 6 | Vector search | `vector_store.py` |
| 7 | Putting RAG together | `rag.py` |
| 8 | Generating docs | `generator.py` |
| 9 | Testing, evaluation and shipping | `tests/`, `evaluate.py`, CI |

---

## Lesson 0: Setup and first run

Follow the **Quick start** in `README.md`. Keep `LLM_PROVIDER=mock` for now: the mock model is free and works offline, so you can learn the *pipeline* before spending money on an API.

Key ideas:

- **Virtual environment (`.venv`)**: a private folder of packages for this project, so it doesn't clash with other projects.
- **`.env` file**: stores your settings and secret API keys. It's listed in `.gitignore`, so it is **never uploaded to GitHub**. `.env.example` (no secrets) is what you commit.

✅ **Exercise:** Run `docai ingest sample_product/docs`, then `docai ask "Can I get a refund?"`. Look at the "Sources" list: which file did the answer come from?

---

## Lesson 1: What an LLM is, and how to call one

A **Large Language Model** predicts the next piece of text (a *token*, roughly ¾ of a word) again and again. Trained on huge amounts of text, it becomes good at writing, summarising and answering.

Every chat LLM API has the same shape:

```
system message  ->  "how to behave"   (role, rules, format)
user message    ->  "what to do now"  (task + data)
response        <-  generated text
```

Open `src/docai/llm.py`. There is one abstract class, `LLM`, with one method, `generate(system, prompt)`, and four implementations:

| Class | Talks to | Cost |
|---|---|---|
| `MockLLM` | nothing, it fakes answers | free |
| `AnthropicLLM` | Claude API | paid per token |
| `OpenAILLM` | OpenAI API | paid per token |
| `OllamaLLM` | a model on your PC | free |

`get_llm()` picks one based on `.env`. This is the **adapter pattern**: the rest of the app doesn't care which model is used.

Important terms:

- **Tokens:** you pay for input + output tokens. `max_tokens` caps the output.
- **Context window:** the maximum tokens a model can read at once.
- **Temperature:** randomness. Low = consistent (good for docs). We use provider defaults.
- **Hallucination:** a confident but false answer. RAG (Lesson 3) reduces this.

✅ **Exercise:** Get an API key (or install Ollama), set `LLM_PROVIDER` in `.env`, and ask the same question again. Compare the answer with the mock's.

---

## Lesson 2: Prompt engineering

Open `src/docai/prompts.py`. A prompt is the "program" you write in English. The prompts here follow five rules:

1. **Role:** "You are a senior technical writer."
2. **Task and rules:** "Answer ONLY from the context." "Never invent prices."
3. **Output format:** exact sections, Markdown, tables, citations like `[1]`.
4. **Delimiters around data:** `<context> ... </context>` so the model can tell instructions from data.
5. **An escape hatch:** "If the answer isn't there, say *I couldn't find that*." Without this, models tend to guess.

✅ **Exercise:** In `RELEASE_NOTES_TEMPLATE`, add the rule *"Add one emoji per heading"*, run `docai gen-release ...` with a real LLM, and see the change. Then try removing the "drop purely internal items" rule: do refactor/CI lines leak into the customer notes?

---

## Lesson 3: Why we need RAG

Ask a plain LLM "What's the refund policy for TaskFlow?" It has never seen TaskFlow, so it will either refuse or **make something up**.

**Retrieval-Augmented Generation** fixes this:

1. **Retrieve** the few doc passages most relevant to the question.
2. **Augment** the prompt by pasting those passages in.
3. **Generate** an answer that is grounded in them, with citations.

Why not fine-tune (retrain) the model on your docs instead?

| | RAG | Fine-tuning |
|---|---|---|
| Docs change daily | Re-run `ingest` (seconds) | Retrain (hours, $$) |
| Show sources | Yes | No |
| Reduces hallucination | Yes | Not reliably |
| Teaches style/format | Somewhat | Yes |

For product docs, **RAG is almost always the right first choice.**

---

## Lesson 4: Chunking

Open `src/docai/chunking.py`. We cut docs into pieces of about 800 characters because:

- Small pieces make search **precise** (one topic per chunk).
- We only send a few chunks to the LLM, which saves **tokens and money**.

Our strategy: split at Markdown headings first (keeps topics together), then pack paragraphs up to `CHUNK_SIZE`, with `CHUNK_OVERLAP` characters repeated between neighbours so nothing is lost at the cut. Each chunk remembers its **source file and heading** for citations.

✅ **Exercise:** Set `CHUNK_SIZE=300` in `.env`, re-ingest, and run `python evaluate.py`. Then try `2000`. Which works better? Why might very large chunks hurt?

---

## Lesson 5: Embeddings

Open `src/docai/embeddings.py`. An **embedding** is a list of numbers that represents a text's content. Similar texts get similar numbers.

- `hashing` (default): counts words. Free and offline, but it only matches **shared words**. "browsers" won't match "Chrome, Firefox".
- `openai` / `ollama`: neural models that capture **meaning**. "logged out" matches "session expired".

> Claude has no embeddings API, so with Claude use `hashing` or `ollama` embeddings (or OpenAI/Voyage embeddings). Mixing providers like this is completely normal.

✅ **Exercise:** Run `python evaluate.py` with `hashing`. One question ("Which browsers are supported?") usually **misses**. Switch to `EMBEDDING_PROVIDER=ollama` (or `openai`), re-ingest, and re-run. Did semantic embeddings fix it?

---

## Lesson 6: Vector search

Open `src/docai/vector_store.py`: a complete vector database in about 60 lines.

**Cosine similarity** measures the angle between two vectors: 1.0 means the same direction, 0 means unrelated. Since we normalise every vector to length 1, the similarity to *all* chunks is a single matrix multiplication: `scores = self.vectors @ q`. Then we take the `top_k` highest.

Production tools (Chroma, FAISS, pgvector, Pinecone, Weaviate) do the same thing, plus indexing tricks to stay fast at millions of vectors.

✅ **Exercise:** In a Python shell, run:
```python
import sys; sys.path.insert(0, "src")
from docai.rag import DocsAssistant
a = DocsAssistant()
for r in a.retrieve("cancel my plan"): print(round(r.score, 2), r.chunk.source, r.chunk.heading)
```
Look at the scores. What's the score of an irrelevant chunk?

---

## Lesson 7: Putting RAG together

Open `src/docai/rag.py`:

- `ingest()` = chunk → embed → save index (run once per docs change).
- `DocsAssistant.ask()` = embed question → search → **guardrail** (if no chunk scores above `min_score`, refuse without calling the LLM) → build a numbered context → call the LLM → return answer + sources.

Notice the safety check that the index and query use the **same embedding model**. Vectors from different models are not comparable.

✅ **Exercise:** Ask an off-topic question: `docai ask "Who won the 2010 World Cup?"`. Which layer stopped it: the score guardrail or the prompt rule? Try with a real LLM too.

---

## Lesson 8: Generating docs

Open `src/docai/generator.py`. The key lesson: **extract facts with normal code, then let the LLM write.**

- `extract_structure()` uses Python's `ast` module to read function names, parameters, types, docstrings and raised exceptions *exactly*, with no AI and no mistakes.
- Those facts go into a strict writer prompt, so the LLM spends its effort on clear explanations and examples, not on guessing what the code does.

The same pattern powers release notes (raw changelog → customer language) and how-to guides (rough engineer notes → structured guide).

✅ **Exercise:** Run `docai gen-api sample_product/code/tasks.py` with a real LLM and review `output/api_reference.md` like an editor. Find one thing it got wrong or vague, then improve the prompt to fix it.

---

## Lesson 9: Testing, evaluation and shipping

- **`tests/`**: `pytest` runs 12 tests with the mock model, so they're free and deterministic. The most valuable tests check **retrieval** ("does this question find the right file?"), because if retrieval fails, even the best LLM can't answer.
- **`evaluate.py`**: a small labelled question set that reports **hit rate @k**. Use it every time you change chunk size, `top_k` or embeddings. Measure, don't guess.
- **`.github/workflows/ci.yml`**: GitHub runs the tests on every push. The green ✓ on your repo shows reviewers it works.

---

## Upload this project to GitHub

1. Create an account at github.com, click **New repository**, name it `product-docs-ai`, keep it **empty** (no README), and click **Create**.
2. In a terminal inside the project folder:

```bash
git init
git add .
git status                 # CHECK: .env must NOT be listed!
git commit -m "Initial commit: GenAI docs assistant and generator"
git branch -M main
git remote add origin https://github.com/<your-username>/product-docs-ai.git
git push -u origin main
```

3. Open the **Actions** tab on GitHub and watch the tests pass.

> ⚠️ If you ever commit an API key by mistake, **revoke it immediately** in the provider's console. Deleting the commit is not enough.

---

## Next steps (ideas to extend your portfolio)

1. **PDF/HTML loaders:** use `pypdf` or `beautifulsoup4` in `chunking.py`.
2. **Hybrid search:** combine hashing (keywords) + semantic scores.
3. **Re-ranking:** retrieve top 10, ask the LLM to pick the best 3.
4. **Streaming answers** in the Streamlit UI.
5. **Conversation memory:** rewrite follow-ups ("and on Pro?") into standalone questions before retrieval.
6. **Swap the vector store** for Chroma and compare speed.
7. **Doc-drift checker:** compare `extract_structure()` output with existing docs and flag functions that are undocumented.
8. **LLM-as-judge evaluation:** have a model grade answers for faithfulness to the sources.
