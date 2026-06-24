"""Part 8 lesson content: Ecosystem, operations, debugging, and glossary."""


LESSON_32 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Hermes / direct Gateway 用户走的是外部 HTTP 路径：请求先进入 <span class="inline">src/gateway/server.ts</span>，再由
<span class="inline">src/gateway/config.ts</span> 解析监听地址、CORS 与鉴权等 Gateway 开关；payload 大小和 HTTP request timeout 则应由部署边界或反向代理兜住。通过这些守卫后，Gateway 暴露的 memory 端点才会
把请求交给 standalone host adapter，最后进入宿主无关的 <span class="inline">TdaiCore</span>。这条路径和 OpenClaw 插件的进程内 hooks 不同：它多了一层网络边界，也多了一组运维责任。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  OpenClaw 进程内插件像办公室里的内部柜台：同楼层的人按内部流程办事。Hermes Gateway 像对外服务窗口：有人从门外递交表单，保安先检查入口、名单、证件、包裹大小和等待时间，再把合规请求转给内部柜台。
</div>

<h2>一条外部 HTTP 调用怎样进入记忆核心</h2>
<div class="flow">
  <div class="node"><div class="nt">Hermes client</div><div class="nd">provider 或直接调用者只知道受控 Gateway 地址与占位 token。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Gateway HTTP route</div><div class="nd"><span class="inline">server.ts</span> 创建 HTTP server，注册 <span class="inline">GET /health</span> 与 memory POST routes。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">config/security guard</div><div class="nd"><span class="inline">config.ts</span> 解析 host、port、CORS origin 与 auth；body / HTTP timeout 交给部署边界。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">standalone adapter</div><div class="nd">把 HTTP 请求转换为 host-neutral 上下文、日志与 LLM 边界。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">复用 capture、recall、search、store 与 pipeline facade。</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">memory layers</div><div class="nd">L0/L1/L2/L3、SQLite / VectorDB、Context Offload 按配置工作。</div></div>
</div>

<h2>server.ts：路由不是核心，边界才是重点</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>create server</h4><p>Gateway 先创建 HTTP server，并把 route table、request parser、错误响应和关闭流程放在同一个入口附近，便于运维检查。</p><div class="mono">createHttpServer(config)</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>public health</h4><p><span class="inline">GET /health</span> 绕过鉴权，用于 liveness / readiness，只返回 <span class="inline">ok</span> 或 <span class="inline">degraded</span> 这类安全状态；Gateway 没有单独的 status route。</p><div class="mono">GET /health -&gt; ok | degraded</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>validate memory request</h4><p>受保护的 memory surface 是 <span class="inline">POST /recall</span>、<span class="inline">/capture</span>、<span class="inline">/search/memories</span>、<span class="inline">/search/conversations</span>、<span class="inline">/session/end</span> 和 <span class="inline">/seed</span>；委托前检查方法、路径、content-type、JSON schema、CORS 和可选 bearer auth。</p><div class="mono">reject early before TdaiCore</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>delegate safely</h4><p>通过 standalone host adapter 构造宿主上下文，让 HTTP 层不直接知道 OpenClaw hook 细节，也不把外部请求对象泄漏到核心。</p><div class="mono">HTTP request -&gt; HostAdapter -&gt; TdaiCore</div></div></div>
</div>

<h2>OpenClaw 进程内路径 vs Hermes/Gateway 外部路径</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw in-process plugin path</h4><p>OpenClaw 启动插件，插件在同一宿主生命周期内注册 hooks 和 tools。before_prompt_build、agent_end、after_tool_call 等事件直接调用 adapter，再进入 <span class="inline">TdaiCore</span>。主要风险是宿主配置、hook 顺序、数据目录和 pipeline 资源隔离。</p></div>
  <div class="col"><h4>Hermes / Gateway external HTTP path</h4><p>Hermes provider 或直接调用方通过 HTTP 调用 Gateway。网络入口必须先处理绑定地址、CORS、鉴权和日志脱敏；body limit 与 HTTP request timeout 应在反向代理、平台或客户端边界处理。主要风险是暴露面、滥用、跨源访问和错误日志泄密。</p></div>
  <div class="col"><h4>共同核心</h4><p>两条路径最终都应收敛到 host-neutral <span class="inline">TdaiCore</span>：记忆层、搜索、召回、存储后端和调度逻辑不应因为调用来自 hook 还是 HTTP 而分叉。</p></div>
</div>

