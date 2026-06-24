"""Part 5 content: L2/L3 scene and persona memory."""


LESSON_17 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L1 原子记忆适合搜索单个事实，但真实活动通常由许多小事实共同构成：一次调试、一次设计讨论、一次偏好变化。
L2 Scene Block 的作用，是把这些零散 L1 组织成可阅读、可导航、可追溯、可增长的情境块，再把稳定结论交给 L3 Persona。
</p>

<div class="card analogy">
  <div class="tag">🗂️ 生活类比</div>
  L1 像散落的便利贴：“喜欢中文回答”“今天在修 dedup”“证据来自消息 m42”。L2 像项目日志的一页：
  把同一次活动的便利贴贴到一起，写上摘要、时间线、热度和证据链接。L3 则像长期画像，只保留多次日志反复支持的稳定特征。
</div>

<h2>L2 在 L1 与 L3 之间架桥</h2>
<div class="flow">
  <div class="node"><div class="nt">L1 atoms</div><div class="nd">可搜索的细粒度事实、偏好、事件、约束</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L2 scene blocks</div><div class="nd">按活动聚合上下文、时间线、证据与摘要</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L3 persona</div><div class="nd">从多个场景提炼稳定画像与长期倾向</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall</div><div class="nd">下一轮按需注入，不把每个原子都塞进 prompt</div></div>
</div>

<p>
如果只用 L1，系统可以找到单条事实，却很难解释“这些事实属于哪一次活动、前后顺序是什么、哪些证据支持它、这件事最近是否还热”。
如果直接从 L1 生成 L3，又容易把一次性的噪声误当成长期人格。L2 因此是中间层：保留事件上下文与活动历史，
让 L3 只从经过场景聚合的证据里提炼稳定特征。
</p>

<h2>L1 与 L2 的职责边界</h2>
<div class="cols">
  <div class="col"><h4>L1 atom responsibilities</h4><p>原子化、可搜索、可去重。每条记录尽量表达一个事实，带类型、优先级、时间与 <span class="inline">source_message_ids</span>，方便 recall 和证据下钻。</p></div>
  <div class="col"><h4>L2 scene responsibilities</h4><p>人类可读、情境化、可导航。一个 scene block 聚合多条相关 L1，维护活动摘要、时间线、来源引用、热度与更新历史。</p></div>
</div>

<h2>Scene Block 的已解析 META 字段</h2>
<table class="t">
  <tr><th>字段</th><th>作用</th></tr>
  <tr><td class="mono">created</td><td>记录场景首次形成的时间，用于区分老背景与新活动。</td></tr>
  <tr><td class="mono">updated</td><td>记录最后一次合并新 L1 的时间，形成活动时间线。</td></tr>
  <tr><td class="mono">summary</td><td>用少量文字描述这次活动的核心上下文，避免把所有 L1 原子直接注入。</td></tr>
  <tr><td class="mono">heat</td><td>表示近期活跃度或重要性，帮助后续 recall 与整理流程优先处理热场景。</td></tr>
</table>

<p>
这些是 <span class="inline">parseSceneBlock</span> 实际解析/格式化的 META key。证据不是一个被解析的 META 字段：
它应保留在 scene 正文叙事、来源引用和链接中，说明哪些 L1 原子支持这段摘要；需要核实时，再通过 L1 的
<span class="inline">source_message_ids</span> 回到 L0 原文。
</p>

<p>
这些字段和正文叙事共同解决一个核心问题：L2 保存“这批事实为什么有关联”。它不会替代 L1 搜索，也不会删除 L0 原文；
它把多条 L1 的关系、顺序与来源线索组织成可读块。这样 recall 可以先注入相关场景摘要，需要核实时再沿正文中的来源引用回到 L1 和 L0。
</p>

<h2>抽取与更新的伪代码</h2>
<pre class="code">new_l1_atoms = read_records_after_l2_cursor(sessionKey)
related_context = load_scene_summaries()
scene_blocks = cluster_atoms_by_activity(new_l1_atoms, related_context)
for block in scene_blocks:
    write_traceable_scene_narrative(block)
    update_summary_and_heat(block)</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>：<span class="inline">SceneExtractor.extract</span> 读取新增 L1 并驱动场景抽取；<span class="inline">buildSceneSummaries</span> 为 prompt 提供已有场景摘要，帮助增量归并。</li>
    <li><span class="inline">src/core/prompts/scene-extraction.ts</span>：scene block prompt contract 要求模型输出可解析、带来源线索、可更新的场景块，而不是自由散文。</li>
    <li><span class="inline">src/core/scene/scene-format.ts</span>：<span class="inline">parseSceneBlock</span> 把文本块解析回 <span class="inline">created</span>、<span class="inline">updated</span>、<span class="inline">summary</span> 与 <span class="inline">heat</span>。</li>
    <li><span class="inline">src/core/record/l1-reader.ts</span>：为 scene extraction 读取 L1 records，说明 L2 的输入不是 L0 原文，而是已经结构化的 L1 原子。</li>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>：下游消费 scene blocks，从多个 L2 场景里提炼稳定 L3 persona。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  设计规则是：L1 保存原子化、可搜索、可追溯的事实；L2 保存人类可读的活动情境、时间线、证据链接、热度与摘要；
  L3 只从多个 L2 场景中提炼稳定特征。这样系统既不会把每个 L1 原子都注入上下文，也不会让 L3 直接吸收未经情境校验的噪声。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
L1 atom memories are good for searching individual facts, but real activity is usually made of many small facts: a debugging session,
a design discussion, or a preference change. L2 Scene Blocks organize scattered L1 atoms into readable, navigable, traceable, growing contexts,
then give stable conclusions to L3 Persona.
</p>

<div class="card analogy">
  <div class="tag">🗂️ Analogy</div>
  L1 is a pile of sticky notes: "prefers Chinese answers", "working on dedup today", "evidence came from message m42".
  L2 is one page in a project log: it groups notes from the same activity and adds a summary, timeline, heat, and evidence links.
  L3 is the long-term profile that keeps only traits repeatedly supported by many log pages.
</div>

<h2>L2 bridges L1 and L3</h2>
<div class="flow">
  <div class="node"><div class="nt">L1 atoms</div><div class="nd">searchable fine-grained facts, preferences, events, and constraints</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">L2 scene blocks</div><div class="nd">activity-level context, timeline, evidence, and summary</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">L3 persona</div><div class="nd">stable traits and long-term tendencies extracted from scenes</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">recall</div><div class="nd">inject what is relevant without dumping every atom into the prompt</div></div>
</div>

<p>
With only L1, the system can find a single fact, but it struggles to explain which activity the facts belonged to, what happened before or after,
which evidence supports the summary, and whether the topic is still hot. If L3 is generated directly from L1, a one-off detail can look like
a stable trait. L2 is the middle layer: it preserves event context and activity history so L3 can derive stable persona only from scene-level evidence.
</p>

<h2>L1 and L2 responsibility boundaries</h2>
<div class="cols">
  <div class="col"><h4>L1 atom responsibilities</h4><p>Atomic, searchable, deduplicated. Each record should express one fact and carry type, priority, time, and <span class="inline">source_message_ids</span> for recall and evidence drill-down.</p></div>
  <div class="col"><h4>L2 scene responsibilities</h4><p>Human-readable, contextual, navigable. A scene block clusters related L1 records and maintains activity summary, timeline, source references, heat, and update history.</p></div>
</div>

<h2>Parsed Scene Block META fields</h2>
<table class="t">
  <tr><th>Field</th><th>Purpose</th></tr>
  <tr><td class="mono">created</td><td>When the scene first formed, separating old background from new activity.</td></tr>
  <tr><td class="mono">updated</td><td>When new L1 atoms were last merged, forming an activity timeline.</td></tr>
  <tr><td class="mono">summary</td><td>Compact description of the activity context, avoiding injection of every L1 atom.</td></tr>
  <tr><td class="mono">heat</td><td>Recent activity or importance signal, so recall and maintenance can prioritize hot scenes.</td></tr>
</table>

<p>
These are the META keys that <span class="inline">parseSceneBlock</span> actually parses and formats. Evidence is not a parsed META field:
it stays in the scene narrative, source references, and links that explain which L1 atoms support the summary; when verification is needed,
L1 <span class="inline">source_message_ids</span> lead back to the raw L0 text.
</p>

