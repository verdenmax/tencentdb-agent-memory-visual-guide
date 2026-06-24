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
    <li><span class="inline">src/utils/checkpoint.ts</span>：<span class="inline">captureAtomically</span> 在锁内拥有并读写 cursor 与 checkpoint 状态/计数器</li>
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
    <li><span class="inline">src/utils/checkpoint.ts</span>: <span class="inline">captureAtomically</span> owns cursor and checkpoint state/counters inside the lock</li>
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

<h2>有锁时：checkpoint 文件锁串行化修改</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>captureAtomically(sessionKey)</h4><p><span class="inline">CheckpointManager</span> 使用 checkpoint 文件级 async lock 串行化修改；<span class="inline">sessionKey</span> 用来在锁内选择该会话拥有的 cursor 与状态。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>read checkpoint</h4><p>文件锁先让 checkpoint 文件修改串行进入，再在锁内读取/更新 <span class="inline">sessionKey</span> 拥有的 cursor 与 checkpoint 状态/计数器；调用方不携带外部旧 cursor。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>record L0</h4><p>回调调用 <span class="inline">recordConversation</span>，只写 cursor 或位置切片之后真正新增的消息。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>advance cursor</h4><p>如果本次写入了消息，就在同一把锁内把 checkpoint 推进到新记录的最大 timestamp。</p></div></div>
</div>

<h2>伪代码</h2>
<pre class="code">captureAtomically(sessionKey):
    lock(checkpoint_file)
    state = read_checkpoint_file()
    cursor = state.sessions[sessionKey].afterTimestamp
    messages = record_after_cursor(cursor)
    if messages:
        state.sessions[sessionKey].afterTimestamp = max_timestamp(messages)
        write_checkpoint_file(state)
    unlock(checkpoint_file)</pre>

<h2>position slice 与 timestamp cursor 分工不同</h2>
<div class="cols">
  <div class="col"><h4>position slice</h4><p>优先使用 prompt build 前缓存的 message count，例如 <span class="inline">originalUserMessageCount</span>。提交后只取这个位置之后的数组切片，能避免同一轮 messages 中 timestamp 漂移、同毫秒或宿主改写时间造成的边界误判。</p></div>
  <div class="col"><h4>timestamp cursor</h4><p>当稳定的原始 timestamp 存在时，checkpoint 中的 <span class="inline">afterTimestamp</span> 可作为增量捕获 fallback 和审计线索。若原始 timestamp 缺失或不可靠，这个游标很弱；缺少缓存或进程重启时只能降低重复风险，提供的保证也弱于 position slice 原本能给出的本轮边界保护。</p></div>
</div>

<p>
因此二者不是互相替代：position slice 保护“本轮新增范围”的结构边界，通常比 timestamp cursor 更强；timestamp cursor 只在稳定原始时间可用时保护跨调用的持久增量边界。
在缺少位置缓存或进程重启的场景，它提供的是较弱的 fallback，而不是等价保证。
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
    <li><span class="inline">src/utils/checkpoint.ts</span>：<span class="inline">CheckpointManager</span>、<span class="inline">captureAtomically</span>、用 checkpoint 文件锁串行化修改，并在锁内读写 sessionKey 拥有的 cursor 与状态</li>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>：position slice、timestamp cursor、增量提取 user / assistant 消息</li>
    <li><span class="inline">src/core/tdai-core.ts</span>：<span class="inline">schedulerStartPromise</span> 防止恢复状态覆盖并发通知</li>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>：<span class="inline">performAutoCapture</span> 如何进入 checkpoint 原子捕获并通知 scheduler</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  重复捕获的风险来自并发 capture 与 stale cursor。<span class="inline">captureAtomically()</span>
  把 checkpoint 文件修改串行化，并在锁内读取/推进 <span class="inline">sessionKey</span> 拥有的 cursor；position slice 优先保护同一轮消息边界，timestamp cursor 仅在稳定原始时间存在时作为较弱的持久 fallback 与审计线索；
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

