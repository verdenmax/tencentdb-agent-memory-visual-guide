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
  便签可以由云端档案柜一次完成“关键词 + 语义”混合查找，也可以由本地助理分别查两份清单后再合并；如果配置里根本没有语义设备，就按关键词查。
</div>

<h2>searchMemories 的召回管线</h2>
<div class="flow">
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">sanitizeText(userText)</span> 去掉不可信控制片段，只保留适合检索的文本。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">strategy</div><div class="nd">配置可选 <span class="inline">keyword</span>、<span class="inline">embedding</span>、<span class="inline">hybrid</span>；未显式配置时按 recall 配置默认值决定。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">candidates</div><div class="nd">FTS5 BM25 和/或向量余弦相似度产生候选 L1。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">threshold / hybrid rank</div><div class="nd">关键词或 embedding 单路结果用 <span class="inline">scoreThreshold</span> 过滤；混合路径优先由原生 store 执行，否则本地候选用 RRF 排名。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">budget</div><div class="nd"><span class="inline">maxResults</span> 与字符预算限制注入规模。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">injected lines</div><div class="nd">只注入 <span class="inline">formatMemoryLine()</span> 生成的简洁 L1 行：<span class="inline">- [type|scene] content</span>，可附活动时间；id 和 score 不进入 prompt，解析注入文本的指标不应依赖 score。</div></div>
</div>

<h2>三种策略怎么选</h2>
<div class="cols">
  <div class="col"><h4>keyword</h4><p><span class="inline">searchByKeyword</span> 走 SQLite FTS5。<span class="inline">buildFtsQuery</span> 把清洗后的词变成 FTS 查询，结果用 BM25 排序，适合精确术语、文件名、函数名。</p></div>
  <div class="col"><h4>embedding</h4><p><span class="inline">searchByEmbedding</span> 先把 query 编成向量，再用余弦相似度找语义接近的 L1。它适合用户换一种说法提问，但依赖 embedding 资源可用。</p></div>
  <div class="col"><h4>hybrid</h4><p>混合召回有两条路：如果 store 声明 <span class="inline">nativeHybridSearch</span>，例如 TCVDB 的 <span class="inline">hybridSearch</span>，就让服务端完成 dense + sparse/RRF-like 混合；SQLite 或非原生路径才由本地 <span class="inline">searchHybrid()</span> 分别跑 keyword 与 embedding，再在 <span class="inline">auto-recall.ts</span> 内部做 RRF 合并。</p></div>
</div>

<p>
降级规则要读窄一点：当配置选择 <span class="inline">embedding</span> 或 <span class="inline">hybrid</span>，但没有配置 vector store 或 embedding service 时，
<span class="inline">searchMemories()</span> 会走 <span class="inline">keyword</span> 路径。
这不是“任何运行时向量/index 错误都必然降级”的承诺；实际异常仍受调用链、timeout 和错误处理保护，主对话应继续，但本轮不一定还能拿到关键词结果。
</p>

<h2>预算控制点</h2>
<table class="t">
  <tr><th>控制项</th><th>作用</th><th>为什么需要</th></tr>
  <tr><td class="mono">maxResults</td><td>限制最多格式化多少条 L1</td><td>避免命中很多时把 prompt 挤满。</td></tr>
  <tr><td class="mono">scoreThreshold</td><td>过滤 keyword 或 embedding 单策略候选</td><td>阈值主要作用在单路分数上；本地 hybrid 更依赖候选数量、RRF 排名、<span class="inline">maxResults</span> 和字符预算，原生 hybrid 则接收 <span class="inline">topK</span>/store-side 行为。</td></tr>
  <tr><td class="mono">timeoutMs</td><td>保护召回耗时</td><td>搜索慢或资源异常时，主对话继续。</td></tr>
  <tr><td class="mono">line truncation</td><td>把每条 memory 行裁成短摘要</td><td>L1 负责给模型线索，不负责搬运完整 transcript。</td></tr>
  <tr><td class="mono">applyRecallBudget</td><td>按总字符预算截断最终注入文本</td><td>让 recall 有边界，给用户问题和系统规则保留空间。</td></tr>
</table>

<h2>核心伪代码</h2>
<pre class="code">clean = sanitizeText(userText)
strategy = cfg.recall.strategy or "hybrid"
if strategy needs embedding and (no vectorStore or no embeddingService):
    strategy = "keyword"
