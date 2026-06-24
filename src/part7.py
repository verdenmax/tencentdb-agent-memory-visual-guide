"""Part 7 lesson content: Context Offload short-term symbolic memory."""


LESSON_27 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
长任务里的工具日志会迅速膨胀：同一个文件被反复读取，命令输出一屏接一屏，早期结果很快变旧却仍占着 live context。
Context Offload 不是替代 L0-L3 长期记忆，而是在当前任务内把这些短期证据压成可导航符号：原始输出落到 refs 文件，紧凑行写入 offload JSONL，
任务画布渲染成 Mermaid MMD，下一轮只把继续工作所需的符号注入回上下文。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  L0-L3 像跨项目档案馆，帮未来会话记住事实、场景和画像；Context Offload 像桌面上的任务白板。
  白板不保存一切细节，只把“证据在哪里、当前做到哪一步、下一步该看哪个节点”保持在眼前。
</div>

<h2>为什么长任务日志会挤爆窗口</h2>
<div class="cols">
  <div class="col"><h4>重复工具调用</h4><p>编码会话常反复 <span class="inline">rg</span>、read file、run test。每次结果都可能被追加进消息历史，即使后续只需要“哪个文件已确认”这个符号。</p></div>
  <div class="col"><h4>大块命令输出</h4><p>构建、测试和日志可能产生成百上千行。原始输出是证据，但下一轮推理通常只需要失败摘要、引用路径和当前状态。</p></div>
  <div class="col"><h4>过期结果滞留</h4><p>早期搜索结果、旧失败栈和已修复错误会继续消耗 token。它们应可追溯，但不该一直挤占实时 prompt window。</p></div>
</div>

<h2>符号压缩流向</h2>
<div class="flow">
  <div class="node"><div class="nt">long task logs</div><div class="nd">工具调用、参数、stdout/stderr、错误栈与耗时。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">refs</div><div class="nd">完整证据写入 <span class="inline">refs/</span>，保留可回看路径。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L1 JSONL</div><div class="nd"><span class="inline">OffloadEntry</span> 保存 summary、result_ref、tool_call_id、node_id。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Mermaid MMD</div><div class="nd">Offload-L2 把 JSONL 行组织成任务节点和状态画布。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Offload-L3 injected context</div><div class="nd">只注入当前任务需要的节点符号，而不是整段工具日志。</div></div>
</div>

<div class="card detail">
  <div class="tag">⚠️ 名称边界</div>
  Offload 内部的 <span class="inline">Offload-L1/L2/L3</span> 是短期流水线阶段，不等于长期记忆的 L0-L3：
  Offload-L1 约等于摘要，Offload-L2 约等于 Mermaid 任务画布，Offload-L3 约等于下一轮注入上下文。长期 L2/L3 仍然指场景块和 persona/profile。
</div>

<h2>长期 L0-L3 与短期 Context Offload</h2>
<div class="cols">
  <div class="col"><h4>长期 L0-L3 memory</h4><p>面向未来会话：L0 留原始对话证据，L1 抽取原子记忆，L2 组织场景块，L3 生成 persona/profile。目标是跨会话复用、搜索和长期演化。</p></div>
  <div class="col"><h4>短期 Context Offload</h4><p>面向当前任务：把工具结果从 live context 移到本地证据文件和任务符号层。目标是让长编码会话可继续、可下钻、可控 token 预算。</p></div>
  <div class="col"><h4>共同点与边界</h4><p>两者都强调证据路径和压缩摘要；差别是生命周期。Offload 解决当前任务导航，不承诺成为跨 session 的长期事实来源。</p></div>
</div>

<h2>三层可见空间</h2>
<div class="layers">
  <div class="layer l-main"><div class="lh"><span class="badge">live</span><span class="name">prompt window</span></div><div class="ld">LLM 当前能直接看到的消息、系统提示、少量 active symbols 和必要 MMD 片段。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">local files</span><span class="name">~/.openclaw/context-offload</span></div><div class="ld"><span class="inline">DEFAULT_DATA_ROOT</span> 下按 agent/session 隔离；包含 <span class="inline">refs/</span>、<span class="inline">mmds/</span>、<span class="inline">offload-&lt;sessionId&gt;.jsonl</span> 与 state。</div></div>
  <div class="layer l-core"><div class="lh"><span class="badge">guide</span><span class="name">generated lesson page</span></div><div class="ld">本页把实现路径解释成学习模型：证据文件、JSONL 符号、MMD 画布、Offload-L3 注入。</div></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">if task_has_many_tool_results:
    write_raw_evidence_to_refs()
    append_compact_rows_to_offload_jsonl()
    update_mermaid_task_canvas()
    inject_only_active_symbols_before_next_llm_call()</pre>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 7：Context Offload 的目的，是解释长任务和工具日志压缩这条第二记忆主线。</li>
    <li><span class="inline">src/offload/index.ts</span>：<span class="inline">registerOffload</span> 注册入口，配置 <span class="inline">OffloadContextEngine</span>，选择 <span class="inline">BackendClient</span> 或 <span class="inline">LocalLlmClient</span>，并连接 hook / context engine 路径。</li>
    <li><span class="inline">src/offload/storage.ts</span>：<span class="inline">DEFAULT_DATA_ROOT</span> 指向 <span class="inline">~/.openclaw/context-offload</span>；<span class="inline">createStorageContext</span> 生成 per-agent / per-session 的 refs、mmds、offload JSONL 和 state 路径。</li>
    <li><span class="inline">src/offload/types.ts</span>：<span class="inline">OffloadEntry</span> 定义 summary、result_ref、tool_call_id、node_id；<span class="inline">PLUGIN_DEFAULTS</span> 定义 Offload-L1/L2/L3 阈值和 token-budget trigger ratios。</li>
    <li><span class="inline">src/offload/context-token-tracker.ts</span>：<span class="inline">ContextSnapshot</span> 与 <span class="inline">buildTiktokenContextSnapshot</span> 记录 stage、totalTokens、messageCount 等 token 快照。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Context Offload 是当前任务的短期符号记忆：把臃肿工具日志变成 refs 证据、JSONL 摘要、Mermaid 节点和少量 Offload-L3 注入。
  L0-L3 长期记忆负责未来会话的事实、场景和画像；Offload 负责当前长任务的导航、下钻和 token 预算。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Tool logs in long tasks grow quickly: the same file is read again and again, command output fills screens, and early results become stale while still occupying live context.
Context Offload does not replace L0-L3 long-term memory. It adds a current-task symbolic layer: raw output goes to refs files, compact rows go to offload JSONL,
task state is rendered as Mermaid MMD, and the next turn injects only the symbols needed to continue.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  L0-L3 is a cross-project archive that helps future sessions remember facts, scenes, and profiles; Context Offload is the whiteboard on your desk.
  The whiteboard does not keep every detail in view. It keeps “where is the evidence, where are we now, which node should we inspect next” visible.
</div>

<h2>Why long task logs crowd the window</h2>
<div class="cols">
  <div class="col"><h4>Repeated tool calls</h4><p>Coding sessions repeatedly run <span class="inline">rg</span>, read files, and run tests. Each result may enter message history even when the next step only needs the symbol “this file was checked”.</p></div>
  <div class="col"><h4>Large command output</h4><p>Builds, tests, and logs can produce hundreds or thousands of lines. The raw output is evidence, but the next reasoning step usually needs a failure summary, reference path, and current state.</p></div>
  <div class="col"><h4>Stale results remain</h4><p>Early search hits, old stack traces, and fixed failures keep consuming tokens. They should remain traceable, but they should not permanently crowd the real-time prompt window.</p></div>
</div>

<h2>Symbolic compression flow</h2>
<div class="flow">
  <div class="node"><div class="nt">long task logs</div><div class="nd">Tool calls, parameters, stdout/stderr, stack traces, and duration.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">refs</div><div class="nd">Full evidence is written under <span class="inline">refs/</span> with a recoverable path.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L1 JSONL</div><div class="nd"><span class="inline">OffloadEntry</span> stores summary, result_ref, tool_call_id, and node_id.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Mermaid MMD</div><div class="nd">Offload-L2 organizes JSONL rows into task nodes and status canvas.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Offload-L3 injected context</div><div class="nd">Only active task symbols are injected, not the whole tool log.</div></div>
</div>

<div class="card detail">
  <div class="tag">⚠️ Naming boundary</div>
  Context Offload's internal <span class="inline">Offload-L1/L2/L3</span> stages are short-term pipeline stages, separate from long-term L0-L3 memory:
  Offload-L1 roughly means summarization, Offload-L2 means the Mermaid task canvas, and Offload-L3 means context injected into the next turn. Long-term L2/L3 still mean scene blocks and persona/profile.
</div>

<h2>Long-term L0-L3 versus short-term Context Offload</h2>
<div class="cols">
  <div class="col"><h4>Long-term L0-L3 memory</h4><p>Future-session oriented: L0 stores raw conversation evidence, L1 extracts atomic memories, L2 organizes scene blocks, and L3 generates persona/profile context. The goal is cross-session reuse, search, and long-term evolution.</p></div>
  <div class="col"><h4>Short-term Context Offload</h4><p>Current-task oriented: move tool results out of live context into local evidence files and a task symbol layer. The goal is long coding-session continuity, drill-down recovery, and controlled token budget.</p></div>
  <div class="col"><h4>Shared principle, different boundary</h4><p>Both care about evidence paths and compressed summaries. The lifecycle differs: Offload solves current-task navigation, not cross-session long-term factual memory.</p></div>
</div>