<h2>With the lock: checkpoint file mutations are serialized</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>captureAtomically(sessionKey)</h4><p><span class="inline">CheckpointManager</span> uses a checkpoint-file async lock to serialize mutations; <span class="inline">sessionKey</span> selects the cursor and state owned by that session inside the lock.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>read checkpoint</h4><p>The checkpoint file lock first serializes file mutations, then reads/updates the <span class="inline">sessionKey</span>-owned cursor and checkpoint state/counters inside the lock; callers do not bring an external stale cursor.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>record L0</h4><p>The callback calls <span class="inline">recordConversation</span> and writes only messages truly new after the cursor or position slice.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>advance cursor</h4><p>If messages were written, the same lock advances the checkpoint to the maximum timestamp from this capture.</p></div></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">captureAtomically(sessionKey):
    lock(checkpoint_file)
    state = read_checkpoint_file()
    cursor = state.sessions[sessionKey].afterTimestamp
    messages = record_after_cursor(cursor)
    if messages:
        state.sessions[sessionKey].afterTimestamp = max_timestamp(messages)
        write_checkpoint_file(state)
    unlock(checkpoint_file)</pre>

<h2>Position slice and timestamp cursor solve different problems</h2>
<div class="cols">
  <div class="col"><h4>position slice</h4><p>The recorder prefers the cached message count from before prompt build, such as <span class="inline">originalUserMessageCount</span>. After commit it slices the array after that position, protecting the turn boundary from timestamp drift, same-millisecond messages, or host timestamp rewrites.</p></div>
  <div class="col"><h4>timestamp cursor</h4><p>When stable raw timestamps exist, checkpoint <span class="inline">afterTimestamp</span> can be an incremental-capture fallback and audit clue. If raw timestamps are absent or unreliable, this cursor is weak; missing-cache or restart cases only reduce duplicate risk and provide a weaker guarantee than the turn-boundary protection a position slice would provide.</p></div>
</div>

<p>
So they are not substitutes. Position slice protects the structural boundary of “messages added by this turn” and is generally stronger than a timestamp cursor.
Timestamp cursor protects the persistent incremental boundary only when stable raw time is available; across missing caches or restarts, it is a weaker fallback rather than an equivalent guarantee.
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
    <li><span class="inline">src/utils/checkpoint.ts</span>: <span class="inline">CheckpointManager</span>, <span class="inline">captureAtomically</span>, checkpoint file locking plus sessionKey-owned cursor/state updates inside the lock</li>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>: position slice, timestamp cursor, incremental user / assistant extraction</li>
    <li><span class="inline">src/core/tdai-core.ts</span>: <span class="inline">schedulerStartPromise</span> prevents restored state from clobbering concurrent notifications</li>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>: how <span class="inline">performAutoCapture</span> enters atomic checkpoint capture and notifies the scheduler</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Duplicate capture risk comes from concurrent capture and stale cursors. <span class="inline">captureAtomically()</span>
  serializes checkpoint file mutations, then reads/advances the <span class="inline">sessionKey</span>-owned cursor inside the lock; position slice protects the same-turn message boundary first,
  timestamp cursor is only a weaker persistent fallback and audit clue when stable raw time exists; <span class="inline">schedulerStartPromise</span> prevents scheduler startup restore from overwriting concurrent capture notifications.
