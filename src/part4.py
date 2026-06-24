"""Part 4 content: L0 and L1 capture, extraction, dedup."""

LESSON_12 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
当一轮对话已经提交（<span class="inline">agent_end</span> / <span class="inline">turn committed</span>）后，
<span class="inline">performAutoCapture</span> 负责把本轮新增的用户与助手消息可靠落到 L0。
它先做最短、最确定的捕获路径：写本地 L0，再尽量建立搜索索引，最后通知 pipeline scheduler；是否触发 L1 抽取由 scheduler 根据阈值、idle timer 和状态决定。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  对话提交后像收银小票已经打印出来：Auto Capture 先把小票存进本地账本，避免丢单；再把小票编号放进索引柜，方便以后搜索；最后提醒后台整理员“有新账了”。
  至于后台整理员现在就归档，还是等凑够一批再处理，是调度规则决定的，不是收银台临时决定。
</div>

<h2>提交后的捕获主线</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>agent_end / turn committed</h4><p>宿主把完整 messages 交给 <span class="inline">performAutoCapture</span>，此时模型回答已产生，捕获不再影响本轮生成内容。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>checkpoint lock</h4><p><span class="inline">CheckpointManager.captureAtomically()</span> 持锁读取 cursor、调用 <span class="inline">recordConversation</span>、推进 cursor，避免并发 agent_end 读到同一个旧游标。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>record L0</h4><p><span class="inline">recordConversation</span> 从本轮消息中抽取 user / assistant，按位置切片与时间游标过滤，清洗后写入 conversations JSONL。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>index</h4><p>如果 vector / FTS store 可用，把 <span class="inline">L0Record</span> 元数据写入搜索索引；不可用时不阻断本地 L0 记录。</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>notify scheduler</h4><p>调用 <span class="inline">scheduler.notifyConversation(sessionKey, [])</span>。Capture 只通知“有新对话轮次”，L1 何时跑由 scheduler 决定。</p></div></div>
</div>

<h2>一次 messages 如何变成 L0Record</h2>
<div class="flow">
  <div class="node"><div class="nt">messages</div><div class="nd">agent_end 提供的会话历史</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">filteredMessages</div><div class="nd">只保留新增 user / assistant，清理召回包裹与结构噪声</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L0Record</div><div class="nd">id、sessionKey、sessionId、role、content、recordedAt、timestamp</div></div>
</div>

<p>
关键是“新增”：<span class="inline">recordConversation</span> 优先使用 before-prompt 阶段缓存的 <span class="inline">originalUserMessageCount</span> 做位置切片，
只看本轮 prompt build 之后追加的消息；如果这个缓存不可用，<span class="inline">captureAtomically</span> 会在原子区内读取 checkpoint 自己维护的 <span class="inline">afterTimestamp</span> 游标并传给回调过滤。
调用方不在临界区外提供 cursor；checkpoint 在同一个锁内负责 cursor 的读取与推进。因此 Auto Capture 不是把整段历史反复写入 L0，而是把提交后新出现的消息增量写入。
</p>

<h2>同步路径 vs 延迟 embedding 路径</h2>
<div class="cols">
  <div class="col"><h4>同步 embedding / VDB 路径</h4><p>当 store 不支持延迟 embedding 时，capture 会在 upsert L0 前尽量同步生成 embedding，再把 <span class="inline">L0Record</span> 和向量一起写入后端。这适合需要一次性提交向量的远程或 VDB 后端。</p></div>
  <div class="col"><h4>延迟 embedding / SQLite 路径</h4><p>当 store 支持 <span class="inline">supportsDeferredEmbedding</span>，capture 先写 metadata + FTS，马上返回主流程；embedding batch 和 <span class="inline">updateL0Embedding</span> 在后台补齐，避免 agent_end 被 多秒级向量调用阻塞。</p></div>
</div>

<h2>伪代码</h2>
<pre class="code">performAutoCapture(messages):
    checkpoint.captureAtomically(sessionKey, pluginStartTimestamp, (afterTimestamp) =&gt; {
        filtered = recordConversation(messages, afterTimestamp)
        return { maxTimestamp: maxTimestamp(filtered), messageCount: filtered.length }
    })
    ...
    scheduler.notifyConversation(sessionKey, [])</pre>

