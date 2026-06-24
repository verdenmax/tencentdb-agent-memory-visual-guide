"""Part 6 content: recall, search, and storage."""


LESSON_22 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Auto Recall 发生在 prompt 真正交给模型之前。插件先保留用户原始输入，并把原始 <span class="inline">event.prompt</span> 交给核心入口；
真正进入 FTS/embedding 检索前，<span class="inline">searchMemories</span> 再调用 <span class="inline">sanitizeText(userText)</span> 清洗查询。
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
  <div class="step"><div class="num">2</div><div class="sc"><h4>交给 TdaiCore</h4><p><span class="inline">api.on("before_prompt_build")</span> 调用 <span class="inline">TdaiCore.handleBeforeRecall</span> 时传入的是原始 <span class="inline">event.prompt</span>，让宿主壳只负责接线，核心层负责 recall 语义。</p><div class="mono">index.ts -&gt; TdaiCore.handleBeforeRecall(raw prompt)</div></div></div>
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
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">searchMemories</span> 在 FTS/embedding 查找前调用 <span class="inline">sanitizeText(userText)</span>，防止把注入标签或控制片段带入检索。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall result</div><div class="nd"><span class="inline">performAutoRecall</span> 生成可注入上下文、命中信息与耗时。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">metrics cache</div><div class="nd"><span class="inline">pendingRecallCache</span> 按 <span class="inline">sessionKey</span> 暂存 recall payload，供 <span class="inline">agent_end</span> 上报 <span class="inline">agent_turn</span> 指标。</div></div>
</div>

<p>
核心入口收到的是原始 prompt；清洗发生在 <span class="inline">searchMemories</span> 内部，清洗后的 query 用于“找记忆”，原始 prompt 用于“记录用户真的说了什么”。这两个数据面不能混淆：
如果 capture 直接保存被 prepend 后的文本，下一轮 L0/L1 会把系统注入当成用户证据，形成自我污染。
</p>

<h2>核心伪代码</h2>
<pre class="code">before_prompt_build(userText):
    pendingOriginalPrompts[sessionKey] = userText
    result = await core.handleBeforeRecall(userText, sessionKey)
    if result within timeout:
        prepend_to_user(result.prependContext)
        append_to_system(result.appendSystemContext)
        pendingRecallCache[sessionKey] = result.recallPayload
    else:
        continue_without_memory()</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">index.ts</span>：<span class="inline">api.on("before_prompt_build")</span> 负责缓存 <span class="inline">pendingOriginalPrompts</span>，把原始 <span class="inline">event.prompt</span> 传给核心入口，接收 recall 结果，并按 <span class="inline">sessionKey</span> 把 payload 放入 <span class="inline">pendingRecallCache</span>。</li>
    <li><span class="inline">src/core/tdai-core.ts</span>：<span class="inline">handleBeforeRecall</span> 是宿主壳调用的核心入口。</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：<span class="inline">performAutoRecall</span> 执行 recall，并用 timeout race 保护主链路。</li>
    <li><span class="inline">src/config.ts</span>：<span class="inline">recall.timeoutMs</span> 与 strategy config 决定召回预算、策略和结果规模。</li>
    <li><span class="inline">searchMemories</span>：在 FTS/embedding lookup 前调用 <span class="inline">sanitizeText(userText)</span> 清洗查询。</li>
    <li><span class="inline">src/utils/sanitize.ts</span>：提供 <span class="inline">sanitizeText</span>，避免把注入标记或不可信控制文本带入检索。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Recall 是增强能力，不是主对话的硬依赖。before-prompt 阶段要先缓存原始输入，并把原始 prompt 交给核心入口；检索层再清洗 query 尝试召回。
  及时返回则注入 <span class="inline">prependContext</span> 与 <span class="inline">appendSystemContext</span>，超时则 fail open，继续无记忆对话。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Auto Recall runs before the final prompt is sent to the model. The plugin first keeps the user's original input and passes the raw