</div>
""",
}


LESSON_15 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L1 是把 L0 原始消息整理成“原子记忆”的抽取层。<span class="inline">extractL1Memories</span>
不会把每条聊天都永久升级为记忆；它先通过 <span class="inline">shouldExtractL1</span> 应用 L0 结构过滤、纯符号/纯问号过滤和 prompt-injection 检测，再把新消息和少量背景消息交给 LLM，让输出成为可追溯、可去重、可排序的结构化 JSON。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  L0 像完整录音，L1 像会议后的索引卡。索引卡不会抄下整段原文，而是按 <span class="inline">persona</span>、<span class="inline">episodic</span>、<span class="inline">instruction</span> 三类留下可复用信息。
  但每张卡都要写上来自哪几段录音，之后有人质疑时才能回到原始证据。
</div>

<h2>L0 消息如何进入 L1 抽取</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>L0 messages</h4><p>pipeline 读取已捕获的 user / assistant L0 记录，它们仍是消息级证据，而不是结论。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>quality gate</h4><p><span class="inline">shouldExtractL1</span> 先复用 L0 的结构过滤，再排除纯符号、纯问号和疑似 prompt-injection 文本；长度过滤在当前实现中是注释掉的。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>background / new split</h4><p>尾部新消息是本批抽取对象；前面的背景窗口只提供上下文，避免 LLM 因缺少前因后果而误解。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>LLM extraction</h4><p><span class="inline">src/core/prompts/l1-extraction.ts</span> 要求模型按场景分段输出 JSON；<span class="inline">parseExtractionResult</span> 去掉 fence 并截取 JSON 数组，随后 <span class="inline">sanitizeJsonForParse</span> 修复控制字符再交给 <span class="inline">JSON.parse</span>。</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>extracted memories</h4><p>每个原子记忆带 <span class="inline">type</span>、<span class="inline">priority</span>、<span class="inline">source_message_ids</span> 与 <span class="inline">metadata</span>，随后交给 writer 持久化。</p></div></div>
</div>

<h2>L0 原文与 L1 原子记忆</h2>
<div class="cols">
  <div class="col"><h4>L0 raw message</h4><p>一条消息记录“谁在什么时候说了什么”。它保留证据，粒度偏细，可能包含寒暄、重复、临时纠错和上下文依赖。</p></div>
  <div class="col"><h4>L1 memory atom</h4><p>一个结构化结论记录“值得未来复用的事实或经验”。它可以来自多条 L0，并用 <span class="inline">source_message_ids</span> 指回证据。</p></div>
</div>

<h2>L1 字段</h2>
<table class="t">
  <thead><tr><th>字段</th><th>含义</th><th>质量作用</th></tr></thead>
  <tbody>
    <tr><td><span class="inline">type</span></td><td>支持的记忆类型：<span class="inline">persona</span>、<span class="inline">episodic</span>、<span class="inline">instruction</span></td><td>偏好归入 persona；决定、计划和事件归入 episodic；长期行为规则归入 instruction</td></tr>
    <tr><td><span class="inline">content</span></td><td>归一化后的最小可复用记忆陈述，不是原文逐字复制</td><td>避免把整段对话搬进长期记忆，只保存稳定含义</td></tr>
    <tr><td><span class="inline">priority</span></td><td>重要度或保留价值</td><td>帮助排序、筛选和后续压缩</td></tr>
    <tr><td><span class="inline">source_message_ids</span></td><td>贡献该记忆的 L0 消息 ID 列表</td><td>保留从 L1 回到 L0 的审计链路</td></tr>
    <tr><td><span class="inline">metadata</span></td><td>主要是 episodic 的活动时间字段（<span class="inline">activity_start_time</span> / <span class="inline">activity_end_time</span>）；其他类型通常为 <span class="inline">{}</span>，如需辅助字段应遵循 schema</td><td>补充可用的时间范围等上下文；<span class="inline">scene</span> 属于上层分段，不是每条记忆的 metadata 字段</td></tr>
  </tbody>
</table>

<h2>为什么同时给 new messages 和 background messages</h2>
<p>
<span class="inline">extractL1Memories</span> 把“新消息”作为本次必须抽取的范围，把“背景消息”作为只读上下文。
这样 LLM 能理解代词、纠错、任务阶段和上一句决定，又不会被整段历史淹没。背景窗口越大，成本和误抽取风险越高；窗口太小，又可能把“好，就按第二个方案”抽成没有意义的孤立句。
</p>

<h2>伪代码</h2>
<pre class="code">qualified = messages.filter(shouldExtractL1)
new_messages = tail(qualified, maxNewMessages)
background = previous_window(qualified)
scenes = call_llm_extraction(new_messages, background)
memories = flatten_scene_memories(scenes)</pre>

<p>
prompt 的输出按 scene 分段：一个场景可包含多条 memory atom，每条都要说明类型、优先级、来源消息和 metadata。
解析时 <span class="inline">parseExtractionResult</span> 先去掉模型可能带上的 Markdown fence 并从回复中截取 JSON 数组；之后 <span class="inline">sanitizeJsonForParse</span> 只负责修复 JSON 字符串里的未转义控制字符，最后再调用 <span class="inline">JSON.parse</span>。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/record/l1-extractor.ts</span>：<span class="inline">extractL1Memories</span> 组织质量门、背景窗口、新消息与 LLM 调用；<span class="inline">parseExtractionResult</span> 去 fence、截取 JSON 数组并调用 <span class="inline">sanitizeJsonForParse</span></li>
    <li><span class="inline">src/core/prompts/l1-extraction.ts</span>：L1 抽取 prompt，限定 <span class="inline">persona</span> / <span class="inline">episodic</span> / <span class="inline">instruction</span> 三类并要求场景分段和结构化 JSON 输出</li>
    <li><span class="inline">src/utils/sanitize.ts</span>：<span class="inline">shouldExtractL1</span> 与 <span class="inline">sanitizeJsonForParse</span></li>
    <li><span class="inline">src/core/record/l1-writer.ts</span>：<span class="inline">ExtractedMemory</span>、<span class="inline">MemoryRecord</span> 的写入结构</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L1 从 L0 消息中抽取结构化原子记忆；<span class="inline">shouldExtractL1</span> 应用 L0 结构过滤、纯符号/纯问号过滤和 prompt-injection 检测；
  new messages 决定抽取范围，background messages 提供有限上下文；LLM 输出按场景分段，并为每条记忆保留
  <span class="inline">persona</span> / <span class="inline">episodic</span> / <span class="inline">instruction</span> 类型、<span class="inline">priority</span>、<span class="inline">source_message_ids</span> 和 <span class="inline">metadata</span>。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L1 is the extraction layer that turns raw L0 messages into memory atoms. <span class="inline">extractL1Memories</span>
does not promote every chat line into permanent memory. It first uses <span class="inline">shouldExtractL1</span> to apply L0 structural filters, pure-symbol / question-only filters, and prompt-injection detection, then sends new messages plus a small background window to the LLM so the result is traceable, deduplicable, sortable structured JSON.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  L0 is the complete recording; L1 is the index card written after the meeting. The card does not copy greetings or repeated sentences.
  It keeps reusable information in the supported <span class="inline">persona</span>, <span class="inline">episodic</span>, and <span class="inline">instruction</span> categories. Each card still names the recording segments it came from, so later review can return to the evidence.
</div>

<h2>How L0 messages enter L1 extraction</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>L0 messages</h4><p>The pipeline reads captured user / assistant L0 records. They are still message-level evidence, not conclusions.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>quality gate</h4><p><span class="inline">shouldExtractL1</span> reuses L0 structural filters, then rejects pure-symbol text, question-only text, and suspected prompt-injection payloads; length filters are commented out in the current implementation.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>background / new split</h4><p>The tail new messages are the extraction target; the earlier background window supplies context so the LLM does not misread the turn.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>LLM extraction</h4><p><span class="inline">src/core/prompts/l1-extraction.ts</span> asks the model for scene-segmented JSON; <span class="inline">parseExtractionResult</span> strips fences and extracts the JSON array, then <span class="inline">sanitizeJsonForParse</span> fixes control characters before <span class="inline">JSON.parse</span>.</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>extracted memories</h4><p>Each memory atom carries <span class="inline">type</span>, <span class="inline">priority</span>, <span class="inline">source_message_ids</span>, and <span class="inline">metadata</span> before being persisted by the writer.</p></div></div>
</div>

<h2>L0 raw text vs L1 memory atom</h2>
<div class="cols">
  <div class="col"><h4>L0 raw message</h4><p>A message records who said what and when. It preserves evidence, has fine granularity, and may include greetings, repetition, temporary corrections, and context-dependent wording.</p></div>
  <div class="col"><h4>L1 memory atom</h4><p>A structured conclusion records a reusable fact or lesson. It may come from multiple L0 messages and points back to them through <span class="inline">source_message_ids</span>.</p></div>
</div>

<h2>L1 fields</h2>
<table class="t">
  <thead><tr><th>Field</th><th>Meaning</th><th>Quality role</th></tr></thead>
  <tbody>
    <tr><td><span class="inline">type</span></td><td>Supported memory type: <span class="inline">persona</span>, <span class="inline">episodic</span>, or <span class="inline">instruction</span></td><td>Preferences fold into persona; decisions, plans, and events into episodic; durable behavior rules into instruction</td></tr>
    <tr><td><span class="inline">content</span></td><td>The smallest normalized reusable memory statement, not a verbatim source copy</td><td>Avoids copying whole dialogue into long-term memory</td></tr>
    <tr><td><span class="inline">priority</span></td><td>Importance or retention value</td><td>Helps sorting, filtering, and later compression</td></tr>
    <tr><td><span class="inline">source_message_ids</span></td><td>List of L0 message IDs that contributed to the memory</td><td>Preserves the audit trail from L1 back to L0</td></tr>
    <tr><td><span class="inline">metadata</span></td><td>Mainly episodic timing fields (<span class="inline">activity_start_time</span> / <span class="inline">activity_end_time</span>); other types usually use <span class="inline">{}</span>, and additional auxiliary fields should follow the schema</td><td>Adds time-range context when available; <span class="inline">scene</span> belongs to the segment level, not each memory's metadata</td></tr>
  </tbody>
</table>

<h2>Why the prompt includes both new and background messages</h2>
<p>
<span class="inline">extractL1Memories</span> treats “new messages” as the required extraction range and “background messages” as read-only context.
That lets the LLM resolve pronouns, corrections, task stage, and previous decisions without drowning in the whole conversation. Too much background raises cost and false extraction risk; too little background can turn “yes, use the second option” into an isolated, meaningless atom.
</p>

<h2>Pseudocode</h2>
<pre class="code">qualified = messages.filter(shouldExtractL1)
new_messages = tail(qualified, maxNewMessages)
background = previous_window(qualified)
scenes = call_llm_extraction(new_messages, background)
memories = flatten_scene_memories(scenes)</pre>

<p>
The prompt output is scene segmented: one scene can contain multiple memory atoms, and each atom names its type, priority, source messages, and metadata.
During parsing, <span class="inline">parseExtractionResult</span> first removes possible Markdown fences and extracts the JSON array from the model response. Then <span class="inline">sanitizeJsonForParse</span> fixes unescaped control characters inside JSON strings before <span class="inline">JSON.parse</span>.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/record/l1-extractor.ts</span>: <span class="inline">extractL1Memories</span> coordinates the quality gate, background window, new messages, and LLM call; <span class="inline">parseExtractionResult</span> strips fences, extracts the JSON array, and calls <span class="inline">sanitizeJsonForParse</span></li>
    <li><span class="inline">src/core/prompts/l1-extraction.ts</span>: L1 extraction prompt limiting types to <span class="inline">persona</span> / <span class="inline">episodic</span> / <span class="inline">instruction</span> and requiring scene segmentation plus structured JSON output</li>
    <li><span class="inline">src/utils/sanitize.ts</span>: <span class="inline">shouldExtractL1</span> and <span class="inline">sanitizeJsonForParse</span></li>
    <li><span class="inline">src/core/record/l1-writer.ts</span>: writer-side <span class="inline">ExtractedMemory</span> and <span class="inline">MemoryRecord</span> shapes</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L1 extracts structured memory atoms from L0 messages; <span class="inline">shouldExtractL1</span> applies L0 structural filters, pure-symbol / question-only filters, and prompt-injection detection first.
  New messages define the extraction target, background messages provide bounded context, and the LLM returns scene-segmented memories with
  <span class="inline">persona</span> / <span class="inline">episodic</span> / <span class="inline">instruction</span> types, <span class="inline">priority</span>, <span class="inline">source_message_ids</span>, and <span class="inline">metadata</span>.
</div>
""",
}