<h2>为什么 capture 不直接抽取 L1</h2>
<p>
<span class="inline">performAutoCapture</span> 的职责是可靠记录和通知。它不知道当前会话是否达到 <span class="inline">everyNConversations</span>，
也不应该复制 idle timeout、warm-up、重试和 shutdown flush 等策略。<span class="inline">MemoryPipelineManager.notifyConversation</span>
更新会话计数、持久化状态，并在达到阈值时 enqueue L1；未达到阈值时重置 idle timer。这样捕获路径更短，调度策略集中在 pipeline manager。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>：<span class="inline">performAutoCapture</span>、L0 写入、L0 vector indexing、<span class="inline">scheduler.notifyConversation</span></li>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>：<span class="inline">recordConversation</span>、位置切片、timestamp cursor、JSONL 写入</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>：<span class="inline">captureAtomically</span> 在锁内拥有并读写 cursor 与计数</li>
    <li><span class="inline">src/core/store/types.ts</span>：<span class="inline">L0Record</span> 的索引记录结构</li>
    <li><span class="inline">src/utils/pipeline-manager.ts</span>：<span class="inline">notifyConversation</span>、L1 threshold / idle trigger</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Auto Capture 的顺序是：提交后增量捕获、原子更新 checkpoint、本地 L0 优先、可用时索引 L0、通知 scheduler。
  这条路径只负责“可靠地把事实放进系统”，L1 抽取时机由 pipeline scheduler 统一裁决。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
After a turn is committed (<span class="inline">agent_end</span> / <span class="inline">turn committed</span>),
<span class="inline">performAutoCapture</span> reliably records the new user and assistant messages into L0.
It keeps the capture path short and deterministic: write local L0 first, index it for search when possible, then notify the pipeline scheduler; whether L1 extraction runs is a scheduler decision.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  After checkout, the receipt already exists. Auto Capture first saves that receipt in the local ledger so it is not lost, then places its number in a search cabinet, then tells the back-office clerk “new work arrived”.
  Whether the clerk files it immediately or waits for a batch is scheduling policy, not a decision made at the register.
</div>

<h2>The post-commit capture path</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>agent_end / turn committed</h4><p>The host passes the full messages array to <span class="inline">performAutoCapture</span>. The model response already exists, so capture no longer changes this turn's generation.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>checkpoint lock</h4><p><span class="inline">CheckpointManager.captureAtomically()</span> holds the lock while reading the cursor, calling <span class="inline">recordConversation</span>, and advancing the cursor. That prevents concurrent agent_end events from reading the same stale cursor.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>record L0</h4><p><span class="inline">recordConversation</span> extracts user / assistant messages for this turn, filters them by position slice and timestamp cursor, sanitizes them, and appends them to conversations JSONL.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>index</h4><p>If a vector / FTS store is available, capture writes <span class="inline">L0Record</span> metadata into the search index. If it is unavailable, local L0 recording still stands.</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>notify scheduler</h4><p>Capture calls <span class="inline">scheduler.notifyConversation(sessionKey, [])</span>. It only says “a new conversation round exists”; scheduler policy decides when L1 runs.</p></div></div>
</div>

<h2>How messages become an L0Record</h2>
<div class="flow">
  <div class="node"><div class="nt">messages</div><div class="nd">session history from agent_end</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">filteredMessages</div><div class="nd">new user / assistant messages, cleaned of recall wrappers and structural noise</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L0Record</div><div class="nd">id, sessionKey, sessionId, role, content, recordedAt, timestamp</div></div>
</div>

<p>
The important word is “new”. <span class="inline">recordConversation</span> prefers the <span class="inline">originalUserMessageCount</span>
recorded before prompt build and slices the raw messages after that position; if that cache is unavailable, <span class="inline">captureAtomically</span> reads the checkpoint-owned <span class="inline">afterTimestamp</span> cursor inside the atomic section and passes it to the callback for filtering.
The caller does not provide a cursor outside the critical section; checkpoint owns cursor read/update under the same lock. Auto Capture therefore does not keep rewriting the whole history into L0. It appends only the incremental messages that appeared after the committed turn.
</p>

