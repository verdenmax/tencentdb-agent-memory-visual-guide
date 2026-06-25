# Accuracy Review & Polish Pass — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify every behavioral/symbol-level claim in all 34 lessons against the current `TencentDB-Agent-Memory` source, then apply accuracy fixes, deep polish, and targeted enhancements — bilingually — while keeping build/HTML/link/drift checks green.

**Architecture:** Approach B from the spec. Work proceeds Part by Part (8 parts, one `src/partN.py` file each). For each Part: a verification subagent (`claude-opus-4.8`) reads the source anchors + current lesson fragments and returns a structured findings report (no edits); the main agent verifies each citation, applies edits to `zh`+`en` together, rebuilds, runs the structural/link checks, and commits. A final Opus-4.8-max long-context subagent reviews the full diff; the main agent fixes anything it surfaces, then runs acceptance and writes the report.

**Tech Stack:** Pure-Python static-site generator (`build.py`, `build_print.py`, `check_html.py`, `check_links.py`), bilingual HTML fragments in `src/part1.py … part8.py`, quizzes in `src/quizzes.py`. Source project under review: TypeScript in `/home/verden/course/TencentDB-Agent-Memory`.

Spec: `docs/superpowers/specs/2026-06-25-content-accuracy-review-and-polish-design.md`

---

## File / Part / Lesson / Anchor Map

The pass touches only `src/part1.py … part8.py` (and `src/quizzes.py` if a quiz is factually wrong). Generated `lessons/*.html`, `index.html`, `print_*.html` are rebuilt, never hand-edited.

| Part | Guide file | Lesson constants | Lessons | Primary source anchors in `TencentDB-Agent-Memory` |
| --- | --- | --- | --- | --- |
| 1 | `src/part1.py` | `LESSON_01..03` | 01 why-agent-memory, 02 one-conversation-flow, 03 two-memory-spines | `README.md`, `README_CN.md`, `package.json`, `index.ts` |
| 2 | `src/part2.py` | `LESSON_04..07` | 04 openclaw-zero-config, 05 hermes-gateway-path, 06 runtime-files, 07 config-levels | `README_CN.md`, `SKILL.md`, `src/cli/README.md`, `openclaw.plugin.json`, `src/config.ts`, `hermes-plugin/memory/memory_tencentdb/README.md` |
| 3 | `src/part3.py` | `LESSON_08..11` | 08 openclaw-plugin-shell, 09 tdai-core-facade, 10 host-adapter-boundaries, 11 runtime-init-config | `index.ts`, `src/core/tdai-core.ts`, `src/adapters/openclaw/host-adapter.ts`, `src/adapters/standalone/host-adapter.ts`, `src/config.ts` |
| 4 | `src/part4.py` | `LESSON_12..16` | 12 auto-capture-hook, 13 l0-jsonl-recorder, 14 checkpoints-races, 15 l1-extraction, 16 l1-dedup-write | `src/core/hooks/auto-capture.ts`, `src/core/conversation/l0-recorder.ts`, `src/utils/checkpoint.ts`, `src/core/record/l1-extractor.ts`, `src/core/record/l1-dedup.ts`, `src/core/record/l1-writer.ts`, `src/core/prompts/l1-extraction.ts`, `src/core/prompts/l1-dedup.ts` |
| 5 | `src/part5.py` | `LESSON_17..21` | 17 why-l2-scene-blocks, 18 scene-extractor-sandbox, 19 scene-index-navigation-backups, 20 persona-generator-incremental, 21 l2-l3-scheduling-triggers | `src/core/scene/scene-extractor.ts`, `src/core/scene/scene-index.ts`, `src/core/scene/scene-navigation.ts`, `src/core/scene/scene-format.ts`, `src/core/persona/persona-generator.ts`, `src/core/persona/persona-trigger.ts`, `src/utils/pipeline-manager.ts`, `src/utils/pipeline-factory.ts` |
| 6 | `src/part6.py` | `LESSON_22..26` | 22 auto-recall-before-prompt, 23 l1-search-recall-budget, 24 l2-navigation-l3-persona-injection, 25 sqlite-vec-fts-bm25-hybrid, 26 tencent-vectordb-embedding | `src/core/hooks/auto-recall.ts`, `src/core/tools/memory-search.ts`, `src/core/tools/conversation-search.ts`, `src/core/store/sqlite.ts`, `src/core/store/search-utils.ts`, `src/core/store/factory.ts`, `src/core/store/embedding.ts`, `src/core/store/bm25-local.ts`, `src/core/store/tcvdb.ts` |
| 7 | `src/part7.py` | `LESSON_27..31` | 27 why-long-task-logs-symbolic-compression, 28 after-tool-call-refs-offload-jsonl, 29 l1-l15-l2-local-llm-pipelines, 30 mermaid-mmd-node-id-drill-down, 31 l3-context-injection-emergency-compression | `src/offload/index.ts`, `src/offload/storage.ts`, `src/offload/hooks/after-tool-call.ts`, `src/offload/hooks/before-prompt-build.ts`, `src/offload/hooks/llm-output.ts`, `src/offload/local-llm/index.ts`, `src/offload/pipelines/l2-mermaid.ts`, `src/offload/mmd-injector.ts`, `src/offload/l3-helpers.ts`, `src/offload/hooks/llm-input-l3.ts` |
| 8 | `src/part8.py` | `LESSON_32..34` | 32 hermes-gateway-http-security, 33 seed-cli-migration-export-read, 34 debug-tests-contribution-glossary | `src/gateway/server.ts`, `src/gateway/config.ts`, `src/cli/commands/seed.ts`, `src/core/seed/seed-runtime.ts`, `scripts/README.memory-tencentdb-ctl.md`, `scripts/migrate-sqlite-to-tcvdb/README.md`, `CONTRIBUTING.md`, `CONTRIBUTING_CN.md`, `vitest.config.ts` |