LESSON_16 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L1 抽取会把多条 L0 消息变成结构化记忆，但抽取结果可能重复，也可能与已有记忆冲突。写入前的
<span class="inline">batchDedup</span> 是质量控制：先召回相似候选，再判断这条新记忆应该 store、update、merge，还是 skip。
它控制的是可搜索 L1 事实的质量，而不是删除 L0 原文证据。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  L0 像会议录音库，L1 像团队知识卡片。录音库不能因为有人做了新卡片就剪掉原声；
  去重只是检查“这张卡是不是已经有了、是不是需要修订旧卡、是不是与旧卡冲突”，让知识卡片架保持清晰。
</div>

<h2>从抽取结果到写入决策</h2>
<div class="flow">
  <div class="node"><div class="nt">extracted memories</div><div class="nd">LLM / logic 产出候选 L1 原子记忆</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">candidate recall</div><div class="nd">向量或 FTS 召回可用时查找相似已有记忆</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">dedup decision</div><div class="nd">判断 store / update / merge / skip 与冲突说明</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">write / update / merge / skip</div><div class="nd">按决策把 L1 写入 JSONL 与可搜索 store，或跳过</div></div>
</div>

<p>
<span class="inline">src/core/record/l1-dedup.ts</span> 中的 <span class="inline">batchDedup</span>
会在批量写入前处理已经分配 <span class="inline">record_id</span> 的抽取结果，返回 <span class="inline">store/update/merge/skip</span> 动作。它优先利用可用召回找候选：同一偏好被重复表达时可 skip；
用户纠正旧偏好时可 update；可合并的信息可 merge；新事实没有相似候选时 store。判断来自
<span class="inline">src/core/prompts/l1-dedup.ts</span> 中的 LLM prompt。
</p>