if strategy == "hybrid":
    if vectorStore.nativeHybridSearch:
        lines = vectorStore.searchL1Hybrid(query=clean, topK=maxResults)
    else:
        lines = searchHybrid(clean, maxResults)  # local candidate lists + RRF
else:
    candidates = search_one_strategy(clean)
    lines = format_top_results(candidates, maxResults, scoreThreshold)
return applyRecallBudget(lines, cfg.recall)</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/config.ts</span> 与 <span class="inline">openclaw.plugin.json</span>：配置默认值包括 <span class="inline">recall.strategy = "hybrid"</span>、<span class="inline">maxResults = 5</span>、<span class="inline">scoreThreshold = 0.3</span>、<span class="inline">timeoutMs = 5000</span>。</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：<span class="inline">searchMemories</span> 选择 <span class="inline">keyword</span>、<span class="inline">embedding</span>、<span class="inline">hybrid</span>；先检查 vector store 与 embedding service 是否配置，再决定是否退回关键词；<span class="inline">searchHybrid</span> 只负责非原生路径的本地 RRF 合并；<span class="inline">formatMemoryLine</span> 生成最终注入行；<span class="inline">applyRecallBudget</span> 做最终裁剪。</li>
    <li><span class="inline">src/core/store/types.ts</span>：<span class="inline">StoreCapabilities.nativeHybridSearch</span> 表示 store 是否支持原生混合检索；<span class="inline">L1SearchResult</span> 与 <span class="inline">L1FtsResult</span> 描述召回候选和 FTS 命中的结构。</li>
    <li><span class="inline">src/core/store/tcvdb.ts</span> 与 <span class="inline">src/core/store/tcvdb-client.ts</span>：TCVDB 后端通过 <span class="inline">searchL1HybridAsync</span>/<span class="inline">hybridSearch</span> 走服务端 dense + sparse/RRF-like 混合检索。</li>
    <li><span class="inline">src/core/store/sqlite.ts</span>：<span class="inline">buildFtsQuery</span> 与 FTS5 helpers 负责关键词查询、BM25 排名和 SQLite 搜索细节。</li>
    <li><span class="inline">src/core/tools/memory-search.ts</span>：显式 memory search 工具路径；当自动召回只给出短片段时，可以用工具继续下钻。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L1 recall 的目标是“少量、相关、可追踪”。<span class="inline">keyword</span> 提供本地可解释检索，
  <span class="inline">embedding</span> 提供语义相似度，<span class="inline">hybrid</span> 可能是 TCVDB 等原生 store-side 混合，也可能是本地 <span class="inline">searchHybrid()</span> 的 RRF fallback。
  未配置 vector store 或 embedding service 时可退回 <span class="inline">keyword</span>；单策略阈值、混合排名、<span class="inline">maxResults</span> 和字符预算共同保证 prompt 不被记忆挤满。
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
  A cloud archive may do "keyword + semantics" in one hybrid lookup, or a local assistant may search two lists and merge them; if semantic equipment was never configured, the assistant uses keywords.
</div>

<h2>The searchMemories recall pipeline</h2>
<div class="flow">
  <div class="node"><div class="nt">sanitized query</div><div class="nd"><span class="inline">sanitizeText(userText)</span> removes untrusted control fragments and keeps text suitable for search.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">strategy</div><div class="nd">Config can select <span class="inline">keyword</span>, <span class="inline">embedding</span>, or <span class="inline">hybrid</span>; if unset, recall config supplies the default.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">candidates</div><div class="nd">FTS5 BM25 and/or vector cosine similarity produce candidate L1 memories.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">threshold / hybrid rank</div><div class="nd">Keyword or embedding single-strategy results use <span class="inline">scoreThreshold</span>; hybrid uses native store ranking when available, otherwise local candidates are RRF-ranked.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">budget</div><div class="nd"><span class="inline">maxResults</span> and character limits bound injection size.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">injected lines</div><div class="nd">Only concise L1 lines from <span class="inline">formatMemoryLine()</span> are injected: <span class="inline">- [type|scene] content</span>, optionally with activity time; id and score do not enter the prompt, so metrics that parse injected text should not rely on score.</div></div>
</div>