Anchor lists are a verified starting point; verification subagents must follow imports/usages into other source files when a claim depends on them, and report the actual file they confirmed each fact in.

---

## Conventions & Shared Procedures

These are used by every Part task (Tasks 1–8). Each task names its own Part number, lesson set, guide file, and anchor list; the procedure below is identical across Parts.

### C1. Findings tracker (session SQL)

Create the tracker once (Task 0), then every Part appends to it:

```sql
CREATE TABLE IF NOT EXISTS review_findings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  part INTEGER NOT NULL,
  lesson TEXT NOT NULL,           -- e.g. '12-auto-capture-hook.html'
  bucket TEXT NOT NULL,          -- 'A_inaccuracy' | 'B_polish' | 'C_enhancement'
  lang TEXT,                     -- 'zh' | 'en' | 'both'
  claim TEXT NOT NULL,           -- the current text / what the guide says
  source_citation TEXT,          -- 'path#symbol' confirmed in source (required for bucket A)
  suggested_change TEXT NOT NULL,
  status TEXT DEFAULT 'open'      -- 'open' | 'applied' | 'rejected'
);
```

### C2. Verification subagent (dispatch per Part; VERIFY ONLY, NO EDITS)

Dispatch with `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. The prompt template (fill in `<PART>`, `<LESSON_LIST>`, `<GUIDE_FILE>`, `<ANCHOR_LIST>`):

```
You are auditing a learning guide for factual accuracy against its source project. DO NOT edit any file. Report findings only.

SOURCE PROJECT (ground truth): /home/verden/course/TencentDB-Agent-Memory
GUIDE FILE (the text under audit): /home/verden/course/tencentdb-agent-memory-visual-guide/<GUIDE_FILE>
This file holds bilingual HTML fragments in Python constants <LESSON_LIST> (each has a "zh" and an "en" string).

ANCHOR SOURCE FILES to read first (follow imports/usages further as needed):
<ANCHOR_LIST>

