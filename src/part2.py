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