<h2>Three visible layers</h2>
<div class="layers">
  <div class="layer l-main"><div class="lh"><span class="badge">live</span><span class="name">prompt window</span></div><div class="ld">The messages, system prompt, a few active symbols, and necessary MMD fragments directly visible to the LLM now.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">local files</span><span class="name">~/.openclaw/context-offload</span></div><div class="ld">Under <span class="inline">DEFAULT_DATA_ROOT</span>, storage is isolated by agent and session; it contains <span class="inline">refs/</span>, <span class="inline">mmds/</span>, <span class="inline">offload-&lt;sessionId&gt;.jsonl</span>, and state.</div></div>
  <div class="layer l-core"><div class="lh"><span class="badge">guide</span><span class="name">generated lesson page</span></div><div class="ld">This page turns the implementation path into a learning model: evidence files, JSONL symbols, MMD canvas, and Offload-L3 injection.</div></div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">if task_has_many_tool_results:
    write_raw_evidence_to_refs()
    append_compact_rows_to_offload_jsonl()
    update_mermaid_task_canvas()
    inject_only_active_symbols_before_next_llm_call()</pre>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 7: Context Offload exists to explain the second memory spine for long tasks and tool-log compression.</li>
    <li><span class="inline">src/offload/index.ts</span>: <span class="inline">registerOffload</span> is the entry point, configures <span class="inline">OffloadContextEngine</span>, chooses <span class="inline">BackendClient</span> or <span class="inline">LocalLlmClient</span>, and wires hook / context-engine registration paths.</li>
    <li><span class="inline">src/offload/storage.ts</span>: <span class="inline">DEFAULT_DATA_ROOT</span> points to <span class="inline">~/.openclaw/context-offload</span>; <span class="inline">createStorageContext</span> builds per-agent / per-session refs, mmds, offload JSONL, and state paths.</li>
    <li><span class="inline">src/offload/types.ts</span>: <span class="inline">OffloadEntry</span> defines summary, result_ref, tool_call_id, and node_id; <span class="inline">PLUGIN_DEFAULTS</span> defines Offload-L1/L2/L3 thresholds and token-budget trigger ratios.</li>
    <li><span class="inline">src/offload/context-token-tracker.ts</span>: <span class="inline">ContextSnapshot</span> and <span class="inline">buildTiktokenContextSnapshot</span> capture stage, totalTokens, messageCount, and related token snapshots.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Context Offload is short-term symbolic memory for the current task: bulky tool logs become refs evidence, JSONL summaries, Mermaid nodes, and small Offload-L3 injections.
  L0-L3 long-term memory serves future-session facts, scenes, and profiles; Offload serves current long-task navigation, drill-down, and token budget.
