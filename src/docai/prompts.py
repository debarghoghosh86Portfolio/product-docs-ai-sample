"""All prompts in one place.

LESSON: The prompt is the "program" you write for an LLM. Good prompts:
  * give the model a ROLE           ("You are a technical writer...")
  * state the TASK and RULES        ("Answer only from the context")
  * give a clear OUTPUT FORMAT      ("Markdown, with these sections")
  * put the DATA in clear delimiters (<context> ... </context>)
  * say what to do when unsure      ("If the answer isn't there, say so")

Keeping prompts together makes them easy to compare, tweak and version in Git.
"""

# ---------------------------------------------------------------------------
# Q&A assistant (RAG)
# ---------------------------------------------------------------------------
QA_SYSTEM = """You are the support assistant for a software product.
Answer the user's question using ONLY the documentation excerpts inside <context>.

Rules:
- If the context does not contain the answer, reply exactly:
  "I couldn't find that in the documentation."
- Never invent features, settings, prices or limits.
- Cite the excerpts you used with their numbers, like [1] or [2][3].
- Be concise. Use numbered steps for procedures."""

QA_TEMPLATE = """<context>
{context}
</context>

Question: {question}

Answer (with citations):"""


# ---------------------------------------------------------------------------
# Docs generator
# ---------------------------------------------------------------------------
WRITER_SYSTEM = """You are a senior technical writer. You write clear, accurate,
developer-friendly documentation in GitHub-flavoured Markdown.
Only describe behaviour that is visible in the material you are given.
If something is unclear, add a short "> Note:" instead of guessing."""

API_REFERENCE_TEMPLATE = """Write an API reference page for the Python module `{module}`.

For the module, write a 1-2 sentence overview.
For EACH class and function below, include:
  - a heading with its name
  - a one-paragraph description in plain English
  - a "Parameters" table (name | type | description) when it has parameters
  - "Returns" and "Raises" when applicable
  - a short, realistic usage example in a ```python code block

Extracted code structure:
{structure}

Full source code (for reference):
```python
{source}
```"""

RELEASE_NOTES_TEMPLATE = """Turn the raw changelog entries below into customer-facing release notes
for version {version} of {product}.

Format:
# {product} {version} release notes
A 2-sentence summary of the release.
## New features
## Improvements
## Bug fixes
## Breaking changes  (omit this section if there are none)

Rules: write for end users, not engineers; explain the benefit of each change;
drop purely internal items (refactors, CI, tests).

Raw changelog:
{changelog}"""

HOW_TO_TEMPLATE = """Write a step-by-step how-to guide titled "{title}" for {product}.
Audience: {audience}.

Use this structure: short intro, "Before you begin" (prerequisites),
numbered steps, "Troubleshooting" (2-3 common problems), "Next steps".

Base the guide ONLY on these product notes:
{notes}"""
