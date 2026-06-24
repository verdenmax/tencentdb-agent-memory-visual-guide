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
  <div class="node"><div class="nt">offload JSONL</div><div class="nd"><span class="inline">OffloadEntry</span> 保存 summary、result_ref、tool_call_id、node_id。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Mermaid MMD</div><div class="nd">L2 把 JSONL 行组织成任务节点和状态画布。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L3 injected context</div><div class="nd">只注入当前任务需要的节点符号，而不是整段工具日志。</div></div>
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
  <div class="layer l-core"><div class="lh"><span class="badge">guide</span><span class="name">generated lesson page</span></div><div class="ld">本页把实现路径解释成学习模型：证据文件、JSONL 符号、MMD 画布、L3 注入。</div></div>
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
    <li><span class="inline">src/offload/types.ts</span>：<span class="inline">OffloadEntry</span> 定义 summary、result_ref、tool_call_id、node_id；<span class="inline">PLUGIN_DEFAULTS</span> 定义 L1/L2/L3 阈值和压缩比例。</li>
    <li><span class="inline">src/offload/context-token-tracker.ts</span>：<span class="inline">ContextSnapshot</span> 与 <span class="inline">buildTiktokenContextSnapshot</span> 记录 stage、totalTokens、messageCount 等 token 快照。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Context Offload 是当前任务的短期符号记忆：把臃肿工具日志变成 refs 证据、JSONL 摘要、Mermaid 节点和少量 L3 注入。
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
  <div class="node"><div class="nt">offload JSONL</div><div class="nd"><span class="inline">OffloadEntry</span> stores summary, result_ref, tool_call_id, and node_id.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Mermaid MMD</div><div class="nd">L2 organizes JSONL rows into task nodes and status canvas.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L3 injected context</div><div class="nd">Only active task symbols are injected, not the whole tool log.</div></div>
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
  <div class="layer l-core"><div class="lh"><span class="badge">guide</span><span class="name">generated lesson page</span></div><div class="ld">This page turns the implementation path into a learning model: evidence files, JSONL symbols, MMD canvas, and L3 injection.</div></div>
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
    <li><span class="inline">src/offload/types.ts</span>: <span class="inline">OffloadEntry</span> defines summary, result_ref, tool_call_id, and node_id; <span class="inline">PLUGIN_DEFAULTS</span> defines L1/L2/L3 thresholds and compression ratios.</li>
    <li><span class="inline">src/offload/context-token-tracker.ts</span>: <span class="inline">ContextSnapshot</span> and <span class="inline">buildTiktokenContextSnapshot</span> capture stage, totalTokens, messageCount, and related token snapshots.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Context Offload is short-term symbolic memory for the current task: bulky tool logs become refs evidence, JSONL summaries, Mermaid nodes, and small L3 injections.
  L0-L3 long-term memory serves future-session facts, scenes, and profiles; Offload serves current long-task navigation, drill-down, and token budget.
</div>
""",
}
