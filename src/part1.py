"""Part 1 content for the TencentDB Agent Memory visual guide."""

# Code examples intentionally use <pre class="code"> instead of nested
# <pre><code> so they share the guide's existing shell CSS styling.

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

<p>
“上层保结构、下层保证据”是读这个项目时最重要的抓手。L3 Persona 和 L2 Scene 把大量历史压成可读、可注入的结构，
让模型先看到稳定结论；L1 Atom 和 L0 Conversation 则保留更细的事实与原始对话，方便在结论可疑时逐层下钻核对。
所以记忆不是只追求更短摘要，而是在“回答时够精炼”和“追责时有证据”之间建立一条可返回的路径。
</p>

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
<pre class="code">on_turn_committed(messages):
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
    return inject(memories, persona)</pre>

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
<pre class="code">on_turn_committed(messages):
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
    return inject(memories, persona)</pre>

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

<p>
按时间线看，只有 recall/search 属于模型回答前的准备阶段：它把已经沉淀的 Persona、Scene 导航和相关 L1 记忆放到本轮上下文里，
帮助模型带着“该记得的东西”开始回答。模型回答之后，capture 才能拿到完整的新消息并写入 L0；随后 pipeline 再异步或按触发条件抽取 L1、
合并 L2、更新 L3。这样设计避免了把尚未完成的回答提前写成事实，也让每一轮都遵循“先召回旧证据，再沉淀新证据”的节奏。
如果排查召回问题，也应按这个顺序定位：先看回答前是否查到了合适记忆，再看回答后是否成功捕获并进入管线。
前后阶段分清后，日志、文件和代码入口才不会混在一起。
</p>

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
<pre class="code">class TdaiCore:
    async handleBeforeRecall(user_text, session_key):
        return perform_auto_recall(user_text, session_key)

    async handleTurnCommitted(messages, session_key):
        captured = perform_auto_capture(messages, session_key)
        scheduler.notify_conversation(session_key, captured)

    async searchMemory(query):
        return execute_memory_search(query)</pre>

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
<pre class="code">class TdaiCore:
    async handleBeforeRecall(user_text, session_key):
        return perform_auto_recall(user_text, session_key)

    async handleTurnCommitted(messages, session_key):
        captured = perform_auto_capture(messages, session_key)
        scheduler.notify_conversation(session_key, captured)

    async searchMemory(query):
        return execute_memory_search(query)</pre>

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

LESSON_03 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
TencentDB Agent Memory 不是一条“万能记忆流水线”，而是两条协作的记忆主线：长期 L0-L3 负责把可复用经验沉淀到未来会话，
短期 Offload 负责把当前长任务的工具结果压缩成可浏览、可下钻的上下文地图。两条线都保留证据，但优化目标完全不同。
</p>

<div class="card analogy">
  <div class="tag">🔌 生活类比</div>
  长期记忆像团队知识库：把反复有用的规则、偏好、场景和画像整理好，下一次项目还能用。短期 Offload 像这次会议的临时白板：
  工具输出、报错、文件片段都先贴到白板背后的附件里，桌面只保留结构化索引，讨论结束后不必把每个临时细节都变成长期偏好。
</div>

<h2>两条主线的分工</h2>
<div class="cols">
  <div class="col"><h4>长期记忆 L0-L3</h4><p>从原始对话开始，逐层抽取 Atom、聚合 Scene、生成 Persona，再在下一轮或下一次会话前召回。它回答“哪些经验值得以后继续使用”。</p></div>
  <div class="col"><h4>短期 Offload</h4><p>从工具结果开始，写入 refs markdown 和 offload JSONL，先由 Offload-L1 产出紧凑摘要行，按需用 Offload-L1.5 判断并精炼近期任务上下文，再由 Offload-L2 生成 Mermaid MMD 画布并分配 node_id，最后通过 Offload-L3 注入压缩符号上下文。它回答“当前任务如何少占 prompt”。</p></div>
</div>

<h2>长期主线：从证据到可召回经验</h2>
<div class="flow">
  <div class="node"><div class="nt">L0 Raw</div><div class="nd">原始对话</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1 Atom</div><div class="nd">事实/偏好</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L2 Scene</div><div class="nd">场景聚合</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L3 Persona</div><div class="nd">稳定画像</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Recall</div><div class="nd">下一轮注入</div></div>
</div>

<p>
这条线的入口和出口分别可以从源码锚点验证：<span class="inline">src/core/hooks/auto-capture.ts</span> 的
<span class="inline">performAutoCapture</span> 捕获已提交对话；<span class="inline">src/core/hooks/auto-recall.ts</span> 的
<span class="inline">performAutoRecall</span> 在需要回答前组合可召回内容。它适合存放“用户长期偏好”“项目固定约束”“反复出现的业务场景”等以后仍有价值的信息。
</p>

