"""Part 1 content for the TencentDB Agent Memory visual guide."""

LESSON_01 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
TencentDB Agent Memory 解决的是一个长程 Agent 的老问题：Agent 做得越久，对话、工具日志、项目规则和用户偏好越多，
上下文窗口却始终有限。这个项目不是把所有历史都粗暴塞回 prompt，而是把信息分层保存、分层召回，让 Agent 既能记住长期经验，
又能在长任务里把临时日志压缩成可追溯的结构。
</p>

<div class="card analogy">
  <div class="tag">🔌 生活类比</div>
  把 Agent 的上下文想成一张办公桌。直接把所有文件堆上桌，很快就看不见重点；TencentDB Agent Memory 像一个分层档案柜：
  桌上只放当前任务地图，抽屉里放摘要，档案室里保留原文，需要证据时再按编号下钻。
</div>

<h2>两个记忆问题</h2>
<div class="cols">
  <div class="col"><h4>长期记忆</h4><p>跨会话记住偏好、事实、场景和用户画像，下一次对话前按需召回。</p></div>
  <div class="col"><h4>短期压缩</h4><p>单个长任务中工具日志太大时，把原文卸载到文件，只把 Mermaid 任务画布留在上下文。</p></div>
</div>

<h2>项目的两条主线</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">L0</span><span class="name">Conversation</span></div><div class="ld">原始对话 JSONL 与可检索索引，负责保留证据。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">L1</span><span class="name">Atom</span></div><div class="ld">LLM 从对话中抽取结构化事实、偏好、约束和事件。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">L2</span><span class="name">Scene</span></div><div class="ld">把原子记忆聚合成场景块，形成可读的情境导航。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">L3</span><span class="name">Persona</span></div><div class="ld">从场景中生成用户画像和长期偏好，稳定注入系统上下文。</div></div>
</div>

<h2>一次对话如何变成可召回记忆</h2>
<div class="flow">
  <div class="node"><div class="nt">User Turn</div><div class="nd">用户输入</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Hook</div><div class="nd">宿主事件</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">统一入口</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L0/L1/L2/L3</div><div class="nd">分层沉淀</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Recall</div><div class="nd">下一轮注入</div></div>
</div>

<h2>伪代码：不要堆历史，要分层处理</h2>
<pre><code>on_turn_committed(messages):
    l0 = record_raw_conversation(messages)
    if pipeline.should_extract_l1():
        atoms = extract_memories(l0)
        store.upsert(atoms)
    if pipeline.should_update_scenes():
        scenes = merge_atoms_into_scene_blocks()
    if pipeline.should_update_persona():
        persona = synthesize_user_profile(scenes)

before_next_turn(user_text):
    memories = search_l1(user_text)
    persona = read_l3_persona()
    return inject(memories, persona)</code></pre>

<div class="card detail">
  <div class="tag">🔬 源码对应</div>
  长期记忆主线从 <span class="inline">index.ts</span> 进入，核心入口在 <span class="inline">src/core/tdai-core.ts</span>。
  L0 捕获看 <span class="inline">src/core/hooks/auto-capture.ts</span> 与 <span class="inline">src/core/conversation/l0-recorder.ts</span>；
  下一轮召回看 <span class="inline">src/core/hooks/auto-recall.ts</span>。
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  TencentDB Agent Memory 的核心不是“记住更多文本”，而是“用层次保留结构，用底层保留证据”。长期记忆解决跨会话经验沉淀，
  短期 offload 解决单次长任务日志爆炸；两者都强调可下钻、可恢复。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
TencentDB Agent Memory solves a recurring long-horizon agent problem: the longer an agent works, the more conversation history,
tool logs, project rules, and user preferences accumulate, while the context window remains limited. The project does not dump
all history back into the prompt; it stores and recalls information by layers.
</p>

<div class="card analogy">
  <div class="tag">🔌 Analogy</div>
  Think of the context window as a desk. If every document is piled on the desk, the important part disappears. TencentDB Agent Memory
  behaves like a layered filing cabinet: the desk keeps the current task map, drawers keep summaries, and the archive keeps evidence.
</div>

<h2>Two memory problems</h2>
<div class="cols">
  <div class="col"><h4>Long-term memory</h4><p>Remember preferences, facts, scenes, and persona across conversations, then recall them before the next turn.</p></div>
  <div class="col"><h4>Short-term compression</h4><p>When a long task produces huge tool logs, offload raw text to files and keep a Mermaid task canvas in context.</p></div>