<h2>为什么去重不是丢弃证据</h2>
<div class="cols">
  <div class="col"><h4>L0 证据层</h4><p>保存原始对话 JSONL：谁说了什么、什么时候说、消息 ID 是什么。它服务审计、回放和重新抽取，去重不应改写这层原始证据。</p></div>
  <div class="col"><h4>L1 质量层</h4><p>保存可召回的结构化事实。去重只决定新 L1 是否会让事实库重复、过时或冲突，从而控制未来 recall 的噪声。</p></div>
</div>

<h2>写入路径：JSONL 与 store upsert</h2>
<p>
抽取流程会先用 <span class="inline">generateMemoryId</span> 预分配唯一记录 ID：它基于时间与随机字节生成待写入记录的 ID，
不是内容稳定哈希，也不是去重后的语义身份。随后 <span class="inline">batchDedup</span> 针对这些 ID 返回决策；
<span class="inline">writeMemory</span> 使用这条预分配 ID 追加或 upsert L1 记录。
store upsert 路径把同一条记录维护到可搜索后端：本地
<span class="inline">sqlite</span> 可提供向量 / FTS 检索，远端 <span class="inline">TCVDB</span>
可提供托管向量检索。JSONL 是持久证据，store 是检索索引；两者一起让记忆既可审计又可召回。
</p>

