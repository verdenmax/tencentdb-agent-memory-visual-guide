"""Part 3 content: hooks, adapters, and TdaiCore integration."""

LESSON_08 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
本课开始进入第三部分：从 OpenClaw 宿主入口读到核心门面。<span class="inline">index.ts</span> 很重要，但它不是记忆算法本体；
它更像插件壳，负责识别注册模式、解析配置、创建 adapter 与 <span class="inline">TdaiCore</span>，再把 tools、hooks 和可选 offload 接到 OpenClaw。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  <span class="inline">index.ts</span> 像家电的插头和控制面板：它知道要插进 OpenClaw 哪个插座、按钮如何命名、开机时读什么配置。
  真正制冷或加热的压缩机不在面板里；记忆系统里对应的核心能力在 <span class="inline">TdaiCore</span> 与 core 模块中。
</div>

<h2>register(api) 先分清两种模式</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>CLI metadata 模式</h4><p>当 <span class="inline">api.registrationMode</span> 是 <span class="inline">cli-metadata</span>，入口只注册命令行展示所需的插件信息，然后立即返回。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Full / discovery 运行模式</h4><p>真实运行时继续读取 <span class="inline">api.pluginConfig</span>，准备时间、reporter、数据目录、adapter、core、tools 和 hooks。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>按配置接入 Offload</h4><p>只有当配置中的 offload 开启时，才调用 <span class="inline">registerOffload</span> 把短期上下文压缩能力接进同一个宿主。</p></div></div>
</div>

<p>
这个分支解释了为什么阅读 <span class="inline">index.ts</span> 时不要把所有代码都当成“记忆算法”：
有一部分只是给 OpenClaw CLI 发现插件、显示工具说明或暴露元数据；另一部分才会进入完整运行路径。
同一个 <span class="inline">register(api)</span> 也可能在不同 OpenClaw 生命周期上下文或注册模式中被调用，
因此 CLI 注册和配置解析都应保持可重复调用时安全。
</p>

<h2>从 OpenClaw API 到核心门面</h2>
<div class="flow">
  <div class="node"><div class="nt">OpenClaw API</div><div class="nd">pluginConfig、hooks、tools、registrationMode</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">index.ts</div><div class="nd">register(api) 插件壳</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">OpenClawHostAdapter</div><div class="nd">隔离宿主调用与日志/路径</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">TdaiCore</div><div class="nd">recall / capture / search / pipeline</div></div>
</div>

<p>
完整模式中，入口先用 <span class="inline">src/config.ts</span> 的 <span class="inline">parseConfig</span> 合并默认值与用户配置；
然后初始化时间、reporter 和数据目录，构造 <span class="inline">src/adapters/openclaw/host-adapter.ts</span> 里的 <span class="inline">OpenClawHostAdapter</span>；
再把 adapter 和配置传给 <span class="inline">src/core/tdai-core.ts</span> 的 <span class="inline">TdaiCore</span>。
接下来，tools 与 hooks 只是把 OpenClaw 生命周期事件转交给 core。
</p>

<h2>插件壳与核心的职责边界</h2>
<div class="cols">
  <div class="col"><h4>index.ts 插件壳</h4><p>理解 OpenClaw 的 <span class="inline">register(api)</span>、CLI metadata、<span class="inline">api.pluginConfig</span>、hook/tool 注册、数据目录初始化，以及是否调用 <span class="inline">src/offload/index.ts</span> 的 <span class="inline">registerOffload</span>。</p></div>
  <div class="col"><h4>TdaiCore 与 core 模块</h4><p>保持宿主无关，承接 recall、capture、search、pipeline、L0-L3 分层与指标。它不需要知道自己来自 OpenClaw、Hermes，还是未来另一个宿主。</p></div>
</div>

<h2>入口伪代码</h2>
<pre class="code">register(api):
    if api.registrationMode == "cli-metadata":
        api.registerCli(lambda program: registerMemoryTdaiCli(program))
        return

    cfg = parseConfig(api.pluginConfig)
    adapter = OpenClawHostAdapter(api, cfg)
    core = TdaiCore(adapter, cfg)
    register_tools_and_hooks(core)
    if cfg.offload.enabled:
        registerOffload(api, cfg.offload)
    api.registerCli(lambda program: registerMemoryTdaiCli(program))</pre>

<h2>为什么需要 pending 缓存</h2>
<p>
OpenClaw 的 before/after hooks 分别发生在模型回答前后。为了干净捕获“原始用户提示”和统计召回指标，
<span class="inline">index.ts</span> 会用 <span class="inline">pendingOriginalPrompts</span>、<span class="inline">pendingRecallCache</span> 这类缓存，
把 before hook 中看到的原始 prompt 与 recall 结果暂存起来，等 after hook 收到最终回答时再合并成一次完整 capture 或 metrics 记录。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">index.ts</span>：<span class="inline">register(api)</span>、<span class="inline">pendingOriginalPrompts</span>、<span class="inline">pendingRecallCache</span></li>
    <li><span class="inline">src/config.ts</span>：<span class="inline">parseConfig</span></li>
    <li><span class="inline">src/adapters/openclaw/host-adapter.ts</span>：<span class="inline">OpenClawHostAdapter</span></li>
    <li><span class="inline">src/core/tdai-core.ts</span>：<span class="inline">TdaiCore</span></li>
    <li><span class="inline">src/offload/index.ts</span>：<span class="inline">registerOffload</span></li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  把宿主相关逻辑留在 <span class="inline">index.ts</span>，可以让 <span class="inline">TdaiCore</span> 保持宿主中立：
  OpenClaw 入口负责接线，核心负责记忆能力。这也是后续理解 hooks、adapters 与 Gateway/Hermes 复用核心的基础。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Part 3 starts by following the OpenClaw host entry into the core facade. <span class="inline">index.ts</span> matters, but it is not the memory algorithm itself.