<h2>Gateway 配置与部署边界要分清</h2>
<table class="t">
  <tr><th>Control</th><th>Default idea</th><th>Risk if loose</th><th>Safe example</th></tr>
  <tr><td class="mono">listen host</td><td>loopback only</td><td>绑定到所有网卡会把 memory API 暴露给非预期网络。</td><td><span class="inline">127.0.0.1</span> 或受防火墙保护的内网地址占位。</td></tr>
  <tr><td class="mono">port</td><td>explicit configured port</td><td>端口冲突或误以为服务启动成功。</td><td><span class="inline">TDAI_GATEWAY_PORT=PORT_PLACEHOLDER</span></td></tr>
  <tr><td class="mono">CORS origins</td><td>narrow allow-list</td><td>浏览器跨源页面可误用本机 Gateway。</td><td><span class="inline">TDAI_CORS_ORIGINS=https://APP_HOST_PLACEHOLDER</span></td></tr>
  <tr><td class="mono">auth token</td><td>shipped open/off, warn loudly</td><td>未授权调用可读取、写入或搜索记忆。</td><td>可信 loopback 外使用 <span class="inline">Authorization: Bearer TOKEN_PLACEHOLDER</span></td></tr>
  <tr><td class="mono">body size</td><td>deployment boundary limit</td><td>大 body 占内存、拖慢解析，或把工具日志误塞进 HTTP。</td><td>在反向代理、serverless 平台或客户端 SDK 设置小 JSON 上限。</td></tr>
  <tr><td class="mono">HTTP request timeout</td><td>deployment boundary timeout</td><td>慢请求耗尽 worker 或让用户误判为 Gateway 挂死。</td><td>在反向代理、负载均衡器或调用方设置请求超时；不要和 LLM provider timeout 混淆。</td></tr>
  <tr><td class="mono">rate / abuse</td><td>deploy boundary enforces quota</td><td>内置开关不能替代反滥用策略；搜索与写入可被刷爆。</td><td>只在可信网络暴露，前置反向代理或平台限流。</td></tr>
  <tr><td class="mono">logging</td><td>structured and redacted</td><td>token、prompt、用户数据或云配置进入日志。</td><td>记录 request id、route、status、duration；不记录 secrets。</td></tr>
</table>

<h2>Hermes provider 配置要只出现占位值</h2>
<div class="cellgroup">
  <div class="cg-cap"><b>provider side</b>：Hermes 只需要知道 provider key、Gateway URL 占位和客户端 token 占位。</div>
  <div class="cells"><span class="cell hl">provider key</span><span class="sep">-&gt;</span><span class="cell">GATEWAY_URL_PLACEHOLDER</span><span class="sep">-&gt;</span><span class="cell q">TOKEN_PLACEHOLDER</span></div>
  <div class="cg-cap"><b>gateway side</b>：Gateway 用自己的 env/config 解析 listen、CORS 与 auth；body size / HTTP timeout 属于部署边界，不从页面复制真实密钥。</div>
  <div class="cells"><span class="cell">TDAI_GATEWAY_HOST</span><span class="cell">TDAI_GATEWAY_PORT</span><span class="cell">TDAI_GATEWAY_API_KEY</span><span class="cell">TDAI_CORS_ORIGINS</span></div>
</div>

<h2>核心伪代码</h2>
<pre class="code">config = load_gateway_config(env)
adapter = StandaloneHostAdapter(config)
tdai_core = TdaiCore(adapter)
server = create_http_server(config, adapter, tdai_core)

on_request(req):
    route = match_gateway_route(req.method, req.path)
    if route is None:
        return not_found()
    if route.name == "health":
        return health_response(ok_or_degraded())
    if route.requires_auth:
        require_bearer_token(req.headers, config.auth_token_placeholder)
    origin = req.headers.get("origin")
    enforce_allowed_origin(origin, config.allowed_origins)
    body = read_json_body(req)
    validate_memory_payload(route.name, body)

    context = adapter.build_context(req.headers, body)
    result = tdai_core.handle(route.operation, context)
    return json_response(redact_secrets(result))</pre>

<h2>运维检查清单</h2>
<div class="timeline">
  <div class="tl"><div class="tm">before bind</div><div class="td">确认监听地址是否只在 loopback 或受控内网；若必须对外暴露，先放到防火墙、反向代理、TLS 和限流之后。</div></div>
  <div class="tl"><div class="tm">before enable</div><div class="td">设置 <span class="inline">TDAI_CORS_ORIGINS</span> 和 bearer auth；在部署边界设置 body size 与 HTTP request timeout。<span class="inline">GET /health</span> 可以轻量公开，但 memory routes 必须受保护。</div></div>
  <div class="tl"><div class="tm">during ops</div><div class="td">日志只保留 route、状态码、耗时、request id 和脱敏错误；不要记录 Authorization、provider secret、完整 prompt 或云服务凭据。</div></div>
  <div class="tl"><div class="tm">when abused</div><div class="td">Gateway 代码里的开关不是完整 WAF。高频写入、超大 payload、跨源调用和搜索刷量需要平台层限速、配额与告警。</div></div>
</div>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 8 Gateway coverage：本课聚焦 Hermes/direct Gateway 用户的 HTTP 运行路径与安全开关。</li>
    <li><span class="inline">src/gateway/server.ts</span>：HTTP server 创建、<span class="inline">GET /health</span> 与 memory POST routes、请求校验和向核心委托。</li>
    <li><span class="inline">src/gateway/config.ts</span>：env/config 解析、listen host/port、<span class="inline">TDAI_CORS_ORIGINS</span>、auth token 与默认值。</li>
    <li><span class="inline">hermes-plugin/memory/memory_tencentdb/README.md</span>：Hermes provider 安装、provider key、配置与 Gateway 路径。</li>
    <li><span class="inline">src/adapters/standalone/host-adapter.ts</span>：standalone host boundary，把 HTTP 调用适配成核心可理解的宿主上下文。</li>
    <li><span class="inline">src/core/tdai-core.ts</span>：Gateway 适配之后的宿主无关 memory facade。</li>
    <li><span class="inline">README_CN.md</span>：Gateway security hardening guidance，强调绑定地址、鉴权、CORS、日志与部署边界。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Hermes / Gateway 路径是外部 HTTP 服务路径，不是 OpenClaw 进程内 hook 路径。HTTP 请求必须先经过
  <span class="inline">server.ts</span> 的路由与校验、<span class="inline">config.ts</span> 的 listen/CORS/auth 开关，再由 standalone host adapter 收敛到 <span class="inline">TdaiCore</span>。
  运行姿态应偏向 loopback、窄 CORS、可信 loopback 外 bearer auth、部署层 body/HTTP timeout、平台限流和日志脱敏；文档与示例只能使用占位凭据和占位端点。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
