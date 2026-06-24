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
