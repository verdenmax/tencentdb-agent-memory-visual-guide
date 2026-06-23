"""Part 2 content: minimal working loop for TencentDB Agent Memory."""

LESSON_04 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
本课把前面讲过的 L0-L3、Recall 和搜索工具接到一个最小可运行闭环里：安装 OpenClaw 插件、打开最小配置、重启 Gateway，
再用几轮对话先验证 L0 捕获和 L1 搜索/召回。这里的目标不是调优，而是先证明“能跑、能存、能找、能在新回合被想起”；L2/L3 可能稍后出现。
</p>

<div class="card analogy">
  <div class="tag">🔌 生活类比</div>
  零配置像给电脑接上一块默认本地硬盘：你不用先规划云数据库、索引参数或复杂密钥，就能保存和读取文件。
  但如果要做更远距离、更大规模或更强向量召回，就要再接入真实 embedding、TCVDB 等高级配置。
</div>

<h2>一条最小闭环</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>安装或更新插件</h4><p>使用 OpenClaw 插件命令安装 <span class="inline">@tencentdb-agent-memory/memory-tencentdb</span>；升级时显式运行同名 update 命令。</p><p class="mono">openclaw plugins install @tencentdb-agent-memory/memory-tencentdb<br>openclaw plugins update @tencentdb-agent-memory/memory-tencentdb</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>启用最小配置</h4><p>在 <span class="inline">~/.openclaw/openclaw.json</span> 中只打开 <span class="inline">enabled</span>。不要在教程示例里写真实 API Key。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>重启 Gateway</h4><p>插件配置、hooks 和 tools 注册发生在 Gateway 生命周期里，改完配置后要重启才能稳定生效。</p><p class="mono">openclaw gateway restart</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>对话 2-3 轮</h4><p>告诉 Agent 一个可复用偏好或项目约束，再继续追问，让自动捕获先沉淀到 L0 原文与 L1 结构化记忆。</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>验证文件与召回/搜索</h4><p>先确认 <span class="inline">~/.openclaw/state/memory-tdai/</span> 下出现 <span class="inline">conversations/</span>、<span class="inline">records/</span>、<span class="inline">scene_blocks/</span> 或 <span class="inline">vectors.db</span> 等产物，再验证 L0 捕获、L1 搜索/召回；L2 场景块和 L3 persona 可能需要管线延迟或触发条件才会出现。</p></div></div>
</div>

<h2>最小配置就是这么少</h2>
<pre class="code">{
  "memory-tencentdb": {
    "enabled": true
  }
}</pre>

<p>
“零配置”的意思是：只要启用插件，默认会使用本地 SQLite 与 sqlite-vec 路径保存数据，适合课程、个人试用和离线 smoke test。
它不是“所有能力都自动最佳”：如果没有配置可用的 embedding，向量行为可能被默认关闭或退化，搜索更多依赖关键词、结构化层级和已有索引。
所以最小配置先证明闭环，高级配置再处理召回质量、并发、远程存储、模型和凭据管理。
</p>

<h2>日常最小配置 vs 高级调优</h2>
<div class="cols">
  <div class="col"><h4>日常最小配置</h4><p>只写 <span class="inline">enabled: true</span>，用默认本地 SQLite + sqlite-vec 路径。适合先验证 OpenClaw 能注册插件、能写入 L0 原文、能抽取并搜索/召回 L1；L2 场景块和 L3 persona 可能稍后在管线延迟或触发条件满足后出现。</p></div>
  <div class="col"><h4>高级调优</h4><p>再按需要配置 embedding、远程数据库、TCVDB、保留策略、调试日志和性能参数。真实 API Key 只放在本机安全配置或环境变量中，不写进公开教程、截图、提交或示例代码。</p></div>
</div>

<h2>完整伪代码</h2>
<pre class="code">openclaw plugins install @tencentdb-agent-memory/memory-tencentdb
openclaw plugins update @tencentdb-agent-memory/memory-tencentdb

# ~/.openclaw/openclaw.json
{
  "memory-tencentdb": { "enabled": true }
}

openclaw gateway restart</pre>

<h2>Smoke test：三种现象一起看</h2>
<ul>
  <li><strong>先看文件产物：</strong>检查 <span class="inline">~/.openclaw/state/memory-tdai/</span>，预期可见 <span class="inline">conversations/</span>、<span class="inline">records/</span>、<span class="inline">scene_blocks/</span>、<span class="inline">vectors.db</span> 等本地状态产物。</li>
  <li><strong>先验证 L0/L1：</strong>连续 2-3 轮告诉 Agent 一个偏好，例如“这个项目的提交信息要简短”，随后开启新 turn 或新会话追问，先确认 L0 原始对话被捕获、L1 结构化记忆能被搜索或 Recall 使用。</li>
  <li><strong>工具范围要分清：</strong><span class="inline">tdai_memory_search</span> 搜索结构化 L1 记忆，<span class="inline">tdai_conversation_search</span> 搜索原始 L0 对话；L2 场景块和 L3 persona 可能在管线延迟或触发条件满足后才出现。</li>
</ul>

<div class="card warn">
  <div class="tag">🔒 凭据安全</div>
  教程示例永远不要放真实 API Key、云数据库密码或团队私有 endpoint。需要展示字段时，用占位符解释存放位置；需要本地运行时，优先使用用户自己的安全配置或环境变量。
</div>

<div class="card detail">
  <div class="tag">🔬 源码 / 文档地图</div>
  <div class="flow">
    <div class="node"><div class="nt">README_CN.md / SKILL.md</div><div class="nd">快速开始与标准安装流程</div></div>
    <div class="arrow">-&gt;</div>
    <div class="node"><div class="nt">src/config.ts</div><div class="nd">parseConfig、默认值、MemoryTdaiConfig</div></div>
    <div class="arrow">-&gt;</div>
    <div class="node hl"><div class="nt">index.ts</div><div class="nd">register(api) 与 CLI metadata 模式</div></div>
  </div>
  阅读顺序可以从 <span class="inline">README_CN.md</span> 的 OpenClaw quick start 和 <span class="inline">SKILL.md</span> 的标准 setup workflow 开始，
  再看 <span class="inline">src/config.ts</span> 如何由 <span class="inline">parseConfig</span> 合并默认值并形成 <span class="inline">MemoryTdaiConfig</span>，
  最后回到 <span class="inline">index.ts</span> 验证插件如何在 <span class="inline">register(api)</span> 中注册 hooks/tools，以及 CLI metadata 模式如何暴露插件信息。
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  零配置闭环的判断标准不是“配置文件很短”，而是：OpenClaw 重新加载插件、Gateway 注册成功、L0 原始对话被保存、L1 结构化记忆能搜索/召回；L2/L3 可能稍后由管线或触发条件产生。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
This lesson turns L0-L3, Recall, and search into a minimal working OpenClaw loop: install the plugin, enable the smallest config,
restart the Gateway, then first verify L0 capture and L1 search/recall. L2/L3 may appear later.
</p>