<h2>How the three strategies differ</h2>
<div class="cols">
  <div class="col"><h4>keyword</h4><p><span class="inline">searchByKeyword</span> uses SQLite FTS5. <span class="inline">buildFtsQuery</span> turns sanitized words into an FTS query, and BM25 ranks the results. This is good for exact terms, file names, and function names.</p></div>
  <div class="col"><h4>embedding</h4><p><span class="inline">searchByEmbedding</span> embeds the query, then finds L1 memories by cosine similarity. It works when the user asks with different wording, but it depends on embedding resources being ready.</p></div>
  <div class="col"><h4>hybrid</h4><p>Hybrid has two paths. If the store declares <span class="inline">nativeHybridSearch</span>, such as TCVDB <span class="inline">hybridSearch</span>, the server does dense + sparse/RRF-like retrieval. SQLite and other non-native paths use local <span class="inline">searchHybrid()</span>: run keyword and embedding separately, then merge rankings with RRF inside <span class="inline">auto-recall.ts</span>.</p></div>
</div>

<p>
Read fallback narrowly. If config selects <span class="inline">embedding</span> or <span class="inline">hybrid</span> but no vector store or embedding service is configured,
<span class="inline">searchMemories()</span> uses the <span class="inline">keyword</span> path.
This is not a guarantee that every runtime vector/index failure will produce keyword results; those failures are still bounded by timeout and error handling so the main chat can continue, but this turn may have no recall.
</p>

<h2>Budget controls</h2>
<table class="t">
  <tr><th>Control</th><th>Effect</th><th>Why it matters</th></tr>
  <tr><td class="mono">maxResults</td><td>Limits how many L1 memories are formatted</td><td>Prevents many hits from crowding the prompt.</td></tr>
  <tr><td class="mono">scoreThreshold</td><td>Filters keyword or embedding single-strategy candidates</td><td>The threshold mainly applies to one scoring scale. Local hybrid relies more on candidate count, RRF rank, <span class="inline">maxResults</span>, and character budgets; native hybrid receives <span class="inline">topK</span> and store-side ranking behavior.</td></tr>
  <tr><td class="mono">timeoutMs</td><td>Bounds recall latency</td><td>If search is slow or resources fail, the main chat continues.</td></tr>
  <tr><td class="mono">line truncation</td><td>Trims each memory line into a short summary</td><td>L1 gives the model clues; it does not transport full transcripts.</td></tr>
  <tr><td class="mono">applyRecallBudget</td><td>Truncates final injected text by total character budget</td><td>Recall stays bounded, leaving room for the user request and system rules.</td></tr>
</table>

<h2>Core pseudocode</h2>
<pre class="code">clean = sanitizeText(userText)
strategy = cfg.recall.strategy or "hybrid"
if strategy needs embedding and (no vectorStore or no embeddingService):
    strategy = "keyword"
if strategy == "hybrid":
    if vectorStore.nativeHybridSearch:
        lines = vectorStore.searchL1Hybrid(query=clean, topK=maxResults)
    else:
        lines = searchHybrid(clean, maxResults)  # local candidate lists + RRF
else:
    candidates = search_one_strategy(clean)
    lines = format_top_results(candidates, maxResults, scoreThreshold)
return applyRecallBudget(lines, cfg.recall)</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/config.ts</span> and <span class="inline">openclaw.plugin.json</span>: config defaults include <span class="inline">recall.strategy = "hybrid"</span>, <span class="inline">maxResults = 5</span>, <span class="inline">scoreThreshold = 0.3</span>, and <span class="inline">timeoutMs = 5000</span>.</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: <span class="inline">searchMemories</span> selects <span class="inline">keyword</span>, <span class="inline">embedding</span>, or <span class="inline">hybrid</span>; checks whether vector store and embedding service are configured before keyword fallback; <span class="inline">searchHybrid</span> owns only the non-native local RRF merge; <span class="inline">formatMemoryLine</span> creates injected lines; <span class="inline">applyRecallBudget</span> does final trimming.</li>
    <li><span class="inline">src/core/store/types.ts</span>: <span class="inline">StoreCapabilities.nativeHybridSearch</span> marks stores that can perform native hybrid search; <span class="inline">L1SearchResult</span> and <span class="inline">L1FtsResult</span> describe recall candidates and FTS hits.</li>
    <li><span class="inline">src/core/store/tcvdb.ts</span> and <span class="inline">src/core/store/tcvdb-client.ts</span>: the TCVDB backend uses <span class="inline">searchL1HybridAsync</span>/<span class="inline">hybridSearch</span> for server-side dense + sparse/RRF-like hybrid retrieval.</li>
    <li><span class="inline">src/core/store/sqlite.ts</span>: <span class="inline">buildFtsQuery</span> and FTS5 helpers handle keyword query construction, BM25 ranking, and SQLite search details.</li>
    <li><span class="inline">src/core/tools/memory-search.ts</span>: explicit memory search tool path; when automatic recall injects only short snippets, the tool can drill deeper.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L1 recall aims for "small, relevant, traceable". <span class="inline">keyword</span> provides local explainable search,
  <span class="inline">embedding</span> provides semantic similarity, and <span class="inline">hybrid</span> may be native store-side retrieval such as TCVDB or local <span class="inline">searchHybrid()</span> RRF fallback.
  Missing vector store or embedding service can fall back to <span class="inline">keyword</span>; single-strategy thresholds, hybrid ranking, <span class="inline">maxResults</span>, and character budgets keep memory from crowding the prompt.
