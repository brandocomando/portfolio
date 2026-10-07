# ADR-011: Conversational Context Continuity & Retrieval Query De-Pollution

## Status
Accepted

## Context & Problem Statement
In multi-turn technical conversations, recruiters and visitors rarely repeat full technical queries. Instead, they interact naturally through:
1. **Short topical selections:** Replying with one of the options suggested by the assistant (e.g., Assistant: *"Would you like to hear about the migration process, the GitOps workflow, or the Terraform setup?"* $\longrightarrow$ User: *"terraform setup"*).
2. **Referential follow-ups:** Inquiring about specific concepts mentioned earlier (e.g., *"the process"*, *"how did that work?"*, *"can you elaborate?"*).
3. **Bare affirmative continuations:** Expressing interest to continue (e.g., *"yes"*, *"tell me more"*, *"sure"*).

Naive conversational RAG architectures fail across two distinct failure modes:
* **Context Starvation:** Searching only the current user message causes short queries (e.g. *"the process"*) to fail retrieval because the query lacks technical context.
* **Query Poisoning & Semantic Drift:** Concatenating the entire chat history or previous assistant responses into the search query floods the retrieval engine with dozens of terms from earlier discussion. The assistant's previous narrative crowds out the specific topic the user just chose.

## Decision
We implement an **Asymmetric Contextual Query Engine** and **Turn Normalizer** in `backend/app/services/synthesizer.py`, `backend/app/api/v1/chat.py`, and `backend/app/services/llm_client.py`:

### 1. Conversational Follow-up Classification
* `is_conversational_followup`: Identifies affirmative phrases, referential queries, and short responses ($\le 8$ words) matching options offered in the assistant's trailing question.
* `is_generic_continuation`: Dissects whether the user reply contains a topic of its own or is a bare affirmative signal (e.g., *"yes, tell me more"*).

### 2. Retrieval Query De-Pollution (`build_search_query`)
* **Topic-Bearing Replies (e.g. *"terraform setup"*):** The query isolates the user's selected topic, repeats it to boost BM25 term frequency, and anchors it solely with the *initial user query*:
  $$\text{SearchQuery} = \text{UserSelection} + \text{" "} + \text{UserSelection} + \text{" "} + \text{PriorUserQuery}$$
  The prior assistant message body is **explicitly excluded**, preventing previous topic descriptions from polluting the candidate set.
* **Bare Continuations (e.g. *"yes, tell me more"*):** The engine extracts only the trailing question offered by the assistant (`_offered_options`) combined with the prior user query.

### 3. API Contract Turn Normalization (`_build_history`)
* Enforces a sliding window of the most recent 12 turns (`MAX_HISTORY_MESSAGES = 12`).
* Drops leading assistant turns (e.g., initial UI greeting messages) to ensure the history starts with a user turn.
* Merges consecutive same-role messages and strips internal system prompts to guarantee the strict alternating `(user, model)` role schema required by the Google GenAI SDK.

## Consequences & Trade-offs

### Positive
* **Zero Query Drift:** Users can seamlessly drill into multi-option questions without prior answers corrupting retrieval ranking.
* **Sub-Millisecond Execution:** Operates deterministically in Cloud Run memory without requiring an intermediate LLM query-rewriting call (saving 800ms–1500ms and avoiding additional API charges).
* **Typo Tolerance:** Includes fuzzy sequence matching (`difflib.SequenceMatcher >= 0.8`) and prefix/suffix matching, supporting typos (e.g., *"gitopss"*, *"securirty"*).

### Negative / Mitigations
* **Heuristic Boundaries:** Complex multi-party dialogues or nested conversational pivots can challenge rule-based intent parsing.
  * *Mitigation:* Extensively verified with 24 dedicated multi-turn integration tests in `backend/tests/test_conversation_context.py` covering affirmative continuations, typo tolerances, and option selections.