<div class="card analogy">
  <div class="tag">🔌 Analogy</div>
  Zero config is like plugging in a default local disk: you can save and read without first designing cloud storage or tuning indexes.
  For stronger vector recall or larger deployments, you still add real embedding and backend configuration later.
</div>

<h2>One minimal loop</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Install or update the plugin</h4><p>Install <span class="inline">@tencentdb-agent-memory/memory-tencentdb</span> with the OpenClaw plugin command; run the matching update command explicitly when upgrading.</p><p class="mono">openclaw plugins install @tencentdb-agent-memory/memory-tencentdb<br>openclaw plugins update @tencentdb-agent-memory/memory-tencentdb</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Enable the smallest config</h4><p>Set only <span class="inline">enabled</span> in <span class="inline">~/.openclaw/openclaw.json</span>. Never put real API keys in guide examples.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Restart the Gateway</h4><p>Plugin config, hooks, and tools are registered during the Gateway lifecycle, so a restart makes the new config take effect reliably.</p><p class="mono">openclaw gateway restart</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Talk for 2-3 turns</h4><p>Give the agent a reusable preference or project constraint, then continue the conversation so capture first lands in L0 raw conversation and L1 structured memory.</p></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>Verify files, recall, and search</h4><p>First check for artifacts under <span class="inline">~/.openclaw/state/memory-tdai/</span>, such as <span class="inline">conversations/</span>, <span class="inline">records/</span>, <span class="inline">scene_blocks/</span>, or <span class="inline">vectors.db</span>; then verify L0 capture and L1 search/recall. L2 scene blocks and L3 persona may appear only after pipeline delay or trigger conditions.</p></div></div>
</div>

<h2>The minimal config</h2>
<pre class="code">{
  "memory-tencentdb": {
    "enabled": true
  }
}</pre>

<p>
Zero config means the plugin can use the default local SQLite plus sqlite-vec path for course work, personal trials, and offline smoke tests.
It does not mean every capability is automatically optimal: when no usable embedding is configured, vector behavior may be disabled or degraded by default.
Start with the loop, then tune embeddings, remote storage, retention, and observability only when the loop is proven.
</p>

<h2>Minimal daily config vs advanced tuning</h2>
<div class="cols">
  <div class="col"><h4>Minimal daily config</h4><p>Use only <span class="inline">enabled: true</span> with the default local SQLite + sqlite-vec path. Verify plugin registration, L0 raw capture, and L1 search/recall first; L2 scene blocks and L3 persona may appear later after pipeline delay or trigger conditions.</p></div>
  <div class="col"><h4>Advanced tuning</h4><p>Add embeddings, remote databases, TCVDB, retention policy, debug logging, and performance settings as needed. Real API keys belong in secure local config or environment variables, not in public examples.</p></div>
</div>

<h2>Pseudocode</h2>
<pre class="code">openclaw plugins install @tencentdb-agent-memory/memory-tencentdb
openclaw plugins update @tencentdb-agent-memory/memory-tencentdb

# ~/.openclaw/openclaw.json
{
  "memory-tencentdb": { "enabled": true }
}

openclaw gateway restart</pre>

<h2>Smoke test: observe three things</h2>
<ul>
  <li><strong>Check file artifacts first:</strong> inspect <span class="inline">~/.openclaw/state/memory-tdai/</span>; expected local state artifacts include <span class="inline">conversations/</span>, <span class="inline">records/</span>, <span class="inline">scene_blocks/</span>, and <span class="inline">vectors.db</span>.</li>
  <li><strong>Verify L0/L1 first:</strong> talk for 2-3 turns, state a durable preference or project rule, then ask about it in a later turn or session. First confirm L0 raw conversation capture and L1 structured memory search/recall.</li>
  <li><strong>Keep tool scope clear:</strong> <span class="inline">tdai_memory_search</span> searches structured L1 memories; <span class="inline">tdai_conversation_search</span> searches raw L0 conversations. L2 scene blocks and L3 persona may appear only after pipeline delay or trigger conditions.</li>
</ul>

<div class="card warn">
  <div class="tag">🔒 Credential safety</div>
  Guide examples must never contain real API keys, cloud database passwords, or private endpoints. Show placeholders only; use secure local config or environment variables for real runs.
</div>