<h2>短期主线：从工具日志到可下钻画布</h2>
<div class="flow">
  <div class="node"><div class="nt">Tool Logs</div><div class="nd">工具结果</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Refs</div><div class="nd">markdown 证据</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L1</div><div class="nd">JSONL 摘要行</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L1.5</div><div class="nd">近期上下文判断/精炼</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L2 MMD</div><div class="nd">任务画布/node_id</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L3</div><div class="nd">压缩符号注入</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">node_id</div><div class="nd">按需下钻</div></div>
</div>

<div class="card detail">
  <div class="tag">⚠️ 名称边界</div>
  长期 L2/L3 仍然指 Scene 场景块和 Persona 用户画像；Offload-L2/L3 是短期上下文卸载的内部阶段，分别指 Mermaid MMD 任务画布和压缩符号注入。
</div>

<p>
Offload 的注册和上下文引擎看 <span class="inline">src/offload/index.ts</span> 中的
<span class="inline">registerOffload</span> 与 <span class="inline">OffloadContextEngine</span>。证据落盘由
<span class="inline">src/offload/storage.ts</span> 的 <span class="inline">writeRefMd</span>、
<span class="inline">appendOffloadEntries</span>、<span class="inline">createStorageContext</span> 负责；是否该提升到
Offload-L2 Mermaid 结构，可看 <span class="inline">src/offload/pipelines/l2-mermaid.ts</span> 的
<span class="inline">checkL2Trigger</span>。这条线不是为了长期学习用户，而是为了让当前任务在工具输出爆炸时仍能保住结构。
</p>

<h2>共同原则：上层保结构，下层保证据</h2>
<div class="cols">
  <div class="col"><h4>上层结构</h4><p>L3 Persona、L2 Scene、Offload-L2 MMD 和 Offload-L3 注入都应该短、稳定、可导航，让模型先看到“地图”。</p></div>
  <div class="col"><h4>下层证据</h4><p>L0 对话、refs markdown、offload JSONL 保存原文、来源和 node_id，让 Agent 只在需要确认细节时下钻。</p></div>
</div>

<h2>为什么不能合并成一条线</h2>
<p>
如果把 Offload 都塞进长期记忆，临时工具日志会污染未来会话；如果把长期偏好只放在 Offload，任务结束后又无法稳定复用。
长期 L0-L3 优化的是跨会话复用：更关心事实是否长期有效、是否能帮助下一次决策。短期 Offload 优化的是当前上下文压力：
更关心如何把大量工具输出变成一张轻量任务图，并保留足够证据让模型按 node_id 回看原文。两条主线协作，而不是互相替代。
</p>

<h2>伪代码：先判断生命周期，再判断注入粒度</h2>
<pre class="code">if information_should_survive_future_sessions:
    send_to_long_term_memory()
else_if information_is_current_task_trace:
    send_to_context_offload()

when_agent_needs_context():
    inject_high_level_structure()
    drill_down_to_evidence_only_when_needed()</pre>

<div class="card detail">
  <div class="tag">🔬 源码对应</div>
  长期主线：<span class="inline">src/core/hooks/auto-capture.ts</span> 的 <span class="inline">performAutoCapture</span>，
  以及 <span class="inline">src/core/hooks/auto-recall.ts</span> 的 <span class="inline">performAutoRecall</span>。
  短期主线：<span class="inline">src/offload/index.ts</span> 的 <span class="inline">registerOffload</span>、
  <span class="inline">OffloadContextEngine</span>；<span class="inline">src/offload/storage.ts</span> 的
  <span class="inline">writeRefMd</span>、<span class="inline">appendOffloadEntries</span>、<span class="inline">createStorageContext</span>；
  <span class="inline">src/offload/pipelines/l2-mermaid.ts</span> 的 <span class="inline">checkL2Trigger</span>。
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  先问信息生命周期：未来会话还需要吗？需要就走长期 L0-L3；只是当前任务轨迹，就走 Offload。再问注入粒度：
  prompt 里优先放上层结构，原文证据留在下层，通过搜索、引用或 node_id 按需取回。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
TencentDB Agent Memory is not one universal memory pipeline. It has two cooperating spines: long-term L0-L3 preserves reusable
experience for future sessions, while short-term Offload compresses the current task's tool traces into a navigable, drill-down context map.
</p>

<div class="card analogy">
  <div class="tag">🔌 Analogy</div>
  Long-term memory is like a team knowledge base: stable rules, preferences, scenes, and persona survive into the next project.
  Offload is like the whiteboard for this meeting: raw outputs are attached behind the board, while the room sees only the structure needed now.
</div>

<h2>Two spines, two jobs</h2>
<div class="cols">
  <div class="col"><h4>Long-term L0-L3</h4><p>Start with raw conversation, extract atoms, aggregate scenes, synthesize persona, then recall before a later turn or future session. It asks: what experience should be reused later?</p></div>
  <div class="col"><h4>Short-term Offload</h4><p>Start with tool results, write refs markdown and offload JSONL, let Offload-L1 produce compact summary rows, optionally let Offload-L1.5 judge and refine recent task context, let Offload-L2 build the Mermaid MMD canvas and assign node_id values, then let Offload-L3 inject compressed symbolic context. It asks: how do we reduce current prompt pressure?</p></div>