</div>

<h2>The two spines</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">L0</span><span class="name">Conversation</span></div><div class="ld">Raw JSONL conversations and searchable evidence.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">L1</span><span class="name">Atom</span></div><div class="ld">Structured facts, preferences, constraints, and events extracted by an LLM.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">L2</span><span class="name">Scene</span></div><div class="ld">Readable scene blocks that aggregate atom memories into context.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">L3</span><span class="name">Persona</span></div><div class="ld">A stable user profile generated from scenes and injected into system context.</div></div>
</div>

<h2>How one turn becomes recallable memory</h2>
<div class="flow">
  <div class="node"><div class="nt">User Turn</div><div class="nd">input</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Hook</div><div class="nd">host event</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">facade</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L0/L1/L2/L3</div><div class="nd">layered memory</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Recall</div><div class="nd">next turn</div></div>
</div>

<h2>Pseudocode: layer history instead of piling it up</h2>
<pre><code>on_turn_committed(messages):
    l0 = record_raw_conversation(messages)
    if pipeline.should_extract_l1():
        atoms = extract_memories(l0)
        store.upsert(atoms)
    if pipeline.should_update_scenes():
        scenes = merge_atoms_into_scene_blocks()
    if pipeline.should_update_persona():
        persona = synthesize_user_profile(scenes)

before_next_turn(user_text):
    memories = search_l1(user_text)
    persona = read_l3_persona()
    return inject(memories, persona)</code></pre>

<div class="card detail">
  <div class="tag">🔬 Source map</div>
  The long-term memory path enters through <span class="inline">index.ts</span>, then through <span class="inline">src/core/tdai-core.ts</span>.
  L0 capture lives in <span class="inline">src/core/hooks/auto-capture.ts</span> and <span class="inline">src/core/conversation/l0-recorder.ts</span>;
  next-turn recall lives in <span class="inline">src/core/hooks/auto-recall.ts</span>.
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The project is not about remembering more text. It preserves structure in upper layers and evidence in lower layers. Long-term memory
  handles cross-session experience, while context offload handles one long task's log explosion.
