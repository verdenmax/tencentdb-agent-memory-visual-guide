# TencentDB Agent Memory Visual Guide — Accuracy Review & Polish Pass (Design Spec)

> Status: design approved by user (2026-06-25); awaiting user review of this written spec before implementation planning.
> Date: 2026-06-25
> Guide repository: `/home/verden/course/tencentdb-agent-memory-visual-guide`
> Source project explained by the guide: `/home/verden/course/TencentDB-Agent-Memory`
> Predecessor spec: `docs/superpowers/specs/2026-06-23-tencentdb-agent-memory-visual-guide-design.md`

---

## 1. Goal

The guide's 7 milestones (M0–M6) are complete: 34 lessons across 8 parts, bilingual, with passing
build/HTML/link/drift checks. This pass raises two qualities without changing scope or curriculum:

1. **Accuracy** — every behavioral, symbol-level, path, ordering, config-field, and backend
   (SQLite vs TCVDB) claim is verified against the *current* `TencentDB-Agent-Memory` source.
2. **Learning quality** — deep prose polish plus targeted enhancements (diagrams, pseudocode,
   expanded thin sections) where they improve a beginner's understanding.

Coverage is **all 34 lessons**, **both languages** (Chinese + English kept information-equivalent),
with build / `check_html` / `check_links` / drift staying green throughout.

## 2. Key decisions

| Decision | Result |
| --- | --- |
| Coverage | All 34 lessons, full per-lesson source verification |
| Change scope | Accuracy fixes + deep polish + enhancements (add diagrams/pseudocode/expand weak sections) |
| Languages | Edit `zh` and `en` together; keep them information-equivalent |
| Execution model | Approach B: subagent parallel verification + author (main agent) applies edits + Opus final review |
| Cadence | Advance Part by Part without stopping for per-Part review; one final report at the end |
| Subagent model | All subagents use the current main model `claude-opus-4.8`; final review uses Opus 4.8 max reasoning + long context |
| Out of scope | No new features/backends, no unrelated refactors, no rewrite, no curriculum/Part-structure changes |

## 3. Execution workflow (Approach B)

Phased by the 8 curriculum parts. Phases run in order; within a phase, per-Part work parallelizes.

### Phase 0 — Baseline & guardrails
- Confirm a clean starting baseline: `build.py`, `build_print.py`, `check_html.py`, `check_links.py`
  all pass and `git status` is clean after rebuild (zero drift).
- Fix the structural-invariant checklist (see §5) as the editing contract.
- Build a per-lesson "source anchor → lesson fragment" map from the predecessor spec and `registry.py`.

### Phase 1 — Parallel verification (per Part; verify only, no edits)
- For each Part, dispatch one verification subagent (`claude-opus-4.8`) that reads the Part's anchor
  source files in `TencentDB-Agent-Memory` plus the current lesson fragments in `src/partN.py`.
- Each subagent returns a structured findings report with three buckets:
  - **(A) Inaccuracies** vs source — each with `path` + symbol citation and a suggested correction.
  - **(B) Polish issues** — awkward phrasing, terminology inconsistency, broken flow, zh/en mismatch.
  - **(C) Enhancement opportunities** — missing/weak diagram, missing pseudocode, thin section.
- Findings are recorded in the session SQL store for tracking.

### Phase 2 — Authoring (main agent; Part by Part, no stop)
- Apply corrections + polish + enhancements to `src/partN.py` (and `quizzes.py` if a quiz is wrong),
  editing `zh` and `en` together and preserving every structural invariant in §5.
- After each Part: rebuild (`build.py`), run `check_html.py` and `check_links.py`; keep generated
  HTML committed so drift stays zero.
- Before applying any subagent-suggested correction, verify its citation against the actual source.

### Phase 3 — Final review (one subagent: Opus 4.8 max + long context)
- Read the full `git diff` of the pass for: accuracy regressions, zh/en equivalence, voice
  consistency, and structural-invariant violations.
- The main agent fixes every confirmed item the review surfaces.

### Phase 4 — Acceptance & report
- Full rebuild + `build_print.py`; `check_html` (0 errors), `check_links` (all resolve), drift clean,
  quiz coverage intact (34/34).
- Deliver a final report: per-lesson summary of changes and the list of inaccuracies fixed with
  source citations.

## 4. Verification contract — what counts as an inaccuracy

A claim is an inaccuracy when any of these does not match current source:
- a symbol name (function/class/method/field), a file path, or a module boundary;
- a described behavior, control-flow, or ordering between stages;
- a configuration field that supposedly controls a behavior;
- a stated difference between the SQLite and Tencent Cloud VectorDB backends;
- a host-specific path (OpenClaw / Hermes / Gateway / standalone) attributed to the wrong host.

Every reported inaccuracy must cite source by `path` + symbol (not line number). Existing encoded
truths in `check_html.py` — the lesson 17 scene-metadata fields `{created, updated, summary, heat}`
and the lesson 29 local-LLM anchors/markers — are treated as established source truth: extend, do
not contradict them, unless the source itself proves them wrong, in which case the check is updated
in the same change.

## 5. Edit-safety rules (structural invariants enforced by `check_html.py`)

- Balanced `div` / `details` / `table` / `pre` / `summary`; `details` count == `summary` count.
- Exactly one `<h1>`; a `<title>` and a `meta description` per lesson.
- Both `lang-zh` and `lang-en` content present and information-equivalent; `zh` keeps ≥ 500 CJK chars.
- Inside `<pre>`, escape literal `<` / `>` as `&lt;` / `-&gt;` (inline tags span/strong/b/em/u/a allowed).
- Course references "第 N 课" must stay within 1..34.
- Keep ≥ 6 visual blocks per lesson (`layers/vflow/flow/cols/cellgroup/timeline/trace` or `table.t`)
  and preserve the key-points card and analogy card.
- nav prev/next chain matches `shell.PAGES`; index TOC + "共 N 课 · N 个部分" pill stay consistent.
- Do not modify `TencentDB-Agent-Memory` source; no large source copies; no secrets/credentials.
- Generated HTML is committed and re-running the build must produce no diff.

## 6. Build & validation commands

```bash
cd src
python3 build.py
python3 build_print.py
python3 check_html.py   # expect 0 errors
python3 check_links.py  # expect all internal links resolve
cd .. && git status --short   # expect clean (no drift) after rebuild
```

## 7. Non-goals

- No new dynamic/backend features, accounts, telemetry, or server-side search.
- No unrelated refactoring; stay within the static-site generator pattern.
- No rewrite of the guide and no change to the curriculum or Part boundaries.
- No modification of the `TencentDB-Agent-Memory` source project.

## 8. Risks & mitigations

| Risk | Mitigation |
| --- | --- |
| Edits break structural invariants | Rebuild + `check_html` + `check_links` after every Part |
| zh/en content drifts apart | Edit both languages together; final review checks equivalence |
| Subagent reports a wrong "fix" | Verify each citation against source before applying |
| Context blow-up on 34 lessons × 2 langs | Scope verification per Part; parallel subagents |
| Silent quiz/registry breakage | Acceptance checks quiz 34/34 and registry↔PAGES alignment |

## 9. Acceptance criteria

- All 34 lessons reviewed against source; every changed claim carries a source citation.
- `check_html.py` reports 0 errors; `check_links.py` reports all internal links resolve.
- Rebuild produces zero `git` drift; print editions build for both languages.
- Quiz coverage remains 34/34 and registry↔PAGES alignment holds.
- A final report is delivered summarizing per-lesson changes and fixed inaccuracies with citations.