Hermes / direct Gateway users take the external HTTP path: the request enters <span class="inline">src/gateway/server.ts</span>, while
<span class="inline">src/gateway/config.ts</span> resolves listen address, CORS, and authentication Gateway switches; payload size and HTTP request timeout belong at the deployment or reverse-proxy boundary. Only after those guards does the Gateway memory route
hand the request to the standalone host adapter and then to the host-neutral <span class="inline">TdaiCore</span>. This differs from the OpenClaw in-process plugin path: it adds a network boundary and a set of operational responsibilities.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  The OpenClaw in-process plugin is like an internal office counter: people in the same building follow internal workflow. The Hermes Gateway is like an external service window: someone submits a form from outside, security checks the entrance, allow-list, credential, package size, and wait time, then forwards valid requests to the internal counter.
</div>

<h2>How an external HTTP call reaches memory core</h2>
<div class="flow">
  <div class="node"><div class="nt">Hermes client</div><div class="nd">A provider or direct caller only knows the controlled Gateway address and a placeholder token.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">Gateway HTTP route</div><div class="nd"><span class="inline">server.ts</span> creates the HTTP server and registers <span class="inline">GET /health</span> plus memory POST routes.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">config/security guard</div><div class="nd"><span class="inline">config.ts</span> resolves host, port, CORS origin, and auth; body / HTTP timeout belongs to the deployment boundary.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">standalone adapter</div><div class="nd">Converts HTTP requests into host-neutral context, logging, and LLM boundaries.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">TdaiCore</div><div class="nd">Reuses the capture, recall, search, store, and pipeline facade.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">memory layers</div><div class="nd">L0/L1/L2/L3, SQLite / VectorDB, and Context Offload operate by configuration.</div></div>
</div>

<h2>server.ts: routes matter less than the boundary</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>create server</h4><p>The Gateway creates the HTTP server and keeps the route table, request parser, error responses, and shutdown flow near one entry point for operational review.</p><div class="mono">createHttpServer(config)</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>public health</h4><p><span class="inline">GET /health</span> bypasses auth for liveness / readiness and only returns safe states such as <span class="inline">ok</span> or <span class="inline">degraded</span>; the Gateway has no separate status route.</p><div class="mono">GET /health -&gt; ok | degraded</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>validate memory request</h4><p>The protected memory surface is <span class="inline">POST /recall</span>, <span class="inline">/capture</span>, <span class="inline">/search/memories</span>, <span class="inline">/search/conversations</span>, <span class="inline">/session/end</span>, and <span class="inline">/seed</span>; check method, path, content-type, JSON schema, CORS, and optional bearer auth before delegation.</p><div class="mono">reject early before TdaiCore</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>delegate safely</h4><p>The standalone host adapter builds host context so the HTTP layer does not know OpenClaw hook details and does not leak external request objects into core.</p><div class="mono">HTTP request -&gt; HostAdapter -&gt; TdaiCore</div></div></div>
</div>

<h2>OpenClaw in-process path vs Hermes/Gateway external path</h2>
<div class="cols">
  <div class="col"><h4>OpenClaw in-process plugin path</h4><p>OpenClaw starts the plugin, and the plugin registers hooks and tools inside the same host lifecycle. Events such as before_prompt_build, agent_end, and after_tool_call call the adapter directly, then enter <span class="inline">TdaiCore</span>. The main risks are host config, hook order, data directory isolation, and pipeline resources.</p></div>
  <div class="col"><h4>Hermes / Gateway external HTTP path</h4><p>A Hermes provider or direct caller invokes the Gateway over HTTP. The network entry must handle bind address, CORS, auth, and redacted logging; body limits and HTTP request timeouts should be handled by the reverse proxy, platform, or client boundary. The main risks are exposure, abuse, cross-origin access, and secret leakage in error logs.</p></div>
  <div class="col"><h4>Shared core</h4><p>Both paths should converge on host-neutral <span class="inline">TdaiCore</span>: memory layers, search, recall, storage backends, and scheduling should not fork merely because a call came from a hook or HTTP.</p></div>
</div>