<div class="card detail">
  <div class="tag">🔬 Source map</div>
  <div class="flow">
    <div class="node"><div class="nt">README_CN.md / SKILL.md</div><div class="nd">quick start and standard setup workflow</div></div>
    <div class="arrow">-&gt;</div>
    <div class="node"><div class="nt">src/config.ts</div><div class="nd">parseConfig, defaults, MemoryTdaiConfig</div></div>
    <div class="arrow">-&gt;</div>
    <div class="node hl"><div class="nt">index.ts</div><div class="nd">register(api) and CLI metadata mode</div></div>
  </div>
  Start with the OpenClaw quick start in <span class="inline">README_CN.md</span> and the standard setup workflow in <span class="inline">SKILL.md</span>.
  Then read <span class="inline">src/config.ts</span> for <span class="inline">parseConfig</span>, defaults, and <span class="inline">MemoryTdaiConfig</span>.
  Finally check <span class="inline">index.ts</span> for <span class="inline">register(api)</span>, hook/tool registration, and CLI metadata mode.
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  A zero-config loop is working when OpenClaw reloads the plugin, Gateway registration succeeds, L0 raw conversation is stored, and L1 structured memory can be searched/recalled; L2/L3 may be produced later by pipeline or trigger conditions.
</div>
""",
}

LESSON_05 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Hermes 路径看起来和 OpenClaw 不同：一个是 Python Agent 的 memory provider，一个是 OpenClaw 插件和 Gateway 生命周期。
但它们不是两套记忆引擎。Hermes 只是另一条宿主入口：provider 把 Hermes 的 recall、capture、search 调用转成 HTTP，交给本地 Gateway，Gateway 再通过 StandaloneHostAdapter 调到同一个 <span class="inline">TdaiCore</span>。
</p>

<div class="card analogy">
  <div class="tag">🚪 生活类比</div>
  OpenClaw 和 Hermes 像从两扇不同的门进入同一座图书馆。门口的登记员不同：OpenClaw 用插件 hooks/tools，Hermes 用 <span class="inline">memory_tencentdb</span> provider。
  但进入馆内后，借书、归档、检索和整理书架都由同一个核心服务处理，所以学习重点是“入口不同，核心收敛”。
</div>

<h2>Hermes 路径不是另一套记忆核心</h2>
<div class="flow">
  <div class="node"><div class="nt">Hermes</div><div class="nd">Python Agent lifecycle</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">memory_tencentdb provider</div><div class="nd">provider key 必须是下划线名</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">local Gateway</div><div class="nd">HTTP sidecar on 127.0.0.1:8420</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">StandaloneHostAdapter</div><div class="nd">隔离宿主差异</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">capture / recall / search / pipeline</div></div>
</div>

<p>
在 <span class="inline">hermes-plugin/memory/memory_tencentdb/README.md</span> 中，provider 被描述为“薄 HTTP client + process supervisor”：它负责接入 Hermes 生命周期、启动或探测 Gateway、把 <span class="inline">prefetch</span> 映射到 <span class="inline">POST /recall</span>，把 <span class="inline">sync_turn</span> 映射到 <span class="inline">POST /capture</span>，并提供搜索工具 schema。
真正的捕获、抽取、存储、召回和管线调度仍在 Node.js Gateway 与核心模块中完成。
</p>

<h2>两种安装路线：从零 Docker，还是挂到已有 Hermes</h2>
<div class="cols">
  <div class="col"><h4>Docker 全新部署</h4><p><span class="inline">README_CN.md</span> 的 Hermes 章节把 Docker 路线定位为“从零启动一个带记忆能力的 Hermes”。镜像把 <span class="inline">hermes-agent</span> 和 <span class="inline">memory_tencentdb</span> provider 聚合在一起，Gateway 暴露在 <span class="inline">8420</span> 端口。适合想先用一条容器路线验证完整能力的人。</p></div>
  <div class="col"><h4>已有 Hermes 安装 provider</h4><p>如果机器上已经有 Hermes，就把 provider 链接或复制到 Hermes 的 memory provider 目录，并在 <span class="inline">~/.hermes/config.yaml</span> 中声明 <span class="inline">memory.provider: memory_tencentdb</span>。目录名必须正好是 <span class="inline">memory_tencentdb</span>，因为 Hermes 用目录名作为 provider key。</p></div>
</div>

<p>
无论从 Docker 进入，还是把 provider 挂到已有 Hermes，关键检查点都一样：Hermes 能发现 provider，provider 能连到本地 Gateway，Gateway 的 HTTP 路由能到达 <span class="inline">TdaiCore</span>。
这也是为什么教程不把 Hermes 讲成“另一套内存系统”：它改变的是宿主集成和进程边界，不改变 L0-L3、Recall/Search 与管线核心。
</p>

<h2>最小伪代码</h2>
<pre class="code">memory:
  provider: memory_tencentdb

MEMORY_TENCENTDB_GATEWAY_HOST="127.0.0.1"
MEMORY_TENCENTDB_GATEWAY_PORT="8420"

curl http://127.0.0.1:8420/health</pre>

<p>
示例只展示占位配置与本地地址。真实 LLM 凭据、Gateway API key、云数据库密码或团队 endpoint 都不应该出现在教程、截图或提交里。
如果要启用鉴权，Gateway 端使用 <span class="inline">TDAI_GATEWAY_API_KEY</span> 或配置文件里的 <span class="inline">server.apiKey</span>；Hermes provider 作为客户端可以使用 <span class="inline">MEMORY_TENCENTDB_GATEWAY_API_KEY</span>。两边值要一致，但本课不写真实值。
</p>

<h2>Gateway 对外暴露什么</h2>
<p>
<span class="inline">src/gateway/server.ts</span> 标明 Gateway 是 Hermes sidecar 的 HTTP server：<span class="inline">GET /health</span> 用于健康检查，<span class="inline">POST /recall</span> 做模型回答前的记忆召回，<span class="inline">POST /capture</span> 捕获一轮对话，<span class="inline">POST /search/memories</span> 搜索 L1 结构化记忆，<span class="inline">POST /search/conversations</span> 搜索 L0 原始对话。
<span class="inline">src/gateway/config.ts</span> 还提供 <span class="inline">server.apiKey</span> / <span class="inline">TDAI_GATEWAY_API_KEY</span> 和 <span class="inline">server.corsOrigins</span> / <span class="inline">TDAI_CORS_ORIGINS</span> 这类可选开关；默认重点是本地 sidecar，跨网络开放前才需要认真收紧鉴权与 CORS。
</p>

<h2>验证顺序</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>先看 health check</h4><p>用 <span class="inline">curl http://127.0.0.1:8420/health</span> 确认 Gateway 已启动；文档里允许返回 <span class="inline">ok</span> 或 <span class="inline">degraded</span>。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>再配置 provider</h4><p>确认 Hermes provider 目录名、<span class="inline">plugin.yaml::name</span> 和 <span class="inline">memory.provider</span> 都对齐到 <span class="inline">memory_tencentdb</span>。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>第一轮对话启动或手动启动</h4><p>已有 Hermes 路线可以让 provider 在第一条对话时自动发现并 <span class="inline">Popen()</span> Gateway，也可以先手动运行 Gateway 再启动 Hermes。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>用 recall/search 验证闭环</h4><p>说出一个可复用偏好或项目事实，然后通过后续提问、记忆搜索或原始对话搜索确认它被捕获、可检索、能被召回。</p></div></div>
</div>

<div class="card detail">
  <div class="tag">🔬 源码 / 文档地图</div>
  <ul>
    <li><span class="inline">README_CN.md</span>：Hermes 安装章节、Docker 路线、已有 Hermes 路线、Gateway 安全配置。</li>
    <li><span class="inline">hermes-plugin/memory/memory_tencentdb/README.md</span>：provider key、supervisor、HTTP 映射、自动发现与故障保护。</li>
    <li><span class="inline">src/gateway/server.ts</span>：<span class="inline">/health</span>、<span class="inline">/recall</span>、<span class="inline">/capture</span>、<span class="inline">/search/*</span> 路由。</li>
    <li><span class="inline">src/gateway/config.ts</span>：host、port、API key、CORS、Gateway 数据目录和 LLM 配置来源。</li>
    <li><span class="inline">src/adapters/standalone/host-adapter.ts</span>：把 Gateway 这种 standalone 宿主适配成核心需要的 HostAdapter。</li>
    <li><span class="inline">src/core/tdai-core.ts</span>：宿主无关门面，集中处理 recall、capture、search 与 pipeline。</li>
  </ul>
</div>

<div class="card warn">
  <div class="tag">🔒 安全边界</div>
  本课只用占位符和本地回环地址。<span class="inline">GET /health</span> 设计为无需 token，便于 Docker healthcheck 或编排系统探活；其他 route 是否鉴权由 Gateway 端配置决定。若绑定到非 loopback 地址，必须先规划 API key、CORS 白名单和网络访问边界。
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Hermes 是另一条宿主路径，不是另一套 memory engine。只要路径能从 <span class="inline">Hermes → memory_tencentdb provider → local Gateway → StandaloneHostAdapter → TdaiCore</span> 走通，后面的 L0/L1/L2/L3、Recall、Capture、Search 学习模型就和 OpenClaw 收敛到同一个核心。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
The Hermes path looks different from OpenClaw: one is a Python Agent memory provider, the other is an OpenClaw plugin and Gateway lifecycle.
But it is not a different memory engine. Hermes is an alternate host entry: the provider translates Hermes recall, capture, and search calls into HTTP, sends them to the local Gateway, and the Gateway reaches the same <span class="inline">TdaiCore</span> through <span class="inline">StandaloneHostAdapter</span>.
</p>

<div class="card analogy">
  <div class="tag">🚪 Analogy</div>
  OpenClaw and Hermes are two doors into the same library. The front desk differs: OpenClaw uses plugin hooks/tools; Hermes uses the <span class="inline">memory_tencentdb</span> provider.
  Once inside, archiving, searching, recall, and shelf organization are handled by the same core service.
</div>

<h2>Hermes is not a second memory core</h2>
<div class="flow">
  <div class="node"><div class="nt">Hermes</div><div class="nd">Python Agent lifecycle</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">memory_tencentdb provider</div><div class="nd">provider key must use underscores</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">local Gateway</div><div class="nd">HTTP sidecar on 127.0.0.1:8420</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">StandaloneHostAdapter</div><div class="nd">isolates host differences</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">capture / recall / search / pipeline</div></div>
</div>

<p>
In <span class="inline">hermes-plugin/memory/memory_tencentdb/README.md</span>, the provider is described as a thin HTTP client plus process supervisor.
It plugs into the Hermes lifecycle, starts or probes the Gateway, maps <span class="inline">prefetch</span> to <span class="inline">POST /recall</span>, maps <span class="inline">sync_turn</span> to <span class="inline">POST /capture</span>, and advertises search tool schemas.
The real capture, extraction, storage, recall, and pipeline scheduling remain in the Node.js Gateway and core modules.
</p>

<h2>Two install routes: fresh Docker or existing Hermes</h2>
<div class="cols">
  <div class="col"><h4>Fresh Docker deployment</h4><p>The Hermes section in <span class="inline">README_CN.md</span> positions Docker as the route for starting a memory-enabled Hermes from scratch. The image bundles <span class="inline">hermes-agent</span> and the <span class="inline">memory_tencentdb</span> provider, with the Gateway exposed on port <span class="inline">8420</span>. This is best when you want one container path to validate the complete loop.</p></div>
  <div class="col"><h4>Install provider into existing Hermes</h4><p>If Hermes is already installed, link or copy the provider into Hermes's memory provider directory and set <span class="inline">memory.provider: memory_tencentdb</span> in <span class="inline">~/.hermes/config.yaml</span>. The directory name must be exactly <span class="inline">memory_tencentdb</span> because Hermes uses it as the provider key.</p></div>
</div>

<p>
Whether you enter through Docker or an existing Hermes install, the checkpoints are the same: Hermes discovers the provider, the provider reaches the local Gateway, and the Gateway HTTP routes reach <span class="inline">TdaiCore</span>.
That is why the guide does not treat Hermes as a separate memory system: it changes host integration and process boundaries, not the L0-L3, Recall/Search, or pipeline core.
</p>

<h2>Pseudocode</h2>
<pre class="code">memory:
  provider: memory_tencentdb

MEMORY_TENCENTDB_GATEWAY_HOST="127.0.0.1"
MEMORY_TENCENTDB_GATEWAY_PORT="8420"

curl http://127.0.0.1:8420/health</pre>

<p>
The example uses placeholders and a loopback address only. Real LLM credentials, Gateway API keys, cloud database passwords, and private team endpoints do not belong in guide examples, screenshots, or commits.
If authentication is enabled, the Gateway side uses <span class="inline">TDAI_GATEWAY_API_KEY</span> or <span class="inline">server.apiKey</span>; the Hermes provider, as the client, can use <span class="inline">MEMORY_TENCENTDB_GATEWAY_API_KEY</span>. They must match, but this lesson never shows a real value.
</p>

<h2>What the Gateway exposes</h2>
<p>
<span class="inline">src/gateway/server.ts</span> marks the Gateway as the HTTP server for the Hermes sidecar: <span class="inline">GET /health</span> is the health check, <span class="inline">POST /recall</span> performs memory recall before the model turn, <span class="inline">POST /capture</span> captures a conversation turn, <span class="inline">POST /search/memories</span> searches L1 structured memories, and <span class="inline">POST /search/conversations</span> searches L0 raw conversations.
<span class="inline">src/gateway/config.ts</span> also exposes optional knobs such as <span class="inline">server.apiKey</span> / <span class="inline">TDAI_GATEWAY_API_KEY</span> and <span class="inline">server.corsOrigins</span> / <span class="inline">TDAI_CORS_ORIGINS</span>. The default learning path is a local sidecar; auth and CORS become critical when you expose it beyond loopback.
</p>

<h2>Verification order</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Start with health check</h4><p>Use <span class="inline">curl http://127.0.0.1:8420/health</span> to confirm the Gateway is up; the docs allow <span class="inline">ok</span> or <span class="inline">degraded</span>.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Configure the provider</h4><p>Confirm the Hermes provider directory name, <span class="inline">plugin.yaml::name</span>, and <span class="inline">memory.provider</span> all align on <span class="inline">memory_tencentdb</span>.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Auto-start on first conversation or start manually</h4><p>In the existing-Hermes route, the provider can auto-discover and <span class="inline">Popen()</span> the Gateway on the first conversation, or you can run the Gateway before launching Hermes.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Verify with recall/search</h4><p>State a reusable preference or project fact, then use a later question, memory search, or conversation search to confirm it was captured, indexed, and recalled.</p></div></div>
</div>

<div class="card detail">
  <div class="tag">🔬 Source map</div>
  <ul>
    <li><span class="inline">README_CN.md</span>: Hermes install section, Docker route, existing-Hermes route, and Gateway security configuration.</li>
    <li><span class="inline">hermes-plugin/memory/memory_tencentdb/README.md</span>: provider key, supervisor, HTTP mapping, auto-discovery, and reliability guards.</li>
    <li><span class="inline">src/gateway/server.ts</span>: <span class="inline">/health</span>, <span class="inline">/recall</span>, <span class="inline">/capture</span>, and <span class="inline">/search/*</span> routes.</li>
    <li><span class="inline">src/gateway/config.ts</span>: host, port, API key, CORS, Gateway data directory, and LLM config sources.</li>
    <li><span class="inline">src/adapters/standalone/host-adapter.ts</span>: adapts a standalone Gateway host into the HostAdapter shape required by the core.</li>
    <li><span class="inline">src/core/tdai-core.ts</span>: host-neutral facade for recall, capture, search, and pipeline management.</li>
  </ul>
</div>

<div class="card warn">
  <div class="tag">🔒 Security boundary</div>
  This lesson uses placeholders and loopback addresses only. <span class="inline">GET /health</span> is intentionally token-free for Docker health checks or orchestrator liveness probes; authentication for other routes is controlled by Gateway-side config. If you bind beyond loopback, plan the API key, CORS allow-list, and network boundary first.
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Hermes is an alternate host path, not another memory engine. Once the path <span class="inline">Hermes → memory_tencentdb provider → local Gateway → StandaloneHostAdapter → TdaiCore</span> works, the L0/L1/L2/L3, Recall, Capture, and Search mental model converges with OpenClaw on the same core.
</div>
""",
}