<h2>Sync path vs deferred embedding path</h2>
<div class="cols">
  <div class="col"><h4>Sync embedding / VDB path</h4><p>When the store does not support deferred embedding, capture tries to embed synchronously before upserting L0, then writes the <span class="inline">L0Record</span> and vector together. This fits remote or VDB backends that need the vector up front.</p></div>
  <div class="col"><h4>Deferred embedding / SQLite path</h4><p>When the store supports <span class="inline">supportsDeferredEmbedding</span>, capture writes metadata + FTS first and returns to the main path quickly. Embedding batch and <span class="inline">updateL0Embedding</span> run in the background, avoiding a multi-second embedding call on agent_end.</p></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">performAutoCapture(messages):
    checkpoint.captureAtomically(sessionKey, pluginStartTimestamp, (afterTimestamp) =&gt; {
        filtered = recordConversation(messages, afterTimestamp)
        return { maxTimestamp: maxTimestamp(filtered), messageCount: filtered.length }
    })
    ...
    scheduler.notifyConversation(sessionKey, [])</pre>

<h2>Why capture does not run L1 directly</h2>
<p>
<span class="inline">performAutoCapture</span> is responsible for reliable recording and notification. It should not duplicate policy such as
<span class="inline">everyNConversations</span>, idle timeout, warm-up, retries, or shutdown flush. <span class="inline">MemoryPipelineManager.notifyConversation</span>
updates the conversation count, persists state, enqueues L1 when the threshold is reached, and otherwise resets the idle timer. That keeps capture short while scheduling policy stays centralized.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>: <span class="inline">performAutoCapture</span>, L0 writes, L0 vector indexing, <span class="inline">scheduler.notifyConversation</span></li>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>: <span class="inline">recordConversation</span>, position slice, timestamp cursor, JSONL append</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>: <span class="inline">captureAtomically</span> owns cursor and count read/update inside the lock</li>
    <li><span class="inline">src/core/store/types.ts</span>: <span class="inline">L0Record</span> index record shape</li>
    <li><span class="inline">src/utils/pipeline-manager.ts</span>: <span class="inline">notifyConversation</span>, L1 threshold / idle triggers</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Auto Capture's order is: post-commit incremental capture, atomic checkpoint update, local L0 first, index L0 when available, notify the scheduler.
  This path only makes facts reliably available to the system; the pipeline scheduler decides when L1 extraction runs.