<h2>Separate Gateway config from deployment safeguards</h2>
<table class="t">
  <tr><th>Control</th><th>Default idea</th><th>Risk if loose</th><th>Safe example</th></tr>
  <tr><td class="mono">listen host</td><td>loopback only</td><td>Binding all interfaces can expose the memory API to unintended networks.</td><td><span class="inline">127.0.0.1</span> or a protected internal address placeholder.</td></tr>
  <tr><td class="mono">port</td><td>explicit configured port</td><td>Port conflicts or a false belief that the service started correctly.</td><td><span class="inline">TDAI_GATEWAY_PORT=PORT_PLACEHOLDER</span></td></tr>
  <tr><td class="mono">CORS origins</td><td>narrow allow-list</td><td>A browser page from another origin may misuse a local Gateway.</td><td><span class="inline">TDAI_CORS_ORIGINS=https://APP_HOST_PLACEHOLDER</span></td></tr>
  <tr><td class="mono">auth token</td><td>shipped open/off, warn loudly</td><td>Unauthorized callers may read, write, or search memory.</td><td>Use <span class="inline">Authorization: Bearer TOKEN_PLACEHOLDER</span> outside trusted loopback.</td></tr>
  <tr><td class="mono">body size</td><td>deployment boundary limit</td><td>Large bodies consume memory, slow parsing, or stuff tool logs into HTTP.</td><td>Set a small JSON limit in the reverse proxy, serverless platform, or client SDK.</td></tr>
  <tr><td class="mono">HTTP request timeout</td><td>deployment boundary timeout</td><td>Slow requests exhaust workers or make users think Gateway is hung.</td><td>Set request timeouts in the reverse proxy, load balancer, or caller; do not confuse this with LLM provider timeout.</td></tr>
  <tr><td class="mono">rate / abuse</td><td>deployment boundary enforces quota</td><td>Built-in switches are not a full abuse strategy; search and writes can be hammered.</td><td>Expose only on trusted networks, with a reverse proxy or platform rate limit.</td></tr>
  <tr><td class="mono">logging</td><td>structured and redacted</td><td>Tokens, prompts, user data, or cloud config can enter logs.</td><td>Log request id, route, status, duration; do not log secrets.</td></tr>
</table>

<h2>Hermes provider config should use placeholders only</h2>
<div class="cellgroup">
  <div class="cg-cap"><b>provider side</b>: Hermes only needs the provider key, Gateway URL placeholder, and client token placeholder.</div>
  <div class="cells"><span class="cell hl">provider key</span><span class="sep">-&gt;</span><span class="cell">GATEWAY_URL_PLACEHOLDER</span><span class="sep">-&gt;</span><span class="cell q">TOKEN_PLACEHOLDER</span></div>
  <div class="cg-cap"><b>gateway side</b>: Gateway resolves listen, CORS, and auth from its own env/config; body size / HTTP timeout are deployment-boundary concerns, and real secrets should never be copied from a page.</div>
  <div class="cells"><span class="cell">TDAI_GATEWAY_HOST</span><span class="cell">TDAI_GATEWAY_PORT</span><span class="cell">TDAI_GATEWAY_API_KEY</span><span class="cell">TDAI_CORS_ORIGINS</span></div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">config = load_gateway_config(env)
adapter = StandaloneHostAdapter(config)
tdai_core = TdaiCore(adapter)
server = create_http_server(config, adapter, tdai_core)

on_request(req):
    route = match_gateway_route(req.method, req.path)
    if route is None:
        return not_found()
    if route.name == "health":
        return health_response(ok_or_degraded())
    if route.requires_auth:
        require_bearer_token(req.headers, config.auth_token_placeholder)
    origin = req.headers.get("origin")
    enforce_allowed_origin(origin, config.allowed_origins)
    body = read_json_body(req)
    validate_memory_payload(route.name, body)

    context = adapter.build_context(req.headers, body)
    result = tdai_core.handle(route.operation, context)
    return json_response(redact_secrets(result))</pre>

<h2>Operations checklist</h2>
<div class="timeline">
  <div class="tl"><div class="tm">before bind</div><div class="td">Confirm whether the listen address is loopback or controlled internal network only. If external exposure is required, put it behind firewall, reverse proxy, TLS, and rate limits first.</div></div>
  <div class="tl"><div class="tm">before enable</div><div class="td">Set <span class="inline">TDAI_CORS_ORIGINS</span> and bearer auth; put body size and HTTP request timeout at the deployment boundary. <span class="inline">GET /health</span> can stay lightweight and public, but memory routes must be protected.</div></div>
  <div class="tl"><div class="tm">during ops</div><div class="td">Logs keep only route, status code, duration, request id, and redacted errors. Do not record Authorization, provider secrets, full prompts, or cloud credentials.</div></div>
  <div class="tl"><div class="tm">when abused</div><div class="td">Gateway code switches are not a full WAF. High-frequency writes, oversized payloads, cross-origin calls, and search hammering need platform rate limits, quota, and alerts.</div></div>
</div>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 8 Gateway coverage: this lesson focuses on the HTTP operational path and security switches for Hermes/direct Gateway users.</li>
    <li><span class="inline">src/gateway/server.ts</span>: HTTP server creation, <span class="inline">GET /health</span> plus memory POST routes, request validation, and delegation to core.</li>
    <li><span class="inline">src/gateway/config.ts</span>: env/config resolution, listen host/port, <span class="inline">TDAI_CORS_ORIGINS</span>, auth token, and defaults.</li>
    <li><span class="inline">hermes-plugin/memory/memory_tencentdb/README.md</span>: Hermes provider install, provider key, configuration, and Gateway path.</li>
    <li><span class="inline">src/adapters/standalone/host-adapter.ts</span>: standalone host boundary that adapts HTTP calls into core-understandable host context.</li>
    <li><span class="inline">src/core/tdai-core.ts</span>: host-neutral memory facade after Gateway adaptation.</li>
    <li><span class="inline">README_CN.md</span>: Gateway security hardening guidance for bind address, auth, CORS, logging, and deployment boundary.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  The Hermes / Gateway path is an external HTTP service path, not the OpenClaw in-process hook path. HTTP requests must pass
  <span class="inline">server.ts</span> routing and validation plus <span class="inline">config.ts</span> listen/CORS/auth switches before the standalone host adapter converges on <span class="inline">TdaiCore</span>.
  The operating posture should favor loopback, narrow CORS, bearer auth outside trusted loopback, deployment-layer body / HTTP timeouts, platform rate limits, and redacted logs; docs and examples should use only placeholder credentials and placeholder endpoints.
