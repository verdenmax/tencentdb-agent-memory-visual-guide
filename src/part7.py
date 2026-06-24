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
