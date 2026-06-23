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
