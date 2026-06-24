"""Per-lesson bilingual self-test (自测题): design-insight multiple-choice + open prompts.

Schema per lesson::

    "NN-file.html": {
        "mcq": [
            {
                "q":   {"zh": "...", "en": "..."},
                "opts": [{"zh": "...", "en": "..."}, ...],
                "answer": 1,                      # 0-based index into opts (as written)
                "why": {"zh": "...", "en": "..."},
            },
        ],
        "open": [{"zh": "...", "en": "..."}],
    }

``render(fname, lang)`` turns it into HTML that build.py appends to the bottom of
each language's lesson body. Options are deterministically shuffled per question
(same permutation for zh and en, so the correct letter matches across languages).

Quiz text (q/opts/why) is raw HTML in a text context (like the lesson body):
write literal ``<``/``&`` as ``&lt;``/``&amp;`` (or wrap code in ``<code>``).
"""
import hashlib

_HEAD = {"zh": "🧪 自测 · 想一想为什么这么设计", "en": "🧪 Self-test - think about the design"}
_SEE = {"zh": "看答案与解析", "en": "Show answer &amp; explanation"}
_CLICK = {"zh": "点击展开", "en": "click to expand"}
_ANS = {"zh": "答案：", "en": "Answer: "}
_SEP = {"zh": "。", "en": ". "}
_OPEN = {
    "zh": "💭 发散思考（没有标准答案，动手或动脑想想）",
    "en": "💭 Open questions (no single right answer - just think or try)",
}


def _shuffle(opts, answer, seed):
    """Deterministically permute opts (stable across builds); return
    (new_opts, new_answer_index) so the correct option lands in a varied slot."""
    order = sorted(
        range(len(opts)),
        key=lambda i: hashlib.md5(f"{seed}:{i}".encode("utf-8")).hexdigest(),
    )
    return [opts[i] for i in order], order.index(answer)