</div>
""",
}


LESSON_13 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L0 不是摘要层，而是“原始对话证据层”：它把可追溯的 user / assistant 消息按 JSONL 追加到本地文件中。
<span class="inline">recordConversation</span> 只负责从原始 messages 中找出本次新增内容，清洗召回包裹、元数据和结构噪声，再一行一条写入当天文件。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  L0 像法庭证物袋，不像会议纪要。证物袋要保存“当时看到的原文”，方便以后核查；纪要可以提炼观点，但不能替代证物。
  所以 L0 先写原文账本，L1/L2/L3 才在后面从账本中抽取结构化记忆。
</div>

<h2>L0 的边界：证据，不是结论</h2>
<div class="cols">
  <div class="col"><h4>L0 raw evidence</h4><p>保存单条消息、角色、时间、会话标识与清洗后的正文。它强调可追加、可 grep、可流式读取、可回放排查。</p></div>
  <div class="col"><h4>L1 extracted memory</h4><p>从多条 L0 中抽取事实、偏好、任务片段或经验。它是解释后的结果，必须能回到 L0 找证据。</p></div>
</div>

<h2>从原始会话到 JSONL</h2>
<div class="flow">
  <div class="node"><div class="nt">raw session messages</div><div class="nd">宿主传入的完整历史</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">slice</div><div class="nd">按位置或 timestamp cursor 只取新增消息</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">filter</div><div class="nd">只保留 user / assistant，跳过不应捕获内容</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">sanitize</div><div class="nd">移除召回包裹、标记、元数据与结构噪声</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">JSONL</div><div class="nd">按天追加，一行一条消息</div></div>
</div>

<p>
<span class="inline">src/core/conversation/l0-recorder.ts</span> 中的 <span class="inline">recordConversation</span>
接收会话消息、会话标识与游标信息。它优先用位置切片避免重复写入；当位置缓存缺失时，再用 timestamp cursor 排除已经记录过的消息。
随后 <span class="inline">extractUserAssistantMessages</span> 只提取 user / assistant 消息，避免把 system、tool 或中间协议文本混进 L0。
</p>

<h2>JSONL 字段</h2>
<table class="t">
  <thead><tr><th>字段</th><th>含义</th><th>为什么重要</th></tr></thead>
  <tbody>
    <tr><td><span class="inline">id</span></td><td>单条 L0 记录 ID</td><td>供索引、去重和回查引用</td></tr>
    <tr><td><span class="inline">sessionKey</span></td><td>逻辑会话键</td><td>把同一任务或窗口的记录归组</td></tr>
    <tr><td><span class="inline">sessionId</span></td><td>宿主会话 ID</td><td>保留宿主侧可追溯来源</td></tr>
    <tr><td><span class="inline">role</span></td><td>user 或 assistant</td><td>区分问题、回答和后续抽取方向</td></tr>
    <tr><td><span class="inline">content</span></td><td>清洗后的消息正文</td><td>L1 抽取与人工排查的原文输入；向量或索引层可能映射为不同文本字段</td></tr>
    <tr><td><span class="inline">timestamp</span> / <span class="inline">recordedAt</span></td><td>消息时间与记录时间</td><td>支持游标过滤、排序和审计</td></tr>
  </tbody>
</table>

<h2>按天写入，而不是一个巨型文件</h2>
<p>
<span class="inline">src/utils/time.ts</span> 的 <span class="inline">formatLocalDate</span> 生成本地日期，L0 recorder 用它决定当天 JSONL 文件名。
这种布局让追加写入很便宜，也让排查时可以按日期定位：今天的 agent 任务只查今天文件，历史导出也可以按天流式处理。
</p>

<h2>清洗和“还原原始 prompt”</h2>
<div class="cols">
  <div class="col"><h4>清洗后再写入</h4><p><span class="inline">src/utils/sanitize.ts</span> 的 <span class="inline">sanitizeText</span> 会移除注入的 memory/context 包裹、召回标记、元数据、时间戳、媒体/base64 和结构噪声；prompt-injection 与内容质量拒绝推迟到 L1 的 <span class="inline">shouldExtractL1</span>。</p></div>
  <div class="col"><h4>被 prepend 污染时回退</h4><p><span class="inline">index.ts</span> 中的 <span class="inline">pendingOriginalPrompts</span> 缓存原始用户 prompt。当 <span class="inline">originalUserText</span> 与匹配的目标消息/timestamp 可用时，recorder 会恢复缓存的原始 prompt；否则回退到清洗与日志记录。</p></div>
</div>

<p>
这一步很关键：L0 要记录用户真正说了什么，而不是“用户消息 + 系统召回上下文”的拼接物。
否则后续 L1 会把 recall 注入的旧记忆误当成本轮新事实，造成证据污染和重复抽取。
</p>

<h2>伪代码</h2>
<pre class="code">recordConversation(rawMessages):
    new_messages = slice_by_position_or_timestamp(rawMessages)
    user_assistant = extract_user_assistant(new_messages)
    clean = sanitize_and_filter(user_assistant)
    append_jsonl(daily_file, clean)</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>：<span class="inline">recordConversation</span>、<span class="inline">extractUserAssistantMessages</span>、位置切片、timestamp cursor、JSONL 追加</li>
    <li><span class="inline">src/utils/sanitize.ts</span>：<span class="inline">sanitizeText</span>、<span class="inline">shouldCaptureL0</span>、召回包裹、元数据与结构噪声清理</li>
    <li><span class="inline">src/utils/time.ts</span>：<span class="inline">formatLocalDate</span>、按本地日期生成 daily file</li>
    <li><span class="inline">index.ts</span>：<span class="inline">pendingOriginalPrompts</span> 缓存被 prepend 前的原始 prompt</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L0 是可追溯证据层：JSONL 一行一条消息，按天追加，带 <span class="inline">sessionKey</span> / <span class="inline">sessionId</span>，
  先切片去重，再提取 user / assistant，清洗召回包裹和结构噪声；当原文缓存与目标消息匹配时恢复原始 prompt，否则回退到清洗与日志。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L0 is not a summary layer. It is the raw conversation evidence layer: append traceable user / assistant messages into local JSONL files.
<span class="inline">recordConversation</span> finds the new messages in the raw messages array, removes recall wrappers, metadata, and structural noise, then writes one message per line to the daily file.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  L0 is an evidence bag, not meeting minutes. The evidence bag keeps what was seen at the time so it can be inspected later; minutes may summarize ideas, but they cannot replace evidence.
  L0 writes the raw ledger first, and L1/L2/L3 extract structured memory from that ledger afterward.
</div>

<h2>L0's boundary: evidence, not conclusions</h2>
<div class="cols">
  <div class="col"><h4>L0 raw evidence</h4><p>Stores each message, role, time, session identifiers, and sanitized text. It favors appendability, grep, streaming reads, and replayable debugging.</p></div>
  <div class="col"><h4>L1 extracted memory</h4><p>Extracts facts, preferences, task fragments, or lessons from multiple L0 messages. It is an interpreted result and should be traceable back to L0 evidence.</p></div>
</div>

<h2>Raw conversation to JSONL</h2>
<div class="flow">
  <div class="node"><div class="nt">raw session messages</div><div class="nd">complete history from the host</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">slice</div><div class="nd">take only new messages by position or timestamp cursor</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">filter</div><div class="nd">keep user / assistant and skip non-capturable text</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">sanitize</div><div class="nd">remove recall wrappers, markers, metadata, and structural noise</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">JSONL</div><div class="nd">daily append, one message per line</div></div>
</div>

<p>
In <span class="inline">src/core/conversation/l0-recorder.ts</span>, <span class="inline">recordConversation</span>
receives session messages, session identifiers, and cursor data. It prefers a position slice to avoid duplicate writes; if that cache is unavailable, it uses a timestamp cursor to exclude messages already recorded.
Then <span class="inline">extractUserAssistantMessages</span> extracts only user / assistant messages so system, tool, or protocol text does not enter L0.
</p>

<h2>JSONL fields</h2>
<table class="t">
  <thead><tr><th>Field</th><th>Meaning</th><th>Why it matters</th></tr></thead>
  <tbody>
    <tr><td><span class="inline">id</span></td><td>Single L0 record ID</td><td>Used for indexing, dedup, and evidence lookup</td></tr>
    <tr><td><span class="inline">sessionKey</span></td><td>Logical session key</td><td>Groups records from the same task or window</td></tr>
    <tr><td><span class="inline">sessionId</span></td><td>Host session ID</td><td>Preserves the traceable host source</td></tr>
    <tr><td><span class="inline">role</span></td><td>user or assistant</td><td>Separates requests, answers, and extraction direction</td></tr>
    <tr><td><span class="inline">content</span></td><td>Sanitized message body</td><td>Raw input for L1 extraction and human inspection; vector or indexing layers may map text into different fields</td></tr>
    <tr><td><span class="inline">timestamp</span> / <span class="inline">recordedAt</span></td><td>Message time and record time</td><td>Supports cursor filtering, ordering, and audit</td></tr>
  </tbody>
</table>

<h2>Daily files, not one giant file</h2>
<p>
<span class="inline">formatLocalDate</span> in <span class="inline">src/utils/time.ts</span> produces the local date, and the L0 recorder uses it to choose the daily JSONL filename.
This layout keeps appends cheap and makes inspection date-scoped: today's agent task can read today's file, while historical export can stream day by day.
</p>

<h2>Sanitization and restoring the original prompt</h2>
<div class="cols">
  <div class="col"><h4>Sanitize before writing</h4><p><span class="inline">sanitizeText</span> in <span class="inline">src/utils/sanitize.ts</span> removes injected memory/context wrappers, recall markers, metadata, timestamps, media/base64, and structural noise; prompt-injection and content-quality rejection is deferred to L1 <span class="inline">shouldExtractL1</span>.</p></div>
  <div class="col"><h4>Fall back when prepend polluted it</h4><p><span class="inline">pendingOriginalPrompts</span> in <span class="inline">index.ts</span> caches the original user prompt. When <span class="inline">originalUserText</span> and a matching target message/timestamp are available, the recorder restores the cached original prompt; otherwise it falls back to sanitization and logging.</p></div>
</div>

<p>
That replacement is essential: L0 should record what the user actually said, not “user message plus system recall context”.
Otherwise L1 may treat old recalled memory as a new fact from this turn, creating evidence pollution and duplicate extraction.
</p>

<h2>Pseudocode</h2>
<pre class="code">recordConversation(rawMessages):
    new_messages = slice_by_position_or_timestamp(rawMessages)
    user_assistant = extract_user_assistant(new_messages)
    clean = sanitize_and_filter(user_assistant)
    append_jsonl(daily_file, clean)</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>: <span class="inline">recordConversation</span>, <span class="inline">extractUserAssistantMessages</span>, position slice, timestamp cursor, JSONL append</li>
    <li><span class="inline">src/utils/sanitize.ts</span>: <span class="inline">sanitizeText</span>, <span class="inline">shouldCaptureL0</span>, recall wrapper, metadata, and structural noise cleanup</li>
    <li><span class="inline">src/utils/time.ts</span>: <span class="inline">formatLocalDate</span>, daily files by local date</li>
    <li><span class="inline">index.ts</span>: <span class="inline">pendingOriginalPrompts</span> caches the original prompt before prepend</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L0 is the traceable evidence layer: JSONL uses one message per line, appends by day, carries <span class="inline">sessionKey</span> / <span class="inline">sessionId</span>,
  slices before extracting user / assistant messages, cleans recall wrappers and structural noise, and restores the original prompt when cached text matches the target message; otherwise it falls back to sanitization and logging.
</div>
""",
}