<span class="inline">event.prompt</span> into the core entry point; before FTS/embedding lookup, <span class="inline">searchMemories</span>
sanitizes the query with <span class="inline">sanitizeText(userText)</span>. If recall returns in time, it injects user-side and system-side context. If recall times out or fails, the main chat
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
  <div class="step"><div class="num">2</div><div class="sc"><h4>Delegate to TdaiCore</h4><p><span class="inline">api.on("before_prompt_build")</span> calls <span class="inline">TdaiCore.handleBeforeRecall</span> with the raw <span class="inline">event.prompt</span>, keeping host wiring in the shell while recall semantics live in the core.</p><div class="mono">index.ts -&gt; TdaiCore.handleBeforeRecall(raw prompt)</div></div></div>
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
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">searchMemories</span> calls <span class="inline">sanitizeText(userText)</span> before FTS/embedding lookup so injected tags or control fragments do not enter search.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall result</div><div class="nd"><span class="inline">performAutoRecall</span> produces injectable context, hit details, and timing.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">metrics cache</div><div class="nd"><span class="inline">pendingRecallCache</span> is keyed by <span class="inline">sessionKey</span> and stores the recall payload used at <span class="inline">agent_end</span> to report the <span class="inline">agent_turn</span> metric.</div></div>
</div>

<p>
The core entry point receives the raw prompt; sanitization happens inside <span class="inline">searchMemories</span>. The sanitized query is for "finding memory"; the original prompt is for "recording what the user actually said". These two data planes must not be mixed.
If capture saved recall-prepended text, later L0/L1 processing would treat system-injected context as user evidence and create self-contamination.
</p>

<h2>Core pseudocode</h2>
<pre class="code">before_prompt_build(userText):
    pendingOriginalPrompts[sessionKey] = userText
    result = await core.handleBeforeRecall(userText, sessionKey)
    if result within timeout:
        prepend_to_user(result.prependContext)
        append_to_system(result.appendSystemContext)
        pendingRecallCache[sessionKey] = result.recallPayload
    else:
        continue_without_memory()</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">index.ts</span>: <span class="inline">api.on("before_prompt_build")</span> caches <span class="inline">pendingOriginalPrompts</span>, passes raw <span class="inline">event.prompt</span> into the core entry point, receives the recall result, and stores the payload in <span class="inline">pendingRecallCache</span> by <span class="inline">sessionKey</span>.</li>
    <li><span class="inline">src/core/tdai-core.ts</span>: <span class="inline">handleBeforeRecall</span> is the core entry point called by the host shell.</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: <span class="inline">performAutoRecall</span> runs recall and uses a timeout race to protect the main path.</li>
    <li><span class="inline">src/config.ts</span>: <span class="inline">recall.timeoutMs</span> and strategy config define recall budget, strategy, and result size.</li>
    <li><span class="inline">searchMemories</span>: calls <span class="inline">sanitizeText(userText)</span> before FTS/embedding lookup.</li>
    <li><span class="inline">src/utils/sanitize.ts</span>: provides <span class="inline">sanitizeText</span> so injection tags or untrusted control text do not enter search.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Recall is an enhancement, not a hard dependency of the main chat. The before-prompt stage stores original input first and passes the raw prompt to the core entry point; the search layer then sanitizes the query before recall. Timely results inject <span class="inline">prependContext</span> and <span class="inline">appendSystemContext</span>, while timeout fails open into a no-memory chat.
