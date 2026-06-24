"""Part 6 content: recall, search, and storage."""


LESSON_22 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Auto Recall 发生在 prompt 真正交给模型之前。插件先保留用户原始输入，再把清洗后的查询交给核心层召回记忆；
如果召回及时返回，就把用户侧上下文和系统侧上下文分别注入。如果超时或失败，主对话必须继续，不让记忆增强阻塞用户响应。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  这像开会前的助理检索：用户刚提出问题，助理快速翻出相关项目笔记，贴在发言稿前后。
  如果档案柜一时打不开，会议不会停在门口；最多这轮先按没有记忆的方式回答。
</div>

<h2>before_prompt_build 路径</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>用户文本进入 hook</h4><p><span class="inline">index.ts</span> 的 before-prompt hook 收到本轮用户文本，并把原始 prompt 写入 <span class="inline">pendingOriginalPrompts</span>，供后续 capture 使用。</p><div class="mono">user text -&gt; pendingOriginalPrompts</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>交给 TdaiCore</h4><p>插件调用 <span class="inline">TdaiCore.handleBeforeRecall</span>，让宿主壳只负责接线，核心层负责 recall 语义。</p><div class="mono">index.ts -&gt; TdaiCore.handleBeforeRecall</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>执行超时竞速</h4><p><span class="inline">performAutoRecall</span> 使用 <span class="inline">recall.timeoutMs</span> 与召回任务 race：配置策略决定查哪些层、取多少上下文，超时则返回跳过注入。</p><div class="mono">recall task -&gt; race(timeoutMs)</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>注入上下文</h4><p>及时返回时，结果里的 <span class="inline">prependContext</span> 被放到用户消息前，<span class="inline">appendSystemContext</span> 被追加到系统上下文。</p><div class="mono">prependContext + appendSystemContext -&gt; prompt</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>模型继续响应</h4><p>模型看到的是增强后的 prompt；如果召回超时或失败，模型仍然收到原始对话路径，不被记忆系统拖住。</p><div class="mono">prompt -&gt; model</div></div></div>
</div>

<h2>两种注入位置</h2>
<div class="cols">
  <div class="col"><h4>Prepend user context</h4><p>适合放“与本轮用户问题直接相关”的记忆片段。它贴近用户文本，让模型把这些事实当成本轮问题的可用背景，而不是新的用户命令。</p></div>
  <div class="col"><h4>Append system context</h4><p>适合放更稳定的系统侧说明，例如 recall 结果摘要、来源提示或使用边界。它补充系统上下文，但不覆盖原始系统规则。</p></div>
</div>

<h2>缓存、清洗与指标</h2>
<div class="flow">
  <div class="node"><div class="nt">original prompt cache</div><div class="nd"><span class="inline">pendingOriginalPrompts</span> 保留用户原文，避免 capture 保存被 recall prepend 污染后的文本。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">sanitize.ts</span> 清洗 prompt/query，防止把注入标签或控制片段带入检索。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall result</div><div class="nd"><span class="inline">performAutoRecall</span> 生成可注入上下文、命中信息与耗时。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">metrics cache</div><div class="nd"><span class="inline">pendingRecallCache</span> 暂存本轮 recall 指标，供之后提交、观测或调试关联。</div></div>
</div>

<p>
清洗后的 query 用于“找记忆”，原始 prompt 用于“记录用户真的说了什么”。这两个数据面不能混淆：
如果 capture 直接保存被 prepend 后的文本，下一轮 L0/L1 会把系统注入当成用户证据，形成自我污染。
</p>

<h2>核心伪代码</h2>
<pre class="code">before_prompt_build(userText):
    pendingOriginalPrompts[sessionKey] = userText
    result = await core.handleBeforeRecall(userText, sessionKey)
    if result within timeout:
        prepend_to_user(result.prependContext)
        append_to_system(result.appendSystemContext)
        pendingRecallCache[turnId] = result.metrics
    else:
        continue_without_memory()</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">index.ts</span>：before prompt hook 负责缓存 <span class="inline">pendingOriginalPrompts</span>，接收 recall 结果，并把 metrics 放入 <span class="inline">pendingRecallCache</span>。</li>
    <li><span class="inline">src/core/tdai-core.ts</span>：<span class="inline">handleBeforeRecall</span> 是宿主壳调用的核心入口。</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：<span class="inline">performAutoRecall</span> 执行 recall，并用 timeout race 保护主链路。</li>
    <li><span class="inline">src/config.ts</span>：<span class="inline">recall.timeoutMs</span> 与 strategy config 决定召回预算、策略和结果规模。</li>
    <li><span class="inline">src/utils/sanitize.ts</span>：负责 prompt/query sanitization，避免把注入标记或不可信控制文本带入检索。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Recall 是增强能力，不是主对话的硬依赖。before-prompt 阶段要先缓存原始输入，再用清洗后的 query 尝试召回；
  及时返回则注入 <span class="inline">prependContext</span> 与 <span class="inline">appendSystemContext</span>，超时则 fail open，继续无记忆对话。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Auto Recall runs before the final prompt is sent to the model. The plugin first keeps the user's original input, then sends a sanitized query
