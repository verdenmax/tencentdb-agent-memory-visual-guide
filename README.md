# TencentDB Agent Memory Visual Guide / TencentDB Agent Memory 图解学习指南

A visual, bilingual (中文 + English) guide to [TencentDB Agent Memory](https://github.com/TencentCloud/TencentDB-Agent-Memory). It starts from one conversation's data flow and is planned to build up to L0-L3 long-term memory, recall/search, context offload, and host integration.

> This is standalone educational material about TencentDB Agent Memory. It explains the project with diagrams, pseudocode, and small cited source references.

## Current lessons

The guide currently contains 20 lessons.

| Lesson | Topic |
| --- | --- |
| 01 | Why Agent Memory |
| 02 | The data flow of one conversation |
| 03 | Two memory spines |
| 04 | OpenClaw zero-config loop |
| 05 | Hermes and Gateway path |
| 06 | Runtime files and data products |
| 07 | Configuration levels and safe defaults |
| 08 | index.ts: the OpenClaw plugin shell |
| 09 | TdaiCore: host-neutral facade |
| 10 | HostAdapter and LLMRunner boundaries |
| 11 | Runtime init and config parsing |
| 12 | Auto Capture after a turn commits |
| 13 | L0 JSONL: raw conversation evidence |
| 14 | Checkpoints: cursors, locks, and duplicate prevention |
| 15 | L1 extraction: conversation to memory atoms |
| 16 | L1 dedup, conflict detection, and write path |
| 17 | Why L2 scene blocks exist |
| 18 | SceneExtractor and sandboxed file-writing tools |
| 19 | Scene index, navigation, and backups |
| 20 | PersonaGenerator and incremental profile updates |

## How to view locally

```bash
cd src
python3 build.py
# open ../index.html in a browser
```

## How to print

```bash
cd src
python3 build_print.py
# open ../print_zh.html or ../print_en.html, then print to PDF in a browser
```

## Validate

```bash
cd src
python3 build.py
python3 build_print.py
python3 check_html.py
python3 check_links.py
```

Generated HTML is committed and kept in sync with `src/`. Re-running the build should not produce a diff.

## Project structure

```text
src/             pure Python generator and lesson sources
lessons/         generated lesson pages
index.html       generated table of contents
print_zh.html    generated Chinese print edition
print_en.html    generated English print edition
docs/superpowers/specs/ approved design spec
```

## License

- Code under `src/` is MIT licensed; see `LICENSE`.
- Educational content is CC BY 4.0 licensed; see `LICENSE-CONTENT`.
