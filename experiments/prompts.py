"""Verbatim prompts and the tool schema. Printed in the paper appendix.

Policies (P):
  free     - no instruction about query language; the agent chooses (we log the script).
  match    - query in the language of the question.
  english  - query in English (translate the information need first).
  dual     - two queries per step: one in the question's language and one in English.
"""

LANG_NAME = {"hi": "Hindi", "te": "Telugu", "en": "English", "bn": "Bengali", "ta": "Tamil"}

SYSTEM_AGENT = (
    "You are a search agent. You answer factual questions by searching a document collection with the "
    "`search` tool, reading the returned passages, and then giving a short final answer.\n"
    "Rules:\n"
    "- You may call `search` at most {max_searches} times. Each call returns the top {k} passages.\n"
    "- When you have enough evidence, or when you have used all your searches, stop calling tools and "
    "reply with the final answer only: a short phrase (a name, date, number, or term), no explanation.\n"
    "- Answer in the same language as the question.\n"
    "- If the evidence does not contain the answer, you may still answer from your own knowledge, but "
    "prefer the evidence.{policy}"
)

POLICY = {
    "free": "",
    "match": "\n- Write every search query in {qlang}, the language of the question.",
    "english": "\n- Write every search query in English, even though the question is in {qlang}. Translate the "
               "information need into an English query.",
    "dual": "\n- At every step call `search` twice: once with a query in {qlang} (the language of the question) "
            "and once with the same information need as an English query. Both calls count as one step.",
}

TOOL_SEARCH = {
    "type": "function",
    "function": {
        "name": "search",
        "description": "Search the document collection. Returns the most relevant passages with their titles.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query."}},
            "required": ["query"],
        },
    },
}

SYSTEM_CLOSED = (
    "You answer factual questions from your own knowledge. Reply with the final answer only: a short "
    "phrase (a name, date, number, or term), no explanation. Answer in the same language as the question."
)

SYSTEM_ORACLE = (
    "You answer a factual question using the passage provided. Reply with the final answer only: a short "
    "phrase (a name, date, number, or term), no explanation. Answer in the same language as the question."
)
USER_ORACLE = "Passage:\n\"\"\"\n{passage}\n\"\"\"\n\nQuestion: {question}"

NO_RESULTS = "No passages found for this query."

SYSTEM_JUDGE = (
    "You are a strict grader of short answers to factual questions. Decide whether the candidate answer "
    "expresses the same fact as any of the gold answers. Accept equivalent forms: a transliteration or "
    "translation of the gold answer into another language or script, a date written differently, a number "
    "with or without units, a name with or without honorifics, a more specific answer that contains the gold "
    "answer. Reject answers that name a different entity, date, or number, that hedge between several "
    "candidates. If the candidate declines to answer, says the information is unavailable, or asks a question "
    "back, that is ABSTAIN."
)
USER_JUDGE = (
    "Question (English): {q_en}\nQuestion (original): {q_L}\nGold answers: {gold}\nCandidate answer: {cand}\n\n"
    "Reply with exactly one word: CORRECT, WRONG, or ABSTAIN (the candidate says it does not know, cannot find the "
    "answer, or asks for clarification instead of answering)."
)

SYSTEM_TRANSLATE = "You are a professional translator. Translate faithfully; keep named entities, numbers and dates exact. Output only the translation."
USER_TRANSLATE = "Translate this {src} question into {tgt}:\n{text}"
