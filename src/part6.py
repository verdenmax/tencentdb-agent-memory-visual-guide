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

<div class="card detail">
  <div class="tag">🧰 MEMORY_TOOLS_GUIDE 运行时约束</div>
  <ul>
    <li><span class="inline">tdai_memory_search</span> 查 L1 structured memory：适合找结构化事实、偏好、决策与摘要。</li>
    <li><span class="inline">tdai_conversation_search</span> 查 L0 raw conversation evidence：适合回到原始对话证据做补充或核验。</li>
    <li><span class="inline">read_file</span> 用于 Scene Navigation 给出的路径：先看地图，再读取相关 scene 文件下钻。</li>
    <li><span class="inline">tdai_memory_search</span> + <span class="inline">tdai_conversation_search</span> 每轮总共最多 3 次；如果 3 次搜索仍未命中，停止继续搜索，基于已有上下文回答。</li>
  </ul>
</div>

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
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>：刷新 scene 文件与索引，让 Scene Navigation 指向可读取的最新场景路径。</li>
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

<div class="card detail">
  <div class="tag">🧰 MEMORY_TOOLS_GUIDE runtime limits</div>
  <ul>
    <li><span class="inline">tdai_memory_search</span> searches L1 structured memory: facts, preferences, decisions, and summaries.</li>
    <li><span class="inline">tdai_conversation_search</span> searches L0 raw conversation evidence for supplementing or verifying original dialogue.</li>
    <li><span class="inline">read_file</span> follows Scene Navigation paths: inspect the map first, then open the relevant scene file for detail.</li>
    <li><span class="inline">tdai_memory_search</span> + <span class="inline">tdai_conversation_search</span> are limited to 3 total calls per turn; after 3 failed searches, stop searching and answer from available context.</li>
  </ul>
</div>

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
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>: refreshes scene files and indexes so Scene Navigation points to current readable scene paths.</li>
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


LESSON_25 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
本课把第 23 课的策略落到本地 SQLite store。<span class="inline">VectorStore</span> 在同一个
<span class="inline">vectors.db</span> 里维护元数据表、FTS5 虚拟表和 <span class="inline">sqlite-vec</span>
的 <span class="inline">vec0</span> 向量表：关键词召回用 FTS5/BM25，语义召回用 cosine distance，
混合召回在客户端做 RRF-style merge：使用共享 helper 或调用路径中的本地等价实现合并排名。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  这像一个本地资料柜有三套索引：登记表记录每份材料的 id、时间和分类；关键词卡片按词找材料；
  语义卡片按“意思相近”找材料。最后助理把两份候选清单做 RRF-style 融合，避免只相信一种索引。
</div>

<h2>本地 store 的四层结构</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">metadata</span><span class="name">l1_records / l0_conversations</span></div><div class="ld">普通 SQLite 表保存可展示、可过滤、可追溯的字段：L1 content/type/priority/scene/timestamps，L0 session、role、message_text 与 recorded_at。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">keyword</span><span class="name">l1_fts / l0_fts</span></div><div class="ld">FTS5 虚拟表保存分词后的索引列，并保留 original 文本用于展示；查询由 <span class="inline">buildFtsQuery()</span> 构造，结果按 <span class="inline">bm25()</span> rank 升序排列。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">vector</span><span class="name">l1_vec / l0_vec</span></div><div class="ld"><span class="inline">vec0</span> 表保存 embedding，使用 <span class="inline">distance_metric=cosine</span> 做近邻搜索；维度来自 embedding 配置。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">embedding</span><span class="name">provider + model + dimensions</span></div><div class="ld">embedding service 记录 provider/model/dimensions。provider、model 或维度变化会让旧向量不可比；store 初始化结合 embedding metadata 判断并触发 drop vec tables + reindex 路径。</div></div>
</div>

<h2>写入路径：一个事务包住元数据、FTS 和向量</h2>
<div class="flow">
  <div class="node"><div class="nt">write L1</div><div class="nd">L1 writer 传入 record 与可选 embedding。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">metadata insert</div><div class="nd"><span class="inline">l1_records</span> 用 <span class="inline">ON CONFLICT</span> 更新普通字段。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">FTS tokenize</div><div class="nd"><span class="inline">tokenizeForFts()</span> 写 <span class="inline">l1_fts</span>；FTS 失败只降级关键词索引。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">embedding</div><div class="nd">有可用向量时进入 vec0；无 embedding 时仍保留 metadata + FTS。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">vector upsert</div><div class="nd"><span class="inline">vec0</span> 不支持 <span class="inline">ON CONFLICT</span>，所以先 delete 再 insert。</div></div>
