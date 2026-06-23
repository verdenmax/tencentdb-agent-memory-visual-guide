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
  <div class="node"><div class="nt">filteredMessages</div><div class="nd">只保留新增 user / assistant，清洗短文本与污染上下文</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L0Record</div><div class="nd">id、sessionKey、sessionId、role、messageText、recordedAt、timestamp</div></div>
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
  <div class="node"><div class="nt">filteredMessages</div><div class="nd">new user / assistant messages, sanitized and filtered</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L0Record</div><div class="nd">id, sessionKey, sessionId, role, messageText, recordedAt, timestamp</div></div>
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
