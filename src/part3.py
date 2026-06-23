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
  <div class="layer l-app"><div class="lt">Host</div><div class="ld">OpenClaw hooks/tools 或 Gateway/Hermes HTTP 调用，负责宿主生命周期与请求形态。</div></div>
  <div class="layer l-part"><div class="lt">Adapters</div><div class="ld">把日志、路径、LLM runner、运行上下文翻译成 core 可用的统一接口。</div></div>
  <div class="layer l-main"><div class="lt">TdaiCore</div><div class="ld">统一处理 recall、capture、memory search、conversation search 与 scheduler。</div></div>
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
  <div class="layer l-app"><div class="lt">Host</div><div class="ld">OpenClaw hooks/tools or Gateway/Hermes HTTP calls own host lifecycle and request shape.</div></div>
  <div class="layer l-part"><div class="lt">Adapters</div><div class="ld">Translate logging, paths, LLM runners, and runtime context into one interface the core can use.</div></div>
  <div class="layer l-main"><div class="lt">TdaiCore</div><div class="ld">Handles recall, capture, memory search, conversation search, and the scheduler uniformly.</div></div>
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