</div>

<p>
<span class="inline">sqlite.ts</span> 使用手动 <span class="inline">BEGIN</span>/<span class="inline">COMMIT</span>，
失败时 <span class="inline">ROLLBACK</span>，让 metadata、FTS 和 vector 尽量保持同一条记录的同步状态。
数据库开启 WAL mode，读写可以更稳地并行；但要记住，FTS 与 vec0 是派生索引，metadata 表才是可追溯事实的主记录。
</p>

<h2>三种召回列对比</h2>
<div class="cols">
  <div class="col"><h4>BM25 keyword recall</h4><p><span class="inline">buildFtsQuery(query)</span> 把用户输入变成可执行的 FTS5 查询；<span class="inline">bm25(l1_fts)</span> 或 <span class="inline">bm25(l0_fts)</span> 排名。适合精确术语、函数名、文件名、中文分词后关键词。</p></div>
  <div class="col"><h4>Vector semantic recall</h4><p>查询先经过同一个 embedding provider 编码，再在 <span class="inline">l1_vec</span>/<span class="inline">l0_vec</span> 上按 cosine distance 取最近邻。适合“换一种说法”的语义相似。</p></div>
  <div class="col"><h4>RRF-style hybrid</h4><p>本地 SQLite 没有服务端原生 hybrid rank；工具层分别拿 FTS 和 vector 候选，再用共享 RRF helper 或调用路径中的本地等价实现按名次加权融合，得到更稳的候选顺序。</p></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">writeMemory(record):
    begin_transaction()
    upsert(l1_records, record.metadata)
    upsert(l1_fts, tokenize_for_fts(record.content))
    if embedding_available:
        delete(l1_vec where record_id = record.id)
        insert(l1_vec, embed(record.content))
    commit()

hybrid(query):
    ftsRanked = searchL1Fts(buildFtsQuery(query))
    vecRanked = searchL1Vector(embed(query))
    return rrf_style_merge_or_local_equivalent([ftsRanked, vecRanked])</pre>

<h2>provider metadata 与 reindex</h2>
<p>
向量不是“纯文本索引”，它绑定了 provider、model 和 dimensions。同一段文字由不同模型生成的向量空间可能完全不同；
维度不同则 <span class="inline">vec0</span> 表结构也不兼容。因此 <span class="inline">embedding_meta</span>
检测到 provider/model/dimensions 改变时，要保留 <span class="inline">l1_records</span> 与
<span class="inline">l0_conversations</span>，重建 <span class="inline">l1_vec</span>/<span class="inline">l0_vec</span>，
再按当前 embedding service 重新索引。local provider 可能需要 warmup；remote provider 是 HTTP 调用，但二者都必须产出与配置维度一致的向量。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/store/sqlite.ts</span>：<span class="inline">VectorStore</span>、<span class="inline">buildFtsQuery</span>、<span class="inline">l1_records</span>/<span class="inline">l0_conversations</span>、FTS5 表、<span class="inline">vec0</span> 表、WAL、事务和 delete + insert upsert。</li>
    <li><span class="inline">src/core/store/search-utils.ts</span>：提供共享 RRF helper，用 <span class="inline">1 / (k + rank + 1)</span> 合并多路排名；具体 recall/search 路径可能调用该 helper，也可能保留本地等价实现。</li>
    <li><span class="inline">src/core/store/embedding.ts</span>：embedding provider info、dimensions、local/remote embedding service 与 not-ready 行为。</li>
    <li><span class="inline">src/core/store/factory.ts</span>：创建本地 SQLite store bundle、接线 embedding service、确定 <span class="inline">vectors.db</span> 路径，并提供 store snapshot；embedding drift / reindex 判断由 store 初始化与 embedding metadata 处理。</li>
    <li><span class="inline">src/core/tools/conversation-search.ts</span>：L0 对话搜索同时尝试 FTS5 与 vector，再把本地候选融合。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  SQLite 本地 store 把“事实记录”和“检索索引”分开：metadata 表负责可追溯事实，FTS5/BM25 负责关键词召回，sqlite-vec/vec0 负责语义召回。
  写入要用事务同步 metadata、FTS 与 vector；vec0 upsert 用 delete + insert；embedding provider 变化后旧向量不可比，通常需要 reindex。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