</div>
""",
}


LESSON_28 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
after-tool-call hook 是 Context Offload 的入口之一：每次工具调用结束后，插件把工具名、调用 ID、参数和结果拼成
<span class="inline">ToolPair</span>。心跳事件和等待审批的事件会被跳过；真正完成的工具结果先进入 pending buffer，
再在数量达到阈值时强制触发 Offload-L1，把原始输出写到 <span class="inline">refs/*.md</span>，把紧凑摘要追加到
<span class="inline">offload-&lt;sessionId&gt;.jsonl</span>。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  这像实验记录员：每个仪器读数先贴到临时夹板，夹板攒到一定数量后，记录员把完整读数归档到证据册，
  再在索引卡上写“读数来自哪里、结论是什么、是否已经进入任务画布”。索引卡轻，证据册完整。
</div>

<h2>after-tool-call 捕获路径</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>解析工具事件</h4><p><span class="inline">createAfterToolCallHandler</span> 从事件中解析 tool call ID、工具名、参数和结果；如果事件缺少可用 ID，后续 dedup 就无法稳定工作。</p><div class="mono">event -&gt; tool_call_id + params + result</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>过滤非结果事件</h4><p>heartbeat 只说明宿主还活着；approval-pending 只说明工具尚未真正执行。两者都不应进入证据层，避免把“尚无结果”当成事实。</p><div class="mono">skip heartbeat / approval-pending</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>加入 ToolPair buffer</h4><p><span class="inline">stateManager.addToolPair</span> 只负责缓存已经完成的工具调用；latest-turn context cache 是 after-tool-call 中另一条独立分支，用来保留本轮任务框架。</p><div class="mono">ToolPair -&gt; pending_pairs</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>达到阈值强制 L1</h4><p><span class="inline">shouldForceL1</span> 使用 <span class="inline">forceTriggerThreshold</span> 判断 pending pairs 是否足够多；达到阈值就走 L1 trigger orchestration。</p><div class="mono">pending_pairs &gt;= forceTriggerThreshold</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>写 refs 与 JSONL</h4><p>L1 输出变成 <span class="inline">OffloadEntry</span>；原始结果由 <span class="inline">writeRefMd</span> 写入 refs，紧凑行由 <span class="inline">appendOffloadEntries</span> 追加。</p><div class="mono">entries -&gt; refs/*.md + offload JSONL</div></div></div>
</div>

<h2>从工具结果到短期符号</h2>
<div class="flow">
  <div class="node"><div class="nt">after-tool-call event</div><div class="nd">包含工具名、调用 ID、参数、stdout/stderr 或结构化结果。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">ToolPair buffer</div><div class="nd">按 agent/session 的 state 暂存，跳过心跳和待审批事件。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1 summarize</div><div class="nd">可插拔 Offload LLM client 生成 summary 与 score；L1 parser 此时把 <span class="inline">node_id</span> 设为 <span class="inline">null</span>。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">refs file</div><div class="nd">完整原始结果写入 <span class="inline">refs/*.md</span>，必要时可下钻。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">offload JSONL row</div><div class="nd">一行保存 summary、score 与 ref path，不把大结果重复塞回上下文。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L2 MMD task symbol</div><div class="nd">Offload-L2 分配 <span class="inline">node_id</span>，并创建 Mermaid 任务节点符号。</div></div>
</div>

<h2>JSONL 行字段与写后标记</h2>
<table class="t">
  <tr><th>字段</th><th>作用</th></tr>
  <tr><td class="mono">tool_call_id</td><td>写入去重的主键之一；同一工具结果重复到达时，<span class="inline">appendOffloadEntries</span> 跳过重复行。</td></tr>
  <tr><td class="mono">tool_call</td><td>紧凑记录工具名和参数摘要，避免 JSONL 行保存完整大参数或敏感原文。</td></tr>
  <tr><td class="mono">summary</td><td>Offload-L1 生成的短摘要，是下一轮上下文最常读取的部分。</td></tr>
  <tr><td class="mono">timestamp</td><td>保留捕获时间，帮助按时间恢复任务过程。</td></tr>
  <tr><td class="mono">score</td><td>表示摘要对当前任务的相关性或重要性，供后续筛选。</td></tr>
  <tr><td class="mono">node_id</td><td>L1 parser 写入时为 <span class="inline">null</span>；Offload-L2 后续分配它来连接 Mermaid MMD 任务节点。</td></tr>
  <tr><td class="mono">result_ref</td><td>指向 <span class="inline">refs/*.md</span> 的原始证据路径。</td></tr>
  <tr><td class="mono">offloaded</td><td>不是 L1 parser 产出的 <span class="inline">OffloadEntry</span> 核心字段；L1 写入后由 <span class="inline">markOffloadStatus</span> 添加/更新，值为 <span class="inline">true</span> 或 <span class="inline">"deleted"</span>。</td></tr>
</table>

<h2>存储隔离：当前 session 与共享 agent 目录</h2>
<div class="cellgroup">
  <div class="cg-cap"><b>current session</b>：只追加本会话 JSONL，避免不同会话的工具结果互相污染。</div>
  <div class="cells"><span class="cell hot">offload-&lt;sessionId&gt;.jsonl</span><span class="cell">latest-turn context</span><span class="cell">pending ToolPairs</span></div>
  <div class="cg-cap"><b>shared agent folders</b>：同一 agent 下共享可下钻产物；refs 用时间戳文件名，mmds 按 agent 目录保存。</div>
  <div class="cells"><span class="cell">refs/</span><span class="cell">mmds/</span><span class="cell">state</span></div>
</div>

<p>
隔离的关键不是“只写一个目录”，而是按 agent/session 创建存储上下文：当前会话的
<span class="inline">offload-&lt;sessionId&gt;.jsonl</span> 保存轻量索引；同一 agent 下共享的
<span class="inline">refs/</span> 用时间戳命名保存可下钻证据，<span class="inline">mmds/</span> 保存任务画布。
写入时再用 <span class="inline">tool_call_id</span> 去重，保证重复 hook、重试或重放不会制造重复 JSONL 行。
</p>

<h2>核心伪代码</h2>
<pre class="code">on_after_tool_call(event):
    pair = collect_tool_name_id_params_result(event)
    if pair.is_heartbeat or pair.is_approval_pending:
        return
    state.pending_pairs.append(pair)
    if len(state.pending_pairs) &gt;= force_trigger_threshold:
        entries = l1_summarize(state.pending_pairs)
        for entry in entries:
            entry.ref = write_ref_md(entry.raw_result)
        append_offload_entries(entries)</pre>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 7 lesson 28：本课聚焦 after-tool-call、refs 与 offload JSONL 的捕获链路。</li>
    <li><span class="inline">src/offload/hooks/after-tool-call.ts</span>：<span class="inline">createAfterToolCallHandler</span> 解析工具调用 ID/参数/结果，跳过 heartbeat 与 approval-pending，并调用 <span class="inline">stateManager.addToolPair</span>。</li>
    <li><span class="inline">src/offload/hooks/llm-output.ts</span>：<span class="inline">shouldForceL1</span> 和 <span class="inline">forceTriggerThreshold</span> 决定 pending pairs 何时触发 L1。</li>
    <li><span class="inline">src/offload/index.ts</span>：编排 L1 trigger、<span class="inline">appendOffloadEntries</span>、<span class="inline">writeRefMd</span> 与 <span class="inline">sanitizeText</span>。</li>
    <li><span class="inline">src/offload/storage.ts</span>：实现 <span class="inline">writeRefMd</span>、<span class="inline">appendOffloadEntries</span>、<span class="inline">readOffloadEntries</span>、<span class="inline">markOffloadStatus</span> 和 <span class="inline">parseJsonlSafe</span>。</li>
    <li><span class="inline">src/offload/local-llm/prompts/l1-prompt.ts</span> 与 <span class="inline">src/offload/local-llm/parsers/l1-parser.ts</span>：定义 L1 摘要 prompt 与解析规则；实际调用通过可插拔 client，可走 <span class="inline">LocalLlmClient</span> 或 <span class="inline">BackendClient</span>。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  after-tool-call 不直接把大工具结果塞回上下文，而是先形成 <span class="inline">ToolPair</span> buffer；
  达到阈值后由 Offload-L1 生成 <span class="inline">OffloadEntry</span>，原文进 refs，摘要进 JSONL。
  agent/session 隔离和写入时去重共同保证可追溯、可恢复、不过量。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
The after-tool-call hook is one entry point for Context Offload. After each tool finishes, the plugin combines the tool name,
tool call ID, parameters, and result into a <span class="inline">ToolPair</span>. Heartbeats and approval-pending events are skipped.
Completed results first enter a pending buffer; when enough pairs accumulate, Offload-L1 is forced, raw output is written to
<span class="inline">refs/*.md</span>, and compact summaries are appended to <span class="inline">offload-&lt;sessionId&gt;.jsonl</span>.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Think of a lab recorder. Each instrument reading first goes onto a clipboard. Once the clipboard is full enough, the recorder files
  the complete readings in an evidence binder and writes index cards saying where the reading lives, what it means, and whether it has entered the task canvas.
  The index card is light; the binder remains complete.
</div>

<h2>The after-tool-call capture path</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Resolve the tool event</h4><p><span class="inline">createAfterToolCallHandler</span> resolves tool call ID, tool name, parameters, and result from the event. Without a stable ID, later write-time dedup cannot be reliable.</p><div class="mono">event -&gt; tool_call_id + params + result</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Filter non-result events</h4><p>A heartbeat only says the host is alive; approval-pending only says the tool has not actually run yet. Neither should become evidence.</p><div class="mono">skip heartbeat / approval-pending</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Add to the ToolPair buffer</h4><p><span class="inline">stateManager.addToolPair</span> buffers completed tool calls only. The latest-turn context cache is a separate after-tool-call branch that preserves the current task frame.</p><div class="mono">ToolPair -&gt; pending_pairs</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Force L1 at the threshold</h4><p><span class="inline">shouldForceL1</span> uses <span class="inline">forceTriggerThreshold</span> to decide whether enough pending pairs have accumulated, then enters L1 trigger orchestration.</p><div class="mono">pending_pairs &gt;= forceTriggerThreshold</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>Write refs and JSONL</h4><p>L1 output becomes <span class="inline">OffloadEntry</span> records; <span class="inline">writeRefMd</span> stores raw results under refs, and <span class="inline">appendOffloadEntries</span> appends compact rows.</p><div class="mono">entries -&gt; refs/*.md + offload JSONL</div></div></div>
</div>

<h2>From tool result to short-term symbol</h2>
<div class="flow">
  <div class="node"><div class="nt">after-tool-call event</div><div class="nd">Carries tool name, call ID, parameters, stdout/stderr, or structured result.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">ToolPair buffer</div><div class="nd">Stored in agent/session state while heartbeat and approval-pending events are ignored.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1 summarize</div><div class="nd">A pluggable Offload LLM client produces summary and score; the L1 parser sets <span class="inline">node_id</span> to <span class="inline">null</span> at this point.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">refs file</div><div class="nd">Full raw output is written under <span class="inline">refs/*.md</span> for drill-down.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">offload JSONL row</div><div class="nd">One compact row stores summary, score, and ref path instead of repeating the large result in context.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L2 MMD task symbol</div><div class="nd">Offload-L2 assigns <span class="inline">node_id</span> and creates the Mermaid task-node symbol.</div></div>
</div>

<h2>JSONL row fields and post-write marker</h2>
<table class="t">
  <tr><th>Field</th><th>Purpose</th></tr>
  <tr><td class="mono">tool_call_id</td><td>One write-time dedup key; when the same tool result arrives again, <span class="inline">appendOffloadEntries</span> skips the duplicate row.</td></tr>
  <tr><td class="mono">tool_call</td><td>Compact tool name and parameter summary, without storing huge arguments or sensitive raw text in the JSONL row.</td></tr>
  <tr><td class="mono">summary</td><td>The Offload-L1 short summary, usually the part injected or read in the next turn.</td></tr>
  <tr><td class="mono">timestamp</td><td>Capture time, useful for reconstructing task order.</td></tr>
  <tr><td class="mono">score</td><td>Relevance or importance signal used by later filtering.</td></tr>
  <tr><td class="mono">node_id</td><td>The L1 parser writes <span class="inline">null</span>; Offload-L2 assigns it later to connect the row to a Mermaid MMD task node.</td></tr>
  <tr><td class="mono">result_ref</td><td>Path to the raw evidence in <span class="inline">refs/*.md</span>.</td></tr>
  <tr><td class="mono">offloaded</td><td>Not a core <span class="inline">OffloadEntry</span> field from the L1 parser. After the L1 write, <span class="inline">markOffloadStatus</span> adds/updates it with <span class="inline">true</span> or <span class="inline">"deleted"</span>.</td></tr>
</table>

<h2>Storage isolation: current session and shared agent folders</h2>
<div class="cellgroup">
  <div class="cg-cap"><b>current session</b>: append only this session's JSONL so tool results from different sessions do not mix.</div>
  <div class="cells"><span class="cell hot">offload-&lt;sessionId&gt;.jsonl</span><span class="cell">latest-turn context</span><span class="cell">pending ToolPairs</span></div>
  <div class="cg-cap"><b>shared agent folders</b>: drill-down artifacts under the same agent; refs use timestamp filenames, and mmds live in the agent directory.</div>
  <div class="cells"><span class="cell">refs/</span><span class="cell">mmds/</span><span class="cell">state</span></div>
</div>

<p>
Isolation is not merely "write one directory"; storage context is created per agent and per session. The current session's
<span class="inline">offload-&lt;sessionId&gt;.jsonl</span> keeps lightweight indexes, while shared <span class="inline">refs/</span>
under the agent directory use timestamp names for drill-down evidence and <span class="inline">mmds/</span> holds task canvases. Write-time dedup by
<span class="inline">tool_call_id</span> prevents repeated hooks, retries, or replays from creating duplicate JSONL rows.
</p>

<h2>Core pseudocode</h2>
<pre class="code">on_after_tool_call(event):
    pair = collect_tool_name_id_params_result(event)
    if pair.is_heartbeat or pair.is_approval_pending:
        return
    state.pending_pairs.append(pair)
    if len(state.pending_pairs) &gt;= force_trigger_threshold:
        entries = l1_summarize(state.pending_pairs)
        for entry in entries:
            entry.ref = write_ref_md(entry.raw_result)
        append_offload_entries(entries)</pre>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 7 lesson 28: this lesson focuses on after-tool-call, refs, and offload JSONL capture.</li>
    <li><span class="inline">src/offload/hooks/after-tool-call.ts</span>: <span class="inline">createAfterToolCallHandler</span> resolves tool call ID/params/result, skips heartbeat and approval-pending events, and calls <span class="inline">stateManager.addToolPair</span>.</li>
    <li><span class="inline">src/offload/hooks/llm-output.ts</span>: <span class="inline">shouldForceL1</span> and <span class="inline">forceTriggerThreshold</span> decide when pending pairs trigger L1.</li>
    <li><span class="inline">src/offload/index.ts</span>: orchestrates L1 triggering, <span class="inline">appendOffloadEntries</span>, <span class="inline">writeRefMd</span>, and <span class="inline">sanitizeText</span>.</li>
    <li><span class="inline">src/offload/storage.ts</span>: implements <span class="inline">writeRefMd</span>, <span class="inline">appendOffloadEntries</span>, <span class="inline">readOffloadEntries</span>, <span class="inline">markOffloadStatus</span>, and <span class="inline">parseJsonlSafe</span>.</li>
    <li><span class="inline">src/offload/local-llm/prompts/l1-prompt.ts</span> and <span class="inline">src/offload/local-llm/parsers/l1-parser.ts</span>: define the L1 summarization prompt and parser rules; execution goes through a pluggable client, either <span class="inline">LocalLlmClient</span> or <span class="inline">BackendClient</span>.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  after-tool-call does not push large tool results straight back into context. It builds a <span class="inline">ToolPair</span> buffer first;
  once the threshold is reached, Offload-L1 creates <span class="inline">OffloadEntry</span> records, raw output goes to refs, and summaries go to JSONL.
  Agent/session isolation plus write-time dedup keep the system traceable, recoverable, and compact.
</div>
""",
}


LESSON_29 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
本地模式不是“一次调用解决所有 Offload 问题”。<span class="inline">LocalLlmClient</span> 暴露和后端 client 相同的方法，
但把三种责任拆成三次本地 LLM 调用：<span class="inline">l1Summarize</span> 把工具对压成高密度摘要，
<span class="inline">l15Judge</span> 判断最新用户轮次与长任务边界，<span class="inline">l2Generate</span> 把未分配的 offload 行组织成 Mermaid MMD 并返回 <span class="inline">node_mapping</span>。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  像一个本地项目助理团队：记录员先把工具结果写成索引卡；调度员判断“这是继续、收尾还是新任务”；白板管理员再把未贴到白板的卡片放进 Mermaid 任务画布，并把卡片编号回填。
</div>

<h2>三次本地模型调用，不共享一份输出</h2>
<div class="flow">
  <div class="node"><div class="nt">tool pairs</div><div class="nd">工具名、参数、调用 ID、结果与最近消息。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1 summaries</div><div class="nd">本地模型只产出 tool_call、summary、tool_call_id、timestamp、score；<span class="inline">node_id</span> 为空。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">host ref backfill</div><div class="nd">宿主 pipeline 先写 refs，再用 refs map 回填 <span class="inline">result_ref</span>。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1.5 task gate</div><div class="nd">判断继续、完成或开始长任务，激活/切换 task 与 MMD。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L2 independent trigger</div><div class="nd">由未分配行数量、timeout 或 task switch 触发 Mermaid 更新。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">node backfill</div><div class="nd">用 <span class="inline">node_mapping</span> 回填 JSONL 行的 node_id。</div></div>