into the core recall path. If recall returns in time, it injects user-side and system-side context. If recall times out or fails, the main chat
continues so memory enhancement never blocks the user's response.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Think of it as a meeting assistant doing a quick lookup before you answer. The assistant may attach relevant project notes around your speaking notes.
  If the archive cabinet is stuck, the meeting does not stop at the door; this turn simply proceeds without memory.
</div>

<h2>The before_prompt_build path</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>User text enters the hook</h4><p>The before-prompt hook in <span class="inline">index.ts</span> receives this turn's user text and stores the original prompt in <span class="inline">pendingOriginalPrompts</span> for later capture.</p><div class="mono">user text -&gt; pendingOriginalPrompts</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Delegate to TdaiCore</h4><p>The plugin calls <span class="inline">TdaiCore.handleBeforeRecall</span>, keeping host wiring in the shell while recall semantics live in the core.</p><div class="mono">index.ts -&gt; TdaiCore.handleBeforeRecall</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Run the timeout race</h4><p><span class="inline">performAutoRecall</span> races the recall work against <span class="inline">recall.timeoutMs</span>: strategy config controls which layers are searched and how much context can return; timeout means skip injection.</p><div class="mono">recall task -&gt; race(timeoutMs)</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Inject context</h4><p>When recall returns in time, <span class="inline">prependContext</span> is placed before the user message, and <span class="inline">appendSystemContext</span> is appended to system context.</p><div class="mono">prependContext + appendSystemContext -&gt; prompt</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>The model responds</h4><p>The model sees the enhanced prompt; if recall timed out or failed, it still receives the original chat path without being held by memory.</p><div class="mono">prompt -&gt; model</div></div></div>
</div>

<h2>Two injection positions</h2>
<div class="cols">
  <div class="col"><h4>Prepend user context</h4><p>Best for memory snippets directly relevant to the current user request. It sits near the user text so the model treats those facts as available background for this turn, not as new user commands.</p></div>
  <div class="col"><h4>Append system context</h4><p>Best for more stable system-side notes such as recall summaries, source hints, or usage boundaries. It extends system context without replacing the original system rules.</p></div>
</div>

<h2>Caches, sanitization, and metrics</h2>
<div class="flow">
  <div class="node"><div class="nt">original prompt cache</div><div class="nd"><span class="inline">pendingOriginalPrompts</span> keeps the user text so capture does not save recall-prepended content as evidence.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">sanitize.ts</span> cleans the prompt/query so injected tags or control fragments do not enter search.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall result</div><div class="nd"><span class="inline">performAutoRecall</span> produces injectable context, hit details, and timing.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">metrics cache</div><div class="nd"><span class="inline">pendingRecallCache</span> temporarily stores this turn's recall metrics for later commit, observation, or debugging correlation.</div></div>
</div>

<p>
The sanitized query is for "finding memory"; the original prompt is for "recording what the user actually said". These two data planes must not be mixed.
If capture saved recall-prepended text, later L0/L1 processing would treat system-injected context as user evidence and create self-contamination.
</p>

<h2>Core pseudocode</h2>
<pre class="code">before_prompt_build(userText):
    pendingOriginalPrompts[sessionKey] = userText
    result = await core.handleBeforeRecall(userText, sessionKey)
    if result within timeout:
        prepend_to_user(result.prependContext)
        append_to_system(result.appendSystemContext)
        pendingRecallCache[turnId] = result.metrics
    else:
        continue_without_memory()</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">index.ts</span>: the before prompt hook caches <span class="inline">pendingOriginalPrompts</span>, receives the recall result, and stores metrics in <span class="inline">pendingRecallCache</span>.</li>
    <li><span class="inline">src/core/tdai-core.ts</span>: <span class="inline">handleBeforeRecall</span> is the core entry point called by the host shell.</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: <span class="inline">performAutoRecall</span> runs recall and uses a timeout race to protect the main path.</li>
    <li><span class="inline">src/config.ts</span>: <span class="inline">recall.timeoutMs</span> and strategy config define recall budget, strategy, and result size.</li>
    <li><span class="inline">src/utils/sanitize.ts</span>: handles prompt/query sanitization so injection tags or untrusted control text do not enter search.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Recall is an enhancement, not a hard dependency of the main chat. The before-prompt stage stores original input first, then uses a sanitized query
  to try recall; timely results inject <span class="inline">prependContext</span> and <span class="inline">appendSystemContext</span>, while timeout fails open into a no-memory chat.
</div>
""",
}