</div>
""",
}


LESSON_24 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
第 22、23 课解释了 Auto Recall 与 L1 搜索。本课看召回结果如何分层注入：每轮变化的 L1 片段进入
<span class="inline">prependContext</span>，贴在 user prompt 前；相对稳定的 L3 persona、L2 Scene Navigation 与工具指南进入
<span class="inline">appendSystemContext</span>，追加到 system prompt 末尾。这样既让模型看到长期画像和场景地图，又尽量不破坏 provider 的 prompt cache。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  这像助理给你准备会议材料：今天临时相关的便签放在发言稿最前面；长期稳定的个人偏好、项目目录和“需要时去哪里查”的说明放在会议手册后附录。
  便签每轮都换，附录大多不变，所以缓存友好。
</div>

<h2>三段 prompt 位置</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">system tail</span><span class="name">appendSystemContext</span></div><div class="ld">稳定上下文：<span class="inline">&lt;user-persona&gt;</span> 包住去掉旧导航后的 persona，<span class="inline">&lt;scene-navigation&gt;</span> 包住场景索引导航，再追加 <span class="inline">MEMORY_TOOLS_GUIDE</span>。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">user prefix</span><span class="name">prependContext</span></div><div class="ld">动态上下文：本轮 <span class="inline">searchMemories()</span> 找到的 L1 snippets，放在 <span class="inline">&lt;relevant-memories&gt;</span> 中，贴近用户问题。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">user text</span><span class="name">current request</span></div><div class="ld">用户真正输入的问题保持在后面；capture 仍使用原始 prompt，避免把注入内容写回 L0/L1 证据。</div></div>
</div>

<h2>persona 与 navigation 怎么组合</h2>
<div class="flow">
  <div class="node"><div class="nt">persona.md</div><div class="nd">可能已经带有上一轮追加的 Scene Navigation。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">strip navigation</div><div class="nd"><span class="inline">stripSceneNavigation()</span> 去掉旧导航，避免 persona 注入时重复携带过期地图。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">user-persona tag</div><div class="nd">只把纯 persona 包进 <span class="inline">&lt;user-persona&gt;</span>。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">scene index</div><div class="nd"><span class="inline">generateSceneNavigation()</span> 从最新 index 生成路径、热度、摘要。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">scene-navigation tag</div><div class="nd">包进 <span class="inline">&lt;scene-navigation&gt;</span>，指导 agent 用 <span class="inline">read_file</span> 下钻。</div></div>
</div>

<p>
<span class="inline">persona-generator.ts</span> 写 <span class="inline">persona.md</span> 时也会先 strip 旧导航，再把新的 Scene Navigation 追加回文件。
Auto Recall 再次读取 <span class="inline">persona.md</span> 时仍会 strip：这是“双保险”。文件里保留导航方便人和 agent 打开 persona 后继续探索；注入时拆成 persona 与 navigation 两块，避免旧导航混进 persona 画像本体。
</p>

<h2>为什么不是注入完整场景</h2>
<div class="cols">
  <div class="col"><h4>自动注入</h4><p>自动路径只提供地图：场景文件 path、热度、更新时间和 summary。它告诉模型“哪里可能有完整证据”，但不把所有 scene block 塞进 prompt。</p></div>
  <div class="col"><h4>显式工具搜索</h4><p>当回答需要细节时，agent 应主动调用 <span class="inline">read_file</span> 读取相关场景，或用 <span class="inline">tdai_memory_search</span> 查 L1、<span class="inline">tdai_conversation_search</span> 查 L0 原文证据。</p></div>
</div>

<p>
Scene Navigation 的设计是 progressive disclosure：先给索引，不给全集。完整场景可能很长，而且不是每轮都相关；把它们全部自动注入会挤占用户问题、系统规则和 L1 相关片段。
导航里的绝对路径让 agent 在确实需要“项目背景、事件经过、阶段结论”时，用 <span class="inline">read_file</span> 精准下钻。
</p>

<h2>核心伪代码</h2>
<pre class="code">stableParts = []
if persona.md exists:
    stableParts.append("&lt;user-persona&gt;" + stripSceneNavigation(persona) + "&lt;/user-persona&gt;")
if scene_index exists:
    stableParts.append("&lt;scene-navigation&gt;" + generateSceneNavigation(index, dataDir) + "&lt;/scene-navigation&gt;")
if stableParts or l1Lines:
    stableParts.append(MEMORY_TOOLS_GUIDE)
prependContext = format_relevant_l1(l1Lines)
appendSystemContext = join(stableParts)</pre>

<h2>为什么更利于 prompt cache</h2>
<p>
很多 provider 的 prompt cache 对稳定前缀或稳定 system 区域更友好。L3 persona、L2 navigation 和工具指南变化频率低，放在 system 末尾可以在连续多轮中保持相同内容；L1 召回每轮跟着用户问题变化，如果也放进 system，就会频繁让系统上下文失效。
把动态 L1 移到 user 前缀，既保持本轮相关性，也让稳定 system-tail 内容更可能复用缓存。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：读取 L1、persona、scene index；用 <span class="inline">stripSceneNavigation</span> 清理 persona；生成 <span class="inline">prependContext</span> 与 <span class="inline">appendSystemContext</span>；追加 <span class="inline">MEMORY_TOOLS_GUIDE</span>。</li>
    <li><span class="inline">src/core/scene/scene-navigation.ts</span>：<span class="inline">generateSceneNavigation</span> 输出 read-file-ready 的场景地图；<span class="inline">stripSceneNavigation</span> 删除旧导航段。</li>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>：生成 persona 时先剥离旧导航，LLM 写完后再追加新的 Scene Navigation 到 <span class="inline">persona.md</span>。</li>
    <li><span class="inline">src/core/tools/memory-search.ts</span>：显式 L1 deeper retrieval；自动召回不够时由 agent 主动查结构化记忆。</li>
    <li><span class="inline">src/core/tools/conversation-search.ts</span>：L0 evidence search tool，用于补充或校验原始对话证据。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Recall output 被拆成动态和稳定两类：L1 相关片段进入 <span class="inline">prependContext</span>，L3 persona、L2 navigation 与工具指南进入 <span class="inline">appendSystemContext</span>。
  Persona 注入前要剥离旧导航；Scene Navigation 只给可 <span class="inline">read_file</span> 下钻的地图；稳定 system-tail 内容更有利于 prompt cache。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Lessons 22 and 23 covered Auto Recall and L1 search. This lesson explains how recall output is split before prompt injection: per-turn L1 snippets go into
<span class="inline">prependContext</span>, before the user prompt; relatively stable L3 persona, L2 Scene Navigation, and the tool guide go into
<span class="inline">appendSystemContext</span>, appended to the system prompt tail. The model sees long-term profile and scene maps, while provider prompt caching stays friendlier.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Think of a meeting assistant preparing materials. Today's relevant sticky notes go at the front of your speaking notes; stable preferences, the project directory, and "where to look next" instructions live in an appendix.
  Sticky notes change every turn; the appendix mostly stays the same, so it is cache-friendly.
</div>

<h2>Three prompt positions</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">system tail</span><span class="name">appendSystemContext</span></div><div class="ld">Stable context: <span class="inline">&lt;user-persona&gt;</span> wraps persona after old navigation is stripped, <span class="inline">&lt;scene-navigation&gt;</span> wraps the scene index navigation, then <span class="inline">MEMORY_TOOLS_GUIDE</span> is appended.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">user prefix</span><span class="name">prependContext</span></div><div class="ld">Dynamic context: this turn's L1 snippets from <span class="inline">searchMemories()</span>, wrapped in <span class="inline">&lt;relevant-memories&gt;</span> and placed near the user request.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">user text</span><span class="name">current request</span></div><div class="ld">The user's real input remains after the prefix; capture still uses the original prompt so injected content is not written back into L0/L1 evidence.</div></div>
</div>

<h2>How persona and navigation combine</h2>
<div class="flow">
  <div class="node"><div class="nt">persona.md</div><div class="nd">May already include Scene Navigation appended during an earlier persona generation.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">strip navigation</div><div class="nd"><span class="inline">stripSceneNavigation()</span> removes the old navigation so injection does not carry duplicate or stale maps.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">user-persona tag</div><div class="nd">Only clean persona is wrapped in <span class="inline">&lt;user-persona&gt;</span>.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">scene index</div><div class="nd"><span class="inline">generateSceneNavigation()</span> builds paths, heat, update time, and summaries from the latest index.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">scene-navigation tag</div><div class="nd">Wrapped in <span class="inline">&lt;scene-navigation&gt;</span> so the agent can drill down with <span class="inline">read_file</span>.</div></div>
</div>

<p>
<span class="inline">persona-generator.ts</span> also strips old navigation before writing <span class="inline">persona.md</span>, then appends fresh Scene Navigation back to the file.
Auto Recall strips again when reading <span class="inline">persona.md</span>: that is a second guard. Keeping navigation in the file helps humans and agents explore from persona, while injection separates persona from navigation so stale maps do not become profile content.
</p>

<h2>Why not inject full scenes automatically</h2>
<div class="cols">
  <div class="col"><h4>Automatic injection</h4><p>The automatic path gives a map: scene file path, heat, update time, and summary. It tells the model where full evidence may live without dumping every scene block into the prompt.</p></div>
  <div class="col"><h4>Explicit tool search</h4><p>When an answer needs detail, the agent should call <span class="inline">read_file</span> for the relevant scene, or use <span class="inline">tdai_memory_search</span> for L1 and <span class="inline">tdai_conversation_search</span> for raw L0 evidence.</p></div>
</div>

<p>
Scene Navigation is progressive disclosure: index first, full content only on demand. Full scenes can be long and are not relevant to every turn; automatic full injection would crowd out the user request, system rules, and relevant L1 snippets.
Absolute paths in navigation let the agent drill down with <span class="inline">read_file</span> only when it needs project background, event history, or stage conclusions.
</p>

<h2>Core pseudocode</h2>
<pre class="code">stableParts = []
if persona.md exists:
    stableParts.append("&lt;user-persona&gt;" + stripSceneNavigation(persona) + "&lt;/user-persona&gt;")
if scene_index exists:
    stableParts.append("&lt;scene-navigation&gt;" + generateSceneNavigation(index, dataDir) + "&lt;/scene-navigation&gt;")
if stableParts or l1Lines:
    stableParts.append(MEMORY_TOOLS_GUIDE)
prependContext = format_relevant_l1(l1Lines)
appendSystemContext = join(stableParts)</pre>

<h2>Why this is better for prompt cache</h2>
<p>
Many providers make prompt caching friendlier for stable prefixes or stable system regions. L3 persona, L2 navigation, and the tool guide change infrequently, so placing them at the system tail lets consecutive turns keep identical content; L1 recall changes with each user request.
If dynamic L1 also lived in system context, it would frequently bust the system cache. Moving L1 to the user prefix keeps turn relevance while letting stable system-tail content be reused more often.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: reads L1, persona, and scene index; strips persona navigation; creates <span class="inline">prependContext</span> and <span class="inline">appendSystemContext</span>; appends <span class="inline">MEMORY_TOOLS_GUIDE</span>.</li>
    <li><span class="inline">src/core/scene/scene-navigation.ts</span>: <span class="inline">generateSceneNavigation</span> emits a read-file-ready scene map; <span class="inline">stripSceneNavigation</span> removes old navigation blocks.</li>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>: strips old navigation during persona generation, then appends fresh Scene Navigation to <span class="inline">persona.md</span>.</li>
    <li><span class="inline">src/core/tools/memory-search.ts</span>: explicit L1 deeper retrieval when automatic recall is not enough.</li>
    <li><span class="inline">src/core/tools/conversation-search.ts</span>: L0 evidence search tool for supplementing or verifying raw conversation evidence.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Recall output is split into dynamic and stable parts: relevant L1 snippets go into <span class="inline">prependContext</span>, while L3 persona, L2 navigation, and the tool guide go into <span class="inline">appendSystemContext</span>.
  Persona is stripped of old navigation before injection; Scene Navigation provides a <span class="inline">read_file</span> drill-down map; stable system-tail content is better for prompt caching.
</div>
""",
}