LESSON_14 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Checkpoint 是捕获路径里的“防重复保险”。重复 L0 捕获通常不是因为 JSONL 自己会重复，而是两个
<span class="inline">agent_end</span> / Gateway 调用并发进入，或者某次捕获读到了过期 cursor。
本课把 <span class="inline">captureAtomically()</span>、position slice、timestamp cursor 和 scheduler 启动门放在同一张图里看。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  把 L0 想成仓库入库单。两名库管如果同时看见“上一张单号是 100”，就都可能把 101 号货物登记一遍。
  正确做法是先锁住登记簿：读到 100、写入新单、把游标推进到 101，这三步完成后再交给下一位库管。
</div>

<h2>没有锁时：旧游标会制造重复捕获</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>并发入口</h4><p>OpenClaw 的 <span class="inline">agent_end</span> 和 Gateway capture 可能几乎同时提交同一会话的 messages。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>读到同一个旧 cursor</h4><p>如果 cursor 在临界区外读取，两个调用都可能看到 <span class="inline">afterTimestamp = T0</span>。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>重复写 L0</h4><p>两个 recorder 都认为 T0 之后的消息是新增，于是相同 user / assistant 记录被追加两次。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>迟到推进</h4><p>最后才写 checkpoint 已经太晚：重复证据已经进入 L0，后续 L1 也可能重复抽取。</p></div></div>
</div>

