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
        register_memory_tdai_cli()
        return

    cfg = parseConfig(api.pluginConfig)
    adapter = OpenClawHostAdapter(api, cfg)
    core = TdaiCore(adapter, cfg)
    register_tools_and_hooks(core)
    if cfg.offload.enabled:
        registerOffload(api, cfg.offload)</pre>

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
        register_memory_tdai_cli()
        return

    cfg = parseConfig(api.pluginConfig)
    adapter = OpenClawHostAdapter(api, cfg)
    core = TdaiCore(adapter, cfg)
    register_tools_and_hooks(core)
    if cfg.offload.enabled:
        registerOffload(api, cfg.offload)</pre>

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