This lesson grounds Lesson 23's strategies in the local SQLite store. <span class="inline">VectorStore</span> keeps metadata tables,
FTS5 virtual tables, and <span class="inline">sqlite-vec</span> <span class="inline">vec0</span> vector tables in the same
<span class="inline">vectors.db</span>: keyword recall uses FTS5/BM25, semantic recall uses cosine distance, and hybrid recall does an RRF-style client-side merge through a shared helper or a local equivalent in the calling path.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Think of a local file cabinet with three indexes. A registry records each document's id, time, and category; keyword cards find documents by words; semantic cards find documents by nearby meaning. The assistant then fuses both candidate lists with an RRF-style merge instead of trusting only one index.
</div>

<h2>The four local store layers</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">metadata</span><span class="name">l1_records / l0_conversations</span></div><div class="ld">Ordinary SQLite tables store displayable, filterable, traceable fields: L1 content/type/priority/scene/timestamps, and L0 session, role, message_text, and recorded_at.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">keyword</span><span class="name">l1_fts / l0_fts</span></div><div class="ld">FTS5 virtual tables store tokenized index columns plus original text for display; <span class="inline">buildFtsQuery()</span> builds the query and <span class="inline">bm25()</span> ranks results ascending by rank.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">vector</span><span class="name">l1_vec / l0_vec</span></div><div class="ld"><span class="inline">vec0</span> tables store embeddings and use <span class="inline">distance_metric=cosine</span> for nearest-neighbor search; dimensions come from embedding config.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">embedding</span><span class="name">provider + model + dimensions</span></div><div class="ld">The embedding service records provider/model/dimensions. Provider, model, or dimension changes make old vectors incomparable; store initialization uses embedding metadata to decide when to drop vec tables and reindex.</div></div>
</div>

<h2>Write path: one transaction around metadata, FTS, and vectors</h2>
<div class="flow">
  <div class="node"><div class="nt">write L1</div><div class="nd">The L1 writer passes a record and optional embedding.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">metadata insert</div><div class="nd"><span class="inline">l1_records</span> uses <span class="inline">ON CONFLICT</span> to update normal fields.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">FTS tokenize</div><div class="nd"><span class="inline">tokenizeForFts()</span> writes <span class="inline">l1_fts</span>; FTS failures only degrade keyword indexing.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">embedding</div><div class="nd">When a usable vector exists, it enters vec0; without embedding, metadata + FTS still persist.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">vector upsert</div><div class="nd"><span class="inline">vec0</span> does not support <span class="inline">ON CONFLICT</span>, so upsert is delete then insert.</div></div>
</div>

<p>
<span class="inline">sqlite.ts</span> uses manual <span class="inline">BEGIN</span>/<span class="inline">COMMIT</span> and
<span class="inline">ROLLBACK</span> on failure, keeping metadata, FTS, and vector rows synchronized for a record as much as possible.
The database runs in WAL mode for safer concurrent reads and writes. Remember that FTS and vec0 are derived indexes; the metadata tables are the traceable source records.
</p>

<h2>Three recall columns</h2>
<div class="cols">
  <div class="col"><h4>BM25 keyword recall</h4><p><span class="inline">buildFtsQuery(query)</span> turns user input into an executable FTS5 query; <span class="inline">bm25(l1_fts)</span> or <span class="inline">bm25(l0_fts)</span> ranks matches. It is strong for exact terms, function names, file names, and tokenized Chinese keywords.</p></div>
  <div class="col"><h4>Vector semantic recall</h4><p>The query is encoded by the same embedding provider, then nearest neighbors are searched in <span class="inline">l1_vec</span>/<span class="inline">l0_vec</span> by cosine distance. This helps when users ask with different wording.</p></div>
  <div class="col"><h4>RRF-style hybrid</h4><p>Local SQLite has no server-side native hybrid rank. Tool code collects FTS and vector candidates separately, then uses a shared RRF helper or a local equivalent in the calling path to fuse rankings into a more robust order.</p></div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">writeMemory(record):
    begin_transaction()
    upsert(l1_records, record.metadata)
    upsert(l1_fts, tokenize_for_fts(record.content))
    if embedding_available:
        delete(l1_vec where record_id = record.id)
        insert(l1_vec, embed(record.content))
    commit()

