# TencentDB Agent Memory Visual Guide - Design Spec

> Status: design approved by user; awaiting user review of this written spec before implementation planning.
> Date: 2026-06-23
> Target guide repository: `/home/verden/course/tencentdb-agent-memory-visual-guide`
> Reference project: `/home/verden/course/llama-cpp-visual-guide`
> Source project explained by the guide: `/home/verden/course/TencentDB-Agent-Memory`

---

## 1. Goal and audience

Build a standalone visual, bilingual learning guide for TencentDB Agent Memory. The guide should help a complete beginner start from the first mental model - "what happens when an agent has a conversation?" - and gradually understand the whole project down to the main source files and symbols.

The teaching spine is **data-flow first**:

```text
User turn
  -> OpenClaw / Hermes hook
  -> TdaiCore
  -> L0 conversation capture
  -> L1 atom extraction
  -> L2 scene aggregation
  -> L3 persona generation
  -> next-turn recall/search injection
```

A second spine covers short-term context compression:

```text
Long task logs
  -> refs/*.md
  -> offload JSONL
  -> L1 / L1.5 / L2 Mermaid canvas
  -> L3 context injection
  -> drill down by node_id
```

### Audience

- Beginners who have never used TencentDB Agent Memory and need a clear visual path.
- Users who want to install and verify the plugin in OpenClaw or Hermes.
- Developers who want to read, debug, test, or contribute to the source code.

### Reader outcomes

By the end, a reader should be able to answer:

- What problem does TencentDB Agent Memory solve?
- How does a single conversation become layered long-term memory?
- How do L0, L1, L2, and L3 differ?
- How does recall decide what to inject before the next turn?
- How does context offload compress long task history without losing evidence?
- Which source files implement each stage?
- How do I configure, verify, debug, test, and contribute to the project?

---

## 2. Key decisions

| Decision | Result |
| --- | --- |
| Project location | New sibling repository: `/home/verden/course/tencentdb-agent-memory-visual-guide` |
| Architecture | Reuse the pure Python static-site generator pattern from `llama-cpp-visual-guide` |
| Curriculum route | Data-flow first, not module-list first |
| Scope | Medium-large guide, about 30-36 lessons |
| Language | Bilingual Chinese / English with page-level toggle and separate print editions |
| Content depth | Detailed teaching version: many diagrams, pseudocode, simplified source snippets, source indexes, quizzes |
| Companion features | Lesson quizzes, client-side catalog filtering/search, print HTML, HTML validation, link validation, GitHub Pages CI |
| Non-goals | No backend service, accounts, comments, dynamic search service, or changes to TencentDB-Agent-Memory source |

---

## 3. Site architecture

The guide is a standalone repository with committed generated HTML. It should be readable via `file://`, any static server, and GitHub Pages.

```text
tencentdb-agent-memory-visual-guide/
├── index.html
├── lessons/
│   ├── 01-why-agent-memory.html
│   └── ...
├── print_zh.html
├── print_en.html
├── src/
│   ├── shell.py
│   ├── registry.py
│   ├── part1.py
│   ├── part2.py
│   ├── part3.py
│   ├── part4.py
│   ├── part5.py
│   ├── part6.py
│   ├── part7.py
│   ├── part8.py
│   ├── quizzes.py
│   ├── build.py
│   ├── build_print.py
│   ├── check_html.py
│   └── check_links.py
├── .github/workflows/
│   ├── ci.yml
│   └── deploy.yml
├── README.md
├── LICENSE
└── LICENSE-CONTENT
```

### Generator design

- `src/shell.py` owns the shared CSS design system, page shell, bilingual toggle, navigation, table of contents, and print-friendly wrappers.
- `src/registry.py` is the single source of truth for lesson ordering and maps lesson filenames to bilingual content objects.
- `src/part1.py ... part8.py` store lesson HTML fragments grouped by curriculum part.
- `src/quizzes.py` stores per-lesson bilingual quiz data.
- `src/build.py` regenerates `index.html` and `lessons/*.html`.
- `src/build_print.py` regenerates `print_zh.html` and `print_en.html`.
- `src/check_html.py` validates structural HTML invariants.
- `src/check_links.py` validates internal links.

### Bilingual behavior

- Every lesson renders both Chinese and English content in the page.
- A top language toggle switches between `zh` and `en`.
- The chosen language persists across pages using `localStorage`.
- Chinese is the default first-visit language.
- English content must be information-equivalent, but it does not need to be a sentence-by-sentence translation.

### Visual style

The visual system should inherit the proven shape of `llama-cpp-visual-guide` but use a TencentDB Agent Memory theme:

- Layered memory and data-flow visuals as first-class page elements.
- Blue/green technology palette with memory-layer accents.
- Cards for macro understanding, source details, analogies, warnings, and key takeaways.
- Flow diagrams, vertical data-flow timelines, layer diagrams, comparison grids, code blocks, accordions, quizzes, and progress navigation.

---

## 4. Curriculum outline

The guide should have about 34 lessons across 8 parts. Exact lesson titles can still be refined during implementation, but the part boundaries and data-flow sequence are fixed.

### Part 1 - Why Agent Memory exists

Purpose: establish the problem, the two memory spines, and the whole-system map.

Candidate lessons:

1. Why agent memory is needed
2. Why flat vector memory is not enough
3. One conversation through the whole system

Core source/docs anchors:

- `README.md`
- `README_CN.md`
- `package.json`
- `index.ts`

### Part 2 - Minimal working loop

Purpose: help readers run and verify the system before reading internals.

Candidate lessons:

4. OpenClaw zero-config installation
5. Hermes / Gateway integration path
6. What files appear on disk after memory starts working
7. Configuration levels and safe defaults

Core source/docs anchors:

- `README_CN.md`
- `SKILL.md`
- `src/cli/README.md`
- `openclaw.plugin.json`
- `src/config.ts`
- `hermes-plugin/memory/memory_tencentdb/README.md`

### Part 3 - Hooks, adapters, and TdaiCore

Purpose: explain how host events enter a host-neutral core.

Candidate lessons:

8. `index.ts` as the OpenClaw plugin shell
9. `TdaiCore` as the host-neutral facade
10. `HostAdapter` and LLM runner boundaries
11. Runtime initialization, CLI metadata mode, and config parsing

Core source anchors:

- `index.ts`
- `src/core/tdai-core.ts`
- `src/adapters/openclaw/host-adapter.ts`
- `src/adapters/standalone/host-adapter.ts`
- `src/config.ts`

### Part 4 - L0 and L1: capture and atom extraction

Purpose: follow one turn from raw messages to structured L1 memory atoms.

Candidate lessons:

12. Auto-capture hook and incremental cursor
13. L0 JSONL format and sanitization
14. Checkpoints, race prevention, and duplicate avoidance
15. L1 extraction prompt and scene-segmented output
16. L1 dedup, conflict detection, and write path

Core source anchors:

- `src/core/hooks/auto-capture.ts`
- `src/core/conversation/l0-recorder.ts`
- `src/utils/checkpoint.ts`
- `src/core/record/l1-extractor.ts`
- `src/core/record/l1-dedup.ts`
- `src/core/record/l1-writer.ts`
- `src/core/prompts/l1-extraction.ts`
- `src/core/prompts/l1-dedup.ts`

### Part 5 - L2 and L3: scenes and persona

Purpose: explain how atom memories become durable scene blocks and an evolving user profile.

Candidate lessons:

17. Why L2 scene blocks exist
18. `SceneExtractor` and sandboxed file-writing tools
19. Scene index, scene navigation, and backups
20. `PersonaGenerator` and incremental profile updates
21. L2/L3 scheduling and trigger rules

Core source anchors:

- `src/core/scene/scene-extractor.ts`
- `src/core/scene/scene-index.ts`
- `src/core/scene/scene-navigation.ts`
- `src/core/scene/scene-format.ts`
- `src/core/persona/persona-generator.ts`
- `src/core/persona/persona-trigger.ts`
- `src/utils/pipeline-manager.ts`
- `src/utils/pipeline-factory.ts`

### Part 6 - Recall, search, and storage

Purpose: show how memory comes back into the next turn and how storage backends support it.

Candidate lessons:

22. Auto-recall before prompt build
23. L1 memory search and recall budgeting
24. L2 navigation plus L3 persona injection
25. SQLite, sqlite-vec, FTS, BM25, and hybrid search
26. Tencent Cloud VectorDB backend and embedding services

Core source anchors:

- `src/core/hooks/auto-recall.ts`
- `src/core/tools/memory-search.ts`
- `src/core/tools/conversation-search.ts`
- `src/core/store/sqlite.ts`
- `src/core/store/search-utils.ts`
- `src/core/store/factory.ts`
- `src/core/store/embedding.ts`
- `src/core/store/bm25-local.ts`
- `src/core/store/tcvdb.ts`

### Part 7 - Context Offload: short-term symbolic memory

Purpose: explain the second memory spine for long tasks and tool-log compression.

Candidate lessons:

27. Why long task logs need symbolic compression
28. `after-tool-call`, refs, and offload JSONL
29. L1 / L1.5 / L2 local LLM pipelines
30. Mermaid MMD canvas, `node_id`, and drill-down recovery
31. L3 context injection and emergency compression