</div>

<p>
关键点是责任边界：L1 只关心“这批工具结果说明了什么”，不负责 refs 路径；
宿主 pipeline 根据 L1 结果写 refs 并回填 <span class="inline">result_ref</span>；
L1.5 只负责 gate task/MMD 是否激活或切换；常规 L2 触发独立运行，task switch 只会成为一次独立 flush 触发。
L2 只关心“未分配摘要应落到 Mermaid 画布的哪个节点”。
拆开后，某一层失败不会伪造另一层结果。
</p>

<h2>L1 / L1.5 / L2 输入输出对照</h2>
<div class="cols">
  <div class="col"><h4>L1 input/output</h4><p><b>L1 input</b>：<span class="inline">tool_pairs</span> 与 <span class="inline">recent_messages</span>。<br><b>L1 output</b>：JSON array，每项只包含 <span class="inline">tool_call</span>、<span class="inline">summary</span>、<span class="inline">tool_call_id</span>、<span class="inline">timestamp</span>、<span class="inline">score</span>，以及 <span class="inline">node_id = null</span>；<span class="inline">result_ref</span> 不是模型输出。</p></div>
  <div class="col"><h4>Host + L1.5 output</h4><p><b>Host step</b>：写 refs，并从 refs map 回填 <span class="inline">result_ref</span>。<br><b>L1.5 input</b>：最近用户/助手消息、当前 active MMD、可选 MMD 列表。<br><b>L1.5 output</b>：是否长任务、继续/完成/新任务判断、应激活哪个 task/MMD。</p></div>
  <div class="col"><h4>L2 input/output</h4><p><b>L2 input</b>：尚未分配 <span class="inline">node_id</span> 的 offload entries 与 active MMD。<br><b>L2 output</b>：Mermaid MMD 文本和 <span class="inline">node_mapping</span>；这是安全回填 node_id 的主路径，wait entries 另有兜底路径。</p></div>
</div>

<h2>本地 client 与后端 client 共用接口</h2>
<div class="card detail">
  <div class="tag">🔌 接口边界</div>
  <span class="inline">LocalLlmClient</span> 实现与 backend client 相同的 <span class="inline">l1Summarize</span>、<span class="inline">l15Judge</span>、<span class="inline">l2Generate</span> 方法。
  上层 pipeline 不需要知道当前模式是 local 还是 backend；差异被封装在本地 <span class="inline">llm-caller.ts</span> 的模型配置、直接调用和 timeout 处理里。
</div>

<table class="t">
  <tr><th>方法</th><th>Prompt file</th><th>Parser file</th><th>失败行为</th></tr>
  <tr><td class="mono">LocalLlmClient.l1Summarize</td><td class="mono">src/offload/local-llm/prompts/l1-prompt.ts</td><td class="mono">src/offload/local-llm/parsers/l1-parser.ts</td><td>L1 parser 只接受 JSON array 契约；解析失败时不应写入伪摘要。</td></tr>
  <tr><td class="mono">LocalLlmClient.l15Judge</td><td class="mono">src/offload/local-llm/prompts/l15-prompt.ts</td><td class="mono">src/offload/local-llm/parsers/l15-parser.ts</td><td>判断契约无效时保持保守：不随意切换 active MMD 或误判新长任务。</td></tr>
  <tr><td class="mono">LocalLlmClient.l2Generate</td><td class="mono">src/offload/local-llm/prompts/l2-prompt.ts</td><td class="mono">src/offload/local-llm/parsers/l2-parser.ts</td><td>L2 parser 要同时拿到 Mermaid 与 <span class="inline">node_mapping</span>；缺失映射就不能安全回填。</td></tr>
</table>

<h2>核心伪代码</h2>
<pre class="code">client = LocalLlmClient(config)
refs_map = write_refs_for_tool_pairs(tool_pairs)
l1_entries = client.l1Summarize(tool_pairs, recent_messages)
entries = backfill_result_ref_from_refs_map(l1_entries, refs_map)
judgment = client.l15Judge(recent_messages, active_mmd, available_mmds)
if judgment.isLongTask:
    activate_or_switch_task_mmd(judgment)

if should_run_l2(null_node_count, timeout, task_switched):
    l2_result = client.l2Generate(unassigned_entries, active_mmd)
    write_or_patch_mmd(l2_result)
    backfill_node_ids(l2_result.node_mapping)</pre>

<h2>独立触发与回填路径</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>L1 先产生未分配 entries</h4><p>L1 parser/model 返回摘要字段和 <span class="inline">node_id = null</span>；宿主写 refs 后再回填 <span class="inline">result_ref</span>，然后追加到 offload JSONL。</p><div class="mono">L1 fields + host result_ref</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>L1.5 gate 任务边界</h4><p>最新用户轮次可能继续旧任务、完成旧任务，或开启新长任务；这只决定 task/MMD 激活与切换，不直接触发 L2 生成。</p><div class="mono">continue / complete / start</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>L2 独立触发</h4><p><span class="inline">src/offload/pipelines/l2-mermaid.ts</span> 按未分配 entries 数量、timeout 或 task switch 独立决定是否生成或修补 MMD。</p><div class="mono">null count / timeout / task switch</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>按 mapping 回填</h4><p><span class="inline">node_mapping</span> 是把 JSONL 行安全连接到 Mermaid 节点的主路径；wait entries 可走兜底路径，避免因等待态缺映射而中断。</p><div class="mono">tool_call_id -&gt; node_id</div></div></div>
</div>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 7 lesson 29：本课聚焦 Offload-L1 / L1.5 / L2 的 local LLM pipeline 分工。</li>
    <li><span class="inline">src/offload/local-llm/index.ts</span>：<span class="inline">LocalLlmClient.l1Summarize</span>、<span class="inline">LocalLlmClient.l15Judge</span>、<span class="inline">LocalLlmClient.l2Generate</span> 是三条独立本地调用入口。</li>
    <li><span class="inline">src/offload/local-llm/llm-caller.ts</span>：封装直接 LLM 调用、timeout 和本地模型配置。</li>
    <li><span class="inline">src/offload/local-llm/prompts/l1-prompt.ts</span> 与 <span class="inline">src/offload/local-llm/parsers/l1-parser.ts</span>：定义 L1 JSON array 摘要契约。</li>
    <li><span class="inline">src/offload/local-llm/prompts/l15-prompt.ts</span> 与 <span class="inline">src/offload/local-llm/parsers/l15-parser.ts</span>：定义 L1.5 任务边界判断契约。</li>
    <li><span class="inline">src/offload/local-llm/prompts/l2-prompt.ts</span> 与 <span class="inline">src/offload/local-llm/parsers/l2-parser.ts</span>：定义 L2 Mermaid 与 <span class="inline">node_mapping</span> 契约。</li>
    <li><span class="inline">src/offload/pipelines/l2-mermaid.ts</span>：实现 L2 的独立触发、<span class="inline">node_mapping</span> 主回填和 wait-entry 兜底路径。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L1、L1.5、L2 是三种不同本地模型责任：摘要工具证据、gate 任务/MMD 激活、维护 Mermaid 任务画布。
  <span class="inline">result_ref</span> 由宿主写 refs 后回填；L2 由 null-count、timeout 或 task-switch 独立触发。
  <span class="inline">LocalLlmClient</span> 与 backend client 共用接口，让 local/backend 模式可以共享上层 pipeline。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Local mode is not “one call solves every Offload problem.” <span class="inline">LocalLlmClient</span> exposes the same methods as the backend client,
but splits responsibility into three local LLM calls: <span class="inline">l1Summarize</span> compresses tool pairs into high-density summaries,
<span class="inline">l15Judge</span> judges the latest user turn and long-task boundary, and <span class="inline">l2Generate</span> organizes unassigned offload rows into Mermaid MMD with <span class="inline">node_mapping</span>.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Imagine a local project-assistant team: the recorder turns tool results into index cards; the dispatcher decides “continue, finish, or start a task”; the whiteboard keeper places unassigned cards onto a Mermaid task canvas and backfills card IDs.
</div>

<h2>Three local model calls, not one shared output</h2>
<div class="flow">
  <div class="node"><div class="nt">tool pairs</div><div class="nd">Tool name, args, call ID, result, and recent messages.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1 summaries</div><div class="nd">The local model returns tool_call, summary, tool_call_id, timestamp, score, and empty node_id.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">host ref backfill</div><div class="nd">The host pipeline writes refs, then backfills <span class="inline">result_ref</span> from its refs map.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1.5 task gate</div><div class="nd">Judge continue, complete, or start long task; activate or switch task/MMD.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L2 independent trigger</div><div class="nd">Null-count, timeout, or task-switch rules trigger Mermaid updates.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">node backfill</div><div class="nd">Use <span class="inline">node_mapping</span> to backfill JSONL node_id values.</div></div>
</div>

<p>
The boundary is the point: L1 only asks “what did these tool results prove?” and does not own refs paths;
the host pipeline writes refs and backfills <span class="inline">result_ref</span> from the L1 results;
L1.5 only gates task/MMD activation or switching; the normal L2 trigger runs independently, and a task switch only becomes an independent flush trigger.
L2 only asks “where should unassigned summaries land on the Mermaid canvas?”
With the calls split, a failure in one layer does not invent output for another layer.
</p>