hybrid(query):
    ftsRanked = searchL1Fts(buildFtsQuery(query))
    vecRanked = searchL1Vector(embed(query))
    return rrf_style_merge_or_local_equivalent([ftsRanked, vecRanked])</pre>

<h2>Provider metadata and reindexing</h2>
<p>
Vectors are not plain text indexes; they are bound to provider, model, and dimensions. The same text embedded by different models may live in incompatible vector spaces, and different dimensions make the <span class="inline">vec0</span> schema incompatible.
So when <span class="inline">embedding_meta</span> detects provider/model/dimensions changes, the store preserves <span class="inline">l1_records</span> and <span class="inline">l0_conversations</span>, rebuilds <span class="inline">l1_vec</span>/<span class="inline">l0_vec</span>, and reindexes with the current embedding service. A local provider may need warmup; a remote provider is HTTP-based, but both must emit vectors matching configured dimensions.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/store/sqlite.ts</span>: <span class="inline">VectorStore</span>, <span class="inline">buildFtsQuery</span>, <span class="inline">l1_records</span>/<span class="inline">l0_conversations</span>, FTS5 tables, <span class="inline">vec0</span> tables, WAL, transactions, and delete + insert upsert.</li>
    <li><span class="inline">src/core/store/search-utils.ts</span>: contains the shared RRF helper for merging ranked lists with <span class="inline">1 / (k + rank + 1)</span>; individual recall/search paths may call that helper or keep a local equivalent.</li>
    <li><span class="inline">src/core/store/embedding.ts</span>: embedding provider info, dimensions, local/remote embedding services, and not-ready behavior.</li>
    <li><span class="inline">src/core/store/factory.ts</span>: creates the local SQLite store bundle, wires the embedding service, resolves the <span class="inline">vectors.db</span> path, and exposes the store snapshot; embedding drift / reindex decisions are handled by store initialization and embedding metadata.</li>
    <li><span class="inline">src/core/tools/conversation-search.ts</span>: L0 conversation search tries FTS5 and vector search, then fuses local candidates.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The local SQLite store separates source records from retrieval indexes: metadata tables keep traceable facts, FTS5/BM25 handles keyword recall, and sqlite-vec/vec0 handles semantic recall.
  Writes synchronize metadata, FTS, and vectors inside a transaction; vec0 upsert is delete + insert; after an embedding provider change, old vectors are not comparable and usually need reindexing.
