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