<h2>L1 / L1.5 / L2 input-output comparison</h2>
<div class="cols">
  <div class="col"><h4>L1 input/output</h4><p><b>L1 input</b>: <span class="inline">tool_pairs</span> plus <span class="inline">recent_messages</span>.<br><b>L1 output</b>: a JSON array whose items contain only <span class="inline">tool_call</span>, <span class="inline">summary</span>, <span class="inline">tool_call_id</span>, <span class="inline">timestamp</span>, <span class="inline">score</span>, and <span class="inline">node_id = null</span>; <span class="inline">result_ref</span> is not model output.</p></div>
  <div class="col"><h4>Host + L1.5 output</h4><p><b>Host step</b>: write refs and backfill <span class="inline">result_ref</span> from the refs map.<br><b>L1.5 input</b>: recent user/assistant messages, current active MMD, and available MMDs.<br><b>L1.5 output</b>: whether this is a long task, whether it continues/completes/starts a task, and which task/MMD should be active.</p></div>
  <div class="col"><h4>L2 input/output</h4><p><b>L2 input</b>: offload entries that still lack <span class="inline">node_id</span>, plus the active MMD.<br><b>L2 output</b>: Mermaid MMD text and <span class="inline">node_mapping</span>; this is the primary safe path for node_id backfill, while wait entries have a fallback.</p></div>
</div>

<h2>One interface for local and backend clients</h2>
<div class="card detail">
  <div class="tag">🔌 Interface boundary</div>
  <span class="inline">LocalLlmClient</span> implements the same <span class="inline">l1Summarize</span>, <span class="inline">l15Judge</span>, and <span class="inline">l2Generate</span> methods as the backend client.
  The upper pipeline does not need to know whether the mode is local or backend; local differences live inside <span class="inline">llm-caller.ts</span>, including model config, direct calls, and timeout handling.
</div>

<table class="t">
  <tr><th>Method</th><th>Prompt file</th><th>Parser file</th><th>Failure behavior</th></tr>
  <tr><td class="mono">LocalLlmClient.l1Summarize</td><td class="mono">src/offload/local-llm/prompts/l1-prompt.ts</td><td class="mono">src/offload/local-llm/parsers/l1-parser.ts</td><td>The L1 parser accepts the JSON array contract only; parse failure should not write invented summaries.</td></tr>
  <tr><td class="mono">LocalLlmClient.l15Judge</td><td class="mono">src/offload/local-llm/prompts/l15-prompt.ts</td><td class="mono">src/offload/local-llm/parsers/l15-parser.ts</td><td>Invalid judgment stays conservative: do not switch active MMDs or start a new long task casually.</td></tr>
  <tr><td class="mono">LocalLlmClient.l2Generate</td><td class="mono">src/offload/local-llm/prompts/l2-prompt.ts</td><td class="mono">src/offload/local-llm/parsers/l2-parser.ts</td><td>The L2 parser needs both Mermaid and <span class="inline">node_mapping</span>; without mapping, node backfill is unsafe.</td></tr>
</table>

<h2>Core pseudocode</h2>
<pre class="code">client = LocalLlmClient(config)
refs_map = write_refs_for_tool_pairs(tool_pairs)
l1_entries = client.l1Summarize(tool_pairs, recent_messages)
entries = backfill_result_ref_from_refs_map(l1_entries, refs_map)
judgment = client.l15Judge(recent_messages, active_mmd, available_mmds)
if judgment.isLongTask:
    activate_or_switch_task_mmd(judgment)

if should_run_l2(null_node_count, timeout, task_switched):
    l2_result = client.l2Generate(unassigned_entries, active_mmd)
    write_or_patch_mmd(l2_result)
    backfill_node_ids(l2_result.node_mapping)</pre>

<h2>Independent trigger and backfill path</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>L1 creates unassigned entries first</h4><p>The L1 parser/model returns summary fields and <span class="inline">node_id = null</span>; the host writes refs, backfills <span class="inline">result_ref</span>, then appends offload JSONL.</p><div class="mono">L1 fields + host result_ref</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>L1.5 gates the task boundary</h4><p>The latest user turn can continue an old task, complete one, or start a new long task; that only activates or switches task/MMD state, not L2 generation.</p><div class="mono">continue / complete / start</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>L2 triggers independently</h4><p><span class="inline">src/offload/pipelines/l2-mermaid.ts</span> independently decides whether to generate or patch MMD from null-node entry count, timeout, or task switch.</p><div class="mono">null count / timeout / task switch</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Backfill by mapping</h4><p><span class="inline">node_mapping</span> is the primary safe path connecting JSONL rows to Mermaid nodes; wait entries can use a fallback so missing wait-state mappings do not block the pipeline.</p><div class="mono">tool_call_id -&gt; node_id</div></div></div>
</div>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 7 lesson 29: this lesson focuses on local LLM pipeline responsibilities for Offload-L1 / L1.5 / L2.</li>
    <li><span class="inline">src/offload/local-llm/index.ts</span>: <span class="inline">LocalLlmClient.l1Summarize</span>, <span class="inline">LocalLlmClient.l15Judge</span>, and <span class="inline">LocalLlmClient.l2Generate</span> are three separate local call entry points.</li>
    <li><span class="inline">src/offload/local-llm/llm-caller.ts</span>: wraps direct LLM calls, timeout handling, and local model configuration.</li>
    <li><span class="inline">src/offload/local-llm/prompts/l1-prompt.ts</span> and <span class="inline">src/offload/local-llm/parsers/l1-parser.ts</span>: define the L1 JSON array summarization contract.</li>
    <li><span class="inline">src/offload/local-llm/prompts/l15-prompt.ts</span> and <span class="inline">src/offload/local-llm/parsers/l15-parser.ts</span>: define the L1.5 task-boundary judgment contract.</li>
    <li><span class="inline">src/offload/local-llm/prompts/l2-prompt.ts</span> and <span class="inline">src/offload/local-llm/parsers/l2-parser.ts</span>: define the L2 Mermaid plus <span class="inline">node_mapping</span> contract.</li>
    <li><span class="inline">src/offload/pipelines/l2-mermaid.ts</span>: implements the independent L2 trigger, primary <span class="inline">node_mapping</span> backfill, and wait-entry fallback path.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L1, L1.5, and L2 are three different local model responsibilities: summarize tool evidence, gate task/MMD activation, and maintain the Mermaid task canvas.
  <span class="inline">result_ref</span> is backfilled by the host after refs are written; L2 runs on independent null-count, timeout, or task-switch triggers.
  <span class="inline">LocalLlmClient</span> shares one interface with the backend client so local/backend modes can reuse the same upper pipeline.
