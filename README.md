# TencentDB Agent Memory Visual Guide / TencentDB Agent Memory 图解学习指南

[![CI](https://github.com/verdenmax/tencentdb-agent-memory-visual-guide/actions/workflows/ci.yml/badge.svg)](https://github.com/verdenmax/tencentdb-agent-memory-visual-guide/actions/workflows/ci.yml)
[![Pages workflow](https://github.com/verdenmax/tencentdb-agent-memory-visual-guide/actions/workflows/pages.yml/badge.svg)](https://github.com/verdenmax/tencentdb-agent-memory-visual-guide/actions/workflows/pages.yml)
[![Lessons](https://img.shields.io/badge/lessons-34-0f766e)](#lesson-table)
[![Parts](https://img.shields.io/badge/parts-8-7048e8)](#what-it-covers)
[![Built with Python 3](https://img.shields.io/badge/built%20with-Python%203-3776AB?logo=python&logoColor=white)](#build--validate)
[![Dependencies](https://img.shields.io/badge/dependencies-0-2b8a3e)](#build--validate)
[![Code: MIT](https://img.shields.io/badge/code-MIT-blue.svg)](LICENSE)
[![Content: CC BY 4.0](https://img.shields.io/badge/content-CC_BY_4.0-blue.svg)](LICENSE-CONTENT)

A visual, bilingual (English + 中文) guide to [TencentDB Agent Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory). The guide contains **34 lessons across 8 parts**, starting from one conversation's data flow and building up to L0-L3 long-term memory, recall/search, context offload, gateway operations, and contribution workflows.

> **Disclaimer:** This is third-party, unofficial educational material about TencentDB Agent Memory. It contains no TencentDB-Agent-Memory source code; it explains the project with diagrams, pseudocode, and small cited source references. TencentDB Agent Memory is licensed by its own authors/repository.

Every lesson is self-contained, embeds both languages (toggle in the page), and uses diagrams, worked-example traces, cited source anchors, key points, analogies, and a short self-test quiz.

---

## What it covers

The guide is organized into eight parts that build up step by step:

| Part | Topic | Lessons |
| --- | --- | --- |
| 1 | Part 1 · Data-flow overview / 第一部分 · 数据流全景 | L01-L03 |
| 2 | Part 2 · Minimal working loop / 第二部分 · 最小运行闭环 | L04-L07 |
| 3 | Part 3 · Hooks, adapters, and TdaiCore / 第三部分 · Hooks、Adapters 与 TdaiCore | L08-L11 |
| 4 | Part 4 · L0 and L1: capture, extraction, dedup / 第四部分 · L0 与 L1：捕获、抽取、去重 | L12-L16 |
| 5 | Part 5 · L2/L3: scene and persona memory / 第五部分 · L2/L3：场景与画像记忆 | L17-L21 |
| 6 | Part 6 · Recall, search, and storage / 第六部分 · Recall、Search 与 Store | L22-L26 |
| 7 | Part 7 · Context Offload: short-term symbolic memory / 第七部分 · Context Offload：短期符号记忆 | L27-L31 |
| 8 | Part 8 · Ecosystem, operations, debugging, and glossary / 第八部分 · 生态、运维、调试与词汇表 | L32-L34 |

## How to read locally

Open the committed HTML directly, or regenerate it first:

```bash
cd src
python3 build.py
# then open ../index.html in a browser
```

The generated pages use relative links, so they work from `file://` and from any static web server.

## How to print / export a PDF

```bash
cd src
python3 build_print.py
# open ../print_zh.html (Chinese) or ../print_en.html (English) in a browser,
# then File -> Print -> Save as PDF (Ctrl/Cmd+P). Each lesson starts on a new page.
```

## Build & validate

```bash
cd src
python3 build.py          # regenerate index.html + lessons/*.html
python3 build_print.py    # regenerate print_zh.html + print_en.html
python3 check_html.py     # structural HTML validation
python3 check_links.py    # internal relative links must resolve
```

Generated HTML is committed and kept in sync with `src/`. Re-running the build and print commands should not produce a diff in `index.html`, `lessons/`, `print_zh.html`, or `print_en.html`.

## GitHub Pages

This repository is ready for GitHub Pages once it is published on GitHub:

1. Open repository **Settings → Pages**.
2. Set **Source** to **GitHub Actions**.
3. Run the **Deploy GitHub Pages** workflow, or push to `main` or `master`.

The README intentionally does not publish a live Pages URL until the guide repository exists on GitHub.

## Lesson table

| Lesson | Part | Topic | Page |
| --- | --- | --- | --- |
| 01 | 1 | Why Agent Memory / 为什么需要 Agent Memory | [`lessons/01-why-agent-memory.html`](lessons/01-why-agent-memory.html) |
| 02 | 1 | The data flow of one conversation / 一次对话的数据流 | [`lessons/02-one-conversation-flow.html`](lessons/02-one-conversation-flow.html) |
| 03 | 1 | Two memory spines / 两条记忆主线 | [`lessons/03-two-memory-spines.html`](lessons/03-two-memory-spines.html) |
| 04 | 2 | OpenClaw zero-config loop / OpenClaw 零配置闭环 | [`lessons/04-openclaw-zero-config.html`](lessons/04-openclaw-zero-config.html) |
| 05 | 2 | Hermes and Gateway path / Hermes 与 Gateway 路径 | [`lessons/05-hermes-gateway-path.html`](lessons/05-hermes-gateway-path.html) |
| 06 | 2 | Runtime files and data products / 运行后会出现哪些文件 | [`lessons/06-runtime-files.html`](lessons/06-runtime-files.html) |
| 07 | 2 | Configuration levels and safe defaults / 配置层级与安全默认值 | [`lessons/07-config-levels.html`](lessons/07-config-levels.html) |
| 08 | 3 | index.ts: the OpenClaw plugin shell / index.ts：OpenClaw 插件壳 | [`lessons/08-openclaw-plugin-shell.html`](lessons/08-openclaw-plugin-shell.html) |
| 09 | 3 | TdaiCore: host-neutral facade / TdaiCore：宿主无关核心门面 | [`lessons/09-tdai-core-facade.html`](lessons/09-tdai-core-facade.html) |
| 10 | 3 | HostAdapter and LLMRunner boundaries / HostAdapter 与 LLMRunner 边界 | [`lessons/10-host-adapter-boundaries.html`](lessons/10-host-adapter-boundaries.html) |
| 11 | 3 | Runtime init and config parsing / 运行时初始化与配置解析 | [`lessons/11-runtime-init-config.html`](lessons/11-runtime-init-config.html) |
| 12 | 4 | Auto Capture after a turn commits / Auto Capture：对话提交后的捕获 | [`lessons/12-auto-capture-hook.html`](lessons/12-auto-capture-hook.html) |
| 13 | 4 | L0 JSONL: raw conversation evidence / L0 JSONL：原始对话证据层 | [`lessons/13-l0-jsonl-recorder.html`](lessons/13-l0-jsonl-recorder.html) |
| 14 | 4 | Checkpoints: cursors, locks, and duplicate prevention / Checkpoint：游标、锁与防重复 | [`lessons/14-checkpoints-races.html`](lessons/14-checkpoints-races.html) |
| 15 | 4 | L1 extraction: conversation to memory atoms / L1 抽取：从对话到原子记忆 | [`lessons/15-l1-extraction.html`](lessons/15-l1-extraction.html) |
| 16 | 4 | L1 dedup, conflict detection, and write path / L1 去重、冲突检测与写入 | [`lessons/16-l1-dedup-write.html`](lessons/16-l1-dedup-write.html) |
| 17 | 5 | Why L2 scene blocks exist / 为什么需要 L2 Scene Blocks | [`lessons/17-why-l2-scene-blocks.html`](lessons/17-why-l2-scene-blocks.html) |
| 18 | 5 | SceneExtractor and sandboxed file-writing tools / SceneExtractor 与沙箱文件写入工具 | [`lessons/18-scene-extractor-sandbox.html`](lessons/18-scene-extractor-sandbox.html) |
| 19 | 5 | Scene index, navigation, and backups / Scene index、导航与备份 | [`lessons/19-scene-index-navigation-backups.html`](lessons/19-scene-index-navigation-backups.html) |
| 20 | 5 | PersonaGenerator and incremental profile updates / PersonaGenerator 与增量画像更新 | [`lessons/20-persona-generator-incremental.html`](lessons/20-persona-generator-incremental.html) |
| 21 | 5 | L2/L3 scheduling and trigger rules / L2/L3 调度与触发规则 | [`lessons/21-l2-l3-scheduling-triggers.html`](lessons/21-l2-l3-scheduling-triggers.html) |
| 22 | 6 | Auto-recall before prompt build / Prompt 构建前的 Auto Recall | [`lessons/22-auto-recall-before-prompt.html`](lessons/22-auto-recall-before-prompt.html) |
| 23 | 6 | L1 memory search and recall budgeting / L1 记忆搜索与召回预算 | [`lessons/23-l1-search-recall-budget.html`](lessons/23-l1-search-recall-budget.html) |
| 24 | 6 | L2 navigation plus L3 persona injection / L2 导航与 L3 Persona 注入 | [`lessons/24-l2-navigation-l3-persona-injection.html`](lessons/24-l2-navigation-l3-persona-injection.html) |
| 25 | 6 | SQLite, sqlite-vec, FTS, BM25, and hybrid search / SQLite、sqlite-vec、FTS、BM25 与混合搜索 | [`lessons/25-sqlite-vec-fts-bm25-hybrid.html`](lessons/25-sqlite-vec-fts-bm25-hybrid.html) |
| 26 | 6 | Tencent Cloud VectorDB backend and embedding services / 腾讯云 VectorDB 后端与 Embedding 服务 | [`lessons/26-tencent-vectordb-embedding.html`](lessons/26-tencent-vectordb-embedding.html) |
| 27 | 7 | Why long task logs need symbolic compression / 为什么长任务日志需要符号压缩 | [`lessons/27-why-long-task-logs-symbolic-compression.html`](lessons/27-why-long-task-logs-symbolic-compression.html) |
| 28 | 7 | after-tool-call, refs, and offload JSONL / after-tool-call、refs 与 offload JSONL | [`lessons/28-after-tool-call-refs-offload-jsonl.html`](lessons/28-after-tool-call-refs-offload-jsonl.html) |
| 29 | 7 | L1 / L1.5 / L2 local LLM pipelines / L1 / L1.5 / L2 本地 LLM 管线 | [`lessons/29-l1-l15-l2-local-llm-pipelines.html`](lessons/29-l1-l15-l2-local-llm-pipelines.html) |
| 30 | 7 | Mermaid MMD canvas, node_id, and drill-down recovery / Mermaid MMD 画布、node_id 与下钻恢复 | [`lessons/30-mermaid-mmd-node-id-drill-down.html`](lessons/30-mermaid-mmd-node-id-drill-down.html) |
| 31 | 7 | L3 context injection and emergency compression / L3 上下文注入与紧急压缩 | [`lessons/31-l3-context-injection-emergency-compression.html`](lessons/31-l3-context-injection-emergency-compression.html) |
| 32 | 8 | Hermes Gateway, HTTP endpoints, and security knobs / Hermes Gateway、HTTP 端点与安全开关 | [`lessons/32-hermes-gateway-http-security.html`](lessons/32-hermes-gateway-http-security.html) |
| 33 | 8 | Seed CLI, migration/export/read scripts, and operational workflows / Seed CLI、迁移/导出/读取脚本与运维工作流 | [`lessons/33-seed-cli-migration-export-read.html`](lessons/33-seed-cli-migration-export-read.html) |
| 34 | 8 | Debugging checklist, tests, contribution path, and glossary / 调试清单、测试、贡献路径与词汇表 | [`lessons/34-debug-tests-contribution-glossary.html`](lessons/34-debug-tests-contribution-glossary.html) |

## Project structure

```text
tencentdb-agent-memory-visual-guide/
├── index.html              generated table of contents (committed)
├── lessons/                generated lesson pages (34 committed HTML files)
├── print_zh.html           generated Chinese print edition
├── print_en.html           generated English print edition
├── src/                    pure Python 3 generator and validation tooling
│   ├── shell.py            page shell, shared CSS, bilingual toggle, lesson order
│   ├── part1.py … part8.py lesson content, one module per part
│   ├── quizzes.py          bilingual per-lesson self-test questions
│   ├── registry.py         ordered filename-to-content map
│   ├── build.py            builds index.html + lessons/*.html
│   ├── build_print.py      builds print_zh.html + print_en.html
│   ├── check_html.py       structural HTML and guide invariant checks
│   └── check_links.py      internal relative link validation
├── .github/workflows/
│   ├── ci.yml              build, validation, scans, and drift checks
│   └── pages.yml           GitHub Pages artifact build and deployment workflow
├── docs/superpowers/specs/ approved design spec
├── LICENSE                 MIT license for code
└── LICENSE-CONTENT         CC BY 4.0 license for educational content
```

## License

Dual-licensed:

- **Code** (the Python generators and validation scripts under `src/`) is MIT licensed; see [LICENSE](LICENSE).
- **Content** (the lesson text and diagrams rendered into `index.html`, `lessons/*.html`, `print_*.html`) is CC BY 4.0 licensed; see [LICENSE-CONTENT](LICENSE-CONTENT).

---

## 中文说明

这是一份 [TencentDB Agent Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory) 的**图解、双语**学习指南。指南包含 **8 个部分、34 课**，从一次对话的数据流讲起，逐步覆盖 L0-L3 长期记忆、召回与搜索、上下文卸载、Gateway 运维以及调试/贡献流程。

> **声明：** 本项目是第三方、非官方学习材料，不包含 TencentDB-Agent-Memory 源码；仅通过图解、伪代码和少量标注来源的引用来讲解。TencentDB Agent Memory 本身由其作者/仓库按其许可证发布。

**本地阅读：** `cd src && python3 build.py`，然后用浏览器打开 `../index.html`。

**打印导出：** `cd src && python3 build_print.py`，打开 `../print_zh.html` 或 `../print_en.html` 后用浏览器打印为 PDF。

**许可：** 双许可 —— `src/` 下代码使用 MIT；课程文字与图解内容使用 CC BY 4.0。