LESSON_06 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
运行后的文件不是隐藏实现细节，而是一张调试地图：当召回、画像、场景或长任务摘要看起来不对时，先看高层产物理解系统“相信了什么”，再一路下钻到低层证据确认它为什么这么相信。
</p>

<div class="card analogy">
  <div class="tag">🗺️ 生活类比</div>
  这些目录像侦探案卷：画像和场景是案情摘要，L1 原子记忆是证词卡片，L0 对话是原始录音；Offload 的 MMD 是任务白板，JSONL 和 refs 是白板背后的材料袋。
</div>

<h2>L0-L3 分层会落到哪些文件</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">L0</span><span class="name">Conversation</span></div><div class="ld"><span class="inline">conversations/</span> 保存原始对话 JSONL，由 <span class="inline">src/core/conversation/l0-recorder.ts</span> 写入，负责保留最底层证据。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">L1</span><span class="name">Atom</span></div><div class="ld"><span class="inline">records/</span> 保存结构化记忆 JSONL，由 <span class="inline">src/core/record/l1-writer.ts</span> 写入，便于搜索和召回。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">L2</span><span class="name">Scene</span></div><div class="ld"><span class="inline">scene_blocks/</span> 保存 Markdown 场景块，由 <span class="inline">src/core/scene/scene-extractor.ts</span> 聚合多条 L1 证据。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">L3</span><span class="name">Persona</span></div><div class="ld"><span class="inline">persona.md</span> 保存长期画像，由 <span class="inline">src/core/persona/persona-generator.ts</span> 从场景中生成稳定偏好和用户特征。</div></div>
</div>