</div>
""",
}


LESSON_23 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
第 22 课看到 Auto Recall 在 prompt 构建前启动；本课下钻到 L1 搜索本身。
<span class="inline">searchMemories()</span> 先清洗用户文本，再按 <span class="inline">keyword</span>、<span class="inline">embedding</span> 或 <span class="inline">hybrid</span> 选择检索路径。
召回的产物不是完整 transcript，而是足够短、足够相关的 L1 片段；更长的证据应通过显式 memory search 工具继续查。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  这像会议助理只把三五条最相关的便签贴到发言稿旁边，而不是把整本会议记录塞进来。
  便签先按关键词或语义找，再按预算裁短；如果语义检索的设备没准备好，就退回可靠的关键词检索。
</div>

<h2>searchMemories 的召回管线</h2>
<div class="flow">
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">sanitizeText(userText)</span> 去掉不可信控制片段，只保留适合检索的文本。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">strategy</div><div class="nd">配置可选 <span class="inline">keyword</span>、<span class="inline">embedding</span>、<span class="inline">hybrid</span>；未显式配置时按 recall 配置默认值决定。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">candidates</div><div class="nd">FTS5 BM25 和/或向量余弦相似度产生候选 L1。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">threshold / RRF</div><div class="nd">单路结果用分数阈值过滤；混合结果用 RRF 合并排序。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">budget</div><div class="nd"><span class="inline">maxResults</span> 与字符预算限制注入规模。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">injected lines</div><div class="nd">只注入 <span class="inline">formatMemoryLine()</span> 生成的简洁 L1 行：<span class="inline">- [type|scene] content</span>，可附活动时间；id 和 score 不进入 prompt，解析注入文本的指标不应依赖 score。</div></div>
</div>

<h2>三种策略怎么选</h2>
<div class="cols">
  <div class="col"><h4>keyword</h4><p><span class="inline">searchByKeyword</span> 走 SQLite FTS5。<span class="inline">buildFtsQuery</span> 把清洗后的词变成 FTS 查询，结果用 BM25 排序，适合精确术语、文件名、函数名。</p></div>
  <div class="col"><h4>embedding</h4><p><span class="inline">searchByEmbedding</span> 先把 query 编成向量，再用余弦相似度找语义接近的 L1。它适合用户换一种说法提问，但依赖 embedding 资源可用。</p></div>
  <div class="col"><h4>hybrid</h4><p><span class="inline">searchHybrid</span> 同时跑 keyword 与 embedding，并在 <span class="inline">auto-recall.ts</span> 内部用本地 RRF 合并两个排行榜。RRF 常量让高排名结果稳定胜出，而不是只看某一路绝对分数。</p></div>
</div>

<p>
降级规则很重要：如果配置选择 <span class="inline">embedding</span> 或 <span class="inline">hybrid</span>，但 embedding client、模型维度或向量索引没有准备好，
<span class="inline">searchMemories()</span> 会安全退回 <span class="inline">keyword</span>。
这不会阻塞主对话，也不会捏造语义分数；它只是使用本地 FTS5 能力继续提供可解释的 L1 候选。
</p>

<h2>预算控制点</h2>
<table class="t">
  <tr><th>控制项</th><th>作用</th><th>为什么需要</th></tr>
  <tr><td class="mono">maxResults</td><td>限制最多格式化多少条 L1</td><td>避免命中很多时把 prompt 挤满。</td></tr>
  <tr><td class="mono">scoreThreshold</td><td>过滤低相关候选</td><td>宁可少注入，也不要把弱相关记忆带进本轮。</td></tr>
  <tr><td class="mono">timeoutMs</td><td>保护召回耗时</td><td>搜索慢或资源异常时，主对话继续。</td></tr>
  <tr><td class="mono">line truncation</td><td>把每条 memory 行裁成短摘要</td><td>L1 负责给模型线索，不负责搬运完整 transcript。</td></tr>
  <tr><td class="mono">applyRecallBudget</td><td>按总字符预算截断最终注入文本</td><td>让 recall 有边界，给用户问题和系统规则保留空间。</td></tr>
</table>

<h2>核心伪代码</h2>
<pre class="code">clean = sanitizeText(userText)
strategy = cfg.recall.strategy or "hybrid"
if strategy needs embedding and embedding not ready:
    strategy = "keyword"
if strategy == "hybrid":
    lines = searchHybrid(clean)  # local RRF merge inside auto-recall
else:
    candidates = search_one_strategy(clean)
    lines = format_top_results(candidates, maxResults, scoreThreshold)
return applyRecallBudget(lines, cfg.recall)</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：<span class="inline">searchMemories</span> 选择 <span class="inline">keyword</span>、<span class="inline">embedding</span>、<span class="inline">hybrid</span>；<span class="inline">searchByKeyword</span>、<span class="inline">searchByEmbedding</span>、<span class="inline">searchHybrid</span> 分别实现三条路径；<span class="inline">searchHybrid</span> 在自动召回路径内完成本地 RRF 合并；<span class="inline">formatMemoryLine</span> 生成最终注入行；<span class="inline">applyRecallBudget</span> 做最终裁剪。</li>
    <li><span class="inline">src/core/store/sqlite.ts</span>：<span class="inline">buildFtsQuery</span> 与 FTS5 helpers 负责关键词查询、BM25 排名和 SQLite 搜索细节。</li>
    <li><span class="inline">src/core/store/types.ts</span>：<span class="inline">L1SearchResult</span> 与 <span class="inline">L1FtsResult</span> 描述召回候选和 FTS 命中的结构。</li>
    <li><span class="inline">src/core/tools/memory-search.ts</span>：显式 memory search 工具路径；当自动召回只给出短片段时，可以用工具继续下钻。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L1 recall 的目标是“少量、相关、可追踪”。<span class="inline">keyword</span> 提供本地可解释检索，
  <span class="inline">embedding</span> 提供语义相似度，<span class="inline">hybrid</span> 用 RRF 合并两者；
  资源不可用时退回 <span class="inline">keyword</span>，最后由 <span class="inline">maxResults</span>、阈值和字符预算保证 prompt 不被记忆挤满。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Lesson 22 showed Auto Recall starting before prompt build; this lesson drills into L1 search itself.
<span class="inline">searchMemories()</span> sanitizes user text, then chooses <span class="inline">keyword</span>, <span class="inline">embedding</span>, or <span class="inline">hybrid</span>.
Recall output is not a full transcript. It is a compact set of relevant L1 snippets; deeper evidence can be fetched through the explicit memory search tool.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Think of a meeting assistant attaching three to five relevant sticky notes beside your speaking notes, not dropping the whole meeting archive into the room.
  The notes are found by words or semantics, then trimmed by budget; if semantic equipment is unavailable, the assistant safely falls back to keyword lookup.
</div>

<h2>The searchMemories recall pipeline</h2>
<div class="flow">
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">sanitizeText(userText)</span> removes untrusted control fragments and keeps text suitable for search.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">strategy</div><div class="nd">Config can select <span class="inline">keyword</span>, <span class="inline">embedding</span>, or <span class="inline">hybrid</span>; if unset, recall config supplies the default.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">candidates</div><div class="nd">FTS5 BM25 and/or vector cosine similarity produce candidate L1 memories.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">threshold / RRF</div><div class="nd">Single-strategy results are filtered by score; hybrid results are merged with RRF.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">budget</div><div class="nd"><span class="inline">maxResults</span> and character limits bound injection size.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">injected lines</div><div class="nd">Only concise L1 lines from <span class="inline">formatMemoryLine()</span> are injected: <span class="inline">- [type|scene] content</span>, optionally with activity time; id and score do not enter the prompt, so metrics that parse injected text should not rely on score.</div></div>
</div>

<h2>How the three strategies differ</h2>
<div class="cols">
  <div class="col"><h4>keyword</h4><p><span class="inline">searchByKeyword</span> uses SQLite FTS5. <span class="inline">buildFtsQuery</span> turns sanitized words into an FTS query, and BM25 ranks the results. This is good for exact terms, file names, and function names.</p></div>
  <div class="col"><h4>embedding</h4><p><span class="inline">searchByEmbedding</span> embeds the query, then finds L1 memories by cosine similarity. It works when the user asks with different wording, but it depends on embedding resources being ready.</p></div>
  <div class="col"><h4>hybrid</h4><p><span class="inline">searchHybrid</span> runs keyword and embedding, then performs a local RRF merge inside <span class="inline">auto-recall.ts</span>. The RRF constant makes high-ranked items win consistently instead of trusting one absolute score scale.</p></div>
</div>

<p>
Fallback is part of the design. If config selects <span class="inline">embedding</span> or <span class="inline">hybrid</span> but the embedding client, dimensions, or vector index are unavailable,
<span class="inline">searchMemories()</span> safely degrades to <span class="inline">keyword</span>.
That does not block the main chat and does not invent semantic scores; it keeps serving explainable L1 candidates through local FTS5.
</p>

<h2>Budget controls</h2>
<table class="t">
  <tr><th>Control</th><th>Effect</th><th>Why it matters</th></tr>
  <tr><td class="mono">maxResults</td><td>Limits how many L1 memories are formatted</td><td>Prevents many hits from crowding the prompt.</td></tr>
  <tr><td class="mono">scoreThreshold</td><td>Filters weak candidates</td><td>It is safer to inject less than to add loosely related memories.</td></tr>
  <tr><td class="mono">timeoutMs</td><td>Bounds recall latency</td><td>If search is slow or resources fail, the main chat continues.</td></tr>
  <tr><td class="mono">line truncation</td><td>Trims each memory line into a short summary</td><td>L1 gives the model clues; it does not transport full transcripts.</td></tr>
  <tr><td class="mono">applyRecallBudget</td><td>Truncates final injected text by total character budget</td><td>Recall stays bounded, leaving room for the user request and system rules.</td></tr>
</table>

<h2>Core pseudocode</h2>
<pre class="code">clean = sanitizeText(userText)
strategy = cfg.recall.strategy or "hybrid"
if strategy needs embedding and embedding not ready:
    strategy = "keyword"
if strategy == "hybrid":
    lines = searchHybrid(clean)  # local RRF merge inside auto-recall
else:
    candidates = search_one_strategy(clean)
    lines = format_top_results(candidates, maxResults, scoreThreshold)
return applyRecallBudget(lines, cfg.recall)</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: <span class="inline">searchMemories</span> selects <span class="inline">keyword</span>, <span class="inline">embedding</span>, or <span class="inline">hybrid</span>; <span class="inline">searchByKeyword</span>, <span class="inline">searchByEmbedding</span>, and <span class="inline">searchHybrid</span> implement the paths; <span class="inline">searchHybrid</span> owns the auto-recall local RRF merge; <span class="inline">formatMemoryLine</span> creates the injected lines; <span class="inline">applyRecallBudget</span> does final trimming.</li>
    <li><span class="inline">src/core/store/sqlite.ts</span>: <span class="inline">buildFtsQuery</span> and FTS5 helpers handle keyword query construction, BM25 ranking, and SQLite search details.</li>
    <li><span class="inline">src/core/store/types.ts</span>: <span class="inline">L1SearchResult</span> and <span class="inline">L1FtsResult</span> describe recall candidates and FTS hits.</li>
    <li><span class="inline">src/core/tools/memory-search.ts</span>: explicit memory search tool path; when automatic recall injects only short snippets, the tool can drill deeper.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L1 recall aims for "small, relevant, traceable". <span class="inline">keyword</span> provides local explainable search,
  <span class="inline">embedding</span> provides semantic similarity, and <span class="inline">hybrid</span> combines both with RRF.
  When resources are unavailable, recall falls back to <span class="inline">keyword</span>; then <span class="inline">maxResults</span>, thresholds, and character budgets keep memory from crowding the prompt.
</div>
""",
}