<div class="cols">
  <div class="col"><h4>SQLite local store</h4><p><span class="inline">src/core/store/sqlite.ts</span> 适合零配置或本地开发。它在本地数据库维护向量与 FTS 索引，让 L1 记录即使没有远端服务也能被相似搜索或关键词搜索找到。</p></div>
  <div class="col"><h4>TCVDB backend</h4><p><span class="inline">src/core/store/tcvdb.ts</span> 适合接入托管向量数据库。<span class="inline">createStoreBundle</span> 根据配置组装 embedding、store 与 fallback，使上层写入逻辑不需要知道具体后端。</p></div>
</div>

<h2>召回降级：召回能力下降时仍保留新记忆</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>vector recall</h4><p>如果已有向量数据且 embedding 服务可用，<span class="inline">batchDedup</span> 用向量相似检索召回候选。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>FTS recall</h4><p>如果向量召回不可用但 FTS 关键词检索可用，则用关键词召回候选，去重判断的召回基础会变弱。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>no recall</h4><p>如果向量与 FTS 召回都不可用，跳过冲突检测，并把本批新记忆按默认 <span class="inline">store</span> 决策写入。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>write path</h4><p><span class="inline">writeMemory</span> 按 store / update / merge / skip 决策维护 JSONL 与 store 写入；需要时可手动依据 JSONL 重建检索层。</p></div></div>
</div>