</div>
""",
}


LESSON_33 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
记忆系统不只在 live agent loop 里工作。初始化种子、SQLite 到 Tencent VectorDB 的迁移、远程快照导出、本地安全读取和诊断打包，都应该通过可审计、可回滚的脚本完成。本课把
<span class="inline">seed</span> CLI、迁移脚本、导出/读取脚本和 <span class="inline">memory-tencentdb-ctl</span> 看成一组运维工作流：先读 README 和脚本说明，再做 dry run、备份、manifest、应用和验证。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  现场对话像餐厅正在营业，不能在客人点菜时搬仓库。Seed、migration、export 和 read scripts 像闭店后的盘点：先锁定清单、拍照备份、试跑一次、看盘点报告，再真正搬货，最后抽查货架是否能被找到。
</div>

<h2>为什么这些动作要离开 live agent loop</h2>
<div class="cols">
  <div class="col"><h4>初始化不是聊天</h4><p><span class="inline">src/cli/commands/seed.ts</span> 接收 operator 提供的 seed 输入；<span class="inline">src/core/seed/input.ts</span> 解析和验证；<span class="inline">seed-runtime.ts</span> 才把合格数据写入存储。它适合准备初始记忆，不应假装成用户的一轮对话。</p></div>
  <div class="col"><h4>迁移不是实时召回</h4><p><span class="inline">scripts/migrate-sqlite-to-tcvdb</span> 把本地 SQLite memory 向 Tencent VectorDB 后端移动。迁移需要配置快照、manifest、dry run、备份和幂等写入，而不是在一次 recall 超时里偷偷完成。</p></div>
  <div class="col"><h4>诊断不是暴露秘密</h4><p>export/read scripts 用于生成可检查的本地或远程快照。它们应保留结构、计数、状态和可脱敏样本，避免把真实 token、endpoint、prompt 或用户敏感内容复制进报告。</p></div>
</div>

<h2>运维时间线：先证明可回滚，再应用</h2>
<div class="timeline">
  <div class="lane"><div class="lane-label">prepare</div><div class="tslot">read docs</div><div class="tslot">choose scope</div><div class="tslot">freeze config</div></div>
  <div class="lane"><div class="lane-label">backup</div><div class="tslot span">copy SQLite / config / existing manifests to BACKUP_DIR_PLACEHOLDER</div></div>
  <div class="lane"><div class="lane-label">dry run</div><div class="tslot">seed preview if documented</div><div class="tslot">migration --dry-run</div><div class="tslot">read-only export</div></div>
  <div class="lane"><div class="lane-label">inspect</div><div class="tslot">manifest</div><div class="tslot">counts</div><div class="tslot">warnings</div><div class="tslot">sample reads</div></div>
  <div class="lane"><div class="lane-label">apply</div><div class="tslot now">run exact reviewed command</div><div class="tslot">write manifest</div></div>
  <div class="lane"><div class="lane-label">verify</div><div class="tslot">local read</div><div class="tslot">search</div><div class="tslot">recall</div><div class="tslot">rollback plan still valid</div></div>
</div>

<h2>Seed 写入路径</h2>
<div class="flow">
  <div class="node"><div class="nt">seed input</div><div class="nd">JSON/JSONL/fixture path uses placeholders and declared session/user scope.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">input parser</div><div class="nd"><span class="inline">input.ts</span> validates shape, ids, timestamps, and required fields.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">seed runtime</div><div class="nd"><span class="inline">seed-runtime.ts</span> normalizes and plans idempotent writes.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">storage adapter</div><div class="nd">SQLite or Tencent VectorDB backend receives checked records.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">verification read</div><div class="nd">read/search confirms the expected records without leaking credentials.</div></div>
</div>

<h2>脚本和命令何时使用</h2>
<div class="card warn">
  <div class="tag">⚠️ 先确认真实参数</div>
  下表里的命令名表达运维语义，不替代脚本 README。不同脚本的真实 flag 可能叫 <span class="inline">--dry-run</span>、<span class="inline">--yes</span> 或只提供“校验后写入”；运行前必须打开对应 README / entry file，确认该命令到底是只读、预演还是写入。
</div>
<table class="t">
  <tr><th>Script / command</th><th>When to use</th><th>Inputs</th><th>Outputs</th><th>Safety check</th></tr>
  <tr><td class="mono">memory-tencentdb seed --input SEED_FILE_PLACEHOLDER</td><td>验证并写入初始 memory seed；若 README 明确支持 preview / dry run，先预演。</td><td>SEED_FILE_PLACEHOLDER、CONFIG_PATH_PLACEHOLDER。</td><td>校验结果、拒绝原因、写入摘要。</td><td>先读 <span class="inline">src/cli/README.md</span>；确认 schema、scope、备份和去重策略。</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --dry-run</td><td>评估从本地 SQLite 到 Tencent VectorDB 的迁移。</td><td>SQLITE_PATH_PLACEHOLDER、TCVDB_CONFIG_PLACEHOLDER。</td><td>迁移计划、collection 检查、manifest 草稿。</td><td>先备份 SQLite，确认 endpoint / token 只来自占位配置或安全环境。</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --apply</td><td>dry run、manifest 和备份都通过后才应用。</td><td>同一份已审阅配置与输入快照。</td><td>写入远程集合、正式 manifest、计数摘要。</td><td>检查 <span class="inline">manifest-write.ts</span>，确保可追踪批次和幂等 key。</td></tr>
  <tr><td class="mono">export-tencent-vdb --output SNAPSHOT_PATH_PLACEHOLDER</td><td>生成远程 VectorDB 诊断快照。</td><td>只读远程配置、collection 名、脱敏规则。</td><td>结构化 snapshot 或摘要文件。</td><td>不导出真实凭据；样本内容按策略截断或脱敏。</td></tr>
  <tr><td class="mono">read-local-memory --db SQLITE_PATH_PLACEHOLDER</td><td>本地排查 recall/search 前的 memory 状态。</td><td>SQLite 路径、查询条件、limit。</td><td>只读表统计、匹配记录、source ids。</td><td>默认只读、小 limit；不要修库。</td></tr>
  <tr><td class="mono">memory-tencentdb-ctl status --config CONFIG_PATH_PLACEHOLDER</td><td>把常见 operator 操作包装成一致入口。</td><td>配置路径、操作名、dry-run/apply 开关。</td><td>状态、诊断、备份或导出位置。</td><td>阅读 wrapper README，确认它实际调用了哪些脚本。</td></tr>
</table>

<h2>核心伪代码</h2>
<pre class="code">operator_reads_docs([
    "src/cli/README.md",
    "scripts/migrate-sqlite-to-tcvdb/README.md",
    "scripts/README.memory-tencentdb-ctl.md",
])

plan = load_operation_plan(CONFIG_PATH_PLACEHOLDER)
assert plan.uses_placeholders_or_secure_env()
backup = create_backup(SQLITE_PATH_PLACEHOLDER, BACKUP_DIR_PLACEHOLDER)

dry_run = run_seed_or_migration(plan, mode="dry-run")
if dry_run.has_errors:
    stop_and_fix_input(dry_run.errors)

manifest = write_manifest(dry_run, backup)
review(manifest.counts, manifest.warnings, manifest.rollback_hint)

if operator_approves_exact_plan:
    result = run_seed_or_migration(plan, mode="apply", idempotency_key=manifest.id)
    verify_with_read_script(result.expected_records, readonly=True)
    verify_with_search_or_recall(SAFE_QUERY_PLACEHOLDER)</pre>

<h2>读脚本时重点看什么</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>入口参数</h4><p><span class="inline">cli-entry.ts</span>、shell wrapper 和 README 应说明哪些参数只读、哪些会写入、哪些需要 dry run。看不懂参数时不要运行。</p><div class="mono">read docs before scripts</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>配置写入</h4><p><span class="inline">config-write.ts</span> 一类脚本可能改变运行配置。应用前先保存配置副本，输出里只允许 CONFIG_PATH_PLACEHOLDER 这类安全占位。</p><div class="mono">backup config before apply</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>manifest 写入</h4><p><span class="inline">manifest-write.ts</span> 是回滚与审计线索：记录输入摘要、批次 id、计数、警告和目标集合，而不是记录真实密钥。</p><div class="mono">manifest proves what changed</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>验证读取</h4><p><span class="inline">read-local-memory.ts</span> 和 export snapshot 用于确认结果。默认只读、小范围、可脱敏；发现异常先停，不要连环 apply。</p><div class="mono">read before and after apply</div></div></div>
</div>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 8 operations：本课覆盖 live loop 外的 seed、migration、export、read、diagnostic 和 operator workflow。</li>
    <li><span class="inline">src/cli/commands/seed.ts</span>、<span class="inline">src/core/seed/seed-runtime.ts</span>、<span class="inline">src/core/seed/input.ts</span>：seed CLI、输入校验和写入运行时。</li>
    <li><span class="inline">src/cli/README.md</span>：CLI 行为、参数和安全使用说明。</li>
    <li><span class="inline">scripts/migrate-sqlite-to-tcvdb/README.md</span>、<span class="inline">cli-entry.ts</span>、<span class="inline">sqlite-to-tcvdb.ts</span>、<span class="inline">config-write.ts</span>、<span class="inline">manifest-write.ts</span>：迁移入口、数据移动、配置写入和 manifest。</li>
    <li><span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span> 与 <span class="inline">scripts/read-local-memory/read-local-memory.ts</span>：远程导出和本地只读检查。</li>
    <li><span class="inline">scripts/export-diagnostic.sh</span>、<span class="inline">scripts/memory-tencentdb-ctl.sh</span>、<span class="inline">scripts/README.memory-tencentdb-ctl.md</span>：诊断打包和 operator wrapper。</li>
    <li><span class="inline">scripts/install_hermes_memory_tencentdb.sh</span>、<span class="inline">scripts/setup-offload.sh</span>：阅读它们以理解安装/离线化脚本的副作用；本课不提供安装步骤，也不建议把它们当迁移快捷方式。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Seed、迁移、导出、诊断和本地读取都是运维脚本工作流，不是实时 agent 对话的一部分。安全顺序是：读文档、限定范围、备份、dry run、检查 manifest / export、再 apply、最后用只读脚本和 recall/search 验证。
  命令示例必须只含占位路径、占位配置和 dry-run/apply 语义，不出现真实 endpoint、token 或安装指令。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
The memory system does more than run inside the live agent loop. Initial seeding, SQLite to Tencent VectorDB migration, remote snapshot export, safe local reads, and diagnostic bundles should be handled by auditable, reversible scripts. This lesson treats the
<span class="inline">seed</span> CLI, migration scripts, export/read scripts, and <span class="inline">memory-tencentdb-ctl</span> as one operational workflow: read the READMEs and script docs first, then dry run, back up, inspect manifests, apply, and verify.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  A live conversation is like a restaurant during service; you should not move the warehouse while guests are ordering. Seed, migration, export, and read scripts are closing-time inventory: lock the checklist, take backup photos, rehearse once, inspect the inventory report, move the stock, then sample-check that shelves can be found.
</div>

<h2>Why these actions stay outside the live agent loop</h2>
<div class="cols">
  <div class="col"><h4>Initialization is not chat</h4><p><span class="inline">src/cli/commands/seed.ts</span> accepts operator-provided seed input; <span class="inline">src/core/seed/input.ts</span> parses and validates it; <span class="inline">seed-runtime.ts</span> writes only accepted data. This prepares initial memory; it should not pretend to be a user turn.</p></div>
  <div class="col"><h4>Migration is not realtime recall</h4><p><span class="inline">scripts/migrate-sqlite-to-tcvdb</span> moves local SQLite memory toward Tencent VectorDB. Migration needs config snapshots, manifests, dry runs, backups, and idempotent writes, not a hidden side effect inside one recall timeout.</p></div>
  <div class="col"><h4>Diagnostics are not secret dumps</h4><p>Export/read scripts create inspectable local or remote snapshots. They should preserve structure, counts, status, and redacted samples without copying real tokens, endpoints, prompts, or sensitive user content into reports.</p></div>
</div>

<h2>Operational timeline: prove rollback first, then apply</h2>
<div class="timeline">
  <div class="lane"><div class="lane-label">prepare</div><div class="tslot">read docs</div><div class="tslot">choose scope</div><div class="tslot">freeze config</div></div>
  <div class="lane"><div class="lane-label">backup</div><div class="tslot span">copy SQLite / config / existing manifests to BACKUP_DIR_PLACEHOLDER</div></div>
  <div class="lane"><div class="lane-label">dry run</div><div class="tslot">seed preview if documented</div><div class="tslot">migration --dry-run</div><div class="tslot">read-only export</div></div>
  <div class="lane"><div class="lane-label">inspect</div><div class="tslot">manifest</div><div class="tslot">counts</div><div class="tslot">warnings</div><div class="tslot">sample reads</div></div>
  <div class="lane"><div class="lane-label">apply</div><div class="tslot now">run exact reviewed command</div><div class="tslot">write manifest</div></div>
  <div class="lane"><div class="lane-label">verify</div><div class="tslot">local read</div><div class="tslot">search</div><div class="tslot">recall</div><div class="tslot">rollback plan still valid</div></div>
</div>

<h2>Seed write path</h2>
<div class="flow">
  <div class="node"><div class="nt">seed input</div><div class="nd">JSON/JSONL/fixture path uses placeholders and declared session/user scope.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">input parser</div><div class="nd"><span class="inline">input.ts</span> validates shape, ids, timestamps, and required fields.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">seed runtime</div><div class="nd"><span class="inline">seed-runtime.ts</span> normalizes and plans idempotent writes.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">storage adapter</div><div class="nd">SQLite or Tencent VectorDB backend receives checked records.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">verification read</div><div class="nd">read/search confirms expected records without leaking credentials.</div></div>
</div>

<h2>When to use each script or command</h2>
<div class="card warn">
  <div class="tag">⚠️ Confirm real flags first</div>
  The command names below express operational semantics; they do not replace each script README. Real flags may be named <span class="inline">--dry-run</span>, <span class="inline">--yes</span>, or may provide only validate-then-write behavior. Before running anything, open the matching README / entry file and confirm whether the command is read-only, a preview, or a write.
</div>
<table class="t">
  <tr><th>Script / command</th><th>When to use</th><th>Inputs</th><th>Outputs</th><th>Safety check</th></tr>
  <tr><td class="mono">memory-tencentdb seed --input SEED_FILE_PLACEHOLDER</td><td>Validate and write initial memory seed data; if the README documents preview / dry run, rehearse first.</td><td>SEED_FILE_PLACEHOLDER, CONFIG_PATH_PLACEHOLDER.</td><td>Validation result, rejection reasons, write summary.</td><td>Read <span class="inline">src/cli/README.md</span> first; confirm schema, scope, backup, and dedup policy.</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --dry-run</td><td>Assess migration from local SQLite to Tencent VectorDB.</td><td>SQLITE_PATH_PLACEHOLDER, TCVDB_CONFIG_PLACEHOLDER.</td><td>Migration plan, collection checks, manifest draft.</td><td>Back up SQLite first; confirm endpoint / token come only from placeholder config or secure environment.</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --apply</td><td>Apply only after dry run, manifest, and backup pass review.</td><td>The same reviewed config and input snapshot.</td><td>Remote collection writes, final manifest, count summary.</td><td>Check <span class="inline">manifest-write.ts</span> for traceable batches and idempotency keys.</td></tr>
  <tr><td class="mono">export-tencent-vdb --output SNAPSHOT_PATH_PLACEHOLDER</td><td>Create a remote VectorDB diagnostic snapshot.</td><td>Read-only remote config, collection name, redaction rules.</td><td>Structured snapshot or summary file.</td><td>Do not export real credentials; truncate or redact sample content by policy.</td></tr>
  <tr><td class="mono">read-local-memory --db SQLITE_PATH_PLACEHOLDER</td><td>Inspect memory state before debugging recall/search.</td><td>SQLite path, query filters, limit.</td><td>Read-only table stats, matching records, source ids.</td><td>Default to read-only and small limits; do not repair the database here.</td></tr>
  <tr><td class="mono">memory-tencentdb-ctl status --config CONFIG_PATH_PLACEHOLDER</td><td>Wrap common operator actions behind one entry point.</td><td>Config path, action name, dry-run/apply switch.</td><td>Status, diagnostics, backup or export location.</td><td>Read the wrapper README and confirm which scripts it actually calls.</td></tr>
</table>

<h2>Core pseudocode</h2>
<pre class="code">operator_reads_docs([
    "src/cli/README.md",
    "scripts/migrate-sqlite-to-tcvdb/README.md",
    "scripts/README.memory-tencentdb-ctl.md",
])

plan = load_operation_plan(CONFIG_PATH_PLACEHOLDER)
assert plan.uses_placeholders_or_secure_env()
backup = create_backup(SQLITE_PATH_PLACEHOLDER, BACKUP_DIR_PLACEHOLDER)

dry_run = run_seed_or_migration(plan, mode="dry-run")
if dry_run.has_errors:
    stop_and_fix_input(dry_run.errors)

manifest = write_manifest(dry_run, backup)
review(manifest.counts, manifest.warnings, manifest.rollback_hint)

if operator_approves_exact_plan:
    result = run_seed_or_migration(plan, mode="apply", idempotency_key=manifest.id)
    verify_with_read_script(result.expected_records, readonly=True)
    verify_with_search_or_recall(SAFE_QUERY_PLACEHOLDER)</pre>

<h2>What to inspect before running scripts</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Entry arguments</h4><p><span class="inline">cli-entry.ts</span>, shell wrappers, and READMEs should say which arguments are read-only, which write data, and which require dry run. If the arguments are unclear, do not run the script.</p><div class="mono">read docs before scripts</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Config writes</h4><p>Scripts such as <span class="inline">config-write.ts</span> may change runtime config. Save a config copy before apply, and allow only safe placeholders such as CONFIG_PATH_PLACEHOLDER in output.</p><div class="mono">backup config before apply</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Manifest writes</h4><p><span class="inline">manifest-write.ts</span> is the rollback and audit trail: record input digests, batch id, counts, warnings, and target collection, not real secrets.</p><div class="mono">manifest proves what changed</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Verification reads</h4><p><span class="inline">read-local-memory.ts</span> and export snapshots confirm results. Default to read-only, narrow scope, and redaction; if something looks wrong, stop instead of chaining apply runs.</p><div class="mono">read before and after apply</div></div></div>
</div>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 8 operations: this lesson covers seed, migration, export, read, diagnostic, and operator workflows outside the live loop.</li>
    <li><span class="inline">src/cli/commands/seed.ts</span>, <span class="inline">src/core/seed/seed-runtime.ts</span>, and <span class="inline">src/core/seed/input.ts</span>: seed CLI, input validation, and write runtime.</li>
    <li><span class="inline">src/cli/README.md</span>: CLI behavior, parameters, and safe usage notes.</li>
    <li><span class="inline">scripts/migrate-sqlite-to-tcvdb/README.md</span>, <span class="inline">cli-entry.ts</span>, <span class="inline">sqlite-to-tcvdb.ts</span>, <span class="inline">config-write.ts</span>, and <span class="inline">manifest-write.ts</span>: migration entry, data movement, config writes, and manifests.</li>
    <li><span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span> and <span class="inline">scripts/read-local-memory/read-local-memory.ts</span>: remote export and local read-only inspection.</li>
    <li><span class="inline">scripts/export-diagnostic.sh</span>, <span class="inline">scripts/memory-tencentdb-ctl.sh</span>, and <span class="inline">scripts/README.memory-tencentdb-ctl.md</span>: diagnostic bundling and operator wrapper.</li>
    <li><span class="inline">scripts/install_hermes_memory_tencentdb.sh</span> and <span class="inline">scripts/setup-offload.sh</span>: read them to understand setup/offload side effects; this lesson gives no installation steps and does not treat them as migration shortcuts.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Seed, migration, export, diagnostics, and local reads are operational script workflows, not realtime agent conversation steps. The safe order is: read docs, limit scope, back up, dry run, inspect manifest / export, apply, then verify with read-only scripts plus recall/search.
  Command examples must use only placeholder paths, placeholder config, and dry-run/apply semantics, with no real endpoints, tokens, or installation instructions.
</div>
""",
}