It is the plugin shell that detects registration mode, parses config, creates the adapter and <span class="inline">TdaiCore</span>, then wires tools, hooks, and optional offload into OpenClaw.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  <span class="inline">index.ts</span> is like an appliance plug and control panel: it knows which OpenClaw socket to use, how buttons are named, and which config to read at startup.
  The compressor that actually cools or heats is elsewhere; in this memory system, the core capability lives in <span class="inline">TdaiCore</span> and core modules.
</div>

<h2>register(api) separates two modes first</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>CLI metadata mode</h4><p>When <span class="inline">api.registrationMode</span> is <span class="inline">cli-metadata</span>, the entry registers plugin information needed by the CLI and returns immediately.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Full / discovery runtime mode</h4><p>At runtime it continues with <span class="inline">api.pluginConfig</span>, time, reporter, data dirs, adapter, core, tools, and hooks.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Attach Offload by config</h4><p>Only when offload is enabled does it call <span class="inline">registerOffload</span> to attach short-term context compression to the same host.</p></div></div>
</div>

<p>
This branch explains why you should not read every line of <span class="inline">index.ts</span> as “the memory algorithm”.
Some code only helps the OpenClaw CLI discover the plugin, show tool descriptions, or expose metadata; the rest enters the full runtime path.
The same <span class="inline">register(api)</span> may run in different OpenClaw lifecycle contexts or registration modes,
so CLI registration and config parsing should stay safe across repeated calls.
</p>

<h2>From OpenClaw API to the core facade</h2>
<div class="flow">
  <div class="node"><div class="nt">OpenClaw API</div><div class="nd">pluginConfig, hooks, tools, registrationMode</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">index.ts</div><div class="nd">register(api) plugin shell</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">OpenClawHostAdapter</div><div class="nd">isolates host calls, logging, paths</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">TdaiCore</div><div class="nd">recall / capture / search / pipeline</div></div>
</div>

<p>
In full mode, the entry first uses <span class="inline">parseConfig</span> from <span class="inline">src/config.ts</span> to merge defaults and user config.
It then initializes time, reporter, and data dirs, constructs <span class="inline">OpenClawHostAdapter</span> from <span class="inline">src/adapters/openclaw/host-adapter.ts</span>,
and passes the adapter plus config to <span class="inline">TdaiCore</span> in <span class="inline">src/core/tdai-core.ts</span>.
Tools and hooks then forward OpenClaw lifecycle events to the core.
</p>

<h2>Shell responsibilities vs core responsibilities</h2>
<div class="cols">
  <div class="col"><h4>index.ts plugin shell</h4><p>Understands OpenClaw <span class="inline">register(api)</span>, CLI metadata, <span class="inline">api.pluginConfig</span>, hook/tool registration, data-dir initialization, and whether to call <span class="inline">registerOffload</span> from <span class="inline">src/offload/index.ts</span>.</p></div>
  <div class="col"><h4>TdaiCore and core modules</h4><p>Stay host-neutral and own recall, capture, search, pipeline, L0-L3 layering, and metrics. They do not need to know whether the caller is OpenClaw, Hermes, or a future host.</p></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">register(api):
    if api.registrationMode == "cli-metadata":
        api.registerCli(lambda program: registerMemoryTdaiCli(program))
        return

    cfg = parseConfig(api.pluginConfig)
    adapter = OpenClawHostAdapter(api, cfg)
    core = TdaiCore(adapter, cfg)
    register_tools_and_hooks(core)
    if cfg.offload.enabled:
        registerOffload(api, cfg.offload)
    api.registerCli(lambda program: registerMemoryTdaiCli(program))</pre>

<h2>Why pending caches exist</h2>
<p>
OpenClaw before/after hooks run on different sides of the model response. To capture the original user prompt cleanly and report recall metrics,
<span class="inline">index.ts</span> uses caches such as <span class="inline">pendingOriginalPrompts</span> and <span class="inline">pendingRecallCache</span>.
The before hook stores the raw prompt and recall result; the after hook combines them with the final answer into one capture or metrics record.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">index.ts</span>: <span class="inline">register(api)</span>, <span class="inline">pendingOriginalPrompts</span>, <span class="inline">pendingRecallCache</span></li>
    <li><span class="inline">src/config.ts</span>: <span class="inline">parseConfig</span></li>
    <li><span class="inline">src/adapters/openclaw/host-adapter.ts</span>: <span class="inline">OpenClawHostAdapter</span></li>
    <li><span class="inline">src/core/tdai-core.ts</span>: <span class="inline">TdaiCore</span></li>
    <li><span class="inline">src/offload/index.ts</span>: <span class="inline">registerOffload</span></li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Keeping host-specific logic in <span class="inline">index.ts</span> lets <span class="inline">TdaiCore</span> remain host-neutral:
  the OpenClaw entry wires the system, and the core owns memory behavior. This is the basis for understanding hooks, adapters, and Gateway/Hermes core reuse.