</div>
""",
}



LESSON_30 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Mermaid MMD 不是为了好看，而是 Context Offload 的紧凑任务状态画布。Offload-L2 可以完整写入新的
<span class="inline">.mmd</span> 文件，也可以按行修补已有画布；但无论是新节点还是补丁里的新工具条目，都必须拿到
<span class="inline">node_id</span>。这个 ID 把注入到 prompt 的任务符号，重新连接回 offload JSONL 摘要行和
<span class="inline">refs/*.md</span> 原始证据。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  把 MMD 当作项目作战地图：地图上一个节点写着“修复登录测试”。<span class="inline">node_id</span> 像坐标编号，
  让你从地图坐标回到索引卡，再翻到证据夹里的原始日志。没有坐标，地图再漂亮也无法复盘证据。
</div>

<h2>MMD 是任务状态画布，不是装饰图</h2>
<div class="layers">
  <div class="layer l-main"><div class="lh"><span class="badge">canvas</span><span class="name">mmds/task.mmd</span></div><div class="ld">用 Mermaid 节点表达当前任务、等待项、已处理项和后续路径；L2 负责 <span class="inline">writeMmd</span> 完整写入或 <span class="inline">patchMmd</span> 行级修补。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">index</span><span class="name">offload JSONL rows</span></div><div class="ld">每行保存 tool_call_id、summary、result_ref、offloaded 和 <span class="inline">node_id</span>；当前 pipeline 通过 <span class="inline">backfillNodeIds</span> 进入 <span class="inline">rewriteAllOffloadEntries</span> 重写行。</div></div>
  <div class="layer l-core"><div class="lh"><span class="badge">evidence</span><span class="name">refs/*.md</span></div><div class="ld">完整工具输出、错误栈或搜索结果留在 refs markdown；prompt 里不需要常驻所有原始行。</div></div>
</div>

<p>
因此评审 MMD 生成时，不应只问“图是否能渲染”。更重要的问题是：每个新工具证据是否被放到明确节点？
节点 ID 是否符合 <span class="inline">MMD_NODE_ID_RE</span>？映射是否能被规范化后回填到 JSONL？
如果任何一步断开，Offload-L3 注入的 active node 就只剩摘要，无法安全下钻。
</p>

<h2>从 active 节点下钻恢复细节</h2>
<div class="flow trace">
  <div class="node hl"><div class="nt">active MMD node</div><div class="nd">例如 <span class="inline">027-N1</span>：当前任务地图上的一个节点。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">node_id</div><div class="nd">Offload-L3 只注入节点和少量周边上下文。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">matching JSONL entries</div><div class="nd"><span class="inline">getCurrentTaskNodeIds</span> 与 lookup map 找到相同行。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">ref markdown</div><div class="nd"><span class="inline">result_ref</span> 指向 refs 文件。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">recovered detail</div><div class="nd">需要时再读完整 stdout、diff、测试失败或搜索命中。</div></div>
</div>

<h2>node_id 生命周期</h2>
<table class="t">
  <tr><th>状态</th><th>含义</th><th>恢复能力</th></tr>
  <tr><td class="mono">null</td><td>L1 刚写入的未分配行；还没有进入 MMD 画布。</td><td>能按时间或 tool_call_id 找到摘要和 ref，但不能从 MMD 节点直接定位。</td></tr>
  <tr><td class="mono">wait</td><td>等待态或兜底映射；L2 尚未能归入稳定任务节点。</td><td>可保守保留，不应伪造具体节点；后续 L2 可再归一化。</td></tr>
  <tr><td class="mono">027-N1</td><td>具体节点 ID，符合 MMD 节点命名规则并出现在 <span class="inline">node_mapping</span>。</td><td>MMD node -&gt; JSONL row -&gt; refs detail 的主下钻路径完整。</td></tr>
  <tr><td class="mono">deleted / offloaded</td><td>行可能被标记为已 offload 或删除态；状态不等于丢失证据。</td><td>注入层可跳过或压缩显示，但仍应能通过索引和 ref 追溯历史。</td></tr>
</table>

<h2>写入、修补与映射回填</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>触发 L2</h4><p><span class="inline">checkL2Trigger</span> 负责未分配行数量和 timeout；task switch 走单独的强制 L2 flush（<span class="inline">task_switch_flush</span>）。</p><div class="mono">null entries / timeout; forced switch flush</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>生成或修补 MMD</h4><p>L2 可以用 <span class="inline">writeMmd</span> 写完整画布，也可以用 <span class="inline">patchMmd</span> 做行级更新；<span class="inline">readMmd</span> 和 <span class="inline">listMmds</span> 支持读取当前任务与候选画布。</p><div class="mono">full write or line patch</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>规范化 node mapping</h4><p><span class="inline">l2-prompt.ts</span> 要求输出 <span class="inline">node_mapping</span>；<span class="inline">l2-parser.ts</span> 解析后，pipeline 用 <span class="inline">MMD_NODE_ID_RE</span> 与映射规范化避免脏 ID。</p><div class="mono">tool_call_id -&gt; normalized node_id</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>回填 JSONL</h4><p><span class="inline">backfillNodeIds</span> 在当前路径中调用 <span class="inline">rewriteAllOffloadEntries</span>，让每个新工具条目都能从 MMD 节点返回证据行。</p><div class="mono">mapping -&gt; rewrite all offload rows</div></div></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">if checkL2Trigger(entries_without_node_id, active_task):
    result = l2Generate(active_mmd, entries_without_node_id)
    if result.full_mmd:
        writeMmd(active_task, result.mmd)
    else:
        patchMmd(active_task, result.line_patches)

    mapping = normalize_node_mapping(result.node_mapping, MMD_NODE_ID_RE)
    backfillNodeIds(ctx, mapping, wait_ids, logger, options)
    # backfillNodeIds persists via rewriteAllOffloadEntries

if task_switch_detected:
    task_switch_flush(active_task)

active_ids = getCurrentTaskNodeIds(active_mmd)
entries = read_offload_jsonl()
lookup = populateOffloadLookupMap(entries)  # for getOffloadEntry(lookup, toolCallId)
for entry in entries:
    if entry.node_id in active_ids:
        detail = readRefMd(ctx, entry.result_ref)</pre>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 7 lesson 30 与 <span class="inline">node_id</span> 下钻要求：本课聚焦 MMD 画布、节点映射和证据恢复。</li>
    <li><span class="inline">src/offload/pipelines/l2-mermaid.ts</span>：<span class="inline">checkL2Trigger</span>、<span class="inline">backfillNodeIds</span>、<span class="inline">MMD_NODE_ID_RE</span> 与 node mapping 规范化；task switch 是单独的强制 L2 flush。</li>
    <li><span class="inline">src/offload/storage.ts</span>：<span class="inline">writeMmd</span>、<span class="inline">patchMmd</span>、<span class="inline">readMmd</span>、<span class="inline">listMmds</span>、<span class="inline">rewriteAllOffloadEntries</span>、<span class="inline">readRefMd</span>。</li>
    <li><span class="inline">src/offload/mmd-injector.ts</span>：<span class="inline">injectMmdIntoMessages</span>、<span class="inline">maybeUpdateMmdInMessages</span> 与 <span class="inline">MMD_MESSAGE_MARKER</span> 管理 prompt 里的 MMD 片段。</li>
    <li><span class="inline">src/offload/l3-helpers.ts</span>：<span class="inline">getCurrentTaskNodeIds</span>、按 <span class="inline">tool_call_id</span> 建索引的 <span class="inline">populateOffloadLookupMap</span>、<span class="inline">getOffloadEntry(map, toolCallId)</span> 支撑按节点下钻。</li>
    <li><span class="inline">src/offload/local-llm/prompts/l2-prompt.ts</span> 与 <span class="inline">src/offload/local-llm/parsers/l2-parser.ts</span>：要求 L2 输出 <span class="inline">node_mapping</span>，否则不能可靠回填。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  MMD 是当前任务的紧凑地图，<span class="inline">node_id</span> 是从地图回到证据的索引。
  L2 不只生成图，还负责完整写入或行级修补 MMD，并把每个新工具条目映射回 JSONL。
  下钻恢复路径是 active MMD node -&gt; node_id -&gt; JSONL entries -&gt; refs markdown，不需要把每行原始日志常驻 prompt。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Mermaid MMD is not a pretty diagram; it is Context Offload's compact task-state canvas. Offload-L2 may write a new
<span class="inline">.mmd</span> file in full, or patch an existing canvas line by line. Either way, every new tool entry must receive a
<span class="inline">node_id</span>. That ID connects injected task context back to offload JSONL summary rows and
<span class="inline">refs/*.md</span> raw evidence.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Treat MMD as a project operations map: one map node says “fix login tests.” The <span class="inline">node_id</span> is its coordinate,
  letting you go from the map coordinate to the index card and then to the evidence folder with the original log. Without coordinates, a pretty map cannot recover evidence.
</div>

<h2>MMD is task-state canvas, not decoration</h2>
<div class="layers">
  <div class="layer l-main"><div class="lh"><span class="badge">canvas</span><span class="name">mmds/task.mmd</span></div><div class="ld">Mermaid nodes express current work, wait items, processed items, and next paths; L2 owns full <span class="inline">writeMmd</span> writes and line-based <span class="inline">patchMmd</span> updates.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">index</span><span class="name">offload JSONL rows</span></div><div class="ld">Each row stores tool_call_id, summary, result_ref, offloaded, and <span class="inline">node_id</span>; the current pipeline goes through <span class="inline">backfillNodeIds</span> into <span class="inline">rewriteAllOffloadEntries</span> to rewrite rows.</div></div>
  <div class="layer l-core"><div class="lh"><span class="badge">evidence</span><span class="name">refs/*.md</span></div><div class="ld">Full tool output, stack traces, or search hits remain in refs markdown; the prompt does not need every original line resident.</div></div>
</div>

<p>
So MMD review should not ask only “does the diagram render?” The more important questions are: did every new tool evidence row land on a clear node?
Does the node ID match <span class="inline">MMD_NODE_ID_RE</span>? Can the mapping be normalized and backfilled to JSONL?
If any step breaks, the active node injected by Offload-L3 becomes only a summary, not a safe drill-down path.
</p>

<h2>Drill down from active node to recovered detail</h2>
<div class="flow trace">
  <div class="node hl"><div class="nt">active MMD node</div><div class="nd">For example <span class="inline">027-N1</span>: a node on the current task map.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">node_id</div><div class="nd">Offload-L3 injects only the node and small surrounding context.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">matching JSONL entries</div><div class="nd"><span class="inline">getCurrentTaskNodeIds</span> plus a lookup map finds rows with the same ID.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">ref markdown</div><div class="nd"><span class="inline">result_ref</span> points at the refs file.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">recovered detail</div><div class="nd">Read full stdout, diff, test failure, or search hits only when needed.</div></div>
</div>

<h2>node_id lifecycle</h2>
<table class="t">
  <tr><th>State</th><th>Meaning</th><th>Recovery ability</th></tr>
  <tr><td class="mono">null</td><td>A newly written L1 row that has not entered the MMD canvas yet.</td><td>You can find the summary and ref by time or tool_call_id, but not directly from an MMD node.</td></tr>
  <tr><td class="mono">wait</td><td>A wait-state or fallback mapping; L2 could not place it in a stable task node yet.</td><td>Preserve it conservatively; do not invent a concrete node. Later L2 runs can normalize it.</td></tr>
  <tr><td class="mono">027-N1</td><td>A concrete node ID that matches the MMD naming rule and appears in <span class="inline">node_mapping</span>.</td><td>The main drill-down path MMD node -&gt; JSONL row -&gt; refs detail is complete.</td></tr>
  <tr><td class="mono">deleted / offloaded</td><td>A row may be marked offloaded or deleted; status is not the same as lost evidence.</td><td>The injection layer may skip or compress display, while indexes and refs still preserve traceability.</td></tr>
</table>

<h2>Write, patch, and backfill mapping</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Trigger L2</h4><p><span class="inline">checkL2Trigger</span> covers unassigned-row count and timeout; task switch uses a separate forced L2 flush (<span class="inline">task_switch_flush</span>).</p><div class="mono">null entries / timeout; forced switch flush</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Generate or patch MMD</h4><p>L2 can write a full canvas with <span class="inline">writeMmd</span>, or make line-based updates with <span class="inline">patchMmd</span>; <span class="inline">readMmd</span> and <span class="inline">listMmds</span> support reading the active task and candidate canvases.</p><div class="mono">full write or line patch</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Normalize node mapping</h4><p><span class="inline">l2-prompt.ts</span> requires <span class="inline">node_mapping</span>; after <span class="inline">l2-parser.ts</span> parses it, the pipeline uses <span class="inline">MMD_NODE_ID_RE</span> and mapping normalization to reject dirty IDs.</p><div class="mono">tool_call_id -&gt; normalized node_id</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Backfill JSONL</h4><p>In the current path, <span class="inline">backfillNodeIds</span> calls <span class="inline">rewriteAllOffloadEntries</span> so every new tool entry can return from MMD node to evidence row.</p><div class="mono">mapping -&gt; rewrite all offload rows</div></div></div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">if checkL2Trigger(entries_without_node_id, active_task):
    result = l2Generate(active_mmd, entries_without_node_id)
    if result.full_mmd:
        writeMmd(active_task, result.mmd)
    else:
        patchMmd(active_task, result.line_patches)

    mapping = normalize_node_mapping(result.node_mapping, MMD_NODE_ID_RE)
    backfillNodeIds(ctx, mapping, wait_ids, logger, options)
    # backfillNodeIds persists via rewriteAllOffloadEntries

if task_switch_detected:
    task_switch_flush(active_task)

active_ids = getCurrentTaskNodeIds(active_mmd)
entries = read_offload_jsonl()
lookup = populateOffloadLookupMap(entries)  # for getOffloadEntry(lookup, toolCallId)
for entry in entries:
    if entry.node_id in active_ids:
        detail = readRefMd(ctx, entry.result_ref)</pre>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 7 lesson 30 and the <span class="inline">node_id</span> drill-down requirement: this lesson focuses on MMD canvas, node mapping, and evidence recovery.</li>
    <li><span class="inline">src/offload/pipelines/l2-mermaid.ts</span>: <span class="inline">checkL2Trigger</span>, <span class="inline">backfillNodeIds</span>, <span class="inline">MMD_NODE_ID_RE</span>, and node mapping normalization; task switch is a separate forced L2 flush.</li>
    <li><span class="inline">src/offload/storage.ts</span>: <span class="inline">writeMmd</span>, <span class="inline">patchMmd</span>, <span class="inline">readMmd</span>, <span class="inline">listMmds</span>, <span class="inline">rewriteAllOffloadEntries</span>, and <span class="inline">readRefMd</span>.</li>
    <li><span class="inline">src/offload/mmd-injector.ts</span>: <span class="inline">injectMmdIntoMessages</span>, <span class="inline">maybeUpdateMmdInMessages</span>, and <span class="inline">MMD_MESSAGE_MARKER</span> manage the MMD fragment in prompt messages.</li>
    <li><span class="inline">src/offload/l3-helpers.ts</span>: <span class="inline">getCurrentTaskNodeIds</span>, <span class="inline">populateOffloadLookupMap</span> keyed by <span class="inline">tool_call_id</span>, and <span class="inline">getOffloadEntry(map, toolCallId)</span> support node-based drill-down.</li>
    <li><span class="inline">src/offload/local-llm/prompts/l2-prompt.ts</span> and <span class="inline">src/offload/local-llm/parsers/l2-parser.ts</span>: require L2 to output <span class="inline">node_mapping</span>; otherwise reliable backfill is impossible.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  MMD is the compact map of the current task, and <span class="inline">node_id</span> is the index from map back to evidence.
  L2 does more than generate a diagram: it writes full MMD files or applies line-based patches, then maps every new tool entry back to JSONL.
  Drill-down recovery is active MMD node -&gt; node_id -&gt; JSONL entries -&gt; refs markdown, without keeping every original log line in prompt.
</div>
""",
}



