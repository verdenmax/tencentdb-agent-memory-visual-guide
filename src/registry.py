"""Single source of truth: ordered map of output filename -> bilingual content."""
import part1
import part2
import part3
import part4
import part5
import part6
import part7
import part8

CONTENT = {
    "01-why-agent-memory.html": part1.LESSON_01,
    "02-one-conversation-flow.html": part1.LESSON_02,
    "03-two-memory-spines.html": part1.LESSON_03,
    "04-openclaw-zero-config.html": part2.LESSON_04,
    "05-hermes-gateway-path.html": part2.LESSON_05,
    "06-runtime-files.html": part2.LESSON_06,
    "07-config-levels.html": part2.LESSON_07,
    "08-openclaw-plugin-shell.html": part3.LESSON_08,
    "09-tdai-core-facade.html": part3.LESSON_09,
    "10-host-adapter-boundaries.html": part3.LESSON_10,
    "11-runtime-init-config.html": part3.LESSON_11,
    "12-auto-capture-hook.html": part4.LESSON_12,
    "13-l0-jsonl-recorder.html": part4.LESSON_13,
    "14-checkpoints-races.html": part4.LESSON_14,
    "15-l1-extraction.html": part4.LESSON_15,
    "16-l1-dedup-write.html": part4.LESSON_16,
    "17-why-l2-scene-blocks.html": part5.LESSON_17,
    "18-scene-extractor-sandbox.html": part5.LESSON_18,
    "19-scene-index-navigation-backups.html": part5.LESSON_19,
    "20-persona-generator-incremental.html": part5.LESSON_20,
    "21-l2-l3-scheduling-triggers.html": part5.LESSON_21,
    "22-auto-recall-before-prompt.html": part6.LESSON_22,
    "23-l1-search-recall-budget.html": part6.LESSON_23,
    "24-l2-navigation-l3-persona-injection.html": part6.LESSON_24,
    "25-sqlite-vec-fts-bm25-hybrid.html": part6.LESSON_25,
    "26-tencent-vectordb-embedding.html": part6.LESSON_26,
    "27-why-long-task-logs-symbolic-compression.html": part7.LESSON_27,
    "28-after-tool-call-refs-offload-jsonl.html": part7.LESSON_28,
    "29-l1-l15-l2-local-llm-pipelines.html": part7.LESSON_29,
    "30-mermaid-mmd-node-id-drill-down.html": part7.LESSON_30,
    "31-l3-context-injection-emergency-compression.html": part7.LESSON_31,
    "32-hermes-gateway-http-security.html": part8.LESSON_32,
    "33-seed-cli-migration-export-read.html": part8.LESSON_33,
    "34-debug-tests-contribution-glossary.html": part8.LESSON_34,
}