<p>
Together, these fields and narrative references answer the core L2 question: why are these facts related? L2 does not replace L1 search or delete raw L0 text.
It organizes relationships, order, and source traceability across many L1 records into a readable block. Recall can inject the relevant scene summary first,
then drill through the narrative/source references back to L1 and L0 when verification is needed.
</p>

<h2>Extraction and update pseudocode</h2>
<pre class="code">new_l1_atoms = read_records_after_l2_cursor(sessionKey)
related_context = load_scene_summaries()
scene_blocks = cluster_atoms_by_activity(new_l1_atoms, related_context)
for block in scene_blocks:
    write_traceable_scene_narrative(block)
    update_summary_and_heat(block)</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>: <span class="inline">SceneExtractor.extract</span> reads new L1 records and drives scene extraction; <span class="inline">buildSceneSummaries</span> supplies existing scene summaries to support incremental merging.</li>
    <li><span class="inline">src/core/prompts/scene-extraction.ts</span>: the scene block prompt contract asks the model for parseable, source-traceable, updatable scene blocks rather than free-form prose.</li>
    <li><span class="inline">src/core/scene/scene-format.ts</span>: <span class="inline">parseSceneBlock</span> parses text blocks back into <span class="inline">created</span>, <span class="inline">updated</span>, <span class="inline">summary</span>, and <span class="inline">heat</span>.</li>
    <li><span class="inline">src/core/record/l1-reader.ts</span>: reads L1 records for scene extraction, showing that L2 consumes structured L1 atoms, not raw L0 text.</li>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>: downstream consumer of scene blocks, deriving stable L3 persona from multiple L2 scenes.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Design rule: L1 stores atomic, searchable, traceable facts; L2 stores human-readable activity contexts, timelines, evidence links, heat, and summaries;
  L3 derives stable traits from multiple L2 scenes. This avoids injecting every L1 atom while also preventing L3 from absorbing context-free noise directly.
</div>
""",
}


LESSON_18 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
SceneExtractor.extract() 是 L2 场景写入的安全执行器：工程代码准备目录、备份、索引和后处理；
LLM 只在 <span class="inline">scene_blocks/</span> 工作区里创建、更新或软删除 Markdown 场景文件，看不到隐藏元数据。
</p>

<div class="card analogy">
  <div class="tag">🧪 生活类比</div>
  把 LLM 想成被邀请整理项目档案的编辑。你只把“场景草稿箱”递给它，而不是整间档案室钥匙。
  它可以改写草稿、补充章节、把废弃页标成删除；档案编号、备份柜、画像档案和检查点仍由管理员保管。
</div>

<h2>extract() 的阶段</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>创建目录并备份</h4><p>确保 <span class="inline">scene_blocks/</span> 存在，然后用 <span class="inline">BackupManager.backupDirectory</span> 备份现有场景块。</p><div class="mono">create dirs -&gt; backup(scene_blocks)</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>读取索引</h4><p>工程代码读取 <span class="inline">.metadata/scene_index.json</span>，把已有场景摘要和文件映射作为 prompt 上下文，而不是让模型直接编辑索引。</p><div class="mono">readSceneIndex(dataDir)</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>构造 prompt</h4><p><span class="inline">buildSceneExtractionPrompt</span> 描述允许的操作：创建新场景、更新已有场景、用软删除标记废弃场景，并发出 persona 更新信号。</p><div class="mono">build prompt from memories + index</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>沙箱化 LLM 运行</h4><p><span class="inline">CleanContextRunner</span> 构造时用 <span class="inline">enableTools=True</span> 启用文件工具；每次运行再传入 <span class="inline">workspaceDir=scene_blocks</span>。可见目录只有 <span class="inline">scene_blocks/</span>。</p><div class="mono">new runner(enableTools) -&gt; run({ workspaceDir })</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>工程后处理</h4><p>运行结束后删除软删除文件、规范化文件名、同步索引，并解析 persona update signals。</p><div class="mono">cleanup -&gt; normalize filenames -&gt; sync index -&gt; parse persona signals</div></div></div>
</div>

<h2>可见与隐藏的文件边界</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">VISIBLE</span><span class="name">scene_blocks/</span></div><div class="ld">LLM 的文件工具只能在这里读写 Markdown scene files：可创建、更新、重命名后被规范化，也可写入软删除标记。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">HIDDEN</span><span class="name">.metadata/ (scene_index.json, recall_checkpoint.json, ...)</span></div><div class="ld">内部元数据目录不暴露给 LLM；索引与 checkpoint 游标由 TypeScript 代码读取、同步和推进，避免模型绕过工程状态机或污染运行状态。</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">HIDDEN</span><span class="name">.backup/</span></div><div class="ld">模型写入前的备份快照由工程代码管理，LLM 不直接查看或修改回滚状态。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">HIDDEN</span><span class="name">persona.md</span></div><div class="ld">模型只能在场景输出里留下 persona update signals；是否更新 L3 Persona 由后续解析与生成流程决定。</div></div>
</div>

<h2>工程代码与 LLM agent 的分工</h2>
<div class="cols">
  <div class="col"><h4>Engineering code responsibilities</h4><p>创建目录、备份 <span class="inline">scene_blocks/</span>、读取并同步 <span class="inline">.metadata/scene_index.json</span>、在 runner 构造时启用 tools、每次运行限制 <span class="inline">workspaceDir</span>、清理软删除、调用 <span class="inline">normalizeSceneFilenames</span>，并用 <span class="inline">parsePersonaUpdateSignal</span> 提取画像更新信号。</p></div>
  <div class="col"><h4>LLM agent responsibilities</h4><p>根据 L1 memories 与已有摘要判断哪些活动应合并、哪些需要新建场景、哪些旧场景应软删除；它写的是可读 Markdown 场景块，不拥有 metadata checkpoint、索引或 persona 文件。</p></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">sceneBlocksDir = dataDir / "scene_blocks"
backup(sceneBlocksDir)
index = readSceneIndex(dataDir)
prompt = buildSceneExtractionPrompt(memories, index)
runner = CleanContextRunner(enableTools=True)
runner.run(prompt, workspaceDir=sceneBlocksDir)
remove_soft_deleted_files()
normalizeSceneFilenames(sceneBlocksDir)
syncSceneIndex(dataDir)</pre>

<p>
这个设计的关键不是“让模型不能写文件”，而是“只让模型写它应该负责的文件”。沙箱允许模型发挥整理场景叙事的能力：
创建新 Markdown scene block、更新已有 block、或通过 soft-delete 标记废弃 block；同时隐藏
<span class="inline">.metadata/</span>（包含 scene index 与 checkpoint 文件）、<span class="inline">.backup/</span> 和 <span class="inline">persona.md</span>。
因此，创造性编辑发生在 L2 场景正文里，备份、索引一致性、文件名规范和 L3 画像升级仍由确定性的工程代码收口。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>：<span class="inline">SceneExtractor.extract</span> 编排目录创建、备份、索引读取、prompt 构造、<span class="inline">runner.run({ workspaceDir: sceneBlocksDir })</span>、清理、索引同步，并包含 <span class="inline">parsePersonaUpdateSignal</span>。</li>
    <li><span class="inline">src/core/scene/scene-index.ts</span>：<span class="inline">readSceneIndex</span> 读取 <span class="inline">.metadata/scene_index.json</span>，<span class="inline">syncSceneIndex</span> 在模型写入后重新同步索引。</li>
    <li><span class="inline">src/utils/clean-context-runner.ts</span>：定义 tool-enabled runner contract；文件工具在构造 runner 时启用，受限 <span class="inline">workspaceDir</span> 在每次 <span class="inline">run()</span> 调用时传入。</li>
    <li><span class="inline">src/core/prompts/scene-extraction.ts</span>：约束 LLM 允许的场景操作：创建、更新、软删除 Markdown scene files，并输出 persona 更新信号。</li>
    <li><span class="inline">src/core/scene/filename-normalizer.ts</span>：把模型产生的场景文件名收敛为规范化命名，降低重复与不可预测路径。</li>
    <li><span class="inline">src/utils/backup.ts</span>：<span class="inline">BackupManager.backupDirectory</span> 在模型写入前保存可回滚快照。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  SceneExtractor 把不确定的 LLM 文件编辑限制在 <span class="inline">scene_blocks/</span>，
  同时把 <span class="inline">.metadata/</span>（含 scene index 与 checkpoint 文件）、<span class="inline">.backup/</span> 和 <span class="inline">persona.md</span> 保持隐藏。
  这样 LLM 能写场景，工程代码仍掌握备份、索引、文件名规范、软删除清理与 persona 信号解析。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
SceneExtractor.extract() is the safe executor for L2 scene writing: engineering code prepares directories, backups, indexes, and post-processing;
the LLM can create, update, or soft-delete Markdown scene files only inside the <span class="inline">scene_blocks/</span> workspace.
</p>

<div class="card analogy">
  <div class="tag">🧪 Analogy</div>
  Think of the LLM as an editor invited to organize project notes. You hand it only the "scene drafts" folder, not the whole archive room.
  It may rewrite drafts, add sections, and mark abandoned pages for deletion; catalog numbers, backup cabinets, persona files, and checkpoints stay with the administrator.
</div>

<h2>extract() phases</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Create directories and back up</h4><p>Ensure <span class="inline">scene_blocks/</span> exists, then use <span class="inline">BackupManager.backupDirectory</span> to snapshot existing scene blocks.</p><div class="mono">create dirs -&gt; backup(scene_blocks)</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Load the index</h4><p>Engineering code reads <span class="inline">.metadata/scene_index.json</span> and passes summaries/file mappings as prompt context instead of letting the model edit the index directly.</p><div class="mono">readSceneIndex(dataDir)</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Build the prompt</h4><p><span class="inline">buildSceneExtractionPrompt</span> describes allowed operations: create scenes, update scenes, mark stale scenes for soft deletion, and emit persona update signals.</p><div class="mono">build prompt from memories + index</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Run the sandboxed LLM</h4><p><span class="inline">CleanContextRunner</span> enables file tools at construction with <span class="inline">enableTools=True</span>; each run then receives <span class="inline">workspaceDir=scene_blocks</span>. The visible directory is only <span class="inline">scene_blocks/</span>.</p><div class="mono">new runner(enableTools) -&gt; run({ workspaceDir })</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>Post-process in code</h4><p>After the run, code removes soft-deleted files, normalizes filenames, syncs the index, and parses persona update signals.</p><div class="mono">cleanup -&gt; normalize filenames -&gt; sync index -&gt; parse persona signals</div></div></div>
</div>

<h2>Visible and hidden file boundary</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">VISIBLE</span><span class="name">scene_blocks/</span></div><div class="ld">The LLM file tools can read/write Markdown scene files only here: create, update, later-normalized rename, or write soft-delete markers.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">HIDDEN</span><span class="name">.metadata/ (scene_index.json, recall_checkpoint.json, ...)</span></div><div class="ld">Internal metadata is not exposed to the LLM; indexes and checkpoint cursors are read, synchronized, and advanced by TypeScript code to prevent bypasses of the engineering state machine or runtime pollution.</div></div>
  <div class="layer l-part"><div class="lh"><span class="badge">HIDDEN</span><span class="name">.backup/</span></div><div class="ld">Rollback snapshots taken before model writes are managed by engineering code, not directly viewed or modified by the LLM.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">HIDDEN</span><span class="name">persona.md</span></div><div class="ld">The model can only leave persona update signals in scene output; later parsing and generation decide whether L3 Persona changes.</div></div>
</div>

<h2>Engineering code vs LLM agent</h2>
<div class="cols">
  <div class="col"><h4>Engineering code responsibilities</h4><p>Create directories, back up <span class="inline">scene_blocks/</span>, read and sync <span class="inline">.metadata/scene_index.json</span>, enable tools when constructing the runner, constrain <span class="inline">workspaceDir</span> per run, clean soft deletes, call <span class="inline">normalizeSceneFilenames</span>, and extract persona update signals with <span class="inline">parsePersonaUpdateSignal</span>.</p></div>
  <div class="col"><h4>LLM agent responsibilities</h4><p>Use L1 memories and existing summaries to decide which activities merge, which scenes are new, and which old scenes should be soft-deleted. It writes readable Markdown scene blocks; it does not own metadata checkpoints, indexes, or persona files.</p></div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">sceneBlocksDir = dataDir / "scene_blocks"
backup(sceneBlocksDir)
index = readSceneIndex(dataDir)
prompt = buildSceneExtractionPrompt(memories, index)
runner = CleanContextRunner(enableTools=True)
runner.run(prompt, workspaceDir=sceneBlocksDir)
remove_soft_deleted_files()
normalizeSceneFilenames(sceneBlocksDir)
syncSceneIndex(dataDir)</pre>

<p>
The key design is not "forbid the model from writing files"; it is "let the model write only the files it should own."
The sandbox lets the model do creative scene editing: create a Markdown scene block, update an existing block, or mark a stale block with soft-delete.
At the same time, <span class="inline">.metadata/</span> (including scene index and checkpoint files), <span class="inline">.backup/</span>, and <span class="inline">persona.md</span> are hidden.
Creative edits happen in L2 scene prose; deterministic code still owns backups, index consistency, filename normalization, and L3 persona promotion.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/scene/scene-extractor.ts</span>: <span class="inline">SceneExtractor.extract</span> orchestrates directory creation, backup, index loading, prompt construction, <span class="inline">runner.run({ workspaceDir: sceneBlocksDir })</span>, cleanup, index sync, and <span class="inline">parsePersonaUpdateSignal</span>.</li>
    <li><span class="inline">src/core/scene/scene-index.ts</span>: <span class="inline">readSceneIndex</span> reads <span class="inline">.metadata/scene_index.json</span>; <span class="inline">syncSceneIndex</span> resynchronizes the index after model writes.</li>
    <li><span class="inline">src/utils/clean-context-runner.ts</span>: defines the tool-enabled runner contract; tools are enabled when the runner is constructed, while the restricted <span class="inline">workspaceDir</span> is supplied on each <span class="inline">run()</span> call.</li>
    <li><span class="inline">src/core/prompts/scene-extraction.ts</span>: constrains allowed scene operations: create, update, soft-delete Markdown scene files, and emit persona update signals.</li>
    <li><span class="inline">src/core/scene/filename-normalizer.ts</span>: converges model-produced scene filenames into normalized names, reducing duplicates and unpredictable paths.</li>
    <li><span class="inline">src/utils/backup.ts</span>: <span class="inline">BackupManager.backupDirectory</span> saves a rollback snapshot before model writes.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  SceneExtractor confines uncertain LLM file edits to <span class="inline">scene_blocks/</span>,
  while <span class="inline">.metadata/</span> (including scene index and checkpoint files), <span class="inline">.backup/</span>, and <span class="inline">persona.md</span> stay hidden.
  The LLM can write scenes; engineering code still owns backups, indexing, filename normalization, soft-delete cleanup, and persona signal parsing.
</div>
""",
}