<p>
本地长期记忆目录通常还会看到 <span class="inline">vectors.db</span>：它是本地 SQLite 向量/全文检索存储，入口可从 <span class="inline">src/core/store/factory.ts</span> 看存储后端如何创建。
<span class="inline">.metadata/</span> 放 manifest、索引状态和检查点线索，对应 <span class="inline">src/utils/manifest.ts</span> 与 <span class="inline">src/utils/checkpoint.ts</span>；<span class="inline">.backup/</span> 用于备份，方便升级或调试前回滚。
所以调试时不要只盯一个数据库文件：目录、JSONL、Markdown、metadata 和 backup 一起构成“可解释的记忆状态”。
</p>

<h2>长期记忆目录 vs Offload 目录</h2>
<div class="cols">
  <div class="col"><h4>长期记忆：跨会话复用</h4><p><span class="inline">memory-tdai/</span> 位于解析后的 OpenClaw state dir 下，常见完整路径是 <span class="inline">~/.openclaw/state/memory-tdai/</span>；standalone 或 fallback 路径可能不同。里面的 <span class="inline">conversations/</span>、<span class="inline">records/</span>、<span class="inline">scene_blocks/</span>、<span class="inline">persona.md</span>、<span class="inline">vectors.db</span>、<span class="inline">.metadata/</span>、<span class="inline">.backup/</span> 关注“未来会话还能不能记得、搜到、解释清楚”。它的证据链是 L3 -&gt; L2 -&gt; L1 -&gt; L0。</p></div>
  <div class="col"><h4>Context Offload：当前任务压缩</h4><p><span class="inline">~/.openclaw/context-offload/&lt;agent&gt;/</span> 下会有 <span class="inline">refs/</span>、<span class="inline">mmds/</span>、<span class="inline">offload-&lt;session&gt;.jsonl</span>、<span class="inline">state.json</span>、<span class="inline">sessions-registry.json</span>。它关注“当前长任务如何把大块材料移出上下文，但仍能找回证据”。实现入口看 <span class="inline">src/offload/storage.ts</span>。</p></div>
</div>

<h2>最小文件形状</h2>
<pre class="code">memory-tdai/
  conversations/     # L0 raw messages
  records/           # L1 atoms
  scene_blocks/      # L2 scenes
  persona.md         # L3 persona
  vectors.db         # local search index

context-offload/
  &lt;agent&gt;/refs/
  &lt;agent&gt;/mmds/
  &lt;agent&gt;/offload-&lt;session&gt;.jsonl</pre>

<p>
Offload 的 <span class="inline">refs/</span> 保存被卸载的大块原文或引用材料，<span class="inline">mmds/</span> 保存 Mermaid/MMD 任务图，<span class="inline">offload-&lt;session&gt;.jsonl</span> 记录会话内的卸载事件。
<span class="inline">state.json</span> 维护当前状态，<span class="inline">sessions-registry.json</span> 则帮助按会话找到对应产物。MMD 适合先看全局任务结构，但如果节点描述和真实材料冲突，最终仍要回到 JSONL 与 refs。
</p>

<h2>下钻调试：先看结构，再找证据</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Persona -&gt; Scene</h4><p>如果用户说“画像不对”，先打开 <span class="inline">persona.md</span> 看具体 claim，再找它来自哪些 <span class="inline">scene_blocks/</span>。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Scene -&gt; Atom</h4><p>场景块只保结构和叙述，不是最终证据。继续到 <span class="inline">records/</span> 找 L1 Atom，核对事实、偏好、约束的抽取是否合理。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Atom -&gt; Conversation</h4><p>如果 L1 本身可疑，回到 <span class="inline">conversations/</span> 的 L0 JSONL，核对原始用户话语、时间和上下文。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>MMD node -&gt; offload JSONL -&gt; refs</h4><p>如果长任务摘要或节点错了，先看 <span class="inline">mmds/</span> 的节点，再查 <span class="inline">offload-&lt;session&gt;.jsonl</span>，最后打开 <span class="inline">refs/</span> 里的原文材料。</p></div></div>
</div>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>：L0 对话 JSONL 写入。</li>
    <li><span class="inline">src/core/record/l1-writer.ts</span>：L1 结构化记录写入。</li>
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>：L2 场景块抽取。</li>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>：L3 persona 生成。</li>
    <li><span class="inline">src/core/store/factory.ts</span>：本地 SQLite/搜索存储创建。</li>
    <li><span class="inline">src/offload/storage.ts</span>：context-offload 目录、refs、MMD、JSONL 和会话状态。</li>
    <li><span class="inline">src/utils/manifest.ts</span>：manifest 元数据。</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>：checkpoint 读写。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  运行产物是调试入口：长期记忆按 Persona -&gt; Scene -&gt; L1 Atom -&gt; L0 Conversation 下钻，Offload 按 MMD node -&gt; offload JSONL -&gt; refs 下钻。高层帮你快速定位结构，低层负责给出可核对证据。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Runtime files are not hidden implementation details. They are a debugging map: when recall, persona, scenes, or long-task summaries look wrong, start with the high-level artifact to see what the system believes, then drill down to the evidence.