QUIZZES = {
    "01-why-agent-memory.html": {
        "mcq": [
            {
                "q": {
                    "zh": "TencentDB Agent Memory 为什么不直接把所有历史都塞回 prompt？",
                    "en": "Why does TencentDB Agent Memory avoid dumping all history back into the prompt?",
                },
                "opts": [
                    {"zh": "因为 Agent 不需要历史", "en": "Because agents do not need history"},
                    {"zh": "因为上下文窗口有限，历史需要分层保存、按需召回", "en": "Because context is limited, so history must be layered and recalled on demand"},
                    {"zh": "因为 JSONL 不能保存长文本", "en": "Because JSONL cannot store long text"},
                    {"zh": "因为 LLM 不能读取文件", "en": "Because LLMs cannot read files"},
                ],
                "answer": 1,
                "why": {
                    "zh": "核心思想是上层保结构、下层保证据；不是丢历史，而是把历史放到合适的层级。",
                    "en": "The core idea is structure in upper layers and evidence in lower layers; history is not discarded, it is placed in the right layer.",
                },
            }
        ],
        "open": [
            {
                "zh": "用你自己的话解释：L3 Persona 和 L1 Atom 分别适合回答什么问题？",
                "en": "In your own words, what kinds of questions are best answered by L3 Persona versus L1 Atom?",
            }
        ],
    },
    "02-one-conversation-flow.html": {
        "mcq": [
            {
                "q": {
                    "zh": "在源码阅读主线里，为什么先找 <code>TdaiCore</code>？",
                    "en": "Why should the source-reading path find <code>TdaiCore</code> early?",
                },
                "opts": [
                    {"zh": "它是宿主无关的核心门面，OpenClaw 和 Gateway 都会走到这里", "en": "It is the host-neutral facade reached by both OpenClaw and Gateway paths"},
                    {"zh": "它负责 CSS 和页面构建", "en": "It owns CSS and page building"},
                    {"zh": "它只保存 README 内容", "en": "It only stores README content"},
                    {"zh": "它替代了所有存储后端", "en": "It replaces every storage backend"},
                ],
                "answer": 0,
                "why": {
                    "zh": "TdaiCore 把 recall、capture、search、pipeline 管理收成统一入口，Adapter 再隔离不同宿主。",
                    "en": "TdaiCore unifies recall, capture, search, and pipeline management, while adapters isolate host differences.",
                },
            }
        ],
        "open": [
            {
                "zh": "画一条线说明：用户发出一句话后，哪些阶段发生在模型回答前，哪些发生在回答后？",
                "en": "Draw a line showing which stages happen before the model responds and which stages happen after the response is committed.",
            }
        ],
    },
    "03-two-memory-spines.html": {
        "mcq": [
            {
                "q": {
                    "zh": "长期 L0-L3 和短期 Offload 最核心的区别是什么？",
                    "en": "What is the core difference between long-term L0-L3 and short-term Offload?",
                },
                "opts": [
                    {"zh": "长期记忆服务跨会话复用，Offload 服务当前任务上下文压缩", "en": "Long-term memory serves cross-session reuse; Offload serves current-task context compression"},
                    {"zh": "长期记忆只能存图片，Offload 只能存文本", "en": "Long-term memory stores only images; Offload stores only text"},
                    {"zh": "两者完全相同，只是名字不同", "en": "They are identical except for the name"},
                    {"zh": "Offload 不保留原文证据", "en": "Offload does not preserve raw evidence"},
                ],
                "answer": 0,
                "why": {
                    "zh": "两条主线都强调可追溯，但优化目标不同：长期记忆面向未来会话，Offload 面向当前长任务。",
                    "en": "Both preserve traceability, but optimize for different goals: long-term memory for future sessions, Offload for the current long task.",
                },
            }
        ],
        "open": [
            {
                "zh": "举一个信息例子：它应该进入长期记忆还是 Offload？为什么？",
                "en": "Give one example of information and decide whether it belongs in long-term memory or Offload. Why?",
            }
        ],
    },
    "04-openclaw-zero-config.html": {
        "mcq": [
            {
                "q": {"zh": "零配置启用后，为什么仍然要重启 Gateway？", "en": "After enabling zero config, why restart the Gateway?"},
                "opts": [
                    {"zh": "让 OpenClaw 重新加载插件配置并注册 hooks/tools", "en": "To let OpenClaw reload plugin config and register hooks/tools"},
                    {"zh": "清空所有记忆文件", "en": "To delete all memory files"},
                    {"zh": "把 SQLite 转成 TCVDB", "en": "To convert SQLite to TCVDB"},
                    {"zh": "重新训练模型", "en": "To retrain the model"},
                ],
                "answer": 0,
                "why": {"zh": "插件配置和 hook 注册发生在 Gateway 生命周期中，改配置后需要重启才能稳定生效。", "en": "Plugin config and hook registration happen during the Gateway lifecycle; restarting makes the new config take effect reliably."},
            }
        ],
        "open": [
            {"zh": "你会用哪三个现象判断 OpenClaw 记忆插件真的工作了？", "en": "Which three observations would you use to decide whether the OpenClaw memory plugin is really working?"}
        ],
    },
    "05-hermes-gateway-path.html": {
        "mcq": [
            {
                "q": {"zh": "Hermes 路径里，为什么目录名必须是 <code>memory_tencentdb</code>？", "en": "In the Hermes path, why must the directory name be <code>memory_tencentdb</code>?"},
                "opts": [
                    {"zh": "Hermes 用它作为 provider key", "en": "Hermes uses it as the provider key"},
                    {"zh": "Node.js 不支持连字符目录", "en": "Node.js does not support hyphenated directories"},
                    {"zh": "SQLite 只能读取下划线目录", "en": "SQLite can only read underscored directories"},
                    {"zh": "这是 OpenClaw 的 hook 名称", "en": "It is the OpenClaw hook name"},
                ],
                "answer": 0,
                "why": {"zh": "README 明确说明 Hermes 用目录名作为 provider key，连字符包名不能替代下划线 provider 名。", "en": "The README states Hermes uses the directory name as the provider key; the hyphenated package name cannot replace the underscored provider name."},
            }
        ],
        "open": [
            {"zh": "Hermes 和 OpenClaw 的入口不同，但为什么教程说它们复用同一个核心？", "en": "Hermes and OpenClaw enter through different paths, so why does the guide say they reuse the same core?"}
        ],
    },
    "06-runtime-files.html": {
        "mcq": [
            {
                "q": {"zh": "如果想核对一条用户画像背后的原始证据，正确的下钻方向是什么？", "en": "To verify raw evidence behind a persona claim, which drill-down direction is correct?"},
                "opts": [
                    {"zh": "Persona -&gt; Scene -&gt; L1 Atom -&gt; L0 Conversation", "en": "Persona -&gt; Scene -&gt; L1 Atom -&gt; L0 Conversation"},
                    {"zh": "vectors.db -&gt; README -&gt; package.json", "en": "vectors.db -&gt; README -&gt; package.json"},
                    {"zh": "L0 -&gt; 删除 records -&gt; 重新启动", "en": "L0 -&gt; delete records -&gt; restart"},
                    {"zh": "Offload MMD -&gt; npm install", "en": "Offload MMD -&gt; npm install"},
                ],
                "answer": 0,
                "why": {"zh": "本项目的核心是高层保结构、低层保证据；画像要通过场景、原子记忆回到原始对话。", "en": "The project keeps structure in upper layers and evidence in lower layers; a persona claim drills down through scenes and atoms to raw conversation."},
            }
        ],
        "open": [
            {"zh": "如果用户说“召回错了”，你会先打开哪个文件或目录？为什么？", "en": "If a user says recall is wrong, which file or directory would you open first, and why?"}
        ],
    },
    "07-config-levels.html": {
        "mcq": [
            {
                "q": {"zh": "远程 embedding 配置最容易漏掉哪组必填信息？", "en": "Which required fields are easiest to miss in remote embedding configuration?"},
                "opts": [
                    {"zh": "apiKey、baseUrl、model、dimensions", "en": "apiKey, baseUrl, model, dimensions"},
                    {"zh": "README、LICENSE、package name", "en": "README, LICENSE, package name"},
                    {"zh": "sceneBackupCount 和 favicon", "en": "sceneBackupCount and favicon"},
                    {"zh": "GitHub Pages source", "en": "GitHub Pages source"},
                ],
                "answer": 0,
                "why": {"zh": "远程 embedding 少任一关键字段都会导致向量能力无法正常启用或被降级。", "en": "Missing any of these fields prevents remote embedding from working correctly or causes degraded behavior."},
            }
        ],
        "open": [
            {"zh": "为什么召回 timeout 是用户体验上的安全默认值？", "en": "Why is a recall timeout a safe default for user experience?"}
        ],
    },
    "08-openclaw-plugin-shell.html": {
        "mcq": [{
            "q": {"zh": "为什么说 <code>index.ts</code> 是插件壳而不是记忆算法本体？", "en": "Why is <code>index.ts</code> a plugin shell rather than the memory algorithm itself?"},
            "opts": [
                {"zh": "它主要负责宿主注册、配置解析、hooks/tools 接线，核心能力委托给 TdaiCore", "en": "It mainly handles host registration, config parsing, hooks/tools wiring, and delegates core work to TdaiCore"},
                {"zh": "它只生成 HTML 页面", "en": "It only generates HTML pages"},
                {"zh": "它保存所有 L1 记忆", "en": "It stores all L1 memories"},
                {"zh": "它是 Hermes provider 目录名", "en": "It is the Hermes provider directory name"},
            ],
            "answer": 0,
            "why": {"zh": "宿主相关入口在 index.ts，真正的 recall/capture/search/pipeline 能力收在 TdaiCore 与 core 模块中。", "en": "Host-specific entry lives in index.ts; recall/capture/search/pipeline live in TdaiCore and core modules."},
        }],
        "open": [{"zh": "如果要定位 hook 注册问题，你会先读 index.ts 的哪几个区域？", "en": "If hook registration is broken, which areas of index.ts would you inspect first?"}],
    },
    "09-tdai-core-facade.html": {
        "mcq": [{
            "q": {"zh": "TdaiCore 的核心价值是什么？", "en": "What is the core value of TdaiCore?"},
            "opts": [
                {"zh": "让 OpenClaw 与 Gateway/Hermes 复用同一套记忆能力", "en": "It lets OpenClaw and Gateway/Hermes reuse the same memory capabilities"},
                {"zh": "替代所有 HTML 构建脚本", "en": "It replaces all HTML build scripts"},
                {"zh": "只负责读取 README", "en": "It only reads README"},
                {"zh": "只负责 CORS", "en": "It only handles CORS"},
            ],
            "answer": 0,
            "why": {"zh": "宿主差异被 adapter 吸收，TdaiCore 统一 expose recall/capture/search/pipeline。", "en": "Adapters absorb host differences; TdaiCore exposes recall/capture/search/pipeline uniformly."},
        }],
        "open": [{"zh": "为什么 Gateway 并发请求需要 scheduler 启动 promise gate？", "en": "Why does the Gateway path need a promise gate for scheduler startup?"}],
    },
    "10-host-adapter-boundaries.html": {
        "mcq": [{
            "q": {"zh": "HostAdapter 隔离的是什么？", "en": "What does HostAdapter isolate?"},
            "opts": [
                {"zh": "宿主运行时差异，例如日志、数据目录、LLM runner", "en": "Host runtime differences such as logging, data dirs, and LLM runner"},
                {"zh": "HTML 颜色变量", "en": "HTML color variables"},
                {"zh": "用户浏览器语言", "en": "The browser language"},
                {"zh": "Git commit 消息", "en": "Git commit messages"},
            ],
            "answer": 0,
            "why": {"zh": "Adapter 让 core 不依赖 OpenClaw 或 Gateway 细节。", "en": "The adapter keeps core independent of OpenClaw or Gateway details."},
        }],
        "open": [{"zh": "如果要新增第三个宿主，应优先实现哪些 adapter 能力？", "en": "If adding a third host, which adapter capabilities would you implement first?"}],
    },
    "11-runtime-init-config.html": {
        "mcq": [{
            "q": {"zh": "为什么零配置能启动？", "en": "Why can zero config start?"},
            "opts": [
                {"zh": "parseConfig 为各功能组填入默认值", "en": "parseConfig fills defaults for functional groups"},
                {"zh": "因为跳过所有配置解析", "en": "Because config parsing is skipped"},
                {"zh": "因为必须连接 TCVDB", "en": "Because TCVDB is mandatory"},
                {"zh": "因为 offload 总是开启", "en": "Because offload is always enabled"},
            ],
            "answer": 0,
            "why": {"zh": "默认值让 capture/recall/pipeline 等可按安全默认运行。", "en": "Defaults let capture/recall/pipeline run with safe baseline behavior."},
        }],
        "open": [{"zh": "如果 embedding 配置不完整，系统应该如何降级才不阻塞主对话？", "en": "If embedding config is incomplete, how should the system degrade without blocking the main chat?"}],
    },
    "12-auto-capture-hook.html": {
        "mcq": [{
            "q": {"zh": "Auto Capture 为什么不直接决定什么时候做 L1 抽取？", "en": "Why doesn't Auto Capture directly decide when to run L1 extraction?"},
            "opts": [
                {"zh": "触发策略属于 pipeline scheduler，capture 只负责可靠记录和通知", "en": "Trigger policy belongs to the pipeline scheduler; capture records reliably and notifies it"},
                {"zh": "因为 L1 已经废弃", "en": "Because L1 is deprecated"},
                {"zh": "因为 L0 不写文件", "en": "Because L0 does not write files"},
                {"zh": "因为 Gateway 禁止 capture", "en": "Because Gateway forbids capture"},
            ],
            "answer": 0,
            "why": {"zh": "职责分离让捕获路径更短、更可靠，调度规则集中在 pipeline manager。", "en": "Separation keeps capture short and reliable while scheduling policy stays in the pipeline manager."},
        }],
        "open": [{"zh": "如果出现重复 L0 记录，你会优先检查 capture 的哪两个机制？", "en": "If duplicate L0 records appear, which two capture mechanisms would you inspect first?"}],
    },
    "13-l0-jsonl-recorder.html": {
        "mcq": [{
            "q": {"zh": "L0 为什么采用 JSONL 一行一条消息？", "en": "Why does L0 use JSONL with one message per line?"},
            "opts": [
                {"zh": "便于追加、grep、流式读取和保留原始证据", "en": "It is easy to append, grep, stream, and preserve raw evidence"},
                {"zh": "因为不能保存时间戳", "en": "Because timestamps cannot be stored"},
                {"zh": "因为必须压缩成二进制", "en": "Because it must be binary-compressed"},
                {"zh": "因为 L1 不能读取 JSON", "en": "Because L1 cannot read JSON"},
            ],
            "answer": 0,
            "why": {"zh": "JSONL 适合增量写入和排查证据，是 L0 的“原文账本”。", "en": "JSONL fits incremental writes and evidence inspection; it is L0's raw ledger."},
        }],
        "open": [{"zh": "recorder 什么时候可以恢复缓存的原始 prompt，什么时候会回退到清洗与日志？", "en": "When can the recorder restore the cached original prompt, and when does it fall back to sanitization and logging?"}],
    },
    "14-checkpoints-races.html": {
        "mcq": [{
            "q": {"zh": "captureAtomically 保护的是哪段关键区？", "en": "Which critical section does captureAtomically protect?"},
            "opts": [
                {"zh": "读游标 -&gt; 写 L0 -&gt; 推进游标", "en": "read cursor -&gt; write L0 -&gt; advance cursor"},
                {"zh": "渲染 HTML -&gt; 打印 PDF", "en": "render HTML -&gt; print PDF"},
                {"zh": "删除 vectors.db -&gt; 重启", "en": "delete vectors.db -&gt; restart"},
                {"zh": "选择 favicon", "en": "choose favicon"},
            ],
            "answer": 0,
            "why": {"zh": "这段必须原子化，否则两个并发 capture 会读到同一个旧游标并重复写入。", "en": "This must be atomic; otherwise concurrent captures can read the same stale cursor and duplicate writes."},
        }],
        "open": [{"zh": "position slice 和 timestamp cursor 分别防哪类问题？", "en": "What different problems do position slice and timestamp cursor defend against?"}],
    },
    "15-l1-extraction.html": {
        "mcq": [{
            "q": {"zh": "L1 为什么保留 <code>source_message_ids</code>？", "en": "Why does L1 keep <code>source_message_ids</code>?"},
            "opts": [
                {"zh": "为了从原子记忆追溯回 L0 原始消息", "en": "To trace an atom memory back to raw L0 messages"},
                {"zh": "为了隐藏消息来源", "en": "To hide message sources"},
                {"zh": "为了替代 sessionKey", "en": "To replace sessionKey"},
                {"zh": "为了生成 favicon", "en": "To generate a favicon"},
            ],
            "answer": 0,
            "why": {"zh": "L1 是结构化摘要，但仍要能回到底层证据。", "en": "L1 is structured summary, but it must still point back to lower-layer evidence."},
        }],
        "open": [{"zh": "为什么 L1 prompt 同时需要 new messages 和 background messages？", "en": "Why does the L1 prompt need both new messages and background messages?"}],
    },
    "16-l1-dedup-write.html": {
        "mcq": [{
            "q": {"zh": "L1 去重为什么不是删除 L0 原文？", "en": "Why does L1 dedup not delete raw L0 text?"},
            "opts": [
                {"zh": "L0 是证据层，去重只控制结构化 L1 记忆质量", "en": "L0 is the evidence layer; dedup controls structured L1 memory quality"},
                {"zh": "因为 L0 不存在", "en": "Because L0 does not exist"},
                {"zh": "因为 dedup 只改 CSS", "en": "Because dedup only changes CSS"},
                {"zh": "因为 TCVDB 禁止更新", "en": "Because TCVDB forbids updates"},
            ],
            "answer": 0,
            "why": {"zh": "原文证据必须保留；去重处理的是可召回结构化事实是否重复/冲突。", "en": "Raw evidence must remain; dedup handles whether recallable structured facts duplicate or conflict."},
        }],
        "open": [{"zh": "如果向量召回与 FTS 召回都不可用，batchDedup 会怎样处理这批新记忆？", "en": "If neither vector recall nor FTS recall is available, how does batchDedup handle the new batch?"}],
    },
    "17-why-l2-scene-blocks.html": {
        "mcq": [{
            "q": {"zh": "L2 Scene Block 主要解决什么问题？", "en": "What problem do L2 scene blocks mainly solve?"},
            "opts": [
                {"zh": "把零散 L1 原子组织成可阅读、可导航、可追溯的情境", "en": "They organize scattered L1 atoms into readable, navigable, traceable contexts"},
                {"zh": "删除所有 L0 原文", "en": "They delete all raw L0 text"},
                {"zh": "替代 README", "en": "They replace the README"},
                {"zh": "强制每轮都调用远程数据库", "en": "They force every turn to call a remote database"},
            ],
            "answer": 0,
            "why": {"zh": "L2 聚合相关 L1，并保留证据线索，供 L3 与 recall 继续使用。", "en": "L2 clusters related L1 atoms and keeps evidence links for L3 and recall."},
        }],
        "open": [{"zh": "什么信息适合停留在 L1，什么信息应该进入 L2 场景？", "en": "What information should stay in L1, and what should become an L2 scene?"}],
    },
    "18-scene-extractor-sandbox.html": {
        "mcq": [{
            "q": {"zh": "SceneExtractor 为什么把 LLM 的 workspaceDir 限制到 <code>scene_blocks/</code>？", "en": "Why does SceneExtractor restrict the LLM workspaceDir to <code>scene_blocks/</code>?"},
            "opts": [
                {"zh": "让 LLM 能写场景文件，但不能直接改 checkpoint、scene_index 或 persona", "en": "So the LLM can write scene files but cannot directly change checkpoints, scene_index, or persona"},
                {"zh": "为了禁止 LLM 写任何文件", "en": "To forbid the LLM from writing any file"},
                {"zh": "为了让 HTML 构建更快", "en": "To make HTML builds faster"},
                {"zh": "为了跳过备份", "en": "To skip backups"},
            ],
            "answer": 0,
            "why": {"zh": "沙箱把创造性编辑限制在场景块目录，工程代码负责索引、备份和后处理。", "en": "The sandbox confines creative edits to scene blocks while engineering code owns indexes, backups, and post-processing."},
        }],
        "open": [{"zh": "如果 LLM 写坏了一个 scene block，备份和索引同步分别能帮你排查什么？", "en": "If the LLM corrupts a scene block, what do backups and index sync help diagnose?"}],
    },
    "19-scene-index-navigation-backups.html": {
        "mcq": [{
            "q": {"zh": "Scene Navigation 为什么包含场景文件路径？", "en": "Why does Scene Navigation include scene file paths?"},
            "opts": [
                {"zh": "让 agent 在需要细节时用 read_file 下钻，而不是每轮注入全文", "en": "So the agent can drill down with read_file when details are needed instead of injecting full scenes every turn"},
                {"zh": "让浏览器下载 SQLite", "en": "To make the browser download SQLite"},
                {"zh": "隐藏所有场景摘要", "en": "To hide all scene summaries"},
                {"zh": "替代 L1 搜索", "en": "To replace L1 search"},
            ],
            "answer": 0,
            "why": {"zh": "导航提供高层索引，完整证据按需读取，节省 prompt budget。", "en": "Navigation gives a high-level index, while full evidence is read on demand to save prompt budget."},
        }],
        "open": [{"zh": "为什么 scene_index 应由工程代码写，而不是让 LLM 直接维护？", "en": "Why should engineering code write scene_index instead of letting the LLM maintain it directly?"}],
    },
    "20-persona-generator-incremental.html": {
        "mcq": [{
            "q": {"zh": "增量 persona 更新优先分析什么？", "en": "What does incremental persona update analyze first?"},
            "opts": [
                {"zh": "自上次 persona 更新时间后变化的场景，同时保留已有画像", "en": "Scenes changed since the last persona update while preserving the existing profile"},
                {"zh": "只分析浏览器 CSS", "en": "Only browser CSS"},
                {"zh": "每次删除所有旧 persona", "en": "Deleting the old persona every time"},
                {"zh": "只读取 L0，不看 L2", "en": "Reading only L0 and ignoring L2"},
            ],
            "answer": 0,
            "why": {"zh": "L3 是稳定画像，增量更新应聚焦新变化并避免重写稳定信息。", "en": "L3 is a stable profile, so incremental updates focus on changes and avoid rewriting stable information."},
        }],
        "open": [{"zh": "为什么 persona.md 写完后还要重新追加 Scene Navigation？", "en": "Why append Scene Navigation again after persona.md is written?"}],
    },
    "21-l2-l3-scheduling-triggers.html": {
        "mcq": [{
            "q": {"zh": "L2 为什么使用 downward-only timer？", "en": "Why does L2 use a downward-only timer?"},
            "opts": [
                {"zh": "新 L1 可把 L2 提前，但不能无限推迟，兼顾响应性与 maxInterval 保证", "en": "New L1 work can move L2 earlier but not postpone it forever, balancing responsiveness and the maxInterval guarantee"},
                {"zh": "为了让所有任务并发写 persona", "en": "To let all tasks write persona concurrently"},
                {"zh": "为了禁用 L1", "en": "To disable L1"},
                {"zh": "为了每秒重建 HTML", "en": "To rebuild HTML every second"},
            ],
            "answer": 0,
            "why": {"zh": "L2 既要及时吸收新 L1，也要避免活跃会话一直延后整理。", "en": "L2 must absorb fresh L1 promptly without letting active sessions postpone consolidation forever."},
        }],
        "open": [{"zh": "为什么 L3 persona 生成需要全局串行，而不是每个 session 并发运行？", "en": "Why should L3 persona generation be globally serialized instead of running concurrently per session?"}],
    },
    "22-auto-recall-before-prompt.html": {
        "mcq": [{
            "q": {"zh": "Auto Recall 超时后为什么跳过注入而不是阻塞主对话？", "en": "Why does Auto Recall skip injection on timeout instead of blocking the main chat?"},
            "opts": [
                {"zh": "记忆是增强能力，不能破坏用户当前响应路径", "en": "Memory is an enhancement and must not break the user's current response path"},
                {"zh": "因为 L1 不可搜索", "en": "Because L1 cannot be searched"},
                {"zh": "因为 persona.md 必须删除", "en": "Because persona.md must be deleted"},
                {"zh": "因为 HTML 需要重新编译", "en": "Because HTML must be rebuilt"},
            ],
            "answer": 0,
            "why": {"zh": "召回失败应降级为无记忆对话，而不是让用户等待或失败。", "en": "Recall failure should degrade to a no-memory chat rather than making the user wait or fail."},
        }],
        "open": [{"zh": "为什么 capture 时需要原始 prompt 缓存，而不是直接保存被 recall prepend 后的文本？", "en": "Why does capture need the original prompt cache instead of saving recall-prepended text?"}],
    },
    "23-l1-search-recall-budget.html": {
        "mcq": [{
            "q": {"zh": "召回预算控制的核心目的是什么？", "en": "What is the core purpose of recall budgeting?"},
            "opts": [
                {"zh": "只注入最相关且足够短的 L1 片段，避免 prompt 被记忆挤满", "en": "Inject only the most relevant and compact L1 snippets so memory does not crowd out the prompt"},
                {"zh": "让所有 L0 原文每轮进入 prompt", "en": "To put all raw L0 text into every prompt"},
                {"zh": "禁用 BM25", "en": "To disable BM25"},
                {"zh": "跳过 query sanitize", "en": "To skip query sanitization"},
            ],
            "answer": 0,
            "why": {"zh": "预算让 recall 有帮助但不过量，长细节可通过工具继续搜索。", "en": "Budgeting keeps recall helpful but bounded; deeper details can be fetched with tools."},
        }],
        "open": [{"zh": "什么时候 embedding 或 hybrid 会退化成 keyword？这种降级为什么安全？", "en": "When does embedding or hybrid degrade to keyword, and why is that safe?"}],
    },
    "24-l2-navigation-l3-persona-injection.html": {
        "mcq": [{
            "q": {"zh": "为什么 L3 persona 和 L2 navigation 放在 appendSystemContext，而 L1 放在 prependContext？", "en": "Why do L3 persona and L2 navigation go into appendSystemContext while L1 goes into prependContext?"},
            "opts": [
                {"zh": "persona/navigation 较稳定，L1 每轮变化；这样更利于 prompt cache", "en": "Persona/navigation are relatively stable while L1 changes each turn, which is better for prompt caching"},
                {"zh": "因为 L1 不能被模型看到", "en": "Because L1 cannot be seen by the model"},
                {"zh": "因为 navigation 是 CSS", "en": "Because navigation is CSS"},
                {"zh": "因为 persona 必须写进 README", "en": "Because persona must be written into README"},
            ],
            "answer": 0,
            "why": {"zh": "稳定上下文与动态片段分离，减少缓存失效并保持每轮相关性。", "en": "Separating stable context from dynamic snippets reduces cache busting while keeping each turn relevant."},
        }],
        "open": [{"zh": "什么时候 agent 应使用 Scene Navigation 的 read_file，而不是依赖自动注入？", "en": "When should the agent use read_file from Scene Navigation instead of relying on automatic injection?"}],
    },
    "25-sqlite-vec-fts-bm25-hybrid.html": {
        "mcq": [{
            "q": {"zh": "SQLite 本地混合搜索为什么同时需要 FTS5 和 sqlite-vec？", "en": "Why does local SQLite hybrid search need both FTS5 and sqlite-vec?"},
            "opts": [
                {"zh": "FTS5/BM25 擅长关键词匹配，sqlite-vec 擅长语义相似，RRF 合并两者", "en": "FTS5/BM25 handles keyword matches, sqlite-vec handles semantic similarity, and RRF merges both"},
                {"zh": "两者都只负责生成 HTML", "en": "Both only generate HTML"},
                {"zh": "sqlite-vec 会删除 FTS", "en": "sqlite-vec deletes FTS"},
                {"zh": "BM25 只能搜索图片", "en": "BM25 can only search images"},
            ],
            "answer": 0,
            "why": {"zh": "关键词和语义召回互补，混合排序提高鲁棒性。", "en": "Keyword and semantic recall complement each other, and hybrid ranking improves robustness."},
        }],
        "open": [{"zh": "为什么 embedding provider 变化后可能需要 reindex？", "en": "Why might changing the embedding provider require reindexing?"}],
    },
    "26-tencent-vectordb-embedding.html": {
        "mcq": [{
            "q": {"zh": "TCVDB native hybridSearch 相比本地 SQLite RRF 的关键差异是什么？", "en": "What is the key difference between TCVDB native hybridSearch and local SQLite RRF?"},
            "opts": [
                {"zh": "TCVDB 可在服务端把 dense embedding、sparse vector 与 RRF rerank 合成一次查询", "en": "TCVDB can combine dense embedding, sparse vector, and RRF rerank server-side in one query"},
                {"zh": "TCVDB 只能保存 README", "en": "TCVDB can only store README"},
                {"zh": "TCVDB 禁止 filter index", "en": "TCVDB forbids filter indexes"},
                {"zh": "TCVDB 会删除 L0", "en": "TCVDB deletes L0"},
            ],
            "answer": 0,
            "why": {"zh": "远程后端把向量、稀疏向量和重排能力下沉到 VectorDB，减少客户端合并工作。", "en": "The remote backend pushes vector, sparse-vector, and reranking work into VectorDB, reducing client-side merging."},
        }],
        "open": [{"zh": "如果 TCVDB 初始化降级，哪些本地证据路径仍应保留？", "en": "If TCVDB initialization degrades, which local evidence paths should still remain?"}],
    },
    "27-why-long-task-logs-symbolic-compression.html": {
        "mcq": [{
            "q": {"zh": "Context Offload 为什么要与 L0-L3 长期记忆并存？", "en": "Why does Context Offload exist beside L0-L3 long-term memory?"},
            "opts": [
                {"zh": "它服务当前长任务，把工具日志压成可追溯符号，保护 live context token 预算", "en": "It serves the current long task, compressing tool logs into traceable symbols to protect the live context token budget"},
                {"zh": "它替代 L0-L3，成为唯一跨会话记忆来源", "en": "It replaces L0-L3 as the only cross-session memory source"},
                {"zh": "它只负责保存真实 API key", "en": "It only stores real API keys"},
                {"zh": "它把所有 Mermaid 图直接发到 VectorDB", "en": "It sends every Mermaid diagram directly to VectorDB"},
            ],
            "answer": 0,
            "why": {"zh": "Offload 面向当前任务导航和 token 控制；L0-L3 面向未来会话的事实、场景和画像。", "en": "Offload is for current-task navigation and token control; L0-L3 is for future-session facts, scenes, and profiles."},
        }],
        "open": [{"zh": "哪些工具结果应该保留为 refs 证据，而不是持续注入 live prompt？", "en": "Which tool results should remain as refs evidence instead of staying injected in the live prompt?"}],
    },
    "28-after-tool-call-refs-offload-jsonl.html": {
        "mcq": [{
            "q": {"zh": "after-tool-call 捕获完成工具结果后，为什么还要写 refs 和 offload JSONL 两种产物？", "en": "After after-tool-call captures a completed tool result, why write both refs and offload JSONL?"},
            "opts": [
                {"zh": "refs 保存完整原始证据，JSONL 保存可去重、可筛选、可注入的紧凑符号", "en": "refs keep full raw evidence; JSONL keeps compact symbols that can be deduped, filtered, and injected"},
                {"zh": "refs 用来保存真实 API key，JSONL 用来删除工具结果", "en": "refs store real API keys, and JSONL deletes tool results"},
                {"zh": "两者内容必须完全相同，方便重复占用上下文", "en": "They must be identical so context can be duplicated"},
                {"zh": "JSONL 只能保存 Mermaid，refs 只能保存 CSS", "en": "JSONL can only store Mermaid, and refs can only store CSS"},
            ],
            "answer": 0,
            "why": {"zh": "Context Offload 的设计是证据与符号分离：原始结果可追溯，摘要行轻量可导航，并用 tool_call_id 写入去重。", "en": "Context Offload separates evidence from symbols: raw results stay traceable, summary rows stay lightweight and navigable, and tool_call_id enables write-time dedup."},
        }],
        "open": [{"zh": "如果同一个 tool_call_id 因重试被重复写入，你希望 JSONL 和 refs 分别表现出什么行为？", "en": "If the same tool_call_id is replayed after a retry, how should JSONL and refs behave?"}],
    },

    "29-l1-l15-l2-local-llm-pipelines.html": {
        "mcq": [{
            "q": {"zh": "为什么本地 Offload 要把 L1、L1.5、L2 拆成三次模型调用？", "en": "Why does local Offload split L1, L1.5, and L2 into three model calls?"},
            "opts": [
                {"zh": "三者责任不同：L1 摘要工具证据，L1.5 判断任务边界，L2 生成 MMD 并返回 node_mapping", "en": "They have different responsibilities: L1 summarizes tool evidence, L1.5 judges task boundaries, and L2 generates MMD with node_mapping"},
                {"zh": "因为 Mermaid 只能由 L1 parser 解析", "en": "Because Mermaid can only be parsed by the L1 parser"},
                {"zh": "因为 L1.5 必须写入真实 API key", "en": "Because L1.5 must write real API keys"},
                {"zh": "因为 backend client 和 local client 不能共享接口", "en": "Because backend and local clients cannot share an interface"},
            ],
            "answer": 0,
            "why": {"zh": "拆分后每层只验证自己的 prompt/parser 契约；LocalLlmClient 仍与 backend client 暴露同一组方法，上层 pipeline 可复用。", "en": "Splitting lets each layer validate its own prompt/parser contract; LocalLlmClient still exposes the same methods as the backend client, so the upper pipeline is reused."},
        }],
        "open": [{"zh": "如果 L2 返回了 Mermaid 但缺少 node_mapping，你会如何防止错误回填 node_id？", "en": "If L2 returns Mermaid but no node_mapping, how would you prevent incorrect node_id backfill?"}],
    },
    "30-mermaid-mmd-node-id-drill-down.html": {
        "mcq": [{
            "q": {"zh": "为什么 Lesson 30 强调每个新工具条目都必须获得 node_id？", "en": "Why does Lesson 30 emphasize that every new tool entry must receive a node_id?"},
            "opts": [
                {"zh": "因为 node_id 把 MMD 任务节点连接回 JSONL 摘要行和 refs 证据，支持下钻恢复", "en": "Because node_id connects MMD task nodes back to JSONL summary rows and refs evidence for drill-down recovery"},
                {"zh": "因为 Mermaid 没有 node_id 就不能显示任何颜色", "en": "Because Mermaid cannot display any color without node_id"},
                {"zh": "因为 node_id 用来保存真实 API key", "en": "Because node_id stores real API keys"},
                {"zh": "因为有了 node_id 就不需要 refs markdown", "en": "Because node_id removes the need for refs markdown"},
            ],
            "answer": 0,
            "why": {"zh": "MMD 是任务地图；node_id 是从地图回到证据的索引。没有它，Offload-L3 注入的活动节点无法可靠定位原始细节。", "en": "MMD is the task map; node_id is the index from the map back to evidence. Without it, an active node injected by Offload-L3 cannot reliably locate raw detail."},
        }],
        "open": [{"zh": "如果 MMD 节点存在但 JSONL 行的 node_id 仍为 null，你会如何恢复或补救下钻链路？", "en": "If an MMD node exists but the JSONL row still has node_id null, how would you recover or repair the drill-down chain?"}],
    },
    "31-l3-context-injection-emergency-compression.html": {
        "mcq": [{
            "q": {"zh": "L3 在真正调用模型前为什么先注入 active MMD，再按 token 压力分层压缩？", "en": "Why does L3 inject the active MMD before applying tiered compression by token pressure?"},
            "opts": [
                {"zh": "因为任务地图是恢复路径，先放入地图再决定压缩哪些旧证据，能保护当前任务语义", "en": "Because the task map is the recovery path; injecting it first lets compression remove old evidence while preserving current-task meaning"},
                {"zh": "因为 emergencyCompress 会永久删除所有 refs 文件", "en": "Because emergencyCompress permanently deletes all refs files"},
                {"zh": "因为 token 计数只能在模型回答之后计算", "en": "Because token counts can only be computed after the model responds"},
                {"zh": "因为 tool-use/tool-result 对可以随意拆开", "en": "Because tool-use/tool-result pairs can be split freely"},
            ],
            "answer": 0,
            "why": {"zh": "before_prompt_build 先准备 active MMD 和确认 offload 的快路径；llm_input_l3 再用精确 token 快照决定温和、激进或紧急压缩，同时保护最新用户消息和工具对结构。", "en": "before_prompt_build prepares the active MMD and confirmed-offload fast path first; llm_input_l3 then uses precise token snapshots for mild, aggressive, or emergency compression while protecting the latest user message and valid tool-pair structure."},
        }],
        "open": [{"zh": "如果模型入口仍然报 token overflow，你会怎样判断该进入 emergency compression，且哪些消息绝不能被删？", "en": "If the model entry still reports token overflow, how would you decide to enter emergency compression, and which messages must never be removed?"}],
    },
    "32-hermes-gateway-http-security.html": {
        "mcq": [{
            "q": {"zh": "Hermes / Gateway 路径和 OpenClaw 进程内插件路径最关键的运维差异是什么？", "en": "What is the key operational difference between the Hermes / Gateway path and the OpenClaw in-process plugin path?"},
            "opts": [
                {"zh": "Hermes / Gateway 多了外部 HTTP 网络边界，必须先处理 bind、CORS、auth、payload、timeout 和日志脱敏", "en": "Hermes / Gateway adds an external HTTP network boundary, so bind, CORS, auth, payload, timeout, and redacted logging must be handled first"},
                {"zh": "Hermes / Gateway 会绕过 TdaiCore，直接写所有记忆文件", "en": "Hermes / Gateway bypasses TdaiCore and writes every memory file directly"},
                {"zh": "OpenClaw 进程内路径必须公开到公网才能工作", "en": "The OpenClaw in-process path must be public on the internet to work"},
                {"zh": "两条路径完全相同，都不需要安全配置", "en": "The two paths are identical and need no security configuration"},
            ],
            "answer": 0,
            "why": {"zh": "两条路径最终都应收敛到 TdaiCore；差异在入口边界。HTTP Gateway 是可被外部调用的服务，必须在委托核心前完成网络与请求安全控制。", "en": "Both paths should converge on TdaiCore; the difference is the entry boundary. An HTTP Gateway is externally callable, so network and request security must be enforced before delegating to core."},
        }],
        "open": [{"zh": "如果必须把 Gateway 暴露到非本机网络，你会怎样组合监听地址、allowed origins、auth token、反向代理限流和日志策略？", "en": "If the Gateway must be exposed beyond the local machine, how would you combine bind address, allowed origins, auth token, reverse-proxy rate limits, and logging policy?"}],
    },
    "33-seed-cli-migration-export-read.html": {
        "mcq": [{
            "q": {"zh": "运行 seed 或 SQLite 到 Tencent VectorDB 迁移前，最安全的默认顺序是什么？", "en": "Before running seed or SQLite to Tencent VectorDB migration, what is the safest default order?"},
            "opts": [
                {"zh": "先读文档，备份，dry run，检查 manifest / export，再 apply 并只读验证", "en": "Read docs, back up, dry run, inspect manifest / export, then apply and verify with read-only checks"},
                {"zh": "直接 apply，因为脚本会自动知道 operator 的意图", "en": "Apply directly because scripts automatically know the operator's intent"},
                {"zh": "把真实 endpoint 和 token 写进教程，方便复制", "en": "Write real endpoints and tokens into the guide for easy copying"},
                {"zh": "在 live recall 超时时顺便迁移，节省一次命令", "en": "Migrate inside a live recall timeout to save one command"},
            ],
            "answer": 0,
            "why": {"zh": "这些脚本是 live loop 外的运维动作。dry run、备份、manifest、占位配置和只读验证能把风险从“不可见副作用”变成可审计、可回滚的变更。", "en": "These scripts are operational actions outside the live loop. Dry runs, backups, manifests, placeholder config, and read-only verification turn hidden side effects into auditable, reversible changes."},
        }],
        "open": [{"zh": "设计一次从本地 SQLite 到 Tencent VectorDB 的迁移演练：你会备份哪些文件，manifest 记录哪些字段，apply 后怎样验证 recall/search 没有退化？", "en": "Design a rehearsal for migrating local SQLite to Tencent VectorDB: which files would you back up, which manifest fields would you record, and how would you verify recall/search after apply?"}],
    },
}