<h2>有锁时：cursor 读取、写入、推进成为一个原子区</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>captureAtomically(sessionKey)</h4><p><span class="inline">CheckpointManager</span> 按会话键加锁，让同一 session 的捕获串行进入。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>read checkpoint</h4><p>在锁内读取 timestamp cursor、记录计数和其他 checkpoint 状态，调用方不携带外部旧 cursor。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>record L0</h4><p>回调调用 <span class="inline">recordConversation</span>，只写 cursor 或位置切片之后真正新增的消息。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>advance cursor</h4><p>如果本次写入了消息，就在同一把锁内把 checkpoint 推进到新记录的最大 timestamp。</p></div></div>
</div>

<h2>伪代码</h2>
<pre class="code">captureAtomically(sessionKey):
    lock(sessionKey)
    cursor = read_checkpoint()
    messages = record_after_cursor(cursor)
    if messages:
        write_checkpoint(max_timestamp(messages))
    unlock(sessionKey)</pre>

<h2>position slice 与 timestamp cursor 分工不同</h2>
<div class="cols">
  <div class="col"><h4>position slice</h4><p>优先使用 prompt build 前缓存的 message count，例如 <span class="inline">originalUserMessageCount</span>。提交后只取这个位置之后的数组切片，能避免同一轮 messages 中 timestamp 漂移、同毫秒或宿主改写时间造成的边界误判。</p></div>
  <div class="col"><h4>timestamp cursor</h4><p>当位置缓存不可用时，checkpoint 中的 <span class="inline">afterTimestamp</span> 仍是增量捕获的 fallback。它也是审计证据：可以解释“上次捕获推进到了哪一刻，为什么这条消息被认为是新增”。</p></div>