</div>
""",
}

LESSON_09 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
<span class="inline">TdaiCore</span> 是 OpenClaw 插件路径与 Gateway/Hermes 路径共用的宿主无关核心门面。
宿主差异由 adapter 吸收；core 对外稳定暴露自动召回、对话提交捕获、记忆搜索、对话搜索与 pipeline scheduler 生命周期。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  如果 OpenClaw 与 Gateway/Hermes 是不同入口大厅，adapter 就是前台翻译，<span class="inline">TdaiCore</span> 是同一个资料室柜台。
  不管访客从哪个大厅来，最终都向同一个柜台办理“查资料、登记新资料、维护后台整理任务”。
</div>

<h2>三层边界：宿主、Adapter、Core</h2>
<div class="layers">
  <div class="layer l-app"><div class="lh"><span class="badge">Host</span><span class="name">OpenClaw / Gateway</span></div><div class="ld">OpenClaw hooks/tools 或 Gateway/Hermes HTTP 调用，负责宿主生命周期与请求形态。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">Adapter</span><span class="name">Host adapters</span></div><div class="ld">把日志、路径、LLM runner、运行上下文翻译成 core 可用的统一接口。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">Core</span><span class="name">TdaiCore</span></div><div class="ld">统一处理 recall、capture、memory search、conversation search 与 scheduler。</div></div>
</div>

<p>
这个边界让核心能力可以被复用：OpenClaw 的 before/after hook 不需要复制 Gateway 的记忆逻辑；Gateway/Hermes 也不需要理解
OpenClaw 的插件注册细节。两条路径都把请求变成 <span class="inline">TdaiCore</span> 能理解的方法调用。
</p>

<h2>生命周期先于能力调用</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>initialize()</h4><p>创建数据目录，调用 <span class="inline">initStores</span> 准备向量/embedding 存储，并用 <span class="inline">createPipelineManager</span> 构造 scheduler。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>handleBeforeRecall</h4><p>在模型回答前转交给 <span class="inline">performAutoRecall</span>，返回要注入上下文的召回片段。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>handleTurnCommitted</h4><p>对话提交后先确保 scheduler 已启动，再调用 <span class="inline">performAutoCapture</span> 写入 L0 并触发后续 pipeline。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>scheduler / destroy()</h4><p>后台 pipeline 持续整理 L1-L3；关闭时 <span class="inline">destroy()</span> 先排空后台任务，再关闭 store。</p></div></div>
</div>

<h2>两条宿主路径复用同一个门面</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw path</h4><p><span class="inline">index.ts</span> 注册 hooks 和 tools。before hook 调 <span class="inline">handleBeforeRecall</span>；after/agent_end 提交完整 turn 给 <span class="inline">handleTurnCommitted</span>；工具调用转到 search 方法。</p></div>
  <div class="col"><h4>Gateway / Hermes path</h4><p>Gateway HTTP handler 接收 Hermes provider 的请求，同样调用 <span class="inline">handleBeforeRecall</span>、<span class="inline">handleTurnCommitted</span> 和搜索方法，因此不复制核心算法。</p></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">core.initialize():
    initDataDirectories()
    storeReady = initStores()
    scheduler = createPipelineManager()

before_prompt(user_text):
    return performAutoRecall(user_text)

turn_committed(messages):
    await ensureSchedulerStarted()
    return performAutoCapture(messages)</pre>

<h2>为什么 schedulerStartPromise 是并发闸门</h2>
<p>
Gateway 场景中，多个 HTTP 请求可能同时进入 <span class="inline">handleTurnCommitted</span>。
如果只用布尔值标记“scheduler 已启动”，第一个请求可能在异步读取 checkpoint 尚未完成时就把标记改成 true；后续请求会越过启动流程，提前更新 scheduler 状态。
当真正的 <span class="inline">scheduler.start(restoredStates)</span> 稍后执行时，恢复出的旧状态可能覆盖这些并发更新。
</p>
<p>
<span class="inline">schedulerStartPromise</span> 把“正在启动”本身保存为同一个 promise。所有并发请求都 await 同一段启动过程；启动成功后，已 resolve 的 promise 又成为廉价哨兵，后续调用不会重复 start。
</p>

<h2>为什么要登记后台任务</h2>
<p>
<span class="inline">performAutoCapture</span> 可能为 L0 embedding 发起延迟后台写入。它们是 fire-and-forget，但并不代表可以在关闭时忽略。
<span class="inline">TdaiCore</span> 用 background task registry 记录这些 in-flight promise；<span class="inline">destroy()</span> 会在关闭 vector store 与 embedding service 前等待它们完成或超时，避免迟到写入打到已关闭数据库连接。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/tdai-core.ts</span>：<span class="inline">TdaiCore</span>、<span class="inline">initialize</span>、<span class="inline">destroy</span>、<span class="inline">handleBeforeRecall</span>、<span class="inline">handleTurnCommitted</span></li>
    <li><span class="inline">src/utils/pipeline-factory.ts</span>：<span class="inline">initStores</span>、<span class="inline">createPipelineManager</span></li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：<span class="inline">performAutoRecall</span></li>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>：<span class="inline">performAutoCapture</span></li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  <span class="inline">TdaiCore</span> 的价值不是“又包一层”，而是把 OpenClaw 与 Gateway/Hermes 的宿主差异挡在 adapter 外侧，
  让 recall、capture、search 与 pipeline lifecycle 只有一套实现、一套资源关闭顺序和一套并发保护。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
<span class="inline">TdaiCore</span> is the host-neutral core facade shared by the OpenClaw plugin path and the Gateway/Hermes path.
Adapters absorb host differences; the core exposes stable methods for auto recall, turn capture, memory search, conversation search, and the pipeline scheduler lifecycle.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  If OpenClaw and Gateway/Hermes are different entrance halls, the adapter is the front-desk translator and <span class="inline">TdaiCore</span> is the same records counter.
  No matter which hall a visitor uses, they reach one counter for “look up records, register new records, and keep background filing running.”
</div>

<h2>Three boundaries: host, adapter, core</h2>
<div class="layers">
  <div class="layer l-app"><div class="lh"><span class="badge">Host</span><span class="name">OpenClaw / Gateway</span></div><div class="ld">OpenClaw hooks/tools or Gateway/Hermes HTTP calls own host lifecycle and request shape.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">Adapter</span><span class="name">Host adapters</span></div><div class="ld">Translate logging, paths, LLM runners, and runtime context into one interface the core can use.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">Core</span><span class="name">TdaiCore</span></div><div class="ld">Handles recall, capture, memory search, conversation search, and the scheduler uniformly.</div></div>
</div>

<p>
This boundary is what makes reuse possible: OpenClaw before/after hooks do not copy Gateway memory logic, and Gateway/Hermes do not need to understand OpenClaw plugin registration details.
Both paths turn host events into method calls that <span class="inline">TdaiCore</span> understands.
</p>

<h2>Lifecycle comes before capability calls</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>initialize()</h4><p>Create data directories, call <span class="inline">initStores</span> for vector/embedding storage, and build the scheduler with <span class="inline">createPipelineManager</span>.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>handleBeforeRecall</h4><p>Before the model answers, delegate to <span class="inline">performAutoRecall</span> and return snippets that can be injected into context.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>handleTurnCommitted</h4><p>After a turn is committed, ensure the scheduler has started, then call <span class="inline">performAutoCapture</span> to write L0 and trigger later pipeline work.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>scheduler / destroy()</h4><p>The background pipeline keeps organizing L1-L3; shutdown drains background tasks before closing stores.</p></div></div>
</div>

<h2>Two host paths reuse the same facade</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw path</h4><p><span class="inline">index.ts</span> registers hooks and tools. The before hook calls <span class="inline">handleBeforeRecall</span>; after/agent_end submits the full turn to <span class="inline">handleTurnCommitted</span>; tools forward to search methods.</p></div>
  <div class="col"><h4>Gateway / Hermes path</h4><p>A Gateway HTTP handler receives requests from the Hermes provider and calls the same <span class="inline">handleBeforeRecall</span>, <span class="inline">handleTurnCommitted</span>, and search methods, so core algorithms are not duplicated.</p></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">core.initialize():
    initDataDirectories()
    storeReady = initStores()
    scheduler = createPipelineManager()

before_prompt(user_text):
    return performAutoRecall(user_text)

turn_committed(messages):
    await ensureSchedulerStarted()
    return performAutoCapture(messages)</pre>

<h2>Why schedulerStartPromise is a concurrency gate</h2>
<p>
In the Gateway path, several HTTP requests can enter <span class="inline">handleTurnCommitted</span> at the same time.
With only a boolean “scheduler started” flag, the first request could flip the flag before the async checkpoint read finishes; later requests would skip startup and update scheduler state too early.
When <span class="inline">scheduler.start(restoredStates)</span> finally runs, restored old state could overwrite those concurrent updates.
</p>
<p>
<span class="inline">schedulerStartPromise</span> stores the in-flight startup itself. Every concurrent request awaits the same promise; after startup succeeds, the resolved promise becomes a cheap sentinel so later calls do not start the scheduler again.
</p>

<h2>Why the background task registry exists</h2>
<p>
<span class="inline">performAutoCapture</span> can launch deferred background writes for L0 embeddings. They are fire-and-forget, but shutdown still has to respect them.
<span class="inline">TdaiCore</span> records those in-flight promises in a background task registry; <span class="inline">destroy()</span> waits for them, or a bounded timeout, before closing the vector store and embedding service. That prevents late writes from hitting a closed database connection.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/tdai-core.ts</span>: <span class="inline">TdaiCore</span>, <span class="inline">initialize</span>, <span class="inline">destroy</span>, <span class="inline">handleBeforeRecall</span>, <span class="inline">handleTurnCommitted</span></li>
    <li><span class="inline">src/utils/pipeline-factory.ts</span>: <span class="inline">initStores</span>, <span class="inline">createPipelineManager</span></li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: <span class="inline">performAutoRecall</span></li>
    <li><span class="inline">src/core/hooks/auto-capture.ts</span>: <span class="inline">performAutoCapture</span></li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The value of <span class="inline">TdaiCore</span> is not “one more wrapper.” It keeps OpenClaw and Gateway/Hermes host differences outside the adapter boundary,
  so recall, capture, search, and pipeline lifecycle share one implementation, one resource shutdown order, and one concurrency guard.
</div>
""",
}