def render(fname, lang):
    """Return the self-test HTML block for ``fname`` in ``lang`` ('' if none)."""
    data = QUIZZES.get(fname)
    if not data or not (data.get("mcq") or data.get("open")):
        return ""
    out = ['<div class="selftest">', f'<h2>{_HEAD[lang]}</h2>']
    for i, item in enumerate(data.get("mcq", []), 1):
        shuffled, ans = _shuffle(item["opts"], item["answer"], f"{fname}:{i}")
        opts = "\n".join(f"    <li>{o[lang]}</li>" for o in shuffled)
        letter = chr(65 + ans)
        out.append(
            f'<div class="quiz">\n'
            f'  <div class="qn">{i}. {item["q"][lang]}</div>\n'
            f'  <ol class="opts">\n{opts}\n  </ol>\n'
            f'  <details class="accordion">\n'
            f'    <summary>{_SEE[lang]} <span class="hint">{_CLICK[lang]}</span></summary>\n'
            f'    <div class="acc-body"><div class="qa"><div class="a">'
            f'<strong>{_ANS[lang]}{letter}</strong>{_SEP[lang]}{item["why"][lang]}'
            f"</div></div></div>\n"
            f"  </details>\n"
            f"</div>"
        )
    opens = data.get("open", [])
    if opens:
        lis = "\n".join(f"    <li>{o[lang]}</li>" for o in opens)
        out.append(
            '<div class="card spark">\n'
            f'  <div class="tag">{_OPEN[lang]}</div>\n'
            f"  <ul>\n{lis}\n  </ul>\n"
            "</div>"
        )
    out.append("</div>")
    return "\n".join(out)


def _validate():
    """Fail fast on authoring mistakes in QUIZZES (clear message names the lesson)."""
    for fname, data in QUIZZES.items():
        for qi, item in enumerate(data.get("mcq", []), 1):
            opts = item["opts"]
            if not (0 <= item["answer"] < len(opts)):
                raise ValueError(
                    f"quizzes[{fname!r}] Q{qi}: answer {item['answer']} out of range 0..{len(opts) - 1}"
                )
            for o in opts:
                if not ({"zh", "en"} <= o.keys()):
                    raise ValueError(f"quizzes[{fname!r}] Q{qi}: an option is missing zh/en")
            if not ({"zh", "en"} <= item["q"].keys() and {"zh", "en"} <= item["why"].keys()):
                raise ValueError(f"quizzes[{fname!r}] Q{qi}: q/why missing zh/en")
        for oi, o in enumerate(data.get("open", []), 1):
            if not ({"zh", "en"} <= o.keys()):
                raise ValueError(f"quizzes[{fname!r}] open{oi}: missing zh/en")


_validate()