FOR EACH lesson constant in <LESSON_LIST>:
1. Read the zh and en content.
2. Extract every checkable claim: symbol names (functions/classes/methods/fields), file paths, module boundaries, behavior, ordering between stages, config fields that control behavior, SQLite-vs-Tencent-VectorDB backend differences, and host attribution (OpenClaw/Hermes/Gateway/standalone).
3. Verify each claim against the source. Open the actual files; do not guess.

RETURN a findings report grouped by lesson. For each finding give:
- bucket: A_inaccuracy | B_polish | C_enhancement
- lang: zh | en | both
- claim: what the guide currently says (short quote)
- source_citation: the file path + symbol where you confirmed the truth (REQUIRED for bucket A; e.g. src/core/hooks/auto-capture.ts#performAutoCapture)
- suggested_change: the concrete correction or improvement

Bucket A = the guide contradicts the source (wrong symbol/path/behavior/order/config/backend/host). MUST have a source_citation.
Bucket B = accurate but awkward wording, inconsistent terminology, broken flow, or zh/en mismatch.
Bucket C = accurate but a beginner would benefit from an added/clearer diagram, added pseudocode, or an expanded thin section.

Be exhaustive on bucket A. If a claim is correct, do not report it. Do not propose changing the curriculum, Part structure, or removing lessons.
```

### C3. Edit-safety invariants (enforced by `check_html.py`)

When applying edits to `<GUIDE_FILE>`, preserve all of:
- Balanced `div`/`details`/`table`/`pre`/`summary`; `details` count == `summary` count.
- Exactly one `<h1>`; keep `<title>` + `meta description` (these come from `shell.py`, so don't remove the lesson title/description fields).
- Both `zh` and `en` present, information-equivalent, each edited in the same step; `zh` keeps ≥ 500 CJK chars.
- Inside `<pre>`: literal `<` → `&lt;`, arrows → `-&gt;` (inline tags `span/strong/b/em/u/a` allowed raw).
- "第 N 课" references stay within 1..34.
- ≥ 6 visual blocks per lesson (`layers/vflow/flow/cols/cellgroup/timeline/trace` or `<table class="t">`); keep the key-points card and the analogy card (`card analogy`).
- Lesson 17: scene metadata table fields stay exactly `{created, updated, summary, heat}`; do not present `evidence` as a parsed metadata field (see `check_lesson17_scene_metadata_source`).
- Lesson 29: keep the required local-LLM anchors/markers (see `check_lesson29_local_llm_contract`).
- Never edit `TencentDB-Agent-Memory`; no large source copies; no secrets.

### C4. Per-Part validation + commit (the "test" for each Part task)

```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide/src
python3 build.py            # regenerate lessons/*.html + index.html
python3 check_html.py       # MUST print "structural check passed", 0 errors
python3 check_links.py      # MUST print "all N internal links resolve"
cd .. && git add -A && git status --short   # expect only src/partN.py, quizzes.py?, lessons/*.html, index.html
git commit -m "docs: accuracy review and polish for Part <PART> (lessons <RANGE>)

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

If `check_html.py` reports any ERROR, fix the offending fragment before committing — never commit a red Part.

---

## Task 0: Baseline & guardrails

**Files:**
- Modify: none (read-only verification + session SQL tracker)

- [ ] **Step 1: Confirm a clean, green baseline**

Run:
```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide/src
python3 build.py && python3 build_print.py && python3 check_html.py && python3 check_links.py
cd .. && git status --short
```
Expected: build writes 35 files; print writes 2 files; `check_html.py` prints `structural check passed` with `0 error(s)`; `check_links.py` prints `all N internal links resolve`; `git status --short` is empty (zero drift). If drift appears, commit the regenerated output first so later Part diffs are clean.

- [ ] **Step 2: Create the findings tracker**

Run the `CREATE TABLE review_findings` statement from Convention C1 in the session database.
Expected: table created.

- [ ] **Step 3: Snapshot baseline counts (for the final report)**

Run:
```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide
ls lessons/*.html | wc -l            # expect 34
grep -c "LESSON_" src/quizzes.py || true
git rev-parse HEAD                    # record as the pass's base commit
```
Expected: 34 lessons; record the base commit SHA in the final report. No commit (nothing changed).

---

## Task 1: Part 1 — Why Agent Memory exists (lessons 01–03)

**Files:**
- Modify: `src/part1.py` (`LESSON_01`, `LESSON_02`, `LESSON_03`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

Use the `task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill the Convention C2 template with:
- `<PART>` = 1
- `<GUIDE_FILE>` = `src/part1.py`
- `<LESSON_LIST>` = `LESSON_01, LESSON_02, LESSON_03`
- `<ANCHOR_LIST>` =
  - `README.md`
  - `README_CN.md`
  - `package.json`
  - `index.ts`

Expected: a findings report grouped by lesson, buckets A/B/C, bucket-A items each carrying a `path#symbol` citation.

- [ ] **Step 2: Record findings**

Insert each returned finding into `review_findings` (Convention C1) with `part = 1`. Expected: rows inserted, all `status='open'`.

- [ ] **Step 3: Verify every bucket-A citation against source before trusting it**

For each `A_inaccuracy`, open the cited source file in `/home/verden/course/TencentDB-Agent-Memory` and confirm the claimed truth. If the subagent's citation does not actually support the correction, mark that finding `status='rejected'` and do not apply it.
Expected: every remaining bucket-A finding is independently confirmed.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part1.py`, updating `zh` and `en` together for each lesson, honoring all Convention C3 invariants. Apply: confirmed bucket-A corrections; accepted bucket-B polish; bucket-C enhancements that genuinely help a beginner (add/clarify a diagram, add pseudocode, expand a thin section). Mark applied findings `status='applied'`.
Expected: `src/part1.py` edited; no curriculum/Part-structure changes.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 1, `<RANGE>` = `01-03`.
Expected: `check_html.py` → `structural check passed` (0 errors); `check_links.py` → all links resolve; `git status` shows only `src/part1.py` (± `src/quizzes.py`) and regenerated `lessons/*.html` + `index.html`; commit succeeds.

---

## Task 2: Part 2 — Minimal working loop (lessons 04–07)

**Files:**
- Modify: `src/part2.py` (`LESSON_04`, `LESSON_05`, `LESSON_06`, `LESSON_07`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 2
- `<GUIDE_FILE>` = `src/part2.py`
- `<LESSON_LIST>` = `LESSON_04, LESSON_05, LESSON_06, LESSON_07`
- `<ANCHOR_LIST>` =
  - `README_CN.md`
  - `SKILL.md`
  - `src/cli/README.md`
  - `openclaw.plugin.json`
  - `src/config.ts`
  - `hermes-plugin/memory/memory_tencentdb/README.md`

Expected: findings report grouped by lesson with A/B/C buckets and bucket-A citations.

- [ ] **Step 2: Record findings**

Insert findings into `review_findings` with `part = 2`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

Open each cited file (especially `src/config.ts` for config-level claims and `openclaw.plugin.json` for zero-config defaults) and confirm. Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part2.py` (`zh`+`en` together), honoring Convention C3. Pay special attention to host attribution (OpenClaw vs Hermes vs Gateway) and to config field names/defaults. Mark applied findings.
Expected: `src/part2.py` edited.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 2, `<RANGE>` = `04-07`.
Expected: checks green; commit succeeds.

---

## Task 3: Part 3 — Hooks, adapters, and TdaiCore (lessons 08–11)

**Files:**
- Modify: `src/part3.py` (`LESSON_08`, `LESSON_09`, `LESSON_10`, `LESSON_11`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 3
- `<GUIDE_FILE>` = `src/part3.py`
- `<LESSON_LIST>` = `LESSON_08, LESSON_09, LESSON_10, LESSON_11`
- `<ANCHOR_LIST>` =
  - `index.ts`
  - `src/core/tdai-core.ts`
  - `src/adapters/openclaw/host-adapter.ts`
  - `src/adapters/standalone/host-adapter.ts`
  - `src/config.ts`

Expected: findings grouped by lesson, A/B/C buckets, bucket-A citations.

- [ ] **Step 2: Record findings**

Insert into `review_findings` with `part = 3`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

Confirm `TdaiCore` method names and the `HostAdapter` interface boundary in the cited files (the facade is the part most likely to drift). Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part3.py` (`zh`+`en` together), honoring Convention C3. Keep the host-neutral-core framing accurate to `tdai-core.ts` and the adapter files. Mark applied findings.
Expected: `src/part3.py` edited.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 3, `<RANGE>` = `08-11`.
Expected: checks green; commit succeeds.

---

## Task 4: Part 4 — L0 and L1: capture and atom extraction (lessons 12–16)

**Files:**
- Modify: `src/part4.py` (`LESSON_12` … `LESSON_16`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 4
- `<GUIDE_FILE>` = `src/part4.py`
- `<LESSON_LIST>` = `LESSON_12, LESSON_13, LESSON_14, LESSON_15, LESSON_16`
- `<ANCHOR_LIST>` =
  - `src/core/hooks/auto-capture.ts`
  - `src/core/conversation/l0-recorder.ts`
  - `src/utils/checkpoint.ts`
  - `src/core/record/l1-extractor.ts`
  - `src/core/record/l1-dedup.ts`
  - `src/core/record/l1-writer.ts`
  - `src/core/prompts/l1-extraction.ts`
  - `src/core/prompts/l1-dedup.ts`

Expected: findings grouped by lesson, A/B/C buckets, bucket-A citations.

- [ ] **Step 2: Record findings**

Insert into `review_findings` with `part = 4`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

This Part makes dense symbol-level claims (`performAutoCapture`, `captureAtomically`, `recordConversation`, `originalUserMessageCount`, `afterTimestamp`, `supportsDeferredEmbedding`, `notifyConversation`, L1 dedup/conflict). Confirm each named symbol exists and behaves as described in the cited file. Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part4.py` (`zh`+`en` together), honoring Convention C3. Keep the capture-vs-scheduler responsibility split and the sync-vs-deferred-embedding paths accurate. Mark applied findings.
Expected: `src/part4.py` edited.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 4, `<RANGE>` = `12-16`.
Expected: checks green; commit succeeds.

---

## Task 5: Part 5 — L2 and L3: scenes and persona (lessons 17–21)

**Files:**
- Modify: `src/part5.py` (`LESSON_17` … `LESSON_21`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 5
- `<GUIDE_FILE>` = `src/part5.py`
- `<LESSON_LIST>` = `LESSON_17, LESSON_18, LESSON_19, LESSON_20, LESSON_21`
- `<ANCHOR_LIST>` =
  - `src/core/scene/scene-extractor.ts`
  - `src/core/scene/scene-index.ts`
  - `src/core/scene/scene-navigation.ts`
  - `src/core/scene/scene-format.ts`
  - `src/core/persona/persona-generator.ts`
  - `src/core/persona/persona-trigger.ts`
  - `src/utils/pipeline-manager.ts`
  - `src/utils/pipeline-factory.ts`

Tell the subagent explicitly: confirm the lesson-17 scene metadata fields are exactly `{created, updated, summary, heat}` and that `evidence` is NOT a parsed metadata field in `scene-format.ts#parseSceneBlock`.

Expected: findings grouped by lesson, A/B/C buckets, bucket-A citations.

- [ ] **Step 2: Record findings**

Insert into `review_findings` with `part = 5`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

Confirm `SceneExtractor` sandbox/file-writing tools, scene index/navigation/backup behavior, and `PersonaGenerator` incremental update logic in the cited files. Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part5.py` (`zh`+`en` together), honoring Convention C3 — including the lesson-17 invariants enforced by `check_lesson17_scene_metadata_source`. Mark applied findings.
Expected: `src/part5.py` edited; lesson-17 metadata table still exactly `{created, updated, summary, heat}`.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 5, `<RANGE>` = `17-21`.
Expected: checks green (including the lesson-17 special check); commit succeeds.

---

## Task 6: Part 6 — Recall, search, and storage (lessons 22–26)

**Files:**
- Modify: `src/part6.py` (`LESSON_22` … `LESSON_26`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 6
- `<GUIDE_FILE>` = `src/part6.py`
- `<LESSON_LIST>` = `LESSON_22, LESSON_23, LESSON_24, LESSON_25, LESSON_26`
- `<ANCHOR_LIST>` =
  - `src/core/hooks/auto-recall.ts`
  - `src/core/tools/memory-search.ts`
  - `src/core/tools/conversation-search.ts`
  - `src/core/store/sqlite.ts`
  - `src/core/store/search-utils.ts`
  - `src/core/store/factory.ts`
  - `src/core/store/embedding.ts`
  - `src/core/store/bm25-local.ts`
  - `src/core/store/tcvdb.ts`

Tell the subagent explicitly: flag any place the guide blurs the SQLite (+ sqlite-vec / FTS / BM25 / hybrid) backend vs the Tencent Cloud VectorDB backend; these must be described per-backend.

Expected: findings grouped by lesson, A/B/C buckets, bucket-A citations.

- [ ] **Step 2: Record findings**

Insert into `review_findings` with `part = 6`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

Confirm recall-budgeting, hybrid-search scoring, and the SQLite-vs-TCVDB differences in the cited store files. Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part6.py` (`zh`+`en` together), honoring Convention C3. Keep every backend-specific claim attributed to the right backend. Mark applied findings.
Expected: `src/part6.py` edited.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 6, `<RANGE>` = `22-26`.
Expected: checks green; commit succeeds.

---

## Task 7: Part 7 — Context Offload: short-term symbolic memory (lessons 27–31)

**Files:**
- Modify: `src/part7.py` (`LESSON_27` … `LESSON_31`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 7
- `<GUIDE_FILE>` = `src/part7.py`
- `<LESSON_LIST>` = `LESSON_27, LESSON_28, LESSON_29, LESSON_30, LESSON_31`
- `<ANCHOR_LIST>` =
  - `src/offload/index.ts`
  - `src/offload/storage.ts`
  - `src/offload/hooks/after-tool-call.ts`
  - `src/offload/hooks/before-prompt-build.ts`
  - `src/offload/hooks/llm-output.ts`
  - `src/offload/local-llm/index.ts`
  - `src/offload/pipelines/l2-mermaid.ts`
  - `src/offload/mmd-injector.ts`
  - `src/offload/l3-helpers.ts`
  - `src/offload/hooks/llm-input-l3.ts`
  - `src/offload/local-llm/prompts/` and `src/offload/local-llm/parsers/` (for the lesson-29 contract below)

Tell the subagent explicitly: confirm the lesson-29 local-LLM contract anchors required by `check_lesson29_local_llm_contract` — `LocalLlmClient.l1Summarize`, `LocalLlmClient.l15Judge`, `LocalLlmClient.l2Generate`, the six `prompts/` + `parsers/` file paths, `node_mapping`, and the distinct `L1 input` / `L1.5 input` / `L2 input` markers. Also keep the long-term L2/L3 (scenes/persona) distinct from Offload-L2/L3 (MMD/symbolic context).

Expected: findings grouped by lesson, A/B/C buckets, bucket-A citations.

- [ ] **Step 2: Record findings**

Insert into `review_findings` with `part = 7`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

Confirm the offload pipeline order (refs → offload JSONL → Offload-L1/L1.5/L2 → MMD `node_id` → Offload-L3 injection), the `node_id` drill-down recovery path, and emergency-compression behavior in the cited files. Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part7.py` (`zh`+`en` together), honoring Convention C3 — including the lesson-29 anchors/markers. Mark applied findings.
Expected: `src/part7.py` edited; lesson-29 required anchors still present in both languages.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 7, `<RANGE>` = `27-31`.
Expected: checks green (including the lesson-29 special check); commit succeeds.

---

## Task 8: Part 8 — Ecosystem, operations, debugging, contribution (lessons 32–34)

**Files:**
- Modify: `src/part8.py` (`LESSON_32`, `LESSON_33`, `LESSON_34`)
- Modify (only if a quiz is factually wrong): `src/quizzes.py`
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Dispatch the verification subagent (verify only)**

`task` tool: `agent_type: "explore"`, `model: "claude-opus-4.8"`, `mode: "background"`. Fill Convention C2 with:
- `<PART>` = 8
- `<GUIDE_FILE>` = `src/part8.py`
- `<LESSON_LIST>` = `LESSON_32, LESSON_33, LESSON_34`
- `<ANCHOR_LIST>` =
  - `src/gateway/server.ts`
  - `src/gateway/config.ts`
  - `src/cli/commands/seed.ts`
  - `src/core/seed/seed-runtime.ts`
  - `scripts/README.memory-tencentdb-ctl.md`
  - `scripts/migrate-sqlite-to-tcvdb/README.md`
  - `CONTRIBUTING.md`
  - `CONTRIBUTING_CN.md`
  - `vitest.config.ts`

Tell the subagent explicitly: verify gateway HTTP endpoint paths and security knobs (`src/gateway/config.ts`), the exact seed/migration/export/read CLI command invocations, the test command(s) from `vitest.config.ts`/CONTRIBUTING, and that the glossary terms match the symbols used elsewhere in the guide.

Expected: findings grouped by lesson, A/B/C buckets, bucket-A citations.

- [ ] **Step 2: Record findings**

Insert into `review_findings` with `part = 8`. Expected: rows inserted.

- [ ] **Step 3: Verify every bucket-A citation against source**

Open the gateway, seed, and scripts files and confirm endpoint paths, command names/flags, and config knobs verbatim — operational commands must be copy-pasteable and correct. Reject unsupported findings.
Expected: confirmed bucket-A set.

- [ ] **Step 4: Apply corrections + polish + enhancements**

Edit `src/part8.py` (`zh`+`en` together), honoring Convention C3. Mark applied findings.
Expected: `src/part8.py` edited.

- [ ] **Step 5: Validate and commit**

Run Convention C4 with `<PART>` = 8, `<RANGE>` = `32-34`.
Expected: checks green; commit succeeds.

---

## Task 9: Final whole-guide accuracy review (Opus 4.8 max, long context)

**Files:**
- Modify: any `src/partN.py` needed to fix issues the review confirms
- Validate: `src/check_html.py`, `src/check_links.py`

- [ ] **Step 1: Produce the full diff of the pass**

Run (use the base commit SHA recorded in Task 0 Step 3 as `<BASE>`):
```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide
git diff <BASE>..HEAD -- src/part1.py src/part2.py src/part3.py src/part4.py src/part5.py src/part6.py src/part7.py src/part8.py src/quizzes.py > /tmp/accuracy-pass.diff
wc -l /tmp/accuracy-pass.diff
```
Expected: a non-empty diff covering the edited Part files.

- [ ] **Step 2: Dispatch the final review subagent**

Use the `task` tool: `agent_type: "general-purpose"`, `model: "claude-opus-4.8"`, `reasoning_effort: "max"`, `context_tier: "long_context"`, `mode: "background"`. Prompt:

```
You are the final accuracy reviewer for a learning guide that was just revised against its source project. DO NOT edit any file — report only.

SOURCE PROJECT (ground truth): /home/verden/course/TencentDB-Agent-Memory
GUIDE REPO: /home/verden/course/tencentdb-agent-memory-visual-guide
DIFF OF THE PASS: /tmp/accuracy-pass.diff  (git diff of src/part*.py + quizzes.py)

Review the entire diff and the current state of src/part1.py..part8.py for:
1. Accuracy regressions — any newly written claim that contradicts the source. Open the source file and confirm. Cite path#symbol.
2. zh/en equivalence — every lesson's Chinese and English must convey the same facts; flag any place an edit landed in one language only or where they now disagree.
3. Voice/terminology consistency — flag terms that are now used inconsistently across lessons.
4. Invariant risks — any edited <pre> with an unescaped '<', any "第 N 课" outside 1..34, any lesson that looks like it dropped its key-points/analogy card or fell below 6 visual blocks, and (lesson 17) the scene metadata fields must remain exactly {created, updated, summary, heat}, (lesson 29) the local-LLM anchors must remain present.

Return a prioritized list. For each item: lesson, severity (must-fix / nice-to-have), the problem, the source citation (for accuracy items), and the concrete fix. Be high signal — only real problems.
```

Expected: a prioritized issue list.

- [ ] **Step 3: Fix every must-fix item**

For each confirmed must-fix, edit the relevant `src/partN.py` (`zh`+`en` together) honoring Convention C3. For nice-to-have items, apply if they clearly help. Update `review_findings` (`status='applied'`) for anything fixed.
Expected: all must-fix items resolved in source.

- [ ] **Step 4: Validate and commit the review fixes**

Run:
```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide/src
python3 build.py && python3 check_html.py && python3 check_links.py
cd .. && git add -A && git commit -m "docs: final accuracy-review fixes across lessons

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```
Expected: `structural check passed` (0 errors); all links resolve; commit succeeds. If the review found nothing to fix, skip the commit and note "no changes" in the report.

---

## Task 10: Acceptance & final report

**Files:**
- Modify: none (validation + reporting)

- [ ] **Step 1: Full acceptance build + validation**

Run:
```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide/src
python3 build.py && python3 build_print.py && python3 check_html.py && python3 check_links.py
cd .. && git status --short
```
Expected: `check_html.py` → `structural check passed`, `0 error(s)`; `check_links.py` → `all N internal links resolve`; `git status --short` empty (zero drift). Fix and re-commit if any check is red.

- [ ] **Step 2: Confirm coverage invariants held**

Run:
```bash
cd /home/verden/course/tencentdb-agent-memory-visual-guide
ls lessons/*.html | wc -l                 # expect 34
grep -c "quiz" lessons/*.html | grep -c ":0" || true   # expect 0 lessons with no quiz block
```
Expected: 34 lessons; every lesson still has a quiz; registry↔PAGES alignment implicitly confirmed by a green `check_html.py`.

- [ ] **Step 3: Compile the final report from the findings tracker**

Run summary queries against `review_findings`:
```sql
SELECT part, bucket, COUNT(*) FROM review_findings GROUP BY part, bucket ORDER BY part, bucket;
SELECT lesson, claim, source_citation, suggested_change
FROM review_findings WHERE bucket='A_inaccuracy' AND status='applied' ORDER BY part, lesson;
```
Build a report with: base commit SHA → final commit SHA; per-Part counts of inaccuracies fixed / polish applied / enhancements added; the full list of bucket-A inaccuracies fixed with their source citations; and confirmation that all acceptance checks are green.

- [ ] **Step 4: Deliver the report to the user**

Present the final report in chat (concise summary + the inaccuracy table). Do not create a markdown file unless the user asks for one.
Expected: user receives the completion report; pass is done.

---

## Self-Review (completed during planning)

- **Spec coverage:** Goal/§1 → Tasks 1–8 (all 34 lessons, both langs, accuracy+polish+enhancements); Approach B/§3 → per-Part verify(subagent)+author(main)+validate, Task 9 final Opus review, Task 10 acceptance+report; Verification contract/§4 → C2 prompt + Step 3 citation re-check in every Part; Edit-safety/§5 → C3 + per-Part validation C4; Build commands/§6 → C4 + Tasks 0/10; Non-goals/§7 → stated in C2/C3 and task notes; Acceptance/§9 → Task 10. No gaps.
- **Placeholder scan:** `<PART>`/`<RANGE>`/`<BASE>` are explicit fill-in parameters defined per task, not TODOs; every code/command step shows the actual command or prompt. No "TBD/handle edge cases/similar to Task N".
- **Type/name consistency:** lesson→file→constant mapping matches `registry.py`; special-check names (`check_lesson17_scene_metadata_source`, `check_lesson29_local_llm_contract`) and required anchors match `check_html.py`; subagent dispatch params (`agent_type`, `model`, `reasoning_effort`, `context_tier`, `mode`) are consistent across tasks.
