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