<h2>伪代码</h2>
<pre class="code">memories = extracted.map(assign_record_id)
decisions = batchDedup(memories)
for memory in memories:
    decision = decisions[memory.record_id] ?? "store"  # educational lookup from returned decisions
    writeMemory(memory, decision)  # store/update/merge/skip + JSONL/store writes</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/record/l1-extractor.ts</span>：为抽取记忆分配 record ID，调用 <span class="inline">batchDedup</span>，应用决策并调用 <span class="inline">writeMemory</span></li>
    <li><span class="inline">src/core/record/l1-dedup.ts</span>：<span class="inline">batchDedup</span> 在写入前批量召回候选并决定 store / update / merge / skip</li>
    <li><span class="inline">src/core/prompts/l1-dedup.ts</span>：去重 prompt 描述如何比较新记忆与候选记忆、发现重复或冲突</li>
    <li><span class="inline">src/core/record/l1-writer.ts</span>：<span class="inline">writeMemory</span> 使用预分配 record ID 追加或 upsert L1 JSONL / store 记录</li>
    <li><span class="inline">src/core/store/factory.ts</span>：<span class="inline">createStoreBundle</span> 连接 embedding、store 后端与降级路径</li>
    <li><span class="inline">src/core/store/sqlite.ts</span>：本地 vector / FTS store；<span class="inline">src/core/store/tcvdb.ts</span>：TCVDB store</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L1 去重发生在写入前，因为抽取可能产生重复或冲突记忆；<span class="inline">batchDedup</span>
  在召回可用时召回相似候选并决定 store / update / merge / skip；<span class="inline">writeMemory</span>
  使用预分配 record ID 写入 L1 JSONL 与 store；召回不可用时跳过冲突检测，并默认 store 本批新记忆。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L1 extraction turns L0 messages into structured memories, but the extracted batch can contain duplicates or facts that conflict with existing memory.
Before writing, <span class="inline">batchDedup</span> acts as quality control: recall similar candidates, then decide whether the new memory action is store, update, merge, or skip.
It governs searchable L1 facts; it does not delete raw L0 evidence.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  L0 is the meeting recording archive; L1 is the team's index-card shelf. You do not cut the recording when a new card is written.
  Dedup only asks whether the card already exists, should revise an older card, or conflicts with one, so the shelf stays useful.
</div>

<h2>From extraction to write decision</h2>
<div class="flow">
  <div class="node"><div class="nt">extracted memories</div><div class="nd">LLM / logic emits candidate L1 atoms</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">candidate recall</div><div class="nd">when vector or FTS recall is available, find similar existing memories</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">dedup decision</div><div class="nd">choose store / update / merge / skip and explain conflicts</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">write / update / merge / skip</div><div class="nd">apply the decision to JSONL and searchable store writes, or skip</div></div>
</div>

<p>
<span class="inline">batchDedup</span> in <span class="inline">src/core/record/l1-dedup.ts</span>
runs before batch writes over extracted memories that already have a <span class="inline">record_id</span>, returning <span class="inline">store/update/merge/skip</span> actions. It prefers available recall for candidates: repeated preferences can be skipped,
corrected preferences can update an existing record, mergeable details can be merged, and unrelated new facts can be stored. The decision comes from the LLM prompt in
<span class="inline">src/core/prompts/l1-dedup.ts</span>.
</p>