LESSON_10 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
<span class="inline">HostAdapter</span> 是宿主与 core 之间的缝合线：宿主上下文、日志、数据目录和 LLM 执行方式都从这里进入，
<span class="inline">TdaiCore</span> 只依赖统一接口，不直接依赖 OpenClaw、Gateway 或 Hermes 的实现细节。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  同一个电器可以在不同国家使用，是因为有电源适配器。Core 像电器本体；OpenClaw 与 Gateway/Hermes 像不同插座；
  <span class="inline">HostAdapter</span> 与 <span class="inline">LLMRunner</span> 把电压、插头形状和供电方式转换成 core 能稳定使用的接口。
</div>

<h2>Adapter 是宿主与 core 的边界</h2>
<div class="layers">
  <div class="layer l-app"><div class="lh"><span class="badge">Host</span><span class="name">OpenClaw / Gateway / Hermes</span></div><div class="ld">OpenClaw plugin API、Gateway HTTP handler、Hermes provider：负责生命周期、请求来源和宿主能力。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">Adapter</span><span class="name">HostAdapter</span></div><div class="ld">统一暴露 logger、runtime context、dataDir 与 LLMRunnerFactory。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">Core</span><span class="name">TdaiCore</span></div><div class="ld">TdaiCore、recall、capture、pipeline、persona prompts：只看接口，不看宿主。</div></div>