</p>

<div class="card analogy">
  <div class="tag">🗺️ Analogy</div>
  Think of the files as a detective case folder: persona and scenes are summaries, L1 atoms are evidence cards, L0 conversations are recordings; Offload MMDs are task boards, with JSONL and refs as the source bags behind them.
</div>

<h2>Where L0-L3 land on disk</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">L0</span><span class="name">Conversation</span></div><div class="ld"><span class="inline">conversations/</span> stores raw conversation JSONL, written by <span class="inline">src/core/conversation/l0-recorder.ts</span>, and preserves bottom-level evidence.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">L1</span><span class="name">Atom</span></div><div class="ld"><span class="inline">records/</span> stores structured memory JSONL, written by <span class="inline">src/core/record/l1-writer.ts</span>, for search and recall.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">L2</span><span class="name">Scene</span></div><div class="ld"><span class="inline">scene_blocks/</span> stores Markdown scene blocks, produced by <span class="inline">src/core/scene/scene-extractor.ts</span> from multiple L1 records.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">L3</span><span class="name">Persona</span></div><div class="ld"><span class="inline">persona.md</span> stores long-term persona, generated by <span class="inline">src/core/persona/persona-generator.ts</span> from scenes.</div></div>
</div>

<p>
The long-term memory directory usually also contains <span class="inline">vectors.db</span>, the local SQLite vector/full-text search store; use <span class="inline">src/core/store/factory.ts</span> to see how storage is created.
<span class="inline">.metadata/</span> keeps manifest and checkpoint clues, connected to <span class="inline">src/utils/manifest.ts</span> and <span class="inline">src/utils/checkpoint.ts</span>; <span class="inline">.backup/</span> keeps backups for rollback before upgrades or debugging.
</p>

<h2>Long-term memory vs Offload directories</h2>
<div class="cols">
  <div class="col"><h4>Long-term memory: cross-session reuse</h4><p><span class="inline">memory-tdai/</span> lives under the resolved OpenClaw state dir, commonly <span class="inline">~/.openclaw/state/memory-tdai/</span>; standalone or fallback paths may differ. Its <span class="inline">conversations/</span>, <span class="inline">records/</span>, <span class="inline">scene_blocks/</span>, <span class="inline">persona.md</span>, <span class="inline">vectors.db</span>, <span class="inline">.metadata/</span>, and <span class="inline">.backup/</span> answer whether a future session can remember, search, and explain something. The evidence chain is L3 -&gt; L2 -&gt; L1 -&gt; L0.</p></div>
  <div class="col"><h4>Context Offload: current-task compression</h4><p>Under <span class="inline">~/.openclaw/context-offload/&lt;agent&gt;/</span>, expect <span class="inline">refs/</span>, <span class="inline">mmds/</span>, <span class="inline">offload-&lt;session&gt;.jsonl</span>, <span class="inline">state.json</span>, and <span class="inline">sessions-registry.json</span>. It answers how the current long task moved large evidence out of context while keeping it recoverable. See <span class="inline">src/offload/storage.ts</span>.</p></div>
</div>

<h2>Minimal file shape</h2>
<pre class="code">memory-tdai/
  conversations/     # L0 raw messages
  records/           # L1 atoms
  scene_blocks/      # L2 scenes
  persona.md         # L3 persona
  vectors.db         # local search index

context-offload/
  &lt;agent&gt;/refs/
  &lt;agent&gt;/mmds/
  &lt;agent&gt;/offload-&lt;session&gt;.jsonl</pre>

<p>
Offload <span class="inline">refs/</span> keep large source text or referenced material; <span class="inline">mmds/</span> keep Mermaid/MMD task diagrams; <span class="inline">offload-&lt;session&gt;.jsonl</span> records offload events for the session.
<span class="inline">state.json</span> tracks current state, and <span class="inline">sessions-registry.json</span> helps find artifacts by session.
</p>

<h2>Drill-down debugging: structure first, evidence second</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Persona -&gt; Scene</h4><p>If the user says "the persona is wrong", open <span class="inline">persona.md</span> for the specific claim, then find the related <span class="inline">scene_blocks/</span>.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Scene -&gt; Atom</h4><p>A scene keeps structure and narrative, not final proof. Continue to <span class="inline">records/</span> and inspect the L1 atom extraction.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Atom -&gt; Conversation</h4><p>If the atom is suspicious, return to <span class="inline">conversations/</span> L0 JSONL and verify the raw user words, time, and context.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>MMD node -&gt; offload JSONL -&gt; refs</h4><p>If a long-task node is wrong, inspect the <span class="inline">mmds/</span> node, then <span class="inline">offload-&lt;session&gt;.jsonl</span>, then the raw material in <span class="inline">refs/</span>.</p></div></div>
</div>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/conversation/l0-recorder.ts</span>: L0 conversation JSONL.</li>
    <li><span class="inline">src/core/record/l1-writer.ts</span>: L1 structured records.</li>
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>: L2 scene extraction.</li>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>: L3 persona generation.</li>
    <li><span class="inline">src/core/store/factory.ts</span>: local SQLite/search store creation.</li>
    <li><span class="inline">src/offload/storage.ts</span>: context-offload directory, refs, MMDs, JSONL, and session state.</li>
    <li><span class="inline">src/utils/manifest.ts</span>: manifest metadata.</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>: checkpoint reads and writes.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Runtime artifacts are debugging entry points: long-term memory drills down Persona -&gt; Scene -&gt; L1 Atom -&gt; L0 Conversation, while Offload drills down MMD node -&gt; offload JSONL -&gt; refs. Upper layers locate structure; lower layers provide verifiable evidence.