Core source anchors:

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

### Part 8 - Ecosystem, operations, debugging, and contribution

Purpose: turn understanding into practical ability.

Candidate lessons:

32. Hermes Gateway, HTTP endpoints, and security knobs
33. Seed CLI, migration/export/read scripts, and operational workflows
34. Debugging checklist, tests, contribution path, and glossary

Core source/docs anchors:

- `src/gateway/server.ts`
- `src/gateway/config.ts`
- `src/cli/commands/seed.ts`
- `src/core/seed/seed-runtime.ts`
- `scripts/README.memory-tencentdb-ctl.md`
- `scripts/migrate-sqlite-to-tcvdb/README.md`
- `CONTRIBUTING.md`
- `CONTRIBUTING_CN.md`
- `vitest.config.ts`

---

## 5. Lesson page contract

Each lesson should be self-contained but visibly connected to the whole data flow.

Recommended structure:

1. Top navigation with progress, part label, lesson number, and language toggle.
2. Hero section with title and one-sentence promise.
3. "Where are we in the flow?" mini-map.
4. Macro explanation card.
5. Main visual diagram.
6. Step-by-step data flow.
7. Source correspondence section with file paths and symbols.
8. Pseudocode or simplified source snippets.
9. Deep-dive accordions for optional details.
10. Key takeaways.
11. Quiz.
12. Previous / next lesson links.

### Diagram requirements

- Use multiple diagrams per lesson when the concept is non-trivial.
- Prefer HTML/CSS diagrams and Mermaid-style text diagrams over external assets.
- Include at least one data-flow or layer-location visual in lessons about L0-L3 or offload.
- Use screenshots or external images only when necessary; keep pages self-contained by default.

### Code requirements

- Use pseudocode first when it clarifies the algorithm.
- Use simplified source snippets for correspondence, not long copied source blocks.
- Cite source by path and symbol, not fixed line number.
- Avoid secrets and real credentials in examples.

### Accuracy requirements

- Claims about behavior must be checked against the current source code or documentation.
- If a behavior depends on configuration, say which config field controls it.
- If a backend differs between SQLite and TCVDB, explain the difference explicitly.
- If a path is host-specific, name the host path: OpenClaw, Hermes, Gateway, or standalone.

---

## 6. Build, validation, and CI

### Local commands

```bash
cd src
python3 build.py
python3 build_print.py
python3 check_html.py
python3 check_links.py
```

Expected behavior:

- Generated HTML is committed and kept in sync with sources.
- Re-running the build should produce no diff.
- `check_html.py` should report zero structural errors.
- `check_links.py` should report no broken internal links.

### CI

Add GitHub Actions workflows:

- `ci.yml`: run build, print build, HTML validation, link validation, and generated-output drift check.
- `deploy.yml`: build and deploy to GitHub Pages when enabled by the repository owner.

The README should state that GitHub Pages needs one-time owner enablement: Settings -> Pages -> Source: GitHub Actions.

---

## 7. Milestones

Each milestone should be independently buildable and reviewable in a browser.

| Milestone | Scope |
| --- | --- |
| M0 - Scaffold | Create repository skeleton, shell, registry, build scripts, checks, README, licenses, and 1-2 representative lessons |
| M1 - Parts 1-2 | Data-flow overview plus minimal OpenClaw/Hermes usage loop |
| M2 - Parts 3-4 | Hooks, adapters, TdaiCore, L0 capture, L1 extraction |
| M3 - Parts 5-6 | L2 scenes, L3 persona, recall/search/store backends |
| M4 - Part 7 | Context offload, refs, MMD, node_id drill-down, L3 compression |
| M5 - Part 8 | Gateway, seed CLI, operations, debugging, testing, contribution, glossary |
| M6 - Final polish | Fill quiz coverage, print editions, CI, README badges, link/HTML/drift validation |

---

## 8. Non-goals

- Do not add dynamic backend services.
- Do not add accounts, comments, telemetry, or server-side search; any search/filtering is static client-side page behavior.
- Do not modify TencentDB-Agent-Memory source as part of the guide.
- Do not copy large blocks of source code.
- Do not publish secrets, API keys, tokens, or real production credentials.
- Do not make the first implementation milestone responsible for writing all 30-36 lessons.

---

## 9. Success criteria

- A beginner can follow the guide from installation to internal source understanding.
- The data-flow spine remains visible throughout the guide.
- Every major subsystem has diagrams, pseudocode or simplified code, and source anchors.
- The site works from `file://` and from GitHub Pages.
- Bilingual toggle persists across pages.
- Print editions build for both Chinese and English.
- HTML and internal links validate in CI.
- Generated HTML stays in sync with `src/`.
