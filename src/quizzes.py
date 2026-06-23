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