</div>
""",
}

LESSON_07 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
配置不是越多越专业。TencentDB Agent Memory 的安全心智模型是：先让零配置闭环能跑，再只调日常旋钮，最后才进入长会话、远程后端、LLM 与运维边界。
本课把 <span class="inline">src/config.ts</span>、<span class="inline">openclaw.plugin.json</span>、<span class="inline">README_CN.md</span> 的“可调参数”说明和 <span class="inline">src/core/store/factory.ts</span> 串起来，形成一张渐进式配置地图。
</p>

<div class="card analogy">
  <div class="tag">🎚️ 生活类比</div>
  配置像调音台：日常只动音量和静音，长会话才调均衡器和压缩器，真正换声卡或接远程设备时才碰驱动、接口和凭据。默认值应该让新手先听到声音，而不是先面对一整排危险旋钮。
</div>

<h2>三层配置：从日常旋钮到运维边界</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">1</span><span class="name">Daily knobs</span></div><div class="ld">日常只调 <span class="inline">capture</span>、<span class="inline">recall</span>、少量 <span class="inline">pipeline</span>：是否捕获、召回条数、召回策略、超时和最小触发条件。目标是“别打扰用户，还能想起来”。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">2</span><span class="name">Long-session tuning</span></div><div class="ld">长会话再看 <span class="inline">extraction</span>、<span class="inline">pipeline</span>、<span class="inline">offload</span>、<span class="inline">bm25</span>：抽取频率、批处理、关键词检索、上下文卸载和报告产物。目标是减少上下文压力，同时保留可追溯证据。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">3</span><span class="name">Backend / LLM / ops</span></div><div class="ld">最后才配置 <span class="inline">embedding</span>、<span class="inline">tcvdb</span>、<span class="inline">llm</span>、<span class="inline">report</span> 和网关鉴权。这里涉及远程服务、模型维度、API Key、后端选择和运维可观测性。</div></div>
</div>

<p>
这三层不是权限等级，而是学习顺序。<span class="inline">parseConfig</span> 会把用户配置和默认值合并成运行时配置；因此文档应鼓励“少量、可解释、可回滚”的改动。
如果一开始就同时改 embedding、TCVDB、清理策略和 LLM，很难判断问题来自网络、凭据、维度、后端还是业务触发条件。
</p>

<h2>配置组各管什么</h2>
<ul>
  <li><strong>capture：</strong>控制对话是否进入 L0/L1 流程，以及 <span class="inline">l0l1RetentionDays</span> 这类保留策略；值为 <span class="inline">0</span> 表示关闭清理，不会自动删 L0/L1。</li>
  <li><strong>extraction：</strong>影响从原始对话抽取结构化记忆的方式，适合在确认捕获稳定后再调。</li>
  <li><strong>pipeline：</strong><span class="inline">PipelineTriggerConfig</span> 这类触发配置决定何时整理 L1、场景、画像或批处理任务。</li>
  <li><strong>recall：</strong><span class="inline">RecallConfig</span> 管理策略、最大条数和 <span class="inline">timeoutMs</span>；超时是安全默认值，防止召回卡住用户请求。</li>
  <li><strong>embedding：</strong><span class="inline">EmbeddingConfig</span> 决定本地或远程向量能力；远程 provider 必须给出 <span class="inline">apiKey</span>、<span class="inline">baseUrl</span>、<span class="inline">model</span>、<span class="inline">dimensions</span>。</li>
  <li><strong>bm25：</strong>关键词检索补足纯向量召回的盲区，适合术语、文件名、错误码和专有名词。</li>
  <li><strong>tcvdb：</strong>远程 Tencent Cloud VectorDB 后端配置，和 <span class="inline">src/core/store/factory.ts</span> 的后端选择一起理解。</li>
  <li><strong>offload：</strong><span class="inline">OffloadConfig</span> 管理长任务材料外置、refs、MMD 和会话状态，服务当前任务压缩。</li>
  <li><strong>llm：</strong>控制抽取、总结或网关相关模型调用；真实密钥必须留在安全本地配置或环境变量中。</li>
  <li><strong>report：</strong>面向调试和可读产物，帮助人查看发生了什么，而不是替代底层证据链。</li>
</ul>

<h2>本地默认与 TCVDB 后端</h2>
<div class="cols">
  <div class="col"><h4>SQLite default</h4><p>零配置预期可运行：默认本地 SQLite / sqlite-vec 路径适合课程、离线试用和个人 smoke test。它降低启动门槛，也让新手先验证 capture、pipeline、recall 的闭环。清理策略默认保守：<span class="inline">capture.l0l1RetentionDays = 0</span> 表示禁用清理；任何激进清理都应显式 opt-in。</p></div>
  <div class="col"><h4>TCVDB backend</h4><p>当数据规模、共享部署或远程向量检索成为真实需求，再配置 <span class="inline">tcvdb</span>。后端选择要回到 <span class="inline">src/core/store/factory.ts</span> 看创建逻辑：配置不是写给好看，而是决定 store bundle 会落到本地还是远程。</p></div>
</div>

<h2>从配置到行为的路径</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>openclaw.plugin.json 暴露入口</h4><p>插件元数据告诉 OpenClaw 这个包有哪些 hooks、tools 和配置面；用户通常从 OpenClaw 配置文件写入 <span class="inline">memory-tencentdb</span>。</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>src/config.ts 解析默认值</h4><p><span class="inline">parseConfig</span> 合并用户输入与默认值，形成 <span class="inline">CaptureConfig</span>、<span class="inline">PipelineTriggerConfig</span>、<span class="inline">RecallConfig</span>、<span class="inline">EmbeddingConfig</span>、<span class="inline">OffloadConfig</span> 等运行时配置。</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>store bundle 选择后端</h4><p><span class="inline">src/core/store/factory.ts</span> 根据配置创建本地 SQLite 或 TCVDB 相关 store bundle，影响 L0/L1/向量和检索能力的落点。</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>hooks / pipeline 改变行为</h4><p>解析后的 capture、recall、pipeline、offload 和 embedding 设置最终影响回答前召回、回答后捕获、后台整理、长任务卸载和报告输出。</p></div></div>
</div>

<h2>远程 embedding 示例只用占位符</h2>
<pre class="code">{
  "memory-tencentdb": {
    "recall": {
      "strategy": "hybrid",
      "maxResults": 5,
      "timeoutMs": 5000
    },
    "embedding": {
      "provider": "openai",
      "baseUrl": "https://example.invalid/v1",
      "apiKey": "${EMBEDDING_API_KEY}",
      "model": "text-embedding-3-small",
      "dimensions": 1536
    }
  }
}</pre>

<p>
这个片段的重点不是推荐某个服务，而是说明远程 embedding 的最小必填组合：endpoint、密钥、模型名和维度必须互相匹配。公开教程、截图、提交和 Gateway 示例中的 API Key 都必须是占位符；如果涉及 Gateway 鉴权，也只能写变量名或假值，不能写真实团队密钥。
</p>

<div class="card detail">
  <div class="tag">🔬 源码 / 文档锚点</div>
  <ul>
    <li><span class="inline">src/config.ts</span>：<span class="inline">CaptureConfig</span>、<span class="inline">PipelineTriggerConfig</span>、<span class="inline">RecallConfig</span>、<span class="inline">EmbeddingConfig</span>、<span class="inline">OffloadConfig</span>、<span class="inline">parseConfig</span>。</li>
    <li><span class="inline">openclaw.plugin.json</span>：插件注册、配置面和 OpenClaw 入口。</li>
    <li><span class="inline">README_CN.md</span>：可调参数 section，适合先看用户能改什么。</li>
    <li><span class="inline">src/core/store/factory.ts</span>：本地 SQLite 与 TCVDB 等后端选择。</li>
  </ul>
</div>

<div class="card warn">
  <div class="tag">🔒 安全默认值</div>
  零配置应该能跑；清理默认保守；召回 timeout 保护交互体验；远程 embedding 缺字段时应失败或降级而不是假装成功；所有公开文档里的 Gateway API Key、embedding key、base URL 都只能是占位符。
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  先用默认值证明闭环，再按 Level 1、Level 2、Level 3 渐进调参。安全默认值的目标是“新手能启动、用户不被阻塞、数据不被意外删除、密钥不进入文档”。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
More configuration does not mean a better setup. The safe mental model is progressive: make the zero-config loop run, tune daily knobs only when needed, then move into long-session, backend, LLM, and operational settings.
</p>

<div class="card analogy">
  <div class="tag">🎚️ Analogy</div>
  Configuration is like a mixing console: everyday use changes volume and mute; long sessions tune compression and EQ; remote devices require drivers, endpoints, and credentials. Defaults should let beginners hear sound before they touch dangerous knobs.
</div>

<h2>Three configuration levels</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">1</span><span class="name">Daily knobs</span></div><div class="ld">Tune <span class="inline">capture</span>, <span class="inline">recall</span>, and a little <span class="inline">pipeline</span>: capture on/off, recall strategy, result count, timeout, and minimal trigger thresholds.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">2</span><span class="name">Long-session tuning</span></div><div class="ld">For long sessions, tune <span class="inline">extraction</span>, <span class="inline">pipeline</span>, <span class="inline">offload</span>, and <span class="inline">bm25</span>: extraction cadence, batching, keyword search, context offload, and reports.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">3</span><span class="name">Backend / LLM / ops</span></div><div class="ld">Only then configure <span class="inline">embedding</span>, <span class="inline">tcvdb</span>, <span class="inline">llm</span>, <span class="inline">report</span>, and gateway authentication, because these involve remote services, model dimensions, API keys, backend choice, and operations.</div></div>
</div>

<p>
The levels are a learning order, not a permission model. <span class="inline">parseConfig</span> combines user settings with defaults into runtime config, so documentation should encourage small, explainable, reversible changes.
</p>

<h2>What each config group controls</h2>
<ul>
  <li><strong>capture:</strong> whether conversations enter L0/L1, plus retention such as <span class="inline">l0l1RetentionDays</span>; <span class="inline">0</span> means cleanup is disabled.</li>
  <li><strong>extraction:</strong> how raw conversations become structured memories after capture is proven stable.</li>
  <li><strong>pipeline:</strong> <span class="inline">PipelineTriggerConfig</span> decides when L1, scenes, persona, or batch work runs.</li>
  <li><strong>recall:</strong> <span class="inline">RecallConfig</span> manages strategy, result count, and <span class="inline">timeoutMs</span>; the timeout avoids blocking the user.</li>
  <li><strong>embedding:</strong> <span class="inline">EmbeddingConfig</span> selects local or remote vector behavior; remote providers require <span class="inline">apiKey</span>, <span class="inline">baseUrl</span>, <span class="inline">model</span>, and <span class="inline">dimensions</span>.</li>
  <li><strong>bm25:</strong> keyword retrieval for terms, file names, error codes, and project-specific names.</li>
  <li><strong>tcvdb:</strong> Tencent Cloud VectorDB backend settings, understood together with <span class="inline">src/core/store/factory.ts</span>.</li>
  <li><strong>offload:</strong> <span class="inline">OffloadConfig</span> controls current-task compression, refs, MMDs, and session state.</li>
  <li><strong>llm:</strong> model calls for extraction, summarization, or gateway behavior; real secrets stay in secure local config or environment variables.</li>
  <li><strong>report:</strong> human-readable diagnostics and artifacts, not a replacement for lower-level evidence.</li>
</ul>

<h2>SQLite default vs TCVDB backend</h2>
<div class="cols">
  <div class="col"><h4>SQLite default</h4><p>Zero config is intended to run. The default local SQLite / sqlite-vec path is good for courses, offline trials, and personal smoke tests. Cleanup is conservative: <span class="inline">capture.l0l1RetentionDays = 0</span> disables cleanup, and aggressive deletion requires explicit opt-in.</p></div>
  <div class="col"><h4>TCVDB backend</h4><p>Configure <span class="inline">tcvdb</span> only when scale, shared deployment, or remote vector retrieval is a real requirement. Read <span class="inline">src/core/store/factory.ts</span> to see how configuration chooses the local or remote store bundle.</p></div>
</div>

<h2>From config to behavior</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>openclaw.plugin.json exposes the entry</h4><p>Plugin metadata tells OpenClaw which hooks, tools, and configuration surface the package provides.</p></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>src/config.ts parses defaults</h4><p><span class="inline">parseConfig</span> produces runtime <span class="inline">CaptureConfig</span>, <span class="inline">PipelineTriggerConfig</span>, <span class="inline">RecallConfig</span>, <span class="inline">EmbeddingConfig</span>, and <span class="inline">OffloadConfig</span>.</p></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Store bundle chooses a backend</h4><p><span class="inline">src/core/store/factory.ts</span> creates the local SQLite or TCVDB-related stores for L0/L1, vector, and search behavior.</p></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Hooks and pipeline change behavior</h4><p>The parsed capture, recall, pipeline, offload, and embedding settings affect pre-answer recall, post-answer capture, background organization, offload, and reports.</p></div></div>
</div>

<h2>Remote embedding example with placeholders only</h2>
<pre class="code">{
  "memory-tencentdb": {
    "recall": {
      "strategy": "hybrid",
      "maxResults": 5,
      "timeoutMs": 5000
    },
    "embedding": {
      "provider": "openai",
      "baseUrl": "https://example.invalid/v1",
      "apiKey": "${EMBEDDING_API_KEY}",
      "model": "text-embedding-3-small",
      "dimensions": 1536
    }
  }
}</pre>

<p>
The point is not to recommend a service; it is to show the required remote embedding fields. Endpoint, key, model, and dimensions must match. Public docs, screenshots, commits, and Gateway examples must use placeholders only.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/config.ts</span>: <span class="inline">CaptureConfig</span>, <span class="inline">PipelineTriggerConfig</span>, <span class="inline">RecallConfig</span>, <span class="inline">EmbeddingConfig</span>, <span class="inline">OffloadConfig</span>, and <span class="inline">parseConfig</span>.</li>
    <li><span class="inline">openclaw.plugin.json</span>: plugin registration, configuration surface, and OpenClaw entry point.</li>
    <li><span class="inline">README_CN.md</span>: the adjustable parameters section.</li>
    <li><span class="inline">src/core/store/factory.ts</span>: local SQLite versus TCVDB backend selection.</li>
  </ul>
</div>

<div class="card warn">
  <div class="tag">🔒 Safe defaults</div>
  Zero config should run; cleanup defaults should be conservative; recall timeout protects interaction; incomplete remote embedding should fail or degrade instead of pretending to work; Gateway API keys and embedding keys in docs must be placeholders.
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Prove the loop with defaults, then tune Level 1, Level 2, and Level 3 progressively. Safe defaults mean beginners can start, users are not blocked, data is not deleted by surprise, and secrets never enter documentation.
</div>
""",
}
