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