</div>

<p>
在 <span class="inline">src/core/types.ts</span> 中，<span class="inline">HostAdapter</span> 回答三个问题：
“怎么记录日志？”、“当前用户/会话/数据目录是谁？”、“怎么创建 LLM runner？”。
这条边界让 core 可以把 <span class="inline">RuntimeContext</span> 当成唯一的身份与路径来源，把 LLM 调用当成可替换能力。
新增宿主时，优先补齐这三个接口，而不是把宿主 SDK 调用散落到 core 里。
</p>

<h2>两种 adapter 路径对比</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw adapter</h4><p><span class="inline">src/adapters/openclaw/host-adapter.ts</span> 持有 <span class="inline">OpenClawPluginApi</span>、插件数据目录和 OpenClaw 配置。它从 <span class="inline">api.logger</span> 取日志，从 hook session 构造上下文，并把 <span class="inline">api.runtime.agent</span> 交给 <span class="inline">OpenClawLLMRunnerFactory</span>。</p></div>
  <div class="col"><h4>Standalone / Gateway adapter</h4><p><span class="inline">src/adapters/standalone/host-adapter.ts</span> 不依赖 OpenClaw。它直接接收 <span class="inline">dataDir</span>、logger、默认用户和 OpenAI-compatible LLM 配置；Gateway 每个请求再覆盖 user/session。</p></div>
</div>

<h2>LLMRunnerFactory 把模型调用藏在接口后</h2>
<div class="flow">
  <div class="node"><div class="nt">Host</div><div class="nd">OpenClaw 或 Gateway/Hermes</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">HostAdapter</div><div class="nd">logger / context / dataDir</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">LLMRunnerFactory</div><div class="nd">createRunner(model, tools)</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Core prompts</div><div class="nd">L1 extraction / L2 scene / L3 persona</div></div>
</div>

<p>
<span class="inline">LLMRunner</span> 的边界很关键：L1 抽取、L1 去重、L2 场景和 L3 画像提示词只调用
<span class="inline">runner.run({prompt, systemPrompt, taskId})</span>。OpenClaw 路径背后可以继续用
<span class="inline">CleanContextRunner</span> 与内嵌 agent runtime；Standalone 路径则通过 OpenAI-compatible HTTP 和可选文件工具执行。
Prompt 本身因此不需要知道宿主具体怎么发起模型调用。Context Offload 也遵循“提示词不碰宿主 SDK”的目标，
但它目前走并行的 <span class="inline">BackendClient</span> / <span class="inline">LocalLlmClient</span> 抽象，而不是这个 core runner factory。
</p>

<h2>伪代码</h2>
<pre class="code">interface HostAdapter:
    getLogger()
    getRuntimeContext()
    getLLMRunnerFactory()

core = TdaiCore({
    hostAdapter,
    config
})</pre>

<h2>为什么这对测试和 Hermes 很重要</h2>
<p>
测试时，可以给 core 一个小型 fake adapter：固定 logger、临时 dataDir、可预测的 fake runner，就能验证 recall/capture/pipeline 逻辑，
不用启动 OpenClaw 或真实 Gateway。Hermes 支持也因此更清晰：Hermes/Gateway 只需要实现 standalone adapter 与 runner 配置，
无需复制 OpenClaw hooks 内的记忆算法。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/types.ts</span>：<span class="inline">HostAdapter</span>、<span class="inline">LLMRunner</span>、<span class="inline">LLMRunnerFactory</span></li>
    <li><span class="inline">src/adapters/openclaw/host-adapter.ts</span>：<span class="inline">OpenClawHostAdapter</span> 包装 OpenClaw API、logger、plugin data dir</li>
    <li><span class="inline">src/adapters/openclaw/llm-runner.ts</span>：<span class="inline">OpenClawLLMRunnerFactory</span> 包装 CleanContextRunner / runtime agent</li>
    <li><span class="inline">src/adapters/standalone/host-adapter.ts</span>：<span class="inline">StandaloneHostAdapter</span> 使用直接配置与请求上下文</li>
    <li><span class="inline">src/adapters/standalone/llm-runner.ts</span>：<span class="inline">StandaloneLLMRunnerFactory</span> 使用 OpenAI-compatible 配置和可选工具沙箱</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  <span class="inline">HostAdapter</span> 隔离宿主运行时差异；<span class="inline">LLMRunner</span> 隔离模型执行差异。
  这让 core、prompt 与测试都围绕稳定接口组织，也让 Gateway/Hermes 成为 OpenClaw 之外的另一条干净接入路径。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
<span class="inline">HostAdapter</span> is the seam between the host and the core: host context, logging, data directories, and LLM execution enter through it.
<span class="inline">TdaiCore</span> depends on the unified interface instead of OpenClaw, Gateway, or Hermes implementation details.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  The same appliance can work in different countries because a power adapter normalizes the socket. The core is the appliance; OpenClaw and Gateway/Hermes are different sockets;
  <span class="inline">HostAdapter</span> and <span class="inline">LLMRunner</span> translate voltage, plug shape, and power delivery into stable interfaces the core can use.