</div>
""",
}

LESSON_02 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
这一课把镜头拉近：一轮真实对话从宿主框架进入插件后，如何被捕获、抽取、聚合，并在下一轮对话前重新注入。
先看数据流，后面课程再逐段拆源码。
</p>

<div class="card analogy">
  <div class="tag">🔌 生活类比</div>
  像快递分拣：入口先登记包裹，流水线按规则抽取信息，仓库按主题归档，下一次需要时按收件地址和关键词把相关包裹找出来。
</div>

<h2>完整路径</h2>
<div class="vflow">
  <div class="step"><b>1. before prompt</b><span>读取 Persona、Scene Navigation，并按用户输入搜索 L1。</span></div>
  <div class="step"><b>2. model turn</b><span>宿主框架运行主 Agent。</span></div>
  <div class="step"><b>3. turn committed</b><span>对话结束后，插件捕获新增 user/assistant 消息。</span></div>
  <div class="step"><b>4. L0 write</b><span>写入 conversations JSONL，并更新 checkpoint。</span></div>
  <div class="step"><b>5. pipeline</b><span>调度 L1 抽取、L2 场景、L3 Persona。</span></div>
</div>

<h2>核心模块关系</h2>
<div class="flow">
  <div class="node"><div class="nt">index.ts</div><div class="nd">OpenClaw 插件壳</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">宿主无关门面</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Auto Capture</div><div class="nd">提交后记录</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Pipeline</div><div class="nd">L1/L2/L3 调度</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Auto Recall</div><div class="nd">下一轮注入</div></div>
</div>

<h2>宿主差异被 Adapter 收起来</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw</h4><p><span class="inline">index.ts</span> 注册 hooks、tools 和 CLI，运行时通过 <span class="inline">OpenClawHostAdapter</span> 调用核心。</p></div>
  <div class="col"><h4>Hermes / Gateway</h4><p>Gateway 通过 HTTP 接收 capture/search/recall 请求，再使用 standalone adapter 进入同一个 <span class="inline">TdaiCore</span>。</p></div>
</div>

<h2>伪代码：TdaiCore 是统一入口（概念示意）</h2>
<pre><code>class TdaiCore:
    async handleBeforeRecall(user_text, session_key):
        return perform_auto_recall(user_text, session_key)

    async handleTurnCommitted(messages, session_key):
        captured = perform_auto_capture(messages, session_key)
        scheduler.notify_conversation(session_key, captured)

    async searchMemory(query):
        return execute_memory_search(query)</code></pre>

<div class="card detail">
  <div class="tag">🔬 源码对应</div>
  入口壳：<span class="inline">index.ts</span>。核心门面：<span class="inline">src/core/tdai-core.ts</span> 的 <span class="inline">TdaiCore</span>。
  宿主适配：<span class="inline">src/adapters/openclaw/host-adapter.ts</span> 与 <span class="inline">src/adapters/standalone/host-adapter.ts</span>。
  调度工厂：<span class="inline">src/utils/pipeline-factory.ts</span>。
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  读源码时先抓住一条线：宿主事件进入 <span class="inline">index.ts</span>，具体能力交给 <span class="inline">TdaiCore</span>，
  核心再调用 capture、pipeline、recall、tools。Adapter 负责隔离 OpenClaw 和 Hermes 的差异。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
This lesson zooms in on one real turn: how it enters the plugin, gets captured, extracted, aggregated, and injected before the next turn.
Start with the data flow; later lessons will open each source file.
</p>

<div class="card analogy">
  <div class="tag">🔌 Analogy</div>
  Think of package sorting: the entrance registers the package, the line extracts routing facts, the warehouse groups by topic, and the next request retrieves the relevant packages.
</div>

<h2>End-to-end path</h2>
<div class="vflow">
  <div class="step"><b>1. before prompt</b><span>Read Persona and Scene Navigation, then search L1 using the user input.</span></div>
  <div class="step"><b>2. model turn</b><span>The host runs the main agent.</span></div>
  <div class="step"><b>3. turn committed</b><span>After the turn, the plugin captures new user/assistant messages.</span></div>
  <div class="step"><b>4. L0 write</b><span>Write conversation JSONL and advance checkpoints.</span></div>
  <div class="step"><b>5. pipeline</b><span>Schedule L1 extraction, L2 scenes, and L3 persona generation.</span></div>
</div>

<h2>Core module relationships</h2>
<div class="flow">
  <div class="node"><div class="nt">index.ts</div><div class="nd">OpenClaw shell</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">host-neutral facade</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Auto Capture</div><div class="nd">after commit</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Pipeline</div><div class="nd">L1/L2/L3 scheduling</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Auto Recall</div><div class="nd">next turn</div></div>
</div>

<h2>Host differences are hidden behind adapters</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw</h4><p><span class="inline">index.ts</span> registers hooks, tools, and CLI commands, then calls the core through <span class="inline">OpenClawHostAdapter</span>.</p></div>
  <div class="col"><h4>Hermes / Gateway</h4><p>The Gateway receives capture/search/recall over HTTP, then enters the same <span class="inline">TdaiCore</span> through the standalone adapter.</p></div>
</div>

<h2>Pseudocode: TdaiCore is the unified entry point (conceptual)</h2>
<pre><code>class TdaiCore:
    async handleBeforeRecall(user_text, session_key):
        return perform_auto_recall(user_text, session_key)

    async handleTurnCommitted(messages, session_key):
        captured = perform_auto_capture(messages, session_key)
        scheduler.notify_conversation(session_key, captured)

    async searchMemory(query):
        return execute_memory_search(query)</code></pre>

<div class="card detail">
  <div class="tag">🔬 Source map</div>
  Shell entry: <span class="inline">index.ts</span>. Core facade: <span class="inline">TdaiCore</span> in <span class="inline">src/core/tdai-core.ts</span>.
  Host adapters: <span class="inline">src/adapters/openclaw/host-adapter.ts</span> and <span class="inline">src/adapters/standalone/host-adapter.ts</span>.
  Pipeline wiring: <span class="inline">src/utils/pipeline-factory.ts</span>.
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Read the source through one line: host events enter <span class="inline">index.ts</span>, capabilities go through <span class="inline">TdaiCore</span>,
  and the core calls capture, pipeline, recall, and tools. Adapters isolate OpenClaw and Hermes differences.
</div>
""",
}