LESSON_31 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L3 是 Context Offload 真正进入模型前的最后一道运行时循环：先在 prompt 构建前注入当前 active MMD，
再把已经确认 offload 的旧工具区域按确定性快路径替换掉，随后用精确 token 快照判断是否需要温和、激进或紧急压缩。
目标不是“尽量删”，而是在不破坏当前任务、最新用户消息和工具调用结构的前提下，把模型输入压回安全窗口。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  像飞机起飞前的配载检查：任务地图先放进驾驶舱；已托运的旧行李用行李票替代；如果重量仍超标，先取下低优先级包，
  再把旧箱子移到货舱清单，最后才启动紧急减载。乘客、驾驶指令和安全联络不能被扔掉。
</div>

<h2>最后一圈发生在模型调用前</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>before prompt</h4><p><span class="inline">before-prompt-build.ts</span> 跳过内部 memory-pipeline session，读取 active MMD，并准备已确认 offload 的快路径。</p><div class="mono">skip internal pipeline; load active MMD</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>inject active MMD</h4><p><span class="inline">injectMmdIntoMessages</span> 用 marker 管理注入片段，避免重复追加；任务地图优先进入上下文。</p><div class="mono">MMD_MESSAGE_MARKER -&gt; task map</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>token snapshot</h4><p><span class="inline">context-token-tracker.ts</span> 与 <span class="inline">l3-token-counter.ts</span> 计算当前消息的 token 使用，而不是凭字符长度猜测。</p><div class="mono">messages -&gt; precise token count</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>mild replacement</h4><p><span class="inline">compressByScoreCascade</span> 优先替换低分、旧的、已 offload 区域，保留可通过 JSONL 与 refs 恢复的摘要。</p><div class="mono">old tool detail -&gt; compact offload marker</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>aggressive / emergency</h4><p>压力仍高时删除旧 offloaded 区域并注入历史 MMD；溢出或仍超阈值时进入 <span class="inline">emergencyCompress</span>。</p><div class="mono">history MMD -&gt; emergency trim</div></div></div>
</div>

<h2>三档压缩策略</h2>
<div class="cols">
  <div class="col"><h4>温和：score cascade</h4><p><b>触发</b>：token 接近阈值但仍可控。<br><b>动作</b>：按 score、年龄和 offload 状态替换旧工具结果。<br><b>恢复证据</b>：保留 tool_call_id、node_id、result_ref 与摘要。</p></div>
  <div class="col"><h4>激进：删除旧 offload 区域</h4><p><b>触发</b>：温和替换后仍超预算。<br><b>动作</b>：<span class="inline">aggressiveCompressUntilBelowThreshold</span> 删除更老的已 offload 消息块，并补入 history MMD。<br><b>恢复证据</b>：从历史 MMD 节点回 JSONL，再回 refs。</p></div>
  <div class="col"><h4>紧急：overflow 兜底</h4><p><b>触发</b>：token 压力仍高，或 <span class="inline">isTokenOverflowError</span> 检测到入口溢出。<br><b>动作</b>：<span class="inline">emergencyCompress</span> 只保留安全骨架、最新用户消息、有效工具对和必要任务地图。<br><b>恢复证据</b>：依赖 active/history MMD 与 JSONL 状态标记。</p></div>
</div>

<h2>快路径为什么要标记 JSONL 状态</h2>
<table class="t">
  <tr><th>状态</th><th>含义</th><th>下一轮行为</th></tr>
  <tr><td class="mono">offloaded: true</td><td><span class="inline">markOffloadStatus</span> 记录这段工具结果已经被安全替换为符号摘要。</td><td>before-prompt-build 可确定性重放替换，不需要重新推断是否压缩。</td></tr>
  <tr><td class="mono">offloaded: "deleted"</td><td>激进压缩已把旧的 live 区域移出上下文，但 JSONL 行和 refs 证据仍可追溯。</td><td>L3 注入层跳过原始区域，改用 history MMD 和节点索引恢复语义。</td></tr>
  <tr><td class="mono">node_id + result_ref</td><td>把 MMD 节点、JSONL 摘要和 refs 原文连接起来。</td><td>即使内容被删除，也能从任务地图下钻。</td></tr>
</table>

<h2>一次 LLM 调用的 hook 时间线</h2>
<div class="timeline">
  <div class="tl"><div class="tm">before_prompt_build</div><div class="td">跳过内部 memory-pipeline session；注入 active MMD；重放 <span class="inline">offloaded: true</span> 的确定性替换；写 token guard 快照。</div></div>
  <div class="tl"><div class="tm">llm_input_l3</div><div class="td"><span class="inline">createLlmInputL3Handler</span> 用精确计数决定 <span class="inline">compressByScoreCascade</span>、<span class="inline">aggressiveCompressUntilBelowThreshold</span> 或 <span class="inline">emergencyCompress</span>。</div></div>
  <div class="tl"><div class="tm">model call</div><div class="td">如果入口抛出 token overflow，<span class="inline">isTokenOverflowError</span> 把它转成紧急压缩信号，而不是盲目重试同一份超大输入。</div></div>
  <div class="tl"><div class="tm">after_tool_call</div><div class="td">工具返回后刷新 active MMD，报告 patch effectiveness，并让下一轮知道哪些替换真正节省了 token。</div></div>
</div>

<h2>安全规则：压缩不能破坏对话结构</h2>
<div class="card warn">
  <div class="tag">⚠️ Safety rules</div>
  <ul>
    <li>保留最新用户消息：它定义当前意图，不能为了省 token 删除。</li>
    <li>保持 tool-use / tool-result 成对有效：不能只删 tool-use 或只删 tool-result，避免宿主协议损坏。</li>
    <li>保护当前任务节点：<span class="inline">l3-helpers.ts</span> 的 current-task node 保护，避免把 active MMD 指向的证据刚好删掉。</li>
    <li>JSONL 写清状态：使用 <span class="inline">markOffloadStatus</span> 标记 <span class="inline">true</span> 和 <span class="inline">"deleted"</span>，让快路径可重复。</li>
    <li>跳过内部 memory-pipeline session：记忆流水线自己的压缩/生成不应递归触发 Context Offload。</li>
  </ul>
</div>

<h2>核心伪代码</h2>
<pre class="code">on_before_prompt_build(messages, session):
    if is_internal_memory_pipeline_session(session):
        return messages
    active_mmd = read_active_mmd(session)
    messages = injectMmdIntoMessages(messages, active_mmd)
    messages = reapply_confirmed_offloads(messages, statuses=[true, "deleted"])
    snapshot = build_precise_token_snapshot(messages)
    return messages, snapshot

on_llm_input_l3(messages, snapshot):
    if snapshot.total_tokens &lt; mild_threshold:
        return messages

    messages = compressByScoreCascade(messages, protect_latest_user=True)
    if count_tokens(messages) &lt; target_threshold:
        markOffloadStatus(replaced_entries, true)
        return messages

    messages = aggressiveCompressUntilBelowThreshold(messages, inject_history_mmd=True)
    markOffloadStatus(deleted_entries, "deleted")
    if count_tokens(messages) &lt; hard_threshold:
        return messages

    return emergencyCompress(messages,
        preserve_latest_user=True,
        preserve_valid_tool_pairs=True,
        preserve_current_task_nodes=True)