</div>

<h2>Long-term spine: evidence to reusable memory</h2>
<div class="flow">
  <div class="node"><div class="nt">L0 Raw</div><div class="nd">conversation</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L1 Atom</div><div class="nd">facts/preferences</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L2 Scene</div><div class="nd">context blocks</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L3 Persona</div><div class="nd">stable profile</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">Recall</div><div class="nd">next turn</div></div>
</div>

<p>
The source anchors are the capture and recall hooks: <span class="inline">performAutoCapture</span> in
<span class="inline">src/core/hooks/auto-capture.ts</span> captures committed conversation, while
<span class="inline">performAutoRecall</span> in <span class="inline">src/core/hooks/auto-recall.ts</span> assembles memory before an answer.
This spine is for durable preferences, project constraints, repeated scenes, and other information that should remain useful later.
</p>

<h2>Short-term spine: tool logs to drill-down canvas</h2>
<div class="flow">
  <div class="node"><div class="nt">Tool Logs</div><div class="nd">results</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Refs</div><div class="nd">markdown evidence</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L1</div><div class="nd">JSONL summary rows</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L1.5</div><div class="nd">recent context judgment/refinement</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L2 MMD</div><div class="nd">task canvas/node_id</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Offload-L3</div><div class="nd">compressed symbolic injection</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">node_id</div><div class="nd">drill-down</div></div>
</div>

<div class="card detail">
  <div class="tag">⚠️ Naming boundary</div>
  Long-term L2/L3 still mean Scene blocks and Persona profiles; Offload-L2/L3 are separate internal context-offload stages for the Mermaid MMD task canvas and compressed symbolic injection.
</div>

<p>
Offload is registered in <span class="inline">src/offload/index.ts</span> through <span class="inline">registerOffload</span>, and the
runtime context is coordinated by <span class="inline">OffloadContextEngine</span>. Storage lives in
<span class="inline">src/offload/storage.ts</span>: <span class="inline">writeRefMd</span>,
<span class="inline">appendOffloadEntries</span>, and <span class="inline">createStorageContext</span> preserve evidence and indexes.
The Offload-L2 promotion decision is anchored by <span class="inline">checkL2Trigger</span> in
<span class="inline">src/offload/pipelines/l2-mermaid.ts</span>. This spine is not learning the user; it is keeping a long current task manageable.
</p>

<h2>Shared principle: structure above, evidence below</h2>
<div class="cols">
  <div class="col"><h4>Upper layers keep structure</h4><p>L3 persona, L2 scenes, Offload-L2 MMD, and Offload-L3 injection should be compact, stable, and navigable. The model sees the map first.</p></div>
  <div class="col"><h4>Lower layers keep evidence</h4><p>L0 conversations, refs markdown, and offload JSONL preserve raw text, sources, and node_id links so the agent can drill down only when needed.</p></div>
</div>

<h2>Why not merge them?</h2>
<p>
If every Offload trace becomes long-term memory, temporary tool noise pollutes future sessions. If durable preferences live only in Offload,
they disappear when the current task ends. Long-term L0-L3 optimizes cross-session reuse: is the fact stable enough to help later decisions?
Offload optimizes current-context pressure: how can huge tool outputs become a compact task graph while still preserving evidence for node_id drill-down?
They cooperate, but they should not replace each other.
</p>

<h2>Pseudocode: choose by lifetime, inject by level</h2>
<pre class="code">if information_should_survive_future_sessions:
    send_to_long_term_memory()
else_if information_is_current_task_trace:
    send_to_context_offload()

when_agent_needs_context():
    inject_high_level_structure()
    drill_down_to_evidence_only_when_needed()</pre>

<div class="card detail">
  <div class="tag">🔬 Source map</div>
  Long-term: <span class="inline">performAutoCapture</span> in <span class="inline">src/core/hooks/auto-capture.ts</span>,
  and <span class="inline">performAutoRecall</span> in <span class="inline">src/core/hooks/auto-recall.ts</span>.
  Short-term: <span class="inline">registerOffload</span> and <span class="inline">OffloadContextEngine</span> in
  <span class="inline">src/offload/index.ts</span>; <span class="inline">writeRefMd</span>,
  <span class="inline">appendOffloadEntries</span>, and <span class="inline">createStorageContext</span> in
  <span class="inline">src/offload/storage.ts</span>; <span class="inline">checkL2Trigger</span> in
  <span class="inline">src/offload/pipelines/l2-mermaid.ts</span>.
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  First ask about lifetime: future sessions go to long-term L0-L3; current-task traces go to Offload. Then ask about injection level:
  put high-level structure in the prompt, and keep raw evidence below for search, references, or node_id drill-down.
</div>
""",
}