</div>

<p>
因此二者不是互相替代：position slice 保护“本轮新增范围”的结构边界，timestamp cursor 保护跨调用的持久增量边界。
一个防数组位置漂移，一个防进程重启或缺少缓存时失去增量依据。
</p>

<h2>schedulerStartPromise：启动状态不能覆盖并发 capture</h2>
<div class="flow">
  <div class="node"><div class="nt">Gateway starts</div><div class="nd">恢复 scheduler 持久化状态</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">schedulerStartPromise</div><div class="nd">所有调用等待同一个启动 promise</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">capture / notify</div><div class="nd">启动完成后再通知会话计数</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">no clobber</div><div class="nd">恢复状态不会覆盖并发捕获刚写入的状态</div></div>
</div>

<p>
<span class="inline">TdaiCore.schedulerStartPromise</span> 解决的是另一类竞态：Gateway 恢复 scheduler 状态时，
同时到来的 capture 如果直接通知 scheduler，可能先写入新计数，随后又被“刚恢复出来的旧状态”覆盖。
启动 promise 把恢复过程变成一道门，让并发调用共享同一个启动结果，而不是各自抢跑。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/utils/checkpoint.ts</span>：<span class="inline">CheckpointManager</span>、<span class="inline">captureAtomically</span>、按 sessionKey 锁住 cursor 读写</li>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>：position slice、timestamp cursor、增量提取 user / assistant 消息</li>
    <li><span class="inline">src/core/tdai-core.ts</span>：<span class="inline">schedulerStartPromise</span> 防止恢复状态覆盖并发通知</li>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>：<span class="inline">performAutoCapture</span> 如何进入 checkpoint 原子捕获并通知 scheduler</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  重复捕获的风险来自并发 capture 与 stale cursor。<span class="inline">captureAtomically()</span>
  把“读游标 -&gt; 写 L0 -&gt; 推进游标”锁成关键区；position slice 优先保护同一轮消息边界，timestamp cursor 作为持久 fallback 与审计证据；
  <span class="inline">schedulerStartPromise</span> 则防止 scheduler 启动恢复覆盖同时发生的捕获通知。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Checkpoints are the duplicate-prevention safety rail in the capture path. Duplicate L0 capture usually does not come from JSONL itself;
it comes from concurrent <span class="inline">agent_end</span> / Gateway calls, or from a capture that reads a stale cursor.
This lesson connects <span class="inline">captureAtomically()</span>, position slicing, timestamp cursors, and the scheduler start gate.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  Think of L0 as a warehouse intake ledger. If two clerks both see “the last receipt was 100”, both may register the same item as 101.
  The fix is to lock the ledger: read 100, write the new receipt, advance the cursor to 101, then let the next clerk in.