</div>

<h2>The adapter is the host/core boundary</h2>
<div class="layers">
  <div class="layer l-app"><div class="lh"><span class="badge">Host</span><span class="name">OpenClaw / Gateway / Hermes</span></div><div class="ld">OpenClaw plugin API, Gateway HTTP handlers, Hermes provider: lifecycle, request source, and host capabilities.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">Adapter</span><span class="name">HostAdapter</span></div><div class="ld">Exposes logger, runtime context, dataDir, and LLMRunnerFactory in one shape.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">Core</span><span class="name">TdaiCore</span></div><div class="ld">TdaiCore, recall, capture, pipeline, persona prompts: interface-only, host-free.</div></div>
</div>

<p>
In <span class="inline">src/core/types.ts</span>, <span class="inline">HostAdapter</span> answers three questions:
“Where do I log?”, “Who is the current user/session/data directory?”, and “How do I create an LLM runner?”.
That boundary lets the core treat <span class="inline">RuntimeContext</span> as the single source for identity and paths, and LLM execution as a replaceable capability.
</p>

<h2>Two adapter paths</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw adapter</h4><p><span class="inline">src/adapters/openclaw/host-adapter.ts</span> holds <span class="inline">OpenClawPluginApi</span>, the plugin data directory, and OpenClaw config. It uses <span class="inline">api.logger</span>, builds context from hook sessions, and passes <span class="inline">api.runtime.agent</span> into <span class="inline">OpenClawLLMRunnerFactory</span>.</p></div>
  <div class="col"><h4>Standalone / Gateway adapter</h4><p><span class="inline">src/adapters/standalone/host-adapter.ts</span> does not depend on OpenClaw. It receives <span class="inline">dataDir</span>, logger, default user, and OpenAI-compatible LLM config directly; each Gateway request can override user/session.</p></div>
</div>

<h2>LLMRunnerFactory hides model execution behind an interface</h2>
<div class="flow">
  <div class="node"><div class="nt">Host</div><div class="nd">OpenClaw or Gateway/Hermes</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">HostAdapter</div><div class="nd">logger / context / dataDir</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">LLMRunnerFactory</div><div class="nd">createRunner(model, tools)</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Core prompts</div><div class="nd">L1 extraction / L2 scene / L3 persona</div></div>
</div>

<p>
The <span class="inline">LLMRunner</span> boundary matters: L1 extraction, L1 dedup, L2 scene generation, and L3 persona generation prompts only call
<span class="inline">runner.run({prompt, systemPrompt, taskId})</span>. The OpenClaw path can keep using
<span class="inline">CleanContextRunner</span> and the embedded agent runtime; the standalone path can call OpenAI-compatible HTTP with optional file tools.
The prompt code does not need to know how the host launches the model. Context Offload follows the same goal of keeping prompts away from host SDKs,
but today it uses a parallel <span class="inline">BackendClient</span> / <span class="inline">LocalLlmClient</span> abstraction rather than this core runner factory.
</p>

<h2>Pseudocode</h2>
<pre class="code">interface HostAdapter:
    getLogger()
    getRuntimeContext()
    getLLMRunnerFactory()

core = TdaiCore({
    hostAdapter,
    config
})</pre>

<h2>Why this matters for testing and Hermes</h2>
<p>
Tests can give the core a tiny fake adapter: fixed logger, controlled dataDir, and predictable fake runner. That verifies recall/capture/pipeline behavior without starting OpenClaw or a real Gateway.
Hermes support is also cleaner: Hermes/Gateway only implements the standalone adapter and runner configuration, without copying the memory algorithms from OpenClaw hooks.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/types.ts</span>: <span class="inline">HostAdapter</span>, <span class="inline">LLMRunner</span>, <span class="inline">LLMRunnerFactory</span></li>
    <li><span class="inline">src/adapters/openclaw/host-adapter.ts</span>: <span class="inline">OpenClawHostAdapter</span> wraps OpenClaw API, logger, plugin data dir</li>
    <li><span class="inline">src/adapters/openclaw/llm-runner.ts</span>: <span class="inline">OpenClawLLMRunnerFactory</span> wraps CleanContextRunner / runtime agent</li>
    <li><span class="inline">src/adapters/standalone/host-adapter.ts</span>: <span class="inline">StandaloneHostAdapter</span> uses direct config and request context</li>
    <li><span class="inline">src/adapters/standalone/llm-runner.ts</span>: <span class="inline">StandaloneLLMRunnerFactory</span> uses OpenAI-compatible config and an optional tool sandbox</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  <span class="inline">HostAdapter</span> isolates host runtime differences; <span class="inline">LLMRunner</span> isolates model execution differences.
  That keeps the core, prompts, and tests organized around stable interfaces, and gives Gateway/Hermes a clean path alongside OpenClaw.