LESSON_19 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
上一课看到 LLM 只负责写 <span class="inline">scene_blocks/</span>。本课看工程代码如何在沙箱外维护
<span class="inline">.metadata/scene_index.json</span>，再生成可被 <span class="inline">read_file</span> 逐步下钻的 Scene Navigation。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  Scene block 是档案页，scene index 是管理员维护的目录卡，Scene Navigation 是贴在工作台上的索引摘要。
  Agent 先看摘要判断哪页可能相关；需要证据时，再按绝对路径取出那一页，而不是把整柜档案每轮都搬进 prompt。
</div>

<h2>从 Markdown 场景到 recall 导航</h2>
<div class="flow">
  <div class="node"><div class="nt">scene markdown files</div><div class="nd">LLM 在 scene_blocks/ 写出的可读场景</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">parser</div><div class="nd">parseSceneBlock 解析 META</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">scene index JSON</div><div class="nd">工程侧写 .metadata/scene_index.json</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">navigation</div><div class="nd">按 heat 排序并带文件路径</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">recall</div><div class="nd">注入高层索引，按需 read_file</div></div>
</div>

<p>
<span class="inline">syncSceneIndex()</span> 是沙箱边界之后的确定性整理步骤。它扫描
<span class="inline">scene_blocks/*.md</span>，对每个 Markdown scene 调用 <span class="inline">parseSceneBlock</span>
读取 <span class="inline">created</span>、<span class="inline">updated</span>、<span class="inline">summary</span>、
<span class="inline">heat</span> 等 META，并把 <span class="inline">filename</span>、<span class="inline">summary</span>、
<span class="inline">heat</span>、<span class="inline">created</span>、<span class="inline">updated</span> 写入
<span class="inline">.metadata/scene_index.json</span>。这个文件位于 LLM 工作区之外：LLM 可以改场景正文，
但不能伪造目录状态、覆盖 checkpoint，或绕过工程代码的清理与一致性检查。
</p>

<h2>Index file vs Navigation markdown</h2>
<div class="cols">
  <div class="col"><h4>Index file</h4><p><span class="inline">.metadata/scene_index.json</span> 是机器可读状态：每条 <span class="inline">SceneIndexEntry</span> 只包含 <span class="inline">filename</span>、<span class="inline">summary</span>、<span class="inline">heat</span>、<span class="inline">created</span>、<span class="inline">updated</span>。它由 <span class="inline">readSceneIndex</span> 读取、由 <span class="inline">writeSceneIndex</span> 写入、由 <span class="inline">syncSceneIndex</span> 从真实 Markdown 重新生成。</p></div>
  <div class="col"><h4>Navigation markdown</h4><p><span class="inline">generateSceneNavigation()</span> 把索引变成 prompt 友好的 Markdown：热场景排在前面，显示摘要和安全的绝对路径示例，如 <span class="inline">/workspace/agent-memory-data/scene_blocks/payment-debugging.md</span>，方便 agent 用 <span class="inline">read_file</span> 逐步展开细节。</p></div>
</div>

<p>
导航不是要替代场景全文，而是做 progressive disclosure。<span class="inline">generateSceneNavigation()</span>
只按 <span class="inline">heat</span> 降序排序，把热度最高的场景放在前面；每条导航保留文件路径，并显示更新时间，
让 agent 在判断“这条摘要相关”之后再读取完整 Markdown。这样 recall 可以花很少的 token 暴露场景地图，
同时仍保留回到完整 L2 叙事和来源引用的能力。
</p>

<h2>为什么追加到 persona 与 recall context</h2>
<p>
Scene Navigation 会被追加到 persona 和 recall 的系统上下文中，因为 L3 画像与本轮 recall 都需要知道“有哪些可用场景”。
Persona 负责稳定长期倾向，但场景导航告诉 agent：某个长期特征背后有哪些近期活动可查；recall 负责本轮相关性，
导航则让它先看摘要，再用 <span class="inline">read_file</span> 下钻完整证据。注入导航而非全文，可以同时保留可发现性与 prompt budget。
</p>

<h2>备份位置与恢复目的</h2>
<table class="t">
  <tr><th>备份对象</th><th>典型位置</th><th>恢复目的</th></tr>
  <tr><td><span class="inline">scene_blocks/</span> directory</td><td><span class="inline">.backup/scene_blocks/scene_blocks_YYYYMMDD_HHmmss_offset42/</span></td><td>LLM 批量编辑前保存整目录；如果模型写坏多个场景，可恢复到写入前快照。</td></tr>
  <tr><td><span class="inline">persona.md</span> file</td><td><span class="inline">.backup/persona/persona_YYYYMMDD_HHmmss_offset42.md</span></td><td>使用 <span class="inline">backupFile(src, "persona", tag, maxKeep)</span> 在 persona 生成前保存旧版本；其他单文件备份也按传入 category 命名。</td></tr>
  <tr><td>retention cleanup</td><td><span class="inline">.backup/</span> 内按数量保留</td><td><span class="inline">BackupManager</span> 控制保留数量，避免备份无限增长，同时保留最近可恢复点。</td></tr>
</table>

<h2>核心伪代码</h2>
<pre class="code">files = list(scene_blocks/*.md)
entries = [parseSceneBlock(file).meta for file in files]
writeSceneIndex(dataDir, entries)
nav = generateSceneNavigation(entries, dataDir)
appendSystemContext("&lt;scene-navigation&gt;" + nav + "&lt;/scene-navigation&gt;")</pre>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/scene/scene-index.ts</span>：<span class="inline">readSceneIndex</span>、<span class="inline">writeSceneIndex</span> 与 <span class="inline">syncSceneIndex</span> 维护工程侧 scene index。</li>
    <li><span class="inline">src/core/scene/scene-navigation.ts</span>：<span class="inline">generateSceneNavigation</span> 生成带路径的导航，<span class="inline">stripSceneNavigation</span> 防止重复注入旧导航。</li>
    <li><span class="inline">src/core/scene/scene-format.ts</span>：解析 scene Markdown META，是索引从真实场景重建的依据。</li>
    <li><span class="inline">src/utils/backup.ts</span>：目录/文件备份与保留策略，保护 LLM 编辑前后的可恢复性。</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：把 Scene Navigation 注入 recall/persona 相关上下文，让 agent 先看索引再按需读文件。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  LLM 写场景正文；工程代码扫描、解析并写 <span class="inline">.metadata/scene_index.json</span>。
  Scene Navigation 按热度排序，包含安全绝对路径，帮助 agent 用 <span class="inline">read_file</span> 按需下钻。
  备份在 LLM 编辑前创建，导航追加到 persona 与 recall context 中，以低 token 成本保留场景可发现性。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
The previous lesson showed that the LLM writes only <span class="inline">scene_blocks/</span>. This lesson shows how engineering code maintains
<span class="inline">.metadata/scene_index.json</span> outside the sandbox, then generates Scene Navigation that is ready for progressive
<span class="inline">read_file</span> drill-down.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  A scene block is an archive page, the scene index is the catalog maintained by the archivist, and Scene Navigation is the summary pinned to the workbench.
  The agent reads the summary first; when evidence is needed, it opens one page by absolute path instead of loading the whole archive every turn.
</div>

<h2>From Markdown scenes to recall navigation</h2>
<div class="flow">
  <div class="node"><div class="nt">scene markdown files</div><div class="nd">readable scenes written by the LLM in scene_blocks/</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">parser</div><div class="nd">parseSceneBlock reads META</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">scene index JSON</div><div class="nd">engineering writes .metadata/scene_index.json</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">navigation</div><div class="nd">sorted by heat with file paths</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">recall</div><div class="nd">inject index, then read_file on demand</div></div>
</div>

<p>
<span class="inline">syncSceneIndex()</span> is the deterministic cleanup step after the sandbox boundary. It scans
<span class="inline">scene_blocks/*.md</span>, calls <span class="inline">parseSceneBlock</span> for each Markdown scene,
reads META such as <span class="inline">created</span>, <span class="inline">updated</span>,
<span class="inline">summary</span>, and <span class="inline">heat</span>, then writes exactly
<span class="inline">filename</span>, <span class="inline">summary</span>, <span class="inline">heat</span>,
<span class="inline">created</span>, and <span class="inline">updated</span> to <span class="inline">.metadata/scene_index.json</span>. That file lives outside the LLM workspace:
the LLM can edit scene prose, but it cannot forge catalog state, overwrite checkpoints, or bypass engineering cleanup and consistency checks.
</p>

<h2>Index file vs navigation markdown</h2>
<div class="cols">
  <div class="col"><h4>Index file</h4><p><span class="inline">.metadata/scene_index.json</span> is machine-readable state: each <span class="inline">SceneIndexEntry</span> contains only <span class="inline">filename</span>, <span class="inline">summary</span>, <span class="inline">heat</span>, <span class="inline">created</span>, and <span class="inline">updated</span>. <span class="inline">readSceneIndex</span> reads it, <span class="inline">writeSceneIndex</span> writes it, and <span class="inline">syncSceneIndex</span> rebuilds it from real Markdown scenes.</p></div>
  <div class="col"><h4>Navigation markdown</h4><p><span class="inline">generateSceneNavigation()</span> converts the index into prompt-friendly Markdown: hot scenes first, compact summaries, and safe absolute path examples such as <span class="inline">/workspace/agent-memory-data/scene_blocks/payment-debugging.md</span> so the agent can drill down with <span class="inline">read_file</span>.</p></div>
</div>

<p>
Navigation does not replace full scenes; it enables progressive disclosure. <span class="inline">generateSceneNavigation()</span>
sorts only by <span class="inline">heat</span> descending so the hottest scenes appear first. Each entry keeps a file path and displays the update time,
so after the agent decides a summary matters, it can read the full Markdown scene. Recall spends only a small token budget on the scene map
while preserving a path back to complete L2 narrative and source references.
</p>

<h2>Why append it to persona and recall context</h2>
<p>
Scene Navigation is appended to persona and recall system context because both L3 persona and turn-level recall need to know which scenes are available.
Persona stores stable long-term tendencies, but navigation tells the agent which recent activities can support or challenge a trait. Recall chooses what matters now,
and navigation lets it inspect summaries first, then use <span class="inline">read_file</span> for full evidence. Injecting navigation instead of full scenes keeps discoverability without spending the whole prompt budget.
</p>

<h2>Backup locations and recovery purpose</h2>
<table class="t">
  <tr><th>Backup target</th><th>Typical location</th><th>Recovery purpose</th></tr>
  <tr><td><span class="inline">scene_blocks/</span> directory</td><td><span class="inline">.backup/scene_blocks/scene_blocks_YYYYMMDD_HHmmss_offset42/</span></td><td>Snapshot the whole directory before LLM batch edits; restore if the model corrupts multiple scenes.</td></tr>
  <tr><td><span class="inline">persona.md</span> file</td><td><span class="inline">.backup/persona/persona_YYYYMMDD_HHmmss_offset42.md</span></td><td><span class="inline">backupFile(src, "persona", tag, maxKeep)</span> saves the old persona before generation; other single-file backups use the provided category name.</td></tr>
  <tr><td>retention cleanup</td><td>inside <span class="inline">.backup/</span> by count</td><td><span class="inline">BackupManager</span> limits retained backups so snapshots do not grow forever while recent restore points remain.</td></tr>
</table>

<h2>Core pseudocode</h2>
<pre class="code">files = list(scene_blocks/*.md)
entries = [parseSceneBlock(file).meta for file in files]
writeSceneIndex(dataDir, entries)
nav = generateSceneNavigation(entries, dataDir)
appendSystemContext("&lt;scene-navigation&gt;" + nav + "&lt;/scene-navigation&gt;")</pre>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/scene/scene-index.ts</span>: <span class="inline">readSceneIndex</span>, <span class="inline">writeSceneIndex</span>, and <span class="inline">syncSceneIndex</span> maintain the engineering-owned scene index.</li>
    <li><span class="inline">src/core/scene/scene-navigation.ts</span>: <span class="inline">generateSceneNavigation</span> creates path-bearing navigation, while <span class="inline">stripSceneNavigation</span> prevents reinjecting stale navigation.</li>
    <li><span class="inline">src/core/scene/scene-format.ts</span>: parses scene Markdown META, the basis for rebuilding the index from real scenes.</li>
    <li><span class="inline">src/utils/backup.ts</span>: directory/file backups and retention protect recoverability before and after LLM edits.</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: injects Scene Navigation into recall/persona-related context so the agent sees the index before reading files on demand.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The LLM writes scene prose; engineering code scans, parses, and writes <span class="inline">.metadata/scene_index.json</span>.
  Scene Navigation is sorted by heat and includes safe absolute paths so the agent can drill down with <span class="inline">read_file</span> only when needed.
  Backups happen before LLM edits, and navigation is appended to persona and recall context to preserve scene discoverability at low token cost.
</div>
""",
}


LESSON_20 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
PersonaGenerator 把 L2 scene blocks 提炼成 L3 <span class="inline">persona.md</span>：第一次生成建立稳定画像，
后续增量更新只优先阅读自上次 persona checkpoint 之后变化的场景，同时保留旧画像中的稳定信息。
</p>

<div class="card analogy">
  <div class="tag">🧑‍🏫 生活类比</div>
  L2 场景像一叠项目日志，L3 persona 像交给新同事的长期协作简介。第一次要读足够多日志形成简介；
  之后不应每次重写整个人设，而是查看最近新增/改动的日志，在保留稳定结论的基础上修订简介。
</div>

<h2>L3 不是证据层，而是注入上下文</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">L1</span><span class="name">evidence atoms</span></div><div class="ld">细粒度事实与 <span class="inline">source_message_ids</span>，负责可搜索、可追溯。</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">L2</span><span class="name">scene blocks</span></div><div class="ld">把相关 L1 聚合成活动叙事、时间线、摘要和场景导航。</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">L3</span><span class="name">persona.md</span></div><div class="ld">稳定偏好、长期目标、协作方式与背景摘要，用于下一轮注入。</div></div>
</div>

<div class="card warn">
  <div class="tag">⚠️ 设计警告</div>
  persona 是被注入给 agent 的高层上下文，不是不可变的事实来源。遇到冲突或需要审计时，应沿
  Scene Navigation 回到 L2 场景，再下钻到 L1/L0 证据，而不是把 <span class="inline">persona.md</span> 当成最终真相。
</div>

<h2>第一次生成 vs 增量更新</h2>
<div class="cols">
  <div class="col"><h4>First generation</h4><p>当没有已有 persona，prompt 输入主要是工程已预加载的可用场景内容、场景总数/变化场景数和生成规则；scene index 由工程代码读取并汇总成这些输入。模型需要从 L2 场景内容中总结长期偏好、工作方式、项目背景和稳定约束，写出一个可读的 <span class="inline">persona.md</span>。</p></div>
  <div class="col"><h4>Incremental update</h4><p>当已有 persona，工程代码先用 <span class="inline">stripSceneNavigation</span> 去掉旧导航，再把现有画像与变化场景一起交给 prompt。模型应保留仍成立的稳定信息，只吸收新证据支持的变化。</p></div>
</div>

<p>
增量模式的关键游标是 <span class="inline">last_persona_time</span>。PersonaGenerator 读取
<span class="inline">.metadata/recall_checkpoint.json</span> 后，用 scene index 里的 <span class="inline">updated</span>
过滤出“自上次 persona 生成后变化过”的场景。这样 L3 不需要每轮重扫所有场景，也不会因为一次局部活动把长期画像全部重写。
</p>

<h2>Persona generation pipeline boundaries</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>触发决策在外层</h4><p><span class="inline">PersonaTrigger.shouldGenerate()</span> 先读取 checkpoint、persona 状态和场景文件，决定本轮是否进入 L3；这个判断不属于 <span class="inline">generateLocalPersona()</span>。</p><div class="mono">trigger.shouldGenerate()</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>可选拉取远端 profile</h4><p>如果启用了支持 profile 的 store，pipeline 在生成前把远端 L2/L3 拉到本地，建立后续同步的 baseline。</p><div class="mono">pullProfilesToLocal()</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>本地生成只负责写 persona</h4><p><span class="inline">generateLocalPersona()</span> 读取 checkpoint、加载旧 persona、按 <span class="inline">scene.updated &gt; last_persona_time</span> 选择场景、备份、运行 LLM、清洗并追加 Scene Navigation；它返回是否成功更新，但不推进 checkpoint。</p><div class="mono">generator.generateLocalPersona(reason)</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>可选同步 profile/storage</h4><p>本地写入成功后，pipeline 可把变化后的 L2 scenes 和 L3 persona 同步回 profile store；这是存储同步，不是运行时注入。</p><div class="mono">syncLocalProfilesToStore()</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>成功后才推进 checkpoint</h4><p>外层 L3 runner 在生成与可选同步成功后调用 <span class="inline">markPersonaGenerated</span>；兼容包装 <span class="inline">generate()</span> 也会在 <span class="inline">generateLocalPersona()</span> 成功后推进。</p><div class="mono">markPersonaGenerated()</div></div></div>
</div>

<h2>工程代码与 LLM 的边界</h2>
<div class="cols">
  <div class="col"><h4>Engineering pipeline</h4><p>负责触发判断、profile 拉取/同步、checkpoint 推进，以及 <span class="inline">generateLocalPersona()</span> 内部的 scene index 过滤、备份、runner 工作区、后处理和 Scene Navigation 追加。checkpoint 只能在成功写入后由外层推进。</p></div>
  <div class="col"><h4>LLM writer</h4><p>负责根据 first 或 incremental prompt 改写 <span class="inline">persona.md</span> 正文。它可以整理表达，但不拥有触发决策、checkpoint、索引或“哪些场景算变化”的判断。</p></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">decision = PersonaTrigger(dataDir).shouldGenerate()
if decision.should:
    baseline = pullProfilesToLocal(dataDir)  # optional profile store
    updated = generator.generateLocalPersona(decision.reason)
    if updated:
        syncLocalProfilesToStore(dataDir, baseline)  # optional
        checkpoint.markPersonaGenerated(total_processed)</pre>

<p>
注意边界：<span class="inline">generateLocalPersona()</span> 会读 checkpoint 来选择变化场景，但不会推进它。只有 <span class="inline">persona.md</span> 写入、清洗和导航追加都成功后，外层 runner 或兼容包装 <span class="inline">generate()</span> 才能前进 checkpoint。否则下一轮仍会看到同一批变化场景，避免“画像没有落盘但游标已经跳过”的数据丢失。
</p>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>：<span class="inline">generateLocalPersona</span> 读取 checkpoint、选择场景、备份、LLM 写入和后处理但不推进 checkpoint；兼容包装 <span class="inline">generate</span> 会在成功后推进。</li>
    <li><span class="inline">src/core/prompts/persona-generation.ts</span>：first 与 incremental prompt 输入不同；prompt 接收场景内容、统计计数和规则，增量模式还带已有 persona。</li>
    <li><span class="inline">src/core/persona/persona-trigger.ts</span>：<span class="inline">PersonaTrigger.shouldGenerate()</span> 在 pipeline 中先于生成执行，封装是否触发 persona 更新的决策。</li>
    <li><span class="inline">src/core/profile/profile-sync.ts</span>：说明 L2/L3 profile 的拉取、校验、本地落盘和同步回存储路径。</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>：运行时读取 persona 与 Scene Navigation，并把它们注入 agent context 供消费。</li>
    <li><span class="inline">src/utils/pipeline-factory.ts</span>：L3 runner 串起 trigger、<span class="inline">generateLocalPersona</span>、可选 profile sync，以及成功后的 <span class="inline">markPersonaGenerated</span>。</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>：保存 <span class="inline">last_persona_time</span>，并通过 <span class="inline">markPersonaGenerated</span> 推进 persona checkpoint。</li>
    <li><span class="inline">src/utils/sanitize.ts</span>：<span class="inline">escapeXmlTags</span> 清洗 persona 文本，避免注入型标签进入后续上下文。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  PersonaGenerator 把 L2 场景提炼为稳定 L3 persona；第一次生成根据可用场景内容和统计计数建立画像，增量更新读取变化场景并保留已有稳定信息。
  触发决策发生在生成前；<span class="inline">generateLocalPersona()</span> 只负责本地写入与后处理，profile 同步和 checkpoint 推进由外层成功路径完成。persona 是注入上下文，不是不可变事实源。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
PersonaGenerator turns L2 scene blocks into the L3 <span class="inline">persona.md</span>: first generation builds the stable profile,
while later incremental updates prioritize scenes changed since the last persona checkpoint and preserve stable facts from the existing profile.
</p>

<div class="card analogy">
  <div class="tag">🧑‍🏫 Analogy</div>
  L2 scenes are project journals; L3 persona is the long-term collaboration brief you give to a new teammate. The first brief needs enough journals.
  Later updates should not rewrite the entire identity every time; they should read recent/changed journals and revise the brief while keeping stable conclusions.
</div>

<h2>L3 is injected context, not the evidence layer</h2>
<div class="layers">
  <div class="layer l-core"><div class="lh"><span class="badge">L1</span><span class="name">evidence atoms</span></div><div class="ld">Fine-grained facts and <span class="inline">source_message_ids</span> for search and traceability.</div></div>
  <div class="layer l-main"><div class="lh"><span class="badge">L2</span><span class="name">scene blocks</span></div><div class="ld">Activity narratives, timelines, summaries, and scene navigation built from related L1 records.</div></div>
  <div class="layer l-app"><div class="lh"><span class="badge">L3</span><span class="name">persona.md</span></div><div class="ld">Stable preferences, long-term goals, collaboration style, and background summary for future injection.</div></div>
</div>

<div class="card warn">
  <div class="tag">⚠️ Design warning</div>
  Persona is high-level context injected into the agent, not an immutable source of truth. When claims conflict or need audit,
  follow Scene Navigation back to L2 scenes, then drill down to L1/L0 evidence instead of treating <span class="inline">persona.md</span> as final truth.
</div>

<h2>First generation vs incremental update</h2>
<div class="cols">
  <div class="col"><h4>First generation</h4><p>When there is no existing persona, the prompt primarily receives preloaded available scene contents, scene counts/changed-scene counts, and generation rules; engineering code reads the scene index and summarizes it into those inputs. The model summarizes long-term preferences, work style, project background, and stable constraints from L2 scene content into a readable <span class="inline">persona.md</span>.</p></div>
  <div class="col"><h4>Incremental update</h4><p>When persona already exists, code first removes old navigation with <span class="inline">stripSceneNavigation</span>, then sends the existing profile plus changed scenes to the prompt. The model should keep still-valid stable information and absorb only changes supported by new evidence.</p></div>
</div>

<p>
The key cursor for incremental mode is <span class="inline">last_persona_time</span>. After reading
<span class="inline">.metadata/recall_checkpoint.json</span>, PersonaGenerator filters the scene index by
<span class="inline">updated</span> to find scenes changed since the last persona generation. L3 therefore avoids rescanning every scene on every run,
and a local activity does not cause the whole long-term profile to be rewritten.
</p>

<h2>Persona generation pipeline boundaries</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Trigger decision happens outside</h4><p><span class="inline">PersonaTrigger.shouldGenerate()</span> reads checkpoint, persona state, and scene files before L3 generation begins; that decision is not part of <span class="inline">generateLocalPersona()</span>.</p><div class="mono">trigger.shouldGenerate()</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Optionally pull remote profiles</h4><p>If a profile-capable store is enabled, the pipeline pulls remote L2/L3 profiles to local storage before generation and records a baseline for later sync.</p><div class="mono">pullProfilesToLocal()</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Local generation writes persona only</h4><p><span class="inline">generateLocalPersona()</span> reads checkpoint, loads old persona, selects scenes with <span class="inline">scene.updated &gt; last_persona_time</span>, backs up, runs the LLM, sanitizes, and appends Scene Navigation. It returns whether an update succeeded, but it does not advance the checkpoint.</p><div class="mono">generator.generateLocalPersona(reason)</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Optionally sync profile storage</h4><p>After a successful local write, the pipeline may sync changed L2 scenes and L3 persona back to the profile store. This is storage synchronization, not runtime injection.</p><div class="mono">syncLocalProfilesToStore()</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>Advance checkpoint only after success</h4><p>The outer L3 runner calls <span class="inline">markPersonaGenerated</span> after generation and optional sync succeed; the compatibility wrapper <span class="inline">generate()</span> also advances after <span class="inline">generateLocalPersona()</span> succeeds.</p><div class="mono">markPersonaGenerated()</div></div></div>
</div>

<h2>Engineering code vs LLM boundary</h2>
<div class="cols">
  <div class="col"><h4>Engineering pipeline</h4><p>Owns trigger decisions, profile pull/sync, checkpoint advancement, and the <span class="inline">generateLocalPersona()</span> internals: scene-index filtering, backups, runner workspace, post-processing, and Scene Navigation appending. The checkpoint advances only from the outer success path.</p></div>
  <div class="col"><h4>LLM writer</h4><p>Uses the first or incremental prompt to rewrite the body of <span class="inline">persona.md</span>. It may organize prose, but it does not own trigger decisions, checkpoints, indexes, or the decision about which scenes count as changed.</p></div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">decision = PersonaTrigger(dataDir).shouldGenerate()
if decision.should:
    baseline = pullProfilesToLocal(dataDir)  # optional profile store
    updated = generator.generateLocalPersona(decision.reason)
    if updated:
        syncLocalProfilesToStore(dataDir, baseline)  # optional
        checkpoint.markPersonaGenerated(total_processed)</pre>

<p>
The boundary matters: <span class="inline">generateLocalPersona()</span> reads checkpoint state to select changed scenes, but it does not advance that state. Only after <span class="inline">persona.md</span> has been written, sanitized, and given fresh navigation may the outer runner or compatibility wrapper <span class="inline">generate()</span> advance the checkpoint. If writing fails, the next run still sees the same changed scenes, avoiding data loss where the profile was not persisted but the cursor skipped ahead.
</p>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/core/persona/persona-generator.ts</span>: <span class="inline">generateLocalPersona</span> reads checkpoint state, selects scenes, backs up, runs the LLM, and post-processes without advancing the checkpoint; compatibility wrapper <span class="inline">generate</span> advances after success.</li>
    <li><span class="inline">src/core/prompts/persona-generation.ts</span>: first and incremental prompt inputs differ; prompts receive scene contents, statistical counts, and rules, while incremental mode also includes existing persona.</li>
    <li><span class="inline">src/core/persona/persona-trigger.ts</span>: <span class="inline">PersonaTrigger.shouldGenerate()</span> runs before generation in the pipeline and decides whether a persona update should run.</li>
    <li><span class="inline">src/core/profile/profile-sync.ts</span>: shows L2/L3 profile pull, validation, local storage, and sync-back paths.</li>
    <li><span class="inline">src/core/hooks/auto-recall.ts</span>: runtime reads persona and Scene Navigation, then injects them into agent context for consumption.</li>
    <li><span class="inline">src/utils/pipeline-factory.ts</span>: the L3 runner connects trigger, <span class="inline">generateLocalPersona</span>, optional profile sync, and success-only <span class="inline">markPersonaGenerated</span>.</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>: stores <span class="inline">last_persona_time</span> and exposes <span class="inline">markPersonaGenerated</span> for advancing persona checkpoint state.</li>
    <li><span class="inline">src/utils/sanitize.ts</span>: <span class="inline">escapeXmlTags</span> sanitizes persona text so injection-like tags do not enter later context.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  PersonaGenerator distills L2 scenes into stable L3 persona; first generation builds from available scene contents and counts, while incremental updates read changed scenes and preserve existing stable information.
  Trigger decisions happen before generation; <span class="inline">generateLocalPersona()</span> owns local writing and post-processing only, while profile sync and checkpoint advancement happen in the outer success path. Persona is injected context, not an immutable source of truth.
</div>
""",
}


LESSON_21 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
MemoryPipelineManager 不在每条消息后立刻跑完整 L1/L2/L3。它把工作分层调度：L1 用阈值、空闲和 shutdown flush 收集批次；
L2 在 L1 成功后按 delay/min/max/active-window 触发场景整理；L3 则在 L2 完成后进入全局串行队列，并用 pending 标记合并重复触发。
</p>

<div class="card analogy">
  <div class="tag">⏱️ 生活类比</div>
  L1 像等你“说完一小段”才记笔记：说够阈值就立刻记，没说够就等空闲。L2 像项目复盘：新笔记来了可以把复盘提前，
  但不能因为你一直聊天而无限推迟。L3 像全公司共享的人物画像，只允许一个编辑一次更新，避免多人同时改同一份 brief。
</div>

<h2>一次活动如何穿过三层调度</h2>
<div class="timeline">
  <div class="lane"><div class="lane-label">conversation</div><div class="tslot">turn 1</div><div class="tslot">turn 2</div><div class="tslot now">turn N</div><div class="tslot span">active session</div></div>
  <div class="lane"><div class="lane-label">L1</div><div class="tslot">reset idle</div><div class="tslot">reset idle</div><div class="tslot now">threshold/idle</div><div class="tslot">enqueue L1</div></div>
  <div class="lane"><div class="lane-label">L2</div><div class="tslot">lastL2 + min</div><div class="tslot now">now + delay</div><div class="tslot span">downward-only fire time</div><div class="tslot">enqueue L2</div></div>
  <div class="lane"><div class="lane-label">L3</div><div class="tslot">L2 success</div><div class="tslot now">global enqueue</div><div class="tslot span">pending dedup while running</div></div>
</div>

<p>
入口是 <span class="inline">notifyConversation(sessionKey, messages)</span>。它先把消息追加到 session buffer，
增加 <span class="inline">conversation_count</span> 并刷新 <span class="inline">last_active_time</span>。
如果计数达到 warm-up 或稳态阈值，就直接 <span class="inline">enqueueL1</span>；否则重置 L1 idle timer。
这让活跃对话按批处理，低频对话也能在空闲后被捕获。
</p>

<h2>L1 resettable timer vs L2 downward-only timer</h2>
<div class="cols">
  <div class="col"><h4>L1 resettable idle</h4><p>每次未达到阈值的新对话都会重新 <span class="inline">schedule()</span> idle timer：旧倒计时取消，新倒计时从当前时刻重新开始。它的目标是 debounce：等用户停下来，再把残余 buffer 交给 L1。</p></div>
  <div class="col"><h4>L2 downward-only</h4><p>L1 成功后计算 <span class="inline">max(now + delay, lastL2 + minInterval)</span>，再用 <span class="inline">tryAdvanceTo()</span>。如果新时间更早，就提前；如果更晚，就保持原计划，避免活跃会话一直把 L2 往后推。</p></div>
</div>

<p>
L2 还承担两个保护：L2 调度路径（包括成功完成以及 retry/skip 收口）会用 <span class="inline">maxInterval</span> 重新设定下一次巡检，保证活跃 session 即使没有新 L1 也会定期整理；
周期性的 maxInterval 定时器触发时检查 <span class="inline">sessionActiveWindowHours</span>，冷 session 不再继续轮询，等下一次 L1 成功再重新唤醒。
因此 downward-only 不是“越快越好”，而是在 delay-after-L1 的响应性、minInterval 的限速和 maxInterval 的兜底之间取平衡。
</p>

<h2>L3 为什么全局串行</h2>
<p>
L2 是按 session 整理场景，L3 persona 却汇总所有场景并写同一个高层画像。多个 session 同时完成 L2 时，如果并发生成 persona，
它们会读取相近但不同步的 scene/persona 状态，最后写入者可能覆盖先完成者。为避免这种全局写冲突，
<span class="inline">enqueueL3</span> 使用一个 <span class="inline">SerialQueue("L3")</span>、一个 <span class="inline">l3Running</span>
和一个 <span class="inline">l3Pending</span>：运行中收到新触发只标 pending，当前 L3 结束后最多再补跑一次。
</p>

<h2>核心伪代码</h2>
<pre class="code">notifyConversation(sessionKey, messages):
    buffer_messages(sessionKey, messages)
    if conversation_count &gt;= effective_threshold:
        enqueueL1(sessionKey)
    else:
        reset_l1_idle_timer(sessionKey)

on_l1_success(sessionKey):
    if destroyed:
        persist_pipeline_state_for_recovery()
        return
    advance_l2_timer_earlier(max(now + delay, lastL2 + minInterval))

on_l2_success():
    if destroyed:
        persist_pipeline_state_for_recovery()
        return
    if l3Running:
        l3Pending = true
    else:
        enqueue_global_l3()

destroy():
    destroyed = true
    cancel_timers_and_flush_buffered_l1_when_safe()
    await_existing_queues_to_drain()
    persist_pipeline_state_for_recovery()</pre>

<h2>Shutdown flush 顺序</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>停止接收新工作</h4><p><span class="inline">destroyed</span> 先置为 true；从这一刻起，<span class="inline">advanceL2Timer()</span> 和 <span class="inline">triggerL3()</span> 都会直接返回，不再安排新的 L2/L3。</p><div class="mono">destroyed = true</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>flush L1 idle</h4><p>取消 L1 idle timer；如果 session 还有 buffered messages，只在安全时用 <span class="inline">enqueueL1(..., "flush")</span> 收尾。</p><div class="mono">cancel idle -&gt; optional L1 flush</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>等待已入队 L1 drain</h4><p>等待 L1 queue 清空；shutdown 期间 L1 成功不会再推进新的 L2 timer，未完成的整理意图留在状态里。</p><div class="mono">await l1Queue.onIdle()</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>drain 已存在的 L2/L3</h4><p>只等待已经在队列中的 L2/L3 工作完成；不会因为 flush 后的 L1 或 L2 再创建新的 L2 timer 或 L3 run。</p><div class="mono">drain queued L2/L3 only</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>持久化状态供恢复</h4><p>无论 flush/drain 成败都保存 <span class="inline">PipelineSessionState</span>，保留 pending 计数与时间戳，便于下次启动恢复未整理的工作。</p><div class="mono">persist state -&gt; recover later</div></div></div>
</div>

<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li><span class="inline">src/utils/pipeline-manager.ts</span>：<span class="inline">notifyConversation</span>、<span class="inline">enqueueL1</span>、<span class="inline">enqueueL2</span>、<span class="inline">enqueueL3</span> 与 <span class="inline">destroy</span> 串起 L1/L2/L3 调度。</li>
    <li><span class="inline">src/utils/managed-timer.ts</span>：<span class="inline">schedule()</span> 实现 resettable timer；<span class="inline">tryAdvanceTo()</span> 实现只能提前不能推迟的 downward-only timer。</li>
    <li><span class="inline">src/utils/serial-queue.ts</span>：L1、L2、L3 都用 concurrency=1 的 FIFO 队列；L3 还在队列外用 <span class="inline">l3Running</span>/<span class="inline">l3Pending</span> 去重。</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>：<span class="inline">PipelineSessionState</span> 保存 <span class="inline">conversation_count</span>、<span class="inline">last_active_time</span>、<span class="inline">last_extraction_updated_time</span>、<span class="inline">l2_pending_l1_count</span>、<span class="inline">l2_last_extraction_time</span> 与 warm-up threshold。</li>
    <li><span class="inline">src/core/persona/persona-trigger.ts</span>：L3 runner 内部再根据显式请求、冷启动、恢复、首次场景和阈值决定是否真正生成 persona。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  L1 的 resettable idle 解决“用户还在说话时先等等”；L2 的 downward-only timer 解决“新 L1 可提前整理，但不能把整理无限推迟”；
  L3 的全局串行队列解决“所有 session 共享同一份 persona 写入面”。Shutdown 时先进入 destroyed 状态，只 drain/flush 合适的已挂起工作并持久化 state；新的 L2/L3 调度留到恢复后处理。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
MemoryPipelineManager does not run the full L1/L2/L3 stack after every message. It schedules work by layer: L1 batches by threshold, idle, and shutdown flush;
L2 consolidates scenes after successful L1 with delay/min/max/active-window rules; L3 enters a global serial queue after L2 and deduplicates repeated triggers with a pending flag.
</p>

<div class="card analogy">
  <div class="tag">⏱️ Analogy</div>
  L1 waits until you have "said a small chunk" before taking notes: enough turns trigger immediately, otherwise idle time catches the remainder.
  L2 is the project review: new notes may pull the review earlier, but continuous chatting must not postpone it forever.
  L3 is the shared company brief about a person, so only one editor should update it at a time.
</div>

<h2>How one activity moves through three schedulers</h2>
<div class="timeline">
  <div class="lane"><div class="lane-label">conversation</div><div class="tslot">turn 1</div><div class="tslot">turn 2</div><div class="tslot now">turn N</div><div class="tslot span">active session</div></div>
  <div class="lane"><div class="lane-label">L1</div><div class="tslot">reset idle</div><div class="tslot">reset idle</div><div class="tslot now">threshold/idle</div><div class="tslot">enqueue L1</div></div>
  <div class="lane"><div class="lane-label">L2</div><div class="tslot">lastL2 + min</div><div class="tslot now">now + delay</div><div class="tslot span">downward-only fire time</div><div class="tslot">enqueue L2</div></div>
  <div class="lane"><div class="lane-label">L3</div><div class="tslot">L2 success</div><div class="tslot now">global enqueue</div><div class="tslot span">pending dedup while running</div></div>
</div>

<p>
The entry point is <span class="inline">notifyConversation(sessionKey, messages)</span>. It appends messages to the session buffer,
increments <span class="inline">conversation_count</span>, and refreshes <span class="inline">last_active_time</span>.
If the count reaches the warm-up or steady-state threshold, it calls <span class="inline">enqueueL1</span>; otherwise it resets the L1 idle timer.
That batches active chats while still capturing low-frequency chats after they go idle.
</p>

<h2>L1 resettable timer vs L2 downward-only timer</h2>
<div class="cols">
  <div class="col"><h4>L1 resettable idle</h4><p>Every below-threshold conversation calls <span class="inline">schedule()</span> again: the old countdown is cancelled and a new countdown starts from now. Its goal is debounce: wait until the user stops, then send the residual buffer to L1.</p></div>
  <div class="col"><h4>L2 downward-only</h4><p>After L1 succeeds, code computes <span class="inline">max(now + delay, lastL2 + minInterval)</span> and calls <span class="inline">tryAdvanceTo()</span>. If the new time is earlier, it moves earlier; if it is later, the old plan remains, so active sessions cannot keep pushing L2 back.</p></div>
</div>

<p>
L2 also has two protections: L2 scheduling paths, including successful runs and retry/skip exits, use <span class="inline">maxInterval</span> to arm the next poll so active sessions are periodically consolidated even without fresh L1;
when the periodic maxInterval timer fires, <span class="inline">sessionActiveWindowHours</span> stops polling cold sessions until the next successful L1 wakes them again.
So downward-only does not mean "always sooner"; it balances delay-after-L1 responsiveness, minInterval rate limiting, and the maxInterval guarantee.
</p>

<h2>Why L3 is globally serialized</h2>
<p>
L2 organizes scenes per session, but L3 persona summarizes all scenes and writes one high-level profile. If several sessions finish L2 and generate persona concurrently,
they may read nearby but inconsistent scene/persona states, and the last writer can overwrite the earlier result. To avoid this global write conflict,
<span class="inline">enqueueL3</span> uses one <span class="inline">SerialQueue("L3")</span>, one <span class="inline">l3Running</span>,
and one <span class="inline">l3Pending</span>: triggers that arrive during a run only mark pending, then the current L3 run is followed by at most one catch-up run.
</p>

<h2>Core pseudocode</h2>
<pre class="code">notifyConversation(sessionKey, messages):
    buffer_messages(sessionKey, messages)
    if conversation_count &gt;= effective_threshold:
        enqueueL1(sessionKey)
    else:
        reset_l1_idle_timer(sessionKey)

on_l1_success(sessionKey):
    if destroyed:
        persist_pipeline_state_for_recovery()
        return
    advance_l2_timer_earlier(max(now + delay, lastL2 + minInterval))

on_l2_success():
    if destroyed:
        persist_pipeline_state_for_recovery()
        return
    if l3Running:
        l3Pending = true
    else:
        enqueue_global_l3()

destroy():
    destroyed = true
    cancel_timers_and_flush_buffered_l1_when_safe()
    await_existing_queues_to_drain()
    persist_pipeline_state_for_recovery()</pre>

<h2>Shutdown flush order</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Stop accepting new work</h4><p><span class="inline">destroyed</span> is set to true first; from then on, <span class="inline">advanceL2Timer()</span> and <span class="inline">triggerL3()</span> return without scheduling fresh L2/L3 work.</p><div class="mono">destroyed = true</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Flush L1 idle</h4><p>Cancel L1 idle timers; if a session still has buffered messages, finish it with <span class="inline">enqueueL1(..., "flush")</span> only when safe.</p><div class="mono">cancel idle -&gt; optional L1 flush</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Wait for queued L1 to drain</h4><p>Wait until the L1 queue is idle; during shutdown, successful L1 does not advance a new L2 timer, so unfinished consolidation intent remains in state.</p><div class="mono">await l1Queue.onIdle()</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Drain existing L2/L3</h4><p>Only wait for L2/L3 work that was already queued; flushed L1 or completed L2 will not create a new L2 timer or L3 run.</p><div class="mono">drain queued L2/L3 only</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>Persist state for recovery</h4><p>Persist <span class="inline">PipelineSessionState</span> whether flush/drain succeeded or failed, preserving pending counts and timestamps so startup can recover unfinished work.</p><div class="mono">persist state -&gt; recover later</div></div></div>
</div>

<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li><span class="inline">src/utils/pipeline-manager.ts</span>: <span class="inline">notifyConversation</span>, <span class="inline">enqueueL1</span>, <span class="inline">enqueueL2</span>, <span class="inline">enqueueL3</span>, and <span class="inline">destroy</span> connect L1/L2/L3 scheduling.</li>
    <li><span class="inline">src/utils/managed-timer.ts</span>: <span class="inline">schedule()</span> implements resettable timers; <span class="inline">tryAdvanceTo()</span> implements the downward-only timer that can move earlier but not later.</li>
    <li><span class="inline">src/utils/serial-queue.ts</span>: L1, L2, and L3 all use FIFO queues with concurrency=1; L3 also deduplicates outside the queue with <span class="inline">l3Running</span>/<span class="inline">l3Pending</span>.</li>
    <li><span class="inline">src/utils/checkpoint.ts</span>: <span class="inline">PipelineSessionState</span> stores <span class="inline">conversation_count</span>, <span class="inline">last_active_time</span>, <span class="inline">last_extraction_updated_time</span>, <span class="inline">l2_pending_l1_count</span>, <span class="inline">l2_last_extraction_time</span>, and warm-up threshold.</li>
    <li><span class="inline">src/core/persona/persona-trigger.ts</span>: inside the L3 runner, explicit request, cold start, recovery, first scene, and threshold conditions decide whether persona should actually be generated.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  L1's resettable idle answers "wait while the user is still talking"; L2's downward-only timer answers "fresh L1 may pull consolidation earlier, but not postpone it forever";
  L3's global serial queue answers "all sessions share one persona write surface." Shutdown first enters the destroyed state, drains/flushes appropriate pending work, and persists state; fresh L2/L3 scheduling is left for recovery after restart.
</div>
""",
}