<h2>Why dedup does not discard evidence</h2>
<div class="cols">
  <div class="col"><h4>L0 evidence layer</h4><p>Raw conversation JSONL records who said what, when, and under which message ID. It supports audit, replay, and re-extraction; dedup should not rewrite this source evidence.</p></div>
  <div class="col"><h4>L1 quality layer</h4><p>Structured facts are optimized for future recall. Dedup only decides whether a new L1 fact would make the fact store repetitive, stale, or conflicting.</p></div>
</div>

<h2>Write path: JSONL plus store upsert</h2>
<p>
The extraction flow first uses <span class="inline">generateMemoryId</span> to preassign a unique record ID. It uses time plus random bytes for the record that may be written;
it is not a content-stable hash or the semantic identity chosen by dedup. <span class="inline">batchDedup</span> then returns decisions keyed by those IDs, and
<span class="inline">writeMemory</span> uses the preassigned ID when appending or upserting the L1 record.
The store upsert path keeps the same record searchable: local <span class="inline">sqlite</span>
can provide vector / FTS search, while <span class="inline">TCVDB</span> can provide managed vector search.
JSONL is durable evidence; the store is the retrieval index. Together they make memory auditable and recallable.
</p>

<div class="cols">
  <div class="col"><h4>SQLite local store</h4><p><span class="inline">src/core/store/sqlite.ts</span> fits zero-config or local development. It maintains local vector and FTS indexes so L1 records remain discoverable through similarity or keyword search without a remote service.</p></div>
  <div class="col"><h4>TCVDB backend</h4><p><span class="inline">src/core/store/tcvdb.ts</span> integrates a managed vector database. <span class="inline">createStoreBundle</span> wires embedding, store backend, and fallback behavior so the writer does not depend on backend details.</p></div>
</div>

<h2>Recall fallback: keep new memories when recall is unavailable</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>vector recall</h4><p>If vector data exists and the embedding service is available, <span class="inline">batchDedup</span> recalls candidates with vector similarity.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>FTS recall</h4><p>If vector recall is unavailable but FTS keyword search exists, keyword recall can still provide candidates, with a weaker recall basis.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>no recall</h4><p>If neither vector nor FTS recall is available, conflict detection is skipped and the new batch defaults to <span class="inline">store</span>.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>write path</h4><p><span class="inline">writeMemory</span> applies store / update / merge / skip decisions to JSONL and store writes; operators can manually rebuild the retrieval layer from JSONL when needed.</p></div></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">memories = extracted.map(assign_record_id)
decisions = batchDedup(memories)
for memory in memories:
    decision = decisions[memory.record_id] ?? "store"  # educational lookup from returned decisions
    writeMemory(memory, decision)  # store/update/merge/skip + JSONL/store writes</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/record/l1-extractor.ts</span>: assigns record IDs to extracted memories, calls <span class="inline">batchDedup</span>, applies decisions, and invokes <span class="inline">writeMemory</span></li>
    <li><span class="inline">src/core/record/l1-dedup.ts</span>: <span class="inline">batchDedup</span> recalls candidates before writes and decides store / update / merge / skip</li>
    <li><span class="inline">src/core/prompts/l1-dedup.ts</span>: dedup prompt for comparing a new memory with candidates and detecting duplicates or conflicts</li>
    <li><span class="inline">src/core/record/l1-writer.ts</span>: <span class="inline">writeMemory</span> uses the preassigned record ID when appending or upserting L1 JSONL / store records</li>
    <li><span class="inline">src/core/store/factory.ts</span>: <span class="inline">createStoreBundle</span> connects embedding, store backends, and the embedding/store fallback path</li>
    <li><span class="inline">src/core/store/sqlite.ts</span>: local vector / FTS store; <span class="inline">src/core/store/tcvdb.ts</span>: TCVDB store</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L1 dedup runs before writing because extraction can produce duplicate or conflicting memories. <span class="inline">batchDedup</span>
  recalls similar candidates when recall is available and chooses store / update / merge / skip. <span class="inline">writeMemory</span>
  writes L1 JSONL and store records with the preassigned record ID; when recall is unavailable, conflict detection is skipped and new memories default to store.
</div>
""",
}