</div>

<h2>Without the lock: stale cursors duplicate capture</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Concurrent entry</h4><p>OpenClaw <span class="inline">agent_end</span> and Gateway capture can submit messages for the same session at nearly the same time.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Same old cursor</h4><p>If the cursor is read outside the critical section, both calls may observe <span class="inline">afterTimestamp = T0</span>.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Duplicate L0 writes</h4><p>Both recorders believe messages after T0 are new, so the same user / assistant records are appended twice.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Late advance</h4><p>Writing the checkpoint afterward is too late: duplicate evidence has already entered L0, and L1 may extract it twice.</p></div></div>
</div>

<h2>With the lock: cursor read, write, and advance are atomic</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>captureAtomically(sessionKey)</h4><p><span class="inline">CheckpointManager</span> locks by session key so captures for the same session enter serially.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>read checkpoint</h4><p>The timestamp cursor, record count, and checkpoint state are read under the lock; callers do not bring an external stale cursor.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>record L0</h4><p>The callback calls <span class="inline">recordConversation</span> and writes only messages truly new after the cursor or position slice.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>advance cursor</h4><p>If messages were written, the same lock advances the checkpoint to the maximum timestamp from this capture.</p></div></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">captureAtomically(sessionKey):
    lock(sessionKey)
    cursor = read_checkpoint()
    messages = record_after_cursor(cursor)
    if messages:
        write_checkpoint(max_timestamp(messages))
    unlock(sessionKey)</pre>

<h2>Position slice and timestamp cursor solve different problems</h2>
<div class="cols">
  <div class="col"><h4>position slice</h4><p>The recorder prefers the cached message count from before prompt build, such as <span class="inline">originalUserMessageCount</span>. After commit it slices the array after that position, protecting the turn boundary from timestamp drift, same-millisecond messages, or host timestamp rewrites.</p></div>
  <div class="col"><h4>timestamp cursor</h4><p>When the position cache is unavailable, the checkpoint <span class="inline">afterTimestamp</span> remains the fallback for incremental capture. It is also evidence: it explains where the previous capture advanced and why this message counted as new.</p></div>
</div>

<p>
So they are not substitutes. Position slice protects the structural boundary of “messages added by this turn”.
Timestamp cursor protects the persistent incremental boundary across calls, restarts, or missing caches.
</p>

<h2>schedulerStartPromise: restored state must not clobber concurrent capture</h2>
<div class="flow">
  <div class="node"><div class="nt">Gateway starts</div><div class="nd">restore persisted scheduler state</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">schedulerStartPromise</div><div class="nd">all callers await one startup promise</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">capture / notify</div><div class="nd">notify conversation counts after startup</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">no clobber</div><div class="nd">restored state does not overwrite concurrent capture state</div></div>
</div>

<p>
<span class="inline">TdaiCore.schedulerStartPromise</span> handles a different race: while Gateway restores scheduler state,
a simultaneous capture could notify the scheduler, write a fresh count, and then be overwritten by an older restored snapshot.
The promise turns startup into a gate, so concurrent callers share the same startup result instead of racing ahead independently.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/utils/checkpoint.ts</span>: <span class="inline">CheckpointManager</span>, <span class="inline">captureAtomically</span>, sessionKey-scoped cursor locking</li>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>: position slice, timestamp cursor, incremental user / assistant extraction</li>
    <li><span class="inline">src/core/tdai-core.ts</span>: <span class="inline">schedulerStartPromise</span> prevents restored state from clobbering concurrent notifications</li>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>: how <span class="inline">performAutoCapture</span> enters atomic checkpoint capture and notifies the scheduler</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Duplicate capture risk comes from concurrent capture and stale cursors. <span class="inline">captureAtomically()</span>
  locks “read cursor -&gt; write L0 -&gt; advance cursor” as the critical section; position slice protects the same-turn message boundary first,
  timestamp cursor remains the persistent fallback and audit evidence; <span class="inline">schedulerStartPromise</span> prevents scheduler startup restore from overwriting concurrent capture notifications.
</div>
""",
}