on_model_error(error, messages):
    if isTokenOverflowError(error):
        return emergencyCompress(messages)
    raise error</pre>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 7 lesson 31：本课收束 Context Offload 在模型调用前的最终运行时循环。</li>
    <li><span class="inline">src/offload/hooks/before-prompt-build.ts</span>：实现 fast-path re-apply、token guard，以及 prompt build 前的 MMD injection。</li>
    <li><span class="inline">src/offload/hooks/llm-input-l3.ts</span>：<span class="inline">createLlmInputL3Handler</span> 编排 <span class="inline">compressByScoreCascade</span>、<span class="inline">aggressiveCompressUntilBelowThreshold</span>、<span class="inline">emergencyCompress</span> 与 <span class="inline">isTokenOverflowError</span>。</li>
    <li><span class="inline">src/offload/mmd-injector.ts</span>：active MMD 插入、marker 识别和重复注入处理。</li>
    <li><span class="inline">src/offload/l3-helpers.ts</span>：替换 helper、lookup map 和 current-task node protection。</li>
    <li><span class="inline">src/offload/hooks/after-tool-call.ts</span>：工具循环内刷新 active MMD，并报告 patch effectiveness。</li>
    <li><span class="inline">src/offload/context-token-tracker.ts</span> 与 <span class="inline">src/offload/l3-token-counter.ts</span>：记录 token snapshot 并做 L3 计数。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L3 的正确顺序是：先注入 active MMD 和重放确认 offload，再用精确 token 计数决定压缩等级。
  温和替换、激进删除和紧急压缩都必须保留最新用户消息、有效工具对和当前任务节点；
  <span class="inline">markOffloadStatus</span> 的 <span class="inline">true</span> / <span class="inline">"deleted"</span> 状态让下一轮可以确定性快路径重放。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L3 is the last runtime loop before Context Offload enters the model call. It first injects the current active MMD before prompt build,
then deterministically re-applies replacements for already confirmed offloads, then uses precise token snapshots to decide whether to run mild,
aggressive, or emergency compression. The goal is not “delete as much as possible”; it is to return model input to a safe window without breaking the current task,
the latest user message, or tool-call structure.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Think of an aircraft weight check before takeoff: the task map goes into the cockpit first; old checked luggage is represented by claim tickets;
  if weight is still high, low-priority bags are moved first, then older boxes become cargo-manifest entries, and only then does emergency shedding start.
  Passengers, flight instructions, and safety communications cannot be thrown away.
</div>

<h2>The final loop before the model call</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>before prompt</h4><p><span class="inline">before-prompt-build.ts</span> skips internal memory-pipeline sessions, reads the active MMD, and prepares the confirmed-offload fast path.</p><div class="mono">skip internal pipeline; load active MMD</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>inject active MMD</h4><p><span class="inline">injectMmdIntoMessages</span> manages injected fragments with a marker so the task map enters context first without duplicate appends.</p><div class="mono">MMD_MESSAGE_MARKER -&gt; task map</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>token snapshot</h4><p><span class="inline">context-token-tracker.ts</span> and <span class="inline">l3-token-counter.ts</span> count actual message tokens instead of guessing by character length.</p><div class="mono">messages -&gt; precise token count</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>mild replacement</h4><p><span class="inline">compressByScoreCascade</span> first replaces low-score, older, already offloaded regions while keeping summaries recoverable through JSONL and refs.</p><div class="mono">old tool detail -&gt; compact offload marker</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>aggressive / emergency</h4><p>If pressure remains high, old offloaded regions are deleted and history MMD is injected; overflow or continued high pressure enters <span class="inline">emergencyCompress</span>.</p><div class="mono">history MMD -&gt; emergency trim</div></div></div>
</div>

<h2>Three compression tiers</h2>
<div class="cols">
  <div class="col"><h4>Mild: score cascade</h4><p><b>Trigger</b>: token usage approaches the threshold but is still manageable.<br><b>Action</b>: replace old tool results by score, age, and offload state.<br><b>Evidence recovery</b>: keep tool_call_id, node_id, result_ref, and summary.</p></div>
  <div class="col"><h4>Aggressive: delete old offloaded regions</h4><p><b>Trigger</b>: mild replacement still misses the budget.<br><b>Action</b>: <span class="inline">aggressiveCompressUntilBelowThreshold</span> removes older offloaded message blocks and injects history MMD.<br><b>Evidence recovery</b>: go from history MMD nodes to JSONL, then to refs.</p></div>
  <div class="col"><h4>Emergency: overflow fallback</h4><p><b>Trigger</b>: token pressure remains high, or <span class="inline">isTokenOverflowError</span> detects an entry overflow.<br><b>Action</b>: <span class="inline">emergencyCompress</span> keeps only the safe skeleton, latest user message, valid tool pairs, and necessary task map.<br><b>Evidence recovery</b>: rely on active/history MMD plus JSONL status markers.</p></div>
</div>

<h2>Why the fast path marks JSONL status</h2>
<table class="t">
  <tr><th>Status</th><th>Meaning</th><th>Next-turn behavior</th></tr>
  <tr><td class="mono">offloaded: true</td><td><span class="inline">markOffloadStatus</span> records that this tool result was safely replaced by a symbolic summary.</td><td>before-prompt-build can deterministically replay the replacement without re-guessing compression.</td></tr>
  <tr><td class="mono">offloaded: "deleted"</td><td>Aggressive compression moved an old live region out of context, while the JSONL row and refs evidence remain traceable.</td><td>The L3 injection layer skips the raw region and recovers meaning through history MMD and node indexes.</td></tr>
  <tr><td class="mono">node_id + result_ref</td><td>Connects the MMD node, JSONL summary, and original refs text.</td><td>Even deleted content can be drilled down from the task map.</td></tr>
</table>

<h2>Timeline of one LLM call</h2>
<div class="timeline">
  <div class="tl"><div class="tm">before_prompt_build</div><div class="td">Skip internal memory-pipeline sessions; inject active MMD; replay deterministic replacements for <span class="inline">offloaded: true</span>; write the token guard snapshot.</div></div>
  <div class="tl"><div class="tm">llm_input_l3</div><div class="td"><span class="inline">createLlmInputL3Handler</span> uses precise counts to choose <span class="inline">compressByScoreCascade</span>, <span class="inline">aggressiveCompressUntilBelowThreshold</span>, or <span class="inline">emergencyCompress</span>.</div></div>
  <div class="tl"><div class="tm">model call</div><div class="td">If the entry throws token overflow, <span class="inline">isTokenOverflowError</span> turns it into an emergency-compression signal instead of blindly retrying the same oversized input.</div></div>
  <div class="tl"><div class="tm">after_tool_call</div><div class="td">After a tool returns, active MMD is refreshed, patch effectiveness is reported, and the next turn knows which replacements actually saved tokens.</div></div>
</div>

<h2>Safety rules: compression must not corrupt conversation structure</h2>
<div class="card warn">
  <div class="tag">⚠️ Safety rules</div>
  <ul>
    <li>Preserve the latest user message: it defines the current intent and must not be deleted to save tokens.</li>
    <li>Keep tool-use / tool-result pairs valid: never delete only one side of a pair, or the host protocol can break.</li>
    <li>Protect current-task nodes: <span class="inline">l3-helpers.ts</span> current-task node protection prevents deleting evidence targeted by the active MMD.</li>
    <li>Write JSONL status clearly: use <span class="inline">markOffloadStatus</span> with <span class="inline">true</span> and <span class="inline">"deleted"</span> so the fast path is repeatable.</li>
    <li>Skip internal memory-pipeline sessions: the memory pipeline's own compression/generation should not recursively trigger Context Offload.</li>
  </ul>
</div>

<h2>Core pseudocode</h2>
<pre class="code">on_before_prompt_build(messages, session):
    if is_internal_memory_pipeline_session(session):
        return messages
    active_mmd = read_active_mmd(session)
    messages = injectMmdIntoMessages(messages, active_mmd)
    messages = reapply_confirmed_offloads(messages, statuses=[true, "deleted"])
    snapshot = build_precise_token_snapshot(messages)
    return messages, snapshot

on_llm_input_l3(messages, snapshot):
    if snapshot.total_tokens &lt; mild_threshold:
        return messages

    messages = compressByScoreCascade(messages, protect_latest_user=True)
    if count_tokens(messages) &lt; target_threshold:
        markOffloadStatus(replaced_entries, true)
        return messages

    messages = aggressiveCompressUntilBelowThreshold(messages, inject_history_mmd=True)
    markOffloadStatus(deleted_entries, "deleted")
    if count_tokens(messages) &lt; hard_threshold:
        return messages

    return emergencyCompress(messages,
        preserve_latest_user=True,
        preserve_valid_tool_pairs=True,
        preserve_current_task_nodes=True)

on_model_error(error, messages):
    if isTokenOverflowError(error):
        return emergencyCompress(messages)
    raise error</pre>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 7 lesson 31: this lesson closes the final Context Offload runtime loop before model calls.</li>
    <li><span class="inline">src/offload/hooks/before-prompt-build.ts</span>: implements fast-path re-apply, token guard, and MMD injection before prompt build.</li>
    <li><span class="inline">src/offload/hooks/llm-input-l3.ts</span>: <span class="inline">createLlmInputL3Handler</span> orchestrates <span class="inline">compressByScoreCascade</span>, <span class="inline">aggressiveCompressUntilBelowThreshold</span>, <span class="inline">emergencyCompress</span>, and <span class="inline">isTokenOverflowError</span>.</li>
    <li><span class="inline">src/offload/mmd-injector.ts</span>: active MMD insertion, marker recognition, and duplicate-injection handling.</li>
    <li><span class="inline">src/offload/l3-helpers.ts</span>: replacement helpers, lookup maps, and current-task node protection.</li>
    <li><span class="inline">src/offload/hooks/after-tool-call.ts</span>: refreshes active MMD inside the tool loop and reports patch effectiveness.</li>
    <li><span class="inline">src/offload/context-token-tracker.ts</span> and <span class="inline">src/offload/l3-token-counter.ts</span>: record token snapshots and count L3 input.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The correct L3 order is: inject active MMD and replay confirmed offloads first, then use precise token counts to choose the compression tier.
  Mild replacement, aggressive deletion, and emergency compression must all preserve the latest user message, valid tool pairs, and current-task nodes.
  <span class="inline">markOffloadStatus</span> values <span class="inline">true</span> / <span class="inline">"deleted"</span> make deterministic fast-path replay possible on the next turn.
</div>
""",
}