</div>
""",
}


LESSON_26 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
第 25 课介绍本地 SQLite store；最后一课切到远程后端。<span class="inline">TcvdbMemoryStore</span>
把 L1、L0 写入带 database 前缀的 Tencent Cloud VectorDB hybrid collections：dense embedding 使用 <span class="inline">tcvdb.embeddingModel</span> 对应的 1024 维索引，sparse vector 由客户端 BM25 encoder 生成，
再用原生 <span class="inline">hybridSearch</span> 与 RRF rerank 合并召回。profiles 是独立的同步/查询集合，不参与 hybrid recall；远程失败时，JSONL 与本地证据文件仍然让记忆系统可追溯、可恢复。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  SQLite 像随身资料柜，所有索引都在本机维护；TCVDB 像云端档案馆，登记、向量检索和混合重排都可以在服务端完成。
  但助理仍会随身带一份原始收据：即使云端一时不可用，本地 JSONL 和 evidence 文件也不会消失。
</div>

<h2>远程后端的五层结构</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">guide code</span><span class="name">factory + config</span></div><div class="ld"><span class="inline">factory.ts</span> 根据 <span class="inline">storeBackend = "tcvdb"</span> 选择 <span class="inline">TcvdbMemoryStore</span>，并返回 <span class="inline">NoopEmbeddingService</span> 作为本地 embedding service。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">store bundle</span><span class="name">TcvdbMemoryStore</span></div><div class="ld">创建 database 前缀 collection；L1/L0 暴露 native hybrid capability，profiles 走 metadata/profile sync 与 query。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">TCVDB client</span><span class="name">HTTP API client</span></div><div class="ld"><span class="inline">tcvdb-client.ts</span> 封装请求、超时和错误对象，避免把远程异常扩散成主对话失败。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">VectorDB collections</span><span class="name">L1/L0 hybrid + profiles metadata</span></div><div class="ld">L1/L0 含 1024 维 dense field、sparse vector 和 filters；profiles 禁用 embedding，使用 dummy vector <span class="inline">[0]</span>、维度 1、无 sparse index。</div></div>
  <div class="layer l-core"><div class="lh"><span class="badge">embedding services</span><span class="name">TCVDB embedding model + local sparse</span></div><div class="ld"><span class="inline">tcvdb.embeddingModel</span> 交给远程 VectorDB 生成 dense 向量；BM25 local encoder 只负责 L1/L0 的客户端 sparse vector。</div></div>
</div>

<h2>初始化到召回的流向</h2>
<div class="flow">
  <div class="node"><div class="nt">config</div><div class="nd">读取 <span class="inline">storeBackend: "tcvdb"</span>、url、username、apiKey、database、embeddingModel 与 timeout。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">create database/collections</div><div class="nd">创建数据库和 L1/L0/profile collections，集合名带 database 前缀。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">upsert L1/L0/profile</div><div class="nd">L1/L0 写元数据、dense text、client sparse vector 与 filters；profile 写同步元数据和 dummy vector。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">hybridSearch</div><div class="nd">服务端 dense embedding + sparse vector + RRF rerank 合成一次查询。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall/query</div><div class="nd">L1/L0 返回 hybrid recall 候选；profile API 单独按 metadata/profile 路径查询。</div></div>
</div>

<h2>本地 SQLite 与云端 TCVDB 对比</h2>
<div class="cols">
  <div class="col"><h4>SQLite local backend</h4><p>元数据、FTS5、sqlite-vec 和 JSONL 都在本地。混合搜索通常由客户端分别查 keyword/vector，再做 RRF-style 合并。优点是零云依赖、便于离线；限制是索引能力和并发能力跟随本机环境。</p></div>
  <div class="col"><h4>Tencent Cloud VectorDB backend</h4><p>L1/L0 集合、dense embedding 字段、sparse vector、filter indexes 和 native <span class="inline">hybridSearch</span> 下沉到 VectorDB；profiles 集合仅做 metadata/profile 同步查询。优点是统一远程检索、服务端 RRF rerank 与迁移/导出路径；要求配置、网络和凭据都可用。</p></div>
</div>

<h2>安全配置字段</h2>
<table class="t">
  <tr><th>字段</th><th>安全示例值</th><th>作用</th></tr>
  <tr><td class="mono">storeBackend</td><td class="mono">"tcvdb"</td><td>让 factory 选择 <span class="inline">TcvdbMemoryStore</span> 和 <span class="inline">NoopEmbeddingService</span>。</td></tr>
  <tr><td class="mono">tcvdb.url</td><td class="mono">https://tencent-vectordb.example.com</td><td>VectorDB HTTP endpoint，占位域名不能当真实地址。</td></tr>
  <tr><td class="mono">tcvdb.username</td><td class="mono">TENCENT_VECTORDB_USERNAME</td><td>用户名占位值，文档和示例不能写真实账号。</td></tr>
  <tr><td class="mono">tcvdb.apiKey</td><td class="mono">TENCENT_VECTORDB_API_KEY</td><td>API key 占位值，只说明从安全配置读取。</td></tr>
  <tr><td class="mono">tcvdb.database</td><td class="mono">agent_memory_demo</td><td>database 名，也用于 collection 前缀。</td></tr>
  <tr><td class="mono">tcvdb.embeddingModel</td><td class="mono">tencent-embedding-demo</td><td>交给 VectorDB 的 dense embedding 模型占位名；TCVDB L1/L0 索引维度由实现固定为 1024，不由用户配置。</td></tr>
  <tr><td class="mono">tcvdb.timeout</td><td class="mono">5000</td><td>远程请求超时毫秒数；超时后远程 search/upsert 按降级路径返回空结果或 no-op。</td></tr>
</table>

<h2>核心伪代码</h2>
<pre class="code">cfg = {
    storeBackend: "tcvdb",
    tcvdb: { url, username, apiKey, database, embeddingModel, timeout }
}
bundle = createStoreBundle(cfg)
// factory returns TcvdbMemoryStore + NoopEmbeddingService
store = new TcvdbMemoryStore({
    url, username, apiKey: "TENCENT_VECTORDB_API_KEY",
    database, embeddingModel, timeout, bm25Encoder
})
store.init():
    createDatabase()
    createCollection(database + "_l1_memories", dense_vector_1024, sparse_vector, filters)
    createCollection(database + "_l0_conversations", dense_vector_1024, sparse_vector, filters)
    createCollection(database + "_profiles", dummy_vector_dimension_1, metadata_only)

recall_hybrid(queryText, sparseVector, topK):
    ann = [{ fieldName: "text", data: [queryText], limit: topK }]
    match = [{ fieldName: "sparse_vector", data: [sparseVector], limit: topK }]
    params = {
        ann,
        match,
        limit: topK,
        outputFields: [...],
        rerank: { method: "rrf", k: 60 }
    }
    return collection.hybridSearch(params)</pre>

<p>
这里的伪代码对应简化的 <span class="inline">searchL1HybridAsync</span> 路径：L1/L0 集合仍会创建 filter indexes，其他查询路径也可以使用 filters；但这个 hybrid recall sketch 不传 <span class="inline">filter</span>。
</p>

<h2>降级、迁移与导出</h2>
<p>
远程后端不是主对话的硬依赖，但 <span class="inline">storeBackend: "tcvdb"</span> 不会自动维持 SQLite/local fallback search。
<span class="inline">factory.ts</span> 选择 TCVDB bundle 并返回 <span class="inline">NoopEmbeddingService</span>；<span class="inline">tcvdb-client.ts</span> 把 HTTP 错误、超时和响应解析收敛到客户端边界。
当 <span class="inline">TcvdbMemoryStore</span> 进入 degraded state 时，远程 search 可能返回空数组，upsert/delete 等远程写入可能 no-op，而不是切到本地 SQLite 查询。
</p>
<p>
降级不等于“证据消失”。capture/extraction 产生的 L0 JSONL、L1 evidence files、scene blocks 与 persona/profile 文件路径仍应保留，下一轮可以继续写可审计的本地证据或等待远程恢复。
已有本地 SQLite 数据可通过 <span class="inline">scripts/migrate-sqlite-to-tcvdb/sqlite-to-tcvdb.ts</span> 迁移到 TCVDB；远程集合也可通过
<span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span> 导出，保证上线和回滚都有可审计路径。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/store/tcvdb.ts</span>：<span class="inline">TcvdbMemoryStore</span>、collection creation、filter indexes、DISK_FLAT-to-HNSW fallback、L1/L0 hybrid upsert/search、profile metadata query/sync，以及 degraded state 下的空结果或 no-op。</li>
    <li><span class="inline">src/core/store/tcvdb-client.ts</span>：HTTP API client、timeout、错误处理和响应解析边界。</li>
    <li><span class="inline">src/core/store/bm25-local.ts</span>：客户端 sparse vector encoder，为 TCVDB hybrid search 提供稀疏向量。</li>
    <li><span class="inline">src/core/store/embedding.ts</span>：embedding service contract 与 <span class="inline">NoopEmbeddingService</span> 行为。</li>
    <li><span class="inline">src/core/store/factory.ts</span>：backend selection、TCVDB store bundle 创建，以及 <span class="inline">NoopEmbeddingService</span> return。</li>
    <li><span class="inline">scripts/migrate-sqlite-to-tcvdb/sqlite-to-tcvdb.ts</span>：从 SQLite 迁移到 TCVDB 的路径。</li>
    <li><span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span>：从 Tencent Cloud VectorDB 导出的路径。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  TCVDB 后端把 L1/L0 dense embedding、sparse vector、filter indexes 和 RRF rerank 下沉到远程 VectorDB；profiles 集合使用 dummy vector 与 metadata/profile query，不是 hybrid recall。
  安全配置只使用占位值；远程初始化或查询失败时，远程操作可能返回空结果或 no-op，并继续依靠 JSONL、evidence files、scene/persona 与迁移/导出路径保留可审计证据。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Lesson 25 explained the local SQLite store; the final M3 lesson switches to the remote backend. <span class="inline">TcvdbMemoryStore</span>
writes L1 and L0 into Tencent Cloud VectorDB hybrid collections prefixed by the database name: dense embeddings use the <span class="inline">tcvdb.embeddingModel</span> 1024-dimensional index,
sparse vectors are generated client-side by the BM25 encoder, and native <span class="inline">hybridSearch</span> with RRF rerank combines recall. Profiles use a separate sync/query collection rather than hybrid recall; if remote access fails, JSONL and local evidence files still keep memory traceable and recoverable.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  SQLite is a portable file cabinet with all indexes maintained locally; TCVDB is a cloud archive where registration, vector retrieval, and hybrid reranking can happen server-side.
  The assistant still carries raw receipts: even if the cloud archive is temporarily unavailable, local JSONL and evidence files do not disappear.
</div>

<h2>Five remote backend layers</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">guide code</span><span class="name">factory + config</span></div><div class="ld"><span class="inline">factory.ts</span> selects <span class="inline">TcvdbMemoryStore</span> when <span class="inline">storeBackend = "tcvdb"</span> and returns <span class="inline">NoopEmbeddingService</span> as the local embedding service.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">store bundle</span><span class="name">TcvdbMemoryStore</span></div><div class="ld">Creates database-prefixed collections; L1/L0 expose native hybrid capability, while profiles use metadata/profile sync and query paths.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">TCVDB client</span><span class="name">HTTP API client</span></div><div class="ld"><span class="inline">tcvdb-client.ts</span> wraps requests, timeouts, and error objects so remote failures do not become main-chat failures.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">VectorDB collections</span><span class="name">L1/L0 hybrid + profiles metadata</span></div><div class="ld">L1/L0 contain a 1024-dimensional dense field, sparse vectors, and filters; profiles disable embedding and use dummy vector <span class="inline">[0]</span>, dimension 1, and no sparse index.</div></div>
  <div class="layer l-core"><div class="lh"><span class="badge">embedding services</span><span class="name">TCVDB embedding model + local sparse</span></div><div class="ld"><span class="inline">tcvdb.embeddingModel</span> is passed to remote VectorDB for dense vectors; the BM25 local encoder only produces L1/L0 client-side sparse vectors.</div></div>
</div>

<h2>Flow from initialization to recall</h2>
<div class="flow">
  <div class="node"><div class="nt">config</div><div class="nd">Read <span class="inline">storeBackend: "tcvdb"</span>, url, username, apiKey, database, embeddingModel, and timeout.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">create database/collections</div><div class="nd">Create the database and L1/L0/profile collections with database-prefixed names.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">upsert L1/L0/profile</div><div class="nd">L1/L0 write metadata, dense text, client sparse vectors, and filters; profiles write sync metadata and a dummy vector.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">hybridSearch</div><div class="nd">Server-side dense embedding + sparse vector + RRF rerank are composed as one query.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall/query</div><div class="nd">L1/L0 return hybrid recall candidates; profile APIs query through separate metadata/profile paths.</div></div>
</div>

<h2>Local SQLite versus cloud TCVDB</h2>
<div class="cols">
  <div class="col"><h4>SQLite local backend</h4><p>Metadata, FTS5, sqlite-vec, and JSONL are local. Hybrid search usually collects keyword/vector candidates separately and does client-side RRF-style merging. It is cloud-free and offline-friendly; its indexing and concurrency follow the local machine.</p></div>
  <div class="col"><h4>Tencent Cloud VectorDB backend</h4><p>L1/L0 collections, dense embedding fields, sparse vectors, filter indexes, and native <span class="inline">hybridSearch</span> move into VectorDB; the profiles collection only does metadata/profile sync queries. It provides centralized remote retrieval, server-side RRF rerank, and migration/export paths; it requires valid config, network, and credentials.</p></div>
</div>

<h2>Safe configuration fields</h2>
<table class="t">
  <tr><th>Field</th><th>Safe example value</th><th>Purpose</th></tr>
  <tr><td class="mono">storeBackend</td><td class="mono">"tcvdb"</td><td>Lets the factory choose <span class="inline">TcvdbMemoryStore</span> and <span class="inline">NoopEmbeddingService</span>.</td></tr>
  <tr><td class="mono">tcvdb.url</td><td class="mono">https://tencent-vectordb.example.com</td><td>VectorDB HTTP endpoint; this placeholder domain is not a real address.</td></tr>
  <tr><td class="mono">tcvdb.username</td><td class="mono">TENCENT_VECTORDB_USERNAME</td><td>Username placeholder; docs and examples must not contain a real account.</td></tr>
  <tr><td class="mono">tcvdb.apiKey</td><td class="mono">TENCENT_VECTORDB_API_KEY</td><td>API key placeholder, indicating secure config lookup only.</td></tr>
  <tr><td class="mono">tcvdb.database</td><td class="mono">agent_memory_demo</td><td>Database name, also used as the collection prefix.</td></tr>
  <tr><td class="mono">tcvdb.embeddingModel</td><td class="mono">tencent-embedding-demo</td><td>Dense embedding model placeholder passed to VectorDB; the TCVDB L1/L0 index dimension is fixed at 1024 by the implementation, not configured by users.</td></tr>
  <tr><td class="mono">tcvdb.timeout</td><td class="mono">5000</td><td>Remote request timeout in milliseconds; timed-out remote search/upsert follows degraded behavior by returning empty results or no-op.</td></tr>
</table>

<h2>Core pseudocode</h2>
<pre class="code">cfg = {
    storeBackend: "tcvdb",
    tcvdb: { url, username, apiKey, database, embeddingModel, timeout }
}
bundle = createStoreBundle(cfg)
// factory returns TcvdbMemoryStore + NoopEmbeddingService
store = new TcvdbMemoryStore({
    url, username, apiKey: "TENCENT_VECTORDB_API_KEY",
    database, embeddingModel, timeout, bm25Encoder
})
store.init():
    createDatabase()
    createCollection(database + "_l1_memories", dense_vector_1024, sparse_vector, filters)
    createCollection(database + "_l0_conversations", dense_vector_1024, sparse_vector, filters)
    createCollection(database + "_profiles", dummy_vector_dimension_1, metadata_only)

recall_hybrid(queryText, sparseVector, topK):
    ann = [{ fieldName: "text", data: [queryText], limit: topK }]
    match = [{ fieldName: "sparse_vector", data: [sparseVector], limit: topK }]
    params = {
        ann,
        match,
        limit: topK,
        outputFields: [...],
        rerank: { method: "rrf", k: 60 }
    }
    return collection.hybridSearch(params)</pre>

<p>
This pseudocode mirrors the simplified <span class="inline">searchL1HybridAsync</span> path: L1/L0 collections still create filter indexes, and other query paths can use filters, but this hybrid recall sketch does not pass <span class="inline">filter</span>.
</p>

<h2>Degradation, migration, and export</h2>
<p>
The remote backend is not a hard dependency of the main chat, but <span class="inline">storeBackend: "tcvdb"</span> does not keep automatic SQLite/local fallback search.
<span class="inline">factory.ts</span> selects the TCVDB bundle and returns <span class="inline">NoopEmbeddingService</span>; <span class="inline">tcvdb-client.ts</span> keeps HTTP errors, timeouts, and response parsing at the client boundary.
When <span class="inline">TcvdbMemoryStore</span> enters degraded state, remote search may return an empty array and remote upsert/delete may no-op instead of switching to local SQLite queries.
</p>
<p>
Degradation does not mean evidence disappears. L0 JSONL, L1 evidence files, scene blocks, and persona/profile file paths produced by capture/extraction should remain available, so the next turn can keep auditable local evidence or wait for remote recovery.
Existing SQLite data can be migrated with <span class="inline">scripts/migrate-sqlite-to-tcvdb/sqlite-to-tcvdb.ts</span>; remote collections can be exported with
<span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span>, keeping rollout and rollback auditable.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/store/tcvdb.ts</span>: <span class="inline">TcvdbMemoryStore</span>, collection creation, filter indexes, DISK_FLAT-to-HNSW fallback, L1/L0 hybrid upsert/search, profile metadata query/sync, and degraded-state empty results or no-op behavior.</li>
    <li><span class="inline">src/core/store/tcvdb-client.ts</span>: HTTP API client, timeout, error handling, and response parsing boundary.</li>
    <li><span class="inline">src/core/store/bm25-local.ts</span>: client-side sparse vector encoder for TCVDB hybrid search.</li>
    <li><span class="inline">src/core/store/embedding.ts</span>: embedding service contract and <span class="inline">NoopEmbeddingService</span> behavior.</li>
    <li><span class="inline">src/core/store/factory.ts</span>: backend selection, TCVDB store bundle creation, and <span class="inline">NoopEmbeddingService</span> return.</li>
    <li><span class="inline">scripts/migrate-sqlite-to-tcvdb/sqlite-to-tcvdb.ts</span>: migration path from SQLite to TCVDB.</li>
    <li><span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span>: export path from Tencent Cloud VectorDB.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The TCVDB backend pushes L1/L0 dense embedding, sparse vectors, filter indexes, and RRF rerank into remote VectorDB; the profiles collection uses a dummy vector and metadata/profile query, not hybrid recall.
  Safe config uses placeholders only; when remote initialization or query fails, remote operations may return empty results or no-op while JSONL, evidence files, scene/persona, and migration/export paths keep auditable evidence.
</div>
""",
}