</div>
""",
}

LESSON_11 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
本课把前几课的“入口壳、adapter、core”串到启动顺序上：OpenClaw 给插件一份原始 <span class="inline">api.pluginConfig</span>，
<span class="inline">index.ts</span> 每次注册只解析一次，随后用统一的 <span class="inline">cfg</span> 初始化时间、目录、存储和 <span class="inline">TdaiCore</span>。
</p>

<div class="card analogy">
  <div class="tag">🧩 生活类比</div>
  开店前先看当天排班表：店长只读一次排班表，把默认岗位补齐，再依次开门、清点库房、接好收银系统，最后才开始接待客人。
  运行时初始化也是这样：配置先变成稳定对象，目录和存储先准备好，hooks 才能安全处理真实对话。
</div>

<h2>启动主线：原始配置到 hooks</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>raw plugin config</h4><p><span class="inline">index.ts</span> 从 <span class="inline">api.pluginConfig</span> 取得原始对象，并记录收到的 key 数量。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>parseConfig</h4><p><span class="inline">src/config.ts</span> 把用户配置与默认值合并成 <span class="inline">MemoryTdaiConfig</span>，本次 register 后续都复用它。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>init dirs</h4><p><span class="inline">resolveOpenClawStateDir</span> 选出 OpenClaw state 目录；<span class="inline">initDataDirectories</span> 创建 conversations、records、scene_blocks、.metadata 和 .backup。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>store bundle</h4><p><span class="inline">initStores</span> 调 <span class="inline">createStoreBundle</span>，并写入或比较 manifest，必要时标记 reindex。</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>core / hooks</h4><p>目录和 store 准备后，<span class="inline">TdaiCore</span> 初始化 pipeline manager，OpenClaw hooks/tools 才把请求转给 core。</p></div></div>
</div>

<p>
注意“每次注册解析一次”并不等于全进程只解析一次。OpenClaw 可能因为插件扫描、Gateway 启动、channel bootstrap 或配置 reload 多次调用
<span class="inline">register(api)</span>；每次调用都收到完整配置，所以入口直接解析当前 raw object，避免复用过期配置。
</p>

<h2>零配置与高级配置的差别</h2>
<div class="cols">
  <div class="col"><h4>零配置</h4><p><span class="inline">parseConfig(undefined)</span> 或 <span class="inline">{}</span> 仍会启动：capture、extraction、pipeline、recall 默认启用；SQLite 是默认 store；embedding provider 为 none，因此向量能力禁用但主对话不被阻塞；offload 默认关闭。</p></div>
  <div class="col"><h4>高级配置</h4><p>用户可以按组覆盖 capture、extraction、pipeline、recall、persona、embedding、offload、store、report、llm、bm25、tcvdb 等行为。远程 embedding 字段不完整时，配置保留错误消息并降级为无 embedding。</p></div>
</div>

<h2>配置组分别喂给谁</h2>
<div class="layers">
  <div class="layer l-app"><div class="lh"><span class="badge">Entry</span><span class="name">timezone / report / offload</span></div><div class="ld">入口先用 timezone 初始化时间模块，用 report 控制上报行为，并仅在 offload.enabled 为 true 时注册 Context Offload。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">Core</span><span class="name">capture / extraction / pipeline / recall / persona</span></div><div class="ld">这些组决定是否捕获 L0、如何抽取 L1、scheduler 何时跑、召回数量/超时/策略，以及 L2/L3 画像生成节奏。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">Store</span><span class="name">storeBackend / embedding / tcvdb / bm25</span></div><div class="ld">storeBackend 决定 SQLite 还是 TCVDB；SQLite 再按 embedding 配置决定是否创建远程 embedding service；TCVDB 使用服务端 embedding 与可选 BM25。</div></div>
</div>

<h2>目录、manifest 与 checkpoint 为什么先初始化</h2>
<p>
<span class="inline">initDataDirectories(dataDir)</span> 先把运行时目录建好，后续 L0 JSONL、L1 records、scene blocks、metadata 和备份才有稳定落点。
<span class="inline">initStores</span> 初始化 store 后会维护 manifest：首次写入 store binding，之后比较当前配置是否和已绑定后端不同。
pipeline 工作时再通过 <span class="inline">CheckpointManager</span> 读取和更新游标，确保抽取、场景和画像任务能从已处理位置继续。
</p>

<h2>伪代码</h2>
<pre class="code">raw = api.pluginConfig
cfg = parseConfig(raw)
initTimeModule(cfg.timezone)
initDataDirectories(dataDir)
store = createStoreBundle(cfg)
core = new TdaiCore(adapter, cfg)</pre>

<p>
这段伪代码省略了日志、hook policy、adapter 创建和异步 store cache，但保留了关键顺序：先把 raw config 固化为 cfg，再准备运行目录和 store bundle，
最后创建 core 并注册 hooks。offload 是旁路能力：只有 <span class="inline">cfg.offload.enabled</span> 为真，入口才调用 <span class="inline">registerOffload(api, cfg.offload)</span>。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/config.ts</span>：<span class="inline">parseConfig</span>、配置接口与默认值</li>
    <li><span class="inline">index.ts</span>：读取 <span class="inline">api.pluginConfig</span>、配置日志、初始化时间和目录、条件注册 offload</li>
    <li><span class="inline">src/utils/pipeline-factory.ts</span>：<span class="inline">initDataDirectories</span>、<span class="inline">initStores</span>、<span class="inline">createPipelineManager</span></li>
    <li><span class="inline">src/core/store/factory.ts</span>：<span class="inline">createStoreBundle</span> 按 storeBackend 与 embedding 配置选后端</li>
    <li><span class="inline">src/utils/openclaw-state-dir.ts</span>：OpenClaw state 目录解析与 fallback</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  运行时初始化的核心不是“读很多配置”，而是把配置稳定化、把默认值补齐、把目录与 store 先接好。
  这样零配置能安全启动，高级配置能精确影响各功能组，offload 和 embedding 不完整时也能降级而不阻塞主对话。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
This lesson connects the plugin shell, adapter, and core to startup order: OpenClaw gives the plugin raw <span class="inline">api.pluginConfig</span>;
<span class="inline">index.ts</span> parses it once for that registration, then uses the resulting <span class="inline">cfg</span> to initialize time, directories, stores, and <span class="inline">TdaiCore</span>.
</p>

<div class="card analogy">
  <div class="tag">🧩 Analogy</div>
  Before a shop opens, the manager reads the roster once, fills default roles, unlocks the door, checks inventory, wires the register, and only then serves customers.
  Runtime initialization is the same: config becomes a stable object first, directories and stores are prepared next, and hooks handle real conversations afterward.
</div>

<h2>Startup path: raw config to hooks</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>raw plugin config</h4><p><span class="inline">index.ts</span> reads <span class="inline">api.pluginConfig</span> and logs how many keys arrived.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>parseConfig</h4><p><span class="inline">src/config.ts</span> merges user config with defaults into <span class="inline">MemoryTdaiConfig</span>; the rest of this register call reuses it.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>init dirs</h4><p><span class="inline">resolveOpenClawStateDir</span> chooses the OpenClaw state directory; <span class="inline">initDataDirectories</span> creates conversations, records, scene_blocks, .metadata, and .backup.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>store bundle</h4><p><span class="inline">initStores</span> calls <span class="inline">createStoreBundle</span>, then writes or compares the manifest and marks reindex when needed.</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>core / hooks</h4><p>After dirs and stores are ready, <span class="inline">TdaiCore</span> initializes the pipeline manager, and OpenClaw hooks/tools forward requests into core.</p></div></div>
</div>

<p>
“Parse once per registration” does not mean “parse once per process.” OpenClaw may call <span class="inline">register(api)</span> during plugin scan, Gateway startup,
channel bootstrap, or config reload. Each call receives the full config, so the entry parses the current raw object directly instead of reusing stale config.
</p>

<h2>Zero config vs advanced config</h2>
<div class="cols">
  <div class="col"><h4>Zero config</h4><p><span class="inline">parseConfig(undefined)</span> or <span class="inline">{}</span> can still start: capture, extraction, pipeline, and recall default on; SQLite is the default store; embedding provider is none, so vector features are disabled without blocking chat; offload defaults off.</p></div>
  <div class="col"><h4>Advanced config</h4><p>Users can override capture, extraction, pipeline, recall, persona, embedding, offload, store, report, llm, bm25, and tcvdb behavior by group. If remote embedding fields are incomplete, config keeps an error message and degrades to no embedding.</p></div>
</div>

<h2>Where config groups feed behavior</h2>
<div class="layers">
  <div class="layer l-app"><div class="lh"><span class="badge">Entry</span><span class="name">timezone / report / offload</span></div><div class="ld">The entry initializes the time module from timezone, controls reporting with report, and registers Context Offload only when offload.enabled is true.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">Core</span><span class="name">capture / extraction / pipeline / recall / persona</span></div><div class="ld">These groups decide whether to capture L0, how to extract L1, when the scheduler runs, recall count/timeout/strategy, and the L2/L3 persona cadence.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">Store</span><span class="name">storeBackend / embedding / tcvdb / bm25</span></div><div class="ld">storeBackend chooses SQLite or TCVDB; SQLite then checks embedding config before creating a remote embedding service; TCVDB uses server-side embedding and optional BM25.</div></div>
</div>

<h2>Why directories, manifest, and checkpoints come first</h2>
<p>
<span class="inline">initDataDirectories(dataDir)</span> creates stable homes for L0 JSONL, L1 records, scene blocks, metadata, and backups before any work writes files.
After store initialization, <span class="inline">initStores</span> maintains the manifest: first it records the store binding, later it compares the current config against that binding.
During pipeline work, <span class="inline">CheckpointManager</span> reads and updates cursors so extraction, scene, and persona jobs resume from the processed position.
</p>

<h2>Pseudocode</h2>
<pre class="code">raw = api.pluginConfig
cfg = parseConfig(raw)
initTimeModule(cfg.timezone)
initDataDirectories(dataDir)
store = createStoreBundle(cfg)
core = new TdaiCore(adapter, cfg)</pre>

<p>
This pseudocode omits logging, hook policy, adapter construction, and the async store cache, but keeps the important order: freeze raw config into cfg,
prepare runtime directories and the store bundle, then create core and register hooks. Offload is a side capability: only when
<span class="inline">cfg.offload.enabled</span> is true does the entry call <span class="inline">registerOffload(api, cfg.offload)</span>.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/config.ts</span>: <span class="inline">parseConfig</span>, interfaces, and defaults</li>
    <li><span class="inline">index.ts</span>: reads <span class="inline">api.pluginConfig</span>, logs config, initializes time and dirs, conditionally registers offload</li>
    <li><span class="inline">src/utils/pipeline-factory.ts</span>: <span class="inline">initDataDirectories</span>, <span class="inline">initStores</span>, <span class="inline">createPipelineManager</span></li>
    <li><span class="inline">src/core/store/factory.ts</span>: <span class="inline">createStoreBundle</span> selects the backend from storeBackend and embedding config</li>
    <li><span class="inline">src/utils/openclaw-state-dir.ts</span>: OpenClaw state directory resolution and fallback</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Runtime initialization is not “reading lots of config”; it stabilizes config, fills defaults, and wires directories and stores before work starts.
  That lets zero config start safely, lets advanced config steer each functional group, and lets incomplete offload or embedding setup degrade without blocking the main chat.
</div>
""",
}
