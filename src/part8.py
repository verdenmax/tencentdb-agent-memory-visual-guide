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
  <div class="step"><div class="num">2</div><div class="sc"><h4>CORS, preflight, health</h4><p>Gateway 先给响应套 CORS 头：origin 不在 allow-list 就省略这些头，由浏览器拦截跨源调用，而不是服务端直接拒绝。<span class="inline">OPTIONS</span> 预检不鉴权直接回 <span class="inline">204</span>；<span class="inline">GET /health</span> 同样绕过鉴权，只返回 <span class="inline">ok</span> 或 <span class="inline">degraded</span>，Gateway 没有单独的 status route。</p><div class="mono">CORS headers -&gt; OPTIONS 204 -&gt; /health</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>auth, then validate memory request</h4><p>受保护的 memory surface 是 <span class="inline">POST /recall</span>、<span class="inline">/capture</span>、<span class="inline">/search/memories</span>、<span class="inline">/search/conversations</span>、<span class="inline">/session/end</span> 和 <span class="inline">/seed</span>；在 CORS 之后先过 bearer auth gate，再按方法、路径解析 JSON body 并校验每条路由的必填字段，更深的 <span class="inline">validateAndNormalizeRaw</span> 归一化只用于 <span class="inline">/seed</span>。</p><div class="mono">reject early before TdaiCore</div></div></div>
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

    # CORS headers first: omit them when origin is not allow-listed,
    # so the browser blocks cross-origin use (no server-side rejection).
    origin = req.headers.get("origin")
    cors_headers = build_cors_headers(origin, config.allowed_origins)

    if req.method == "OPTIONS":
        return preflight_204(cors_headers)                  # preflight, no auth
    if route.name == "health":
        return health_response(ok_or_degraded(), cors_headers)  # GET /health bypasses auth

    if route.requires_auth:                                 # auth gate after CORS + health
        require_bearer_token(req.headers, config.auth_token_placeholder)

    body = read_json_body(req)                              # parse JSON
    validate_required_fields(route.name, body)              # per-route required fields
    if route.name == "seed":
        body = validateAndNormalizeRaw(body)                # deeper checks only for /seed

    context = adapter.build_context(req.headers, body)
    result = tdai_core.handle(route.operation, context)
    return json_response(redact_secrets(result), cors_headers)</pre>

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
  <div class="step"><div class="num">2</div><div class="sc"><h4>CORS, preflight, health</h4><p>The Gateway applies CORS headers first: a disallowed origin simply gets those headers omitted, so the browser blocks the cross-origin call rather than the server rejecting it. <span class="inline">OPTIONS</span> preflight returns <span class="inline">204</span> without auth, and <span class="inline">GET /health</span> also bypasses auth, returning only <span class="inline">ok</span> or <span class="inline">degraded</span>; the Gateway has no separate status route.</p><div class="mono">CORS headers -&gt; OPTIONS 204 -&gt; /health</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>auth, then validate memory request</h4><p>The protected memory surface is <span class="inline">POST /recall</span>, <span class="inline">/capture</span>, <span class="inline">/search/memories</span>, <span class="inline">/search/conversations</span>, <span class="inline">/session/end</span>, and <span class="inline">/seed</span>; after CORS it runs the bearer auth gate, then matches method and path, parses the JSON body, and checks the per-route required fields, with the deeper <span class="inline">validateAndNormalizeRaw</span> normalization applied only to <span class="inline">/seed</span>.</p><div class="mono">reject early before TdaiCore</div></div></div>
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

    # CORS headers first: omit them when origin is not allow-listed,
    # so the browser blocks cross-origin use (no server-side rejection).
    origin = req.headers.get("origin")
    cors_headers = build_cors_headers(origin, config.allowed_origins)

    if req.method == "OPTIONS":
        return preflight_204(cors_headers)                  # preflight, no auth
    if route.name == "health":
        return health_response(ok_or_degraded(), cors_headers)  # GET /health bypasses auth

    if route.requires_auth:                                 # auth gate after CORS + health
        require_bearer_token(req.headers, config.auth_token_placeholder)

    body = read_json_body(req)                              # parse JSON
    validate_required_fields(route.name, body)              # per-route required fields
    if route.name == "seed":
        body = validateAndNormalizeRaw(body)                # deeper checks only for /seed

    context = adapter.build_context(req.headers, body)
    result = tdai_core.handle(route.operation, context)
    return json_response(redact_secrets(result), cors_headers)</pre>

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


LESSON_34 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
本指南最后一课把读者从“理解系统”带到“能排查、能验证、能贡献”。遇到记忆问题时，不要从猜测开始；先把症状归类，再按
运行时文件、Gateway 状态、配置、recall/search 行为、capture checkpoints、Context Offload artifacts、日志和测试逐层收敛。贡献代码时，则从
<span class="inline">CONTRIBUTING.md</span>、<span class="inline">CONTRIBUTING_CN.md</span>、<span class="inline">package.json</span> scripts 和
<span class="inline">vitest.config.ts</span> 找到项目认可的验证路径。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  调试记忆系统像修一条城市快递链路：先问包裹是没寄出、没入库、找不到、送错人，还是路上被压缩归档；再查网点台账、分拣规则、路由状态、签收记录和质检报告。贡献代码则像改配送规则：先读规章，再改小步，最后用演练和测试证明没有把别的路线弄坏。
</div>

<h2>从症状到贡献路径的闭环</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>symptom</h4><p>把用户反馈写成可观察症状：没有 capture、recall 为空、搜索命中错误、Gateway 无响应、offload 下钻失败，或测试失败。</p><div class="mono">name the failure before fixing it</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>config check</h4><p>核对 enable flags、data dir、recall budget、embedding / tcvdb 后端和 offload 开关；不要先删除数据或改真实凭据。</p><div class="mono">config explains many silent fallbacks</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>runtime files</h4><p>打开 L0 JSONL、L1 records、scene_blocks、persona、vectors.db 和 context-offload artifacts，确认问题发生在哪一层。</p><div class="mono">files are evidence, not guesses</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>recall / search</h4><p>用安全查询复现召回或搜索；检查 source ids、预算裁剪、hybrid strategy、降级路径和排序解释。</p><div class="mono">query -&gt; candidates -&gt; injected context</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>capture / offload</h4><p>检查 capture checkpoint、cursor、锁、refs、JSONL 摘要、MMD、node_id 和 drill-down 链路是否连续。</p><div class="mono">checkpoint -&gt; evidence -&gt; compressed map</div></div></div>
  <div class="step"><div class="num">6</div><div class="sc"><h4>tests</h4><p>先写能复现问题的测试，再运行项目已有脚本；通过后才进入贡献文档要求的提交流程。</p><div class="mono">red -&gt; green -&gt; contribution path</div></div></div>
</div>

<h2>运维调试清单 vs 贡献者验证清单</h2>
<div class="cols">
  <div class="col">
    <h4>Operator debugging checklist</h4>
    <ol>
      <li><strong>症状</strong>：确认是 capture、recall、search、Gateway、offload、seed/migration 还是测试问题。</li>
      <li><strong>运行时文件</strong>：检查 conversations / JSONL、records、scene_blocks、persona、vectors.db、context-offload。</li>
      <li><strong>Gateway status</strong>：检查 <span class="inline">GET /health</span>、helper status、监听地址、CORS、auth 和日志脱敏。</li>
      <li><strong>配置</strong>：核对默认值、data dir、embedding dimensions、backend、timeouts、budgets 和 feature flags。</li>
      <li><strong>召回 / 搜索</strong>：用只读查询查看候选、source ids、排序、预算裁剪和降级原因。</li>
      <li><strong>capture checkpoints</strong>：检查 cursor、position slice、锁和重复写入线索。</li>
      <li><strong>offload artifacts</strong>：确认 refs、JSONL、MMD、node_id 和 drill-down 文件都能互相指向。</li>
      <li><strong>日志</strong>：保留 route、status、duration、request id；不要输出 token、endpoint、完整 prompt 或用户隐私。</li>
      <li><strong>测试</strong>：用现有测试复现问题，再确认修复没有破坏其他路径。</li>
    </ol>
  </div>
  <div class="col">
    <h4>Contributor validation checklist</h4>
    <ol>
      <li>先读 <span class="inline">CONTRIBUTING.md</span> 与 <span class="inline">CONTRIBUTING_CN.md</span>，确认分支、提交、测试和 PR 预期。</li>
      <li>阅读 <span class="inline">package.json</span> scripts，使用项目已有的 test / build 命令；类型检查随 build 脚本中的 tsdown / tsc 运行。</li>
      <li>阅读 <span class="inline">vitest.config.ts</span>，理解测试环境、include/exclude、超时，以及 mock、env、global reset 行为。</li>
      <li>改动指南时同步 <span class="inline">src/shell.py</span>、<span class="inline">src/registry.py</span>、<span class="inline">src/quizzes.py</span> 与对应 <span class="inline">part*.py</span>。</li>
      <li>改动核心项目时把新行为连接到真实边界：TdaiCore、HostAdapter、Gateway route、store backend 或 pipeline scheduler。</li>
      <li>测试必须证明行为：先失败，再通过；不要只测试 mock 调用次数。</li>
      <li>更新文档和 glossary 链接，确保术语能回到主要课程页。</li>
      <li>提交前运行共享验证块，确认没有 broken links、HTML 错误、真实密钥或生成文件漂移。</li>
    </ol>
  </div>
</div>

<h2>核心伪代码</h2>
<pre class="code">def debug_memory_issue(symptom):
    case = classify(symptom, [
        "capture_missing", "recall_empty", "search_wrong",
        "gateway_down", "offload_broken", "test_failure",
    ])

    runtime = inspect_runtime_files(DATA_DIR_PLACEHOLDER)
    gateway = check_gateway_health(GATEWAY_URL_PLACEHOLDER)
    config = load_redacted_config(CONFIG_PATH_PLACEHOLDER)

    if case in ["recall_empty", "search_wrong"]:
        candidates = run_readonly_search(SAFE_QUERY_PLACEHOLDER)
        explain_budget_and_ranking(candidates)

    if case == "capture_missing":
        inspect_checkpoints_and_locks(runtime.checkpoints)

    if case == "offload_broken":
        verify_refs_jsonl_mmd_node_ids(runtime.offload_dir)

    collect_redacted_logs(request_id=REQUEST_ID_PLACEHOLDER)
    write_or_update_test_that_fails(case)
    run_existing_project_scripts(["test", "build"])
    follow_contributing_docs_before_pr()</pre>

<h2>Glossary / index：术语要能回到主课</h2>
<table class="t">
  <tr><th>Term</th><th>Meaning</th><th>Primary lesson link</th></tr>
  <tr><td class="mono">L0</td><td>原始对话证据层，一行一条 JSONL 记录，支撑追溯。</td><td><a href="13-l0-jsonl-recorder.html">Lesson 13</a></td></tr>
  <tr><td class="mono">L1</td><td>从对话抽取出的原子记忆，带 source ids、去重和写入路径。</td><td><a href="15-l1-extraction.html">Lesson 15</a></td></tr>
  <tr><td class="mono">L2</td><td>把 L1 组织成可导航的场景块，服务中期情境理解。</td><td><a href="17-why-l2-scene-blocks.html">Lesson 17</a></td></tr>
  <tr><td class="mono">L3 Persona</td><td>从场景中增量生成的用户画像 / 偏好摘要，注入为稳定上下文。</td><td><a href="20-persona-generator-incremental.html">Lesson 20</a></td></tr>
  <tr><td class="mono">Scene Block</td><td>可增长、可追溯、可 read_file 下钻的场景文件。</td><td><a href="17-why-l2-scene-blocks.html">Lesson 17</a></td></tr>
  <tr><td class="mono">Auto Capture</td><td>对话提交后可靠写入 L0、索引和通知 pipeline 的路径。</td><td><a href="12-auto-capture-hook.html">Lesson 12</a></td></tr>
  <tr><td class="mono">Auto Recall</td><td>prompt 构建前按预算注入相关记忆，超时则保护主对话。</td><td><a href="22-auto-recall-before-prompt.html">Lesson 22</a></td></tr>
  <tr><td class="mono">TdaiCore</td><td>宿主无关的 recall、capture、search、pipeline 门面。</td><td><a href="09-tdai-core-facade.html">Lesson 09</a></td></tr>
  <tr><td class="mono">HostAdapter</td><td>隔离 OpenClaw、Gateway 等宿主差异的边界。</td><td><a href="10-host-adapter-boundaries.html">Lesson 10</a></td></tr>
  <tr><td class="mono">Hermes Gateway</td><td>外部 HTTP 入口，必须处理 health、CORS、auth、日志与部署边界。</td><td><a href="32-hermes-gateway-http-security.html">Lesson 32</a></td></tr>
  <tr><td class="mono">SQLite</td><td>本地元数据、FTS、BM25 和向量表的默认存储线索。</td><td><a href="25-sqlite-vec-fts-bm25-hybrid.html">Lesson 25</a></td></tr>
  <tr><td class="mono">Tencent VectorDB</td><td>远程向量后端，配合 embedding、hybrid search 和降级策略。</td><td><a href="26-tencent-vectordb-embedding.html">Lesson 26</a></td></tr>
  <tr><td class="mono">Context Offload</td><td>短期符号记忆，把长任务工具日志压缩成可恢复地图。</td><td><a href="27-why-long-task-logs-symbolic-compression.html">Lesson 27</a></td></tr>
  <tr><td class="mono">refs</td><td>Offload 摘要回到工具结果证据的引用链。</td><td><a href="28-after-tool-call-refs-offload-jsonl.html">Lesson 28</a></td></tr>
  <tr><td class="mono">JSONL</td><td>追加友好的逐行 JSON 证据格式，用于 L0 与 offload 摘要。</td><td><a href="13-l0-jsonl-recorder.html">Lesson 13</a></td></tr>
  <tr><td class="mono">MMD</td><td>Mermaid 任务地图，概括长任务结构并支持下钻。</td><td><a href="30-mermaid-mmd-node-id-drill-down.html">Lesson 30</a></td></tr>
  <tr><td class="mono">node_id</td><td>MMD 节点与 JSONL / refs 证据之间的稳定索引。</td><td><a href="30-mermaid-mmd-node-id-drill-down.html">Lesson 30</a></td></tr>
  <tr><td class="mono">seed</td><td>将初始记忆数据导入系统的运维动作，必须先验证和 dry run。</td><td><a href="33-seed-cli-migration-export-read.html">Lesson 33</a></td></tr>
  <tr><td class="mono">migration</td><td>例如 SQLite 到 Tencent VectorDB 的可备份、可审计数据移动。</td><td><a href="33-seed-cli-migration-export-read.html">Lesson 33</a></td></tr>
  <tr><td class="mono">glossary</td><td>把术语映射回主要课程页，减少读者和贡献者的上下文漂移。</td><td><a href="34-debug-tests-contribution-glossary.html">Lesson 34</a></td></tr>
</table>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 final guide expectations：最终指南应提供 operator / contributor map、调试清单、测试路径、贡献路径和 glossary。</li>
    <li><span class="inline">CONTRIBUTING.md</span> 与 <span class="inline">CONTRIBUTING_CN.md</span>：贡献前应阅读的流程、测试、提交和 PR 说明。</li>
    <li><span class="inline">package.json</span> scripts 与 <span class="inline">vitest.config.ts</span>：项目认可的 test / build 入口；build 通过 tsdown / tsc 执行构建与类型检查，Vitest 配置测试环境、include/exclude、超时和 mock/env/global reset。</li>
    <li>本图解指南源码：<span class="inline">README.md</span>、<span class="inline">src/shell.py</span>、<span class="inline">src/registry.py</span>、<span class="inline">src/quizzes.py</span>、<span class="inline">src/part1.py</span> 到 <span class="inline">src/part8.py</span>。</li>
    <li>Glossary lesson links：L0、L1、L2、L3 Persona、Scene Block、Auto Capture、Auto Recall、TdaiCore、HostAdapter、Hermes Gateway、SQLite、Tencent VectorDB、Context Offload、refs、JSONL、MMD、node_id、seed、migration 和 glossary 都应指向现有课程页。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  调试顺序是：症状 -&gt; 运行时文件 -&gt; Gateway 状态 -&gt; 配置 -&gt; recall/search -&gt; capture checkpoints -&gt; offload artifacts -&gt; 日志 -&gt; 测试。
  贡献顺序是：读 CONTRIBUTING、读 package scripts / Vitest 配置、写能失败的测试、小步修复、更新指南索引和 glossary、运行共享验证块，再提交。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
The final lesson moves from understanding the system to debugging, validating, and contributing to it. When memory behavior fails, do not start with guesses: classify the symptom, then narrow it through runtime files, Gateway status, config, recall/search behavior, capture checkpoints, Context Offload artifacts, logs, and tests. When contributing code, use
<span class="inline">CONTRIBUTING.md</span>, <span class="inline">CONTRIBUTING_CN.md</span>, <span class="inline">package.json</span> scripts, and
<span class="inline">vitest.config.ts</span> as the accepted validation path.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  Debugging a memory system is like repairing a city delivery chain: first ask whether the package was never sent, never warehoused, hard to find, delivered to the wrong person, or compressed into archive on the road; then inspect branch ledgers, sorting rules, route status, signatures, and quality reports. Contributing code is changing a delivery rule: read the rules, make a small change, then prove with drills and tests that other routes still work.
</div>

<h2>From symptom to contribution path</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>symptom</h4><p>Write the report as an observable symptom: missing capture, empty recall, wrong search hit, unresponsive Gateway, broken offload drill-down, or failing tests.</p><div class="mono">name the failure before fixing it</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>config check</h4><p>Check enable flags, data dir, recall budget, embedding / tcvdb backend, and offload switches before deleting data or changing real credentials.</p><div class="mono">config explains many silent fallbacks</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>runtime files</h4><p>Open L0 JSONL, L1 records, scene_blocks, persona, vectors.db, and context-offload artifacts to locate the layer where the issue begins.</p><div class="mono">files are evidence, not guesses</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>recall / search</h4><p>Reproduce recall or search with a safe query; inspect source ids, budget trimming, hybrid strategy, fallback path, and ranking explanation.</p><div class="mono">query -&gt; candidates -&gt; injected context</div></div></div>
  <div class="step"><div class="num">5</div><div class="sc"><h4>capture / offload</h4><p>Check capture checkpoint, cursor, lock, refs, JSONL summaries, MMD, node_id, and drill-down continuity.</p><div class="mono">checkpoint -&gt; evidence -&gt; compressed map</div></div></div>
  <div class="step"><div class="num">6</div><div class="sc"><h4>tests</h4><p>Write the test that reproduces the problem first, then run existing project scripts; only after it passes should the contribution docs guide the submission.</p><div class="mono">red -&gt; green -&gt; contribution path</div></div></div>
</div>

<h2>Operator debugging checklist vs contributor validation checklist</h2>
<div class="cols">
  <div class="col">
    <h4>Operator debugging checklist</h4>
    <ol>
      <li><strong>Symptom</strong>: decide whether this is capture, recall, search, Gateway, offload, seed/migration, or test behavior.</li>
      <li><strong>Runtime files</strong>: inspect conversations / JSONL, records, scene_blocks, persona, vectors.db, and context-offload.</li>
      <li><strong>Gateway status</strong>: check <span class="inline">GET /health</span>, helper status, bind address, CORS, auth, and redacted logs.</li>
      <li><strong>Config</strong>: verify defaults, data dir, embedding dimensions, backend, timeouts, budgets, and feature flags.</li>
      <li><strong>Recall / search</strong>: use read-only queries to inspect candidates, source ids, ranking, budget cuts, and fallback reasons.</li>
      <li><strong>Capture checkpoints</strong>: inspect cursor, position slice, locks, and duplicate-write clues.</li>
      <li><strong>Offload artifacts</strong>: confirm refs, JSONL, MMD, node_id, and drill-down files point to each other.</li>
      <li><strong>Logs</strong>: keep route, status, duration, and request id; never print tokens, endpoints, full prompts, or private user data.</li>
      <li><strong>Tests</strong>: reproduce the issue with existing tests, then confirm the fix does not break other paths.</li>
    </ol>
  </div>
  <div class="col">
    <h4>Contributor validation checklist</h4>
    <ol>
      <li>Read <span class="inline">CONTRIBUTING.md</span> and <span class="inline">CONTRIBUTING_CN.md</span> for branch, commit, test, and PR expectations.</li>
      <li>Read <span class="inline">package.json</span> scripts and use the existing test / build commands; type checks run through tsdown / tsc in the build scripts.</li>
      <li>Read <span class="inline">vitest.config.ts</span> to understand test environment, include/exclude rules, timeouts, and mock/env/global reset behavior.</li>
      <li>For guide changes, keep <span class="inline">src/shell.py</span>, <span class="inline">src/registry.py</span>, <span class="inline">src/quizzes.py</span>, and the matching <span class="inline">part*.py</span> in sync.</li>
      <li>For core changes, connect new behavior to a real boundary: TdaiCore, HostAdapter, Gateway route, store backend, or pipeline scheduler.</li>
      <li>Tests must prove behavior: fail first, then pass; do not only test mock call counts.</li>
      <li>Update docs and glossary links so terms return to their primary lesson pages.</li>
      <li>Before committing, run the shared validation block and check for broken links, HTML mistakes, real secrets, or generated-file drift.</li>
    </ol>
  </div>
</div>

<h2>Core pseudocode</h2>
<pre class="code">def debug_memory_issue(symptom):
    case = classify(symptom, [
        "capture_missing", "recall_empty", "search_wrong",
        "gateway_down", "offload_broken", "test_failure",
    ])

    runtime = inspect_runtime_files(DATA_DIR_PLACEHOLDER)
    gateway = check_gateway_health(GATEWAY_URL_PLACEHOLDER)
    config = load_redacted_config(CONFIG_PATH_PLACEHOLDER)

    if case in ["recall_empty", "search_wrong"]:
        candidates = run_readonly_search(SAFE_QUERY_PLACEHOLDER)
        explain_budget_and_ranking(candidates)

    if case == "capture_missing":
        inspect_checkpoints_and_locks(runtime.checkpoints)

    if case == "offload_broken":
        verify_refs_jsonl_mmd_node_ids(runtime.offload_dir)

    collect_redacted_logs(request_id=REQUEST_ID_PLACEHOLDER)
    write_or_update_test_that_fails(case)
    run_existing_project_scripts(["test", "build"])
    follow_contributing_docs_before_pr()</pre>

<h2>Glossary / index: terms should return to the main lesson</h2>
<table class="t">
  <tr><th>Term</th><th>Meaning</th><th>Primary lesson link</th></tr>
  <tr><td class="mono">L0</td><td>Raw conversation evidence, stored as JSONL records for traceability.</td><td><a href="13-l0-jsonl-recorder.html">Lesson 13</a></td></tr>
  <tr><td class="mono">L1</td><td>Atomic memory extracted from conversations, with source ids, dedup, and write path.</td><td><a href="15-l1-extraction.html">Lesson 15</a></td></tr>
  <tr><td class="mono">L2</td><td>Navigable scene blocks that organize L1 into mid-term context.</td><td><a href="17-why-l2-scene-blocks.html">Lesson 17</a></td></tr>
  <tr><td class="mono">L3 Persona</td><td>Incremental profile / preference summary generated from scenes and injected as stable context.</td><td><a href="20-persona-generator-incremental.html">Lesson 20</a></td></tr>
  <tr><td class="mono">Scene Block</td><td>A growing, traceable scene file that supports read_file drill-down.</td><td><a href="17-why-l2-scene-blocks.html">Lesson 17</a></td></tr>
  <tr><td class="mono">Auto Capture</td><td>The path that writes L0, indexes vectors, and notifies pipeline after a turn commits.</td><td><a href="12-auto-capture-hook.html">Lesson 12</a></td></tr>
  <tr><td class="mono">Auto Recall</td><td>Before-prompt memory injection under budget, with timeout fallback to protect the main chat.</td><td><a href="22-auto-recall-before-prompt.html">Lesson 22</a></td></tr>
  <tr><td class="mono">TdaiCore</td><td>The host-neutral facade for recall, capture, search, and pipeline operations.</td><td><a href="09-tdai-core-facade.html">Lesson 09</a></td></tr>
  <tr><td class="mono">HostAdapter</td><td>The boundary that isolates host differences such as OpenClaw and Gateway.</td><td><a href="10-host-adapter-boundaries.html">Lesson 10</a></td></tr>
  <tr><td class="mono">Hermes Gateway</td><td>The external HTTP entry that owns health, CORS, auth, logging, and deployment-boundary concerns.</td><td><a href="32-hermes-gateway-http-security.html">Lesson 32</a></td></tr>
  <tr><td class="mono">SQLite</td><td>Local storage clues for metadata tables, FTS, BM25, and vectors.</td><td><a href="25-sqlite-vec-fts-bm25-hybrid.html">Lesson 25</a></td></tr>
  <tr><td class="mono">Tencent VectorDB</td><td>Remote vector backend used with embedding, hybrid search, and degradation strategy.</td><td><a href="26-tencent-vectordb-embedding.html">Lesson 26</a></td></tr>
  <tr><td class="mono">Context Offload</td><td>Short-term symbolic memory that compresses long-task tool logs into a recoverable map.</td><td><a href="27-why-long-task-logs-symbolic-compression.html">Lesson 27</a></td></tr>
  <tr><td class="mono">refs</td><td>The reference chain from Offload summaries back to tool-result evidence.</td><td><a href="28-after-tool-call-refs-offload-jsonl.html">Lesson 28</a></td></tr>
  <tr><td class="mono">JSONL</td><td>Append-friendly one-JSON-object-per-line evidence used by L0 and offload summaries.</td><td><a href="13-l0-jsonl-recorder.html">Lesson 13</a></td></tr>
  <tr><td class="mono">MMD</td><td>Mermaid task map that summarizes long-task structure and supports drill-down.</td><td><a href="30-mermaid-mmd-node-id-drill-down.html">Lesson 30</a></td></tr>
  <tr><td class="mono">node_id</td><td>The stable index between MMD nodes and JSONL / refs evidence.</td><td><a href="30-mermaid-mmd-node-id-drill-down.html">Lesson 30</a></td></tr>
  <tr><td class="mono">seed</td><td>The operational import of initial memory data, requiring validation and dry run first.</td><td><a href="33-seed-cli-migration-export-read.html">Lesson 33</a></td></tr>
  <tr><td class="mono">migration</td><td>Auditable, backed-up data movement such as SQLite to Tencent VectorDB.</td><td><a href="33-seed-cli-migration-export-read.html">Lesson 33</a></td></tr>
  <tr><td class="mono">glossary</td><td>The map from terms back to primary lesson pages, reducing context drift for readers and contributors.</td><td><a href="34-debug-tests-contribution-glossary.html">Lesson 34</a></td></tr>
</table>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec final guide expectations: the closing guide should provide an operator / contributor map, debugging checklist, test path, contribution path, and glossary.</li>
    <li><span class="inline">CONTRIBUTING.md</span> and <span class="inline">CONTRIBUTING_CN.md</span>: contribution flow, tests, commits, and PR expectations to read before changing behavior.</li>
    <li><span class="inline">package.json</span> scripts and <span class="inline">vitest.config.ts</span>: accepted test / build entry points; build runs tsdown / tsc for build and type checks, while Vitest config covers environment, include/exclude, timeouts, and mock/env/global reset.</li>
    <li>Visual-guide source: <span class="inline">README.md</span>, <span class="inline">src/shell.py</span>, <span class="inline">src/registry.py</span>, <span class="inline">src/quizzes.py</span>, and <span class="inline">src/part1.py</span> through <span class="inline">src/part8.py</span>.</li>
    <li>Glossary lesson links: L0, L1, L2, L3 Persona, Scene Block, Auto Capture, Auto Recall, TdaiCore, HostAdapter, Hermes Gateway, SQLite, Tencent VectorDB, Context Offload, refs, JSONL, MMD, node_id, seed, migration, and glossary should all point to existing lesson pages.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Debug in this order: symptom -&gt; runtime files -&gt; Gateway status -&gt; config -&gt; recall/search -&gt; capture checkpoints -&gt; offload artifacts -&gt; logs -&gt; tests.
  Contribute in this order: read CONTRIBUTING, read package scripts / Vitest config, write the failing test, make the small fix, update guide indexes and glossary, run the shared validation block, then commit.
</div>
""",
}


LESSON_33 = {
    "zh": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
记忆系统不只在 live agent loop 里工作。初始化种子、SQLite 到 Tencent VectorDB 的迁移、远程快照导出、本地安全读取和 Gateway 生命周期检查，都应该通过可审计、可回滚的命令完成。本课区分
<span class="inline">openclaw memory-tdai seed</span> CLI、迁移脚本、导出/读取脚本和 <span class="inline">memory-tencentdb-ctl</span> Gateway helper：先读 README 和脚本说明，再做 dry run、备份、manifest、提交和验证。
</p>

<div class="card analogy">
  <div class="tag">🧭 生活类比</div>
  现场对话像餐厅正在营业，不能在客人点菜时搬仓库。Seed、migration、export 和 read scripts 像闭店后的盘点：先锁定清单、拍照备份、试跑一次、看盘点报告，再真正搬货，最后抽查货架是否能被找到。
</div>

<h2>为什么这些动作要离开 live agent loop</h2>
<div class="cols">
  <div class="col"><h4>初始化不是聊天</h4><p><span class="inline">src/cli/commands/seed.ts</span> 接收 operator 提供的 seed JSON 文件；<span class="inline">src/core/seed/input.ts</span> 解析、验证并规范化 sessions；<span class="inline">seed-runtime.ts</span> 组织 seed pipeline，并等待 L1 capture 空闲。它适合准备初始记忆，不应假装成用户的一轮对话。</p></div>
  <div class="col"><h4>迁移不是实时召回</h4><p><span class="inline">scripts/migrate-sqlite-to-tcvdb</span> 把本地 SQLite memory 向 Tencent VectorDB 后端移动。迁移需要配置快照、manifest、dry run、备份和幂等写入，而不是在一次 recall 超时里偷偷完成。</p></div>
  <div class="col"><h4>诊断不是暴露秘密</h4><p>export/read scripts 用于生成可检查的本地或远程快照。它们应保留结构、计数、状态和可脱敏样本，避免把真实 token、endpoint、prompt 或用户敏感内容复制进报告。</p></div>
</div>

<h2>运维时间线：先证明可回滚，再应用</h2>
<div class="timeline">
  <div class="lane"><div class="lane-label">prepare</div><div class="tslot">read docs</div><div class="tslot">choose scope</div><div class="tslot">freeze config</div></div>
  <div class="lane"><div class="lane-label">backup</div><div class="tslot span">copy SQLite / config / existing manifests to BACKUP_DIR_PLACEHOLDER</div></div>
  <div class="lane"><div class="lane-label">dry run</div><div class="tslot">seed JSON validation</div><div class="tslot">migration --dry-run</div><div class="tslot">read-only export</div></div>
  <div class="lane"><div class="lane-label">inspect</div><div class="tslot">manifest</div><div class="tslot">counts</div><div class="tslot">warnings</div><div class="tslot">sample reads</div></div>
  <div class="lane"><div class="lane-label">commit</div><div class="tslot now">run exact reviewed command</div><div class="tslot">write manifest</div></div>
  <div class="lane"><div class="lane-label">verify</div><div class="tslot">local read</div><div class="tslot">search</div><div class="tslot">recall</div><div class="tslot">rollback plan still valid</div></div>
</div>

<h2>Seed 写入路径</h2>
<div class="flow">
  <div class="node"><div class="nt">seed input</div><div class="nd">JSON file only: Format A object or Format B array, with placeholder paths and declared session/user scope.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">input parser</div><div class="nd"><span class="inline">input.ts</span> validates shape, ids, timestamps, required fields, and normalizes sessions.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">seed runtime</div><div class="nd"><span class="inline">seed-runtime.ts</span> orchestrates the seed pipeline, waits for L1 capture to idle, and expects a fresh output directory; do not assume resume.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">storage adapter</div><div class="nd">SQLite or Tencent VectorDB backend receives checked records.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">verification read</div><div class="nd">read/search confirms the expected records without leaking credentials.</div></div>
</div>

<h2>脚本和命令何时使用</h2>
<div class="card warn">
  <div class="tag">⚠️ 先确认真实参数</div>
  下表使用当前已知命令形态和占位路径，但不替代脚本 README。注意 OpenClaw CLI namespace 仍是 <span class="inline">memory-tdai</span>，即使插件品牌叫 <span class="inline">memory-tencentdb</span>。运行前必须打开对应 README / entry file，确认该命令到底是只读、预演还是写入。表中的 <span class="inline">seed</span> 是 OpenClaw 子命令（<span class="inline">openclaw memory-tdai seed</span>）；<span class="inline">migrate-sqlite-to-tcvdb</span>、<span class="inline">export-tencent-vdb</span>、<span class="inline">read-local-memory</span> 则是 <span class="inline">package.json</span> 注册的 bin，通常用对应的 npm run 脚本、<span class="inline">node ./bin/&lt;name&gt;.mjs</span> 或软链到 PATH 后调用，直接粘贴裸命令名前先确认它已在 PATH 上。
</div>
<table class="t">
  <tr><th>Script / command</th><th>When to use</th><th>Inputs</th><th>Outputs</th><th>Safety check</th></tr>
  <tr><td class="mono">openclaw memory-tdai seed --input SEED_FILE_PLACEHOLDER</td><td>验证并写入初始 memory seed JSON 文件。</td><td>SEED_FILE_PLACEHOLDER（Format A object 或 Format B array）。</td><td>校验结果、拒绝原因、seed pipeline 写入摘要。</td><td>CLI namespace 是 <span class="inline">memory-tdai</span>；seed runtime 期望新的输出目录，不要假设可 resume。</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --dry-run</td><td>评估从本地 SQLite 到 Tencent VectorDB 的迁移。</td><td><span class="inline">--plugin-data-dir</span> 与 <span class="inline">--openclaw-config-path</span>（必填）、TCVDB 连接 flag <span class="inline">--tcvdb-url</span> / <span class="inline">--tcvdb-username</span> / <span class="inline">--tcvdb-database</span> / <span class="inline">--tcvdb-embedding-model</span>（api-key 用 <span class="inline">--tcvdb-api-key</span> 占位）；<span class="inline">--sqlite-path</span> 可选，默认取 data dir 下的 <span class="inline">vectors.db</span>。</td><td>迁移计划、collection 检查、manifest 草稿。</td><td>先备份 SQLite，确认 endpoint / token 只来自占位配置或安全环境。</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --yes</td><td>dry run、manifest 和备份都通过后，使用相同输入执行提交；不要使用不存在的 <span class="inline">--apply</span>。</td><td>同一份已审阅配置与输入快照。</td><td>写入远程集合、正式 manifest、计数摘要。</td><td><span class="inline">--apply-config</span> 是配置更新，不是迁移 apply；写入幂等性来自迁移里的 upsertL0 / upsertL1。</td></tr>
  <tr><td class="mono">export-tencent-vdb --output SNAPSHOT_PATH_PLACEHOLDER</td><td>生成远程 VectorDB 诊断快照。</td><td>只读远程配置、collection 名、脱敏规则。</td><td>结构化 snapshot 或摘要文件。</td><td>不导出真实凭据；样本内容按策略截断或脱敏。</td></tr>
  <tr><td class="mono">read-local-memory --data-dir LOCAL_MEMORY_DIR_PLACEHOLDER</td><td>本地排查 recall/search 前的 memory 状态。</td><td>包含 <span class="inline">vectors.db</span> 的本地 memory 数据目录、查询条件、limit；也可用 <span class="inline">-d</span>。</td><td>只读表统计、匹配记录、source ids。</td><td>参数指向 data dir，不是单个 SQLite db 文件；默认只读、小 limit。</td></tr>
  <tr><td class="mono">TDAI_DATA_DIR=LOCAL_MEMORY_DIR_PLACEHOLDER scripts/memory-tencentdb-ctl.sh status</td><td>检查 Gateway 生命周期和配置状态。</td><td>固定路径或环境变量中的 data dir；没有 <span class="inline">--config</span> flag。</td><td>Gateway 状态与配置诊断。</td><td>它是 Gateway lifecycle/config helper，不是 seed、migrate、export、read 脚本的总编排器。</td></tr>
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
    result = run_seed_or_migration(plan, mode="commit")
    verify_with_read_script(result.expected_records, readonly=True)
    verify_with_search_or_recall(SAFE_QUERY_PLACEHOLDER)</pre>

<h2>读脚本时重点看什么</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>入口参数</h4><p><span class="inline">cli-entry.ts</span>、shell wrapper 和 README 应说明哪些参数只读、哪些会写入、哪些需要 dry run。看不懂参数时不要运行。</p><div class="mono">read docs before scripts</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>配置写入</h4><p><span class="inline">config-write.ts</span> 一类脚本可能改变运行配置。更新配置前先保存副本，输出里只允许 CONFIG_PATH_PLACEHOLDER 这类安全占位。</p><div class="mono">backup config before update</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>manifest 写入</h4><p><span class="inline">manifest-write.ts</span> 会重写 store pointer 并创建 <span class="inline">.migrate.bak</span> 备份；它提供回滚与审计线索，但不要引用不存在的 <span class="inline">manifest.id</span>。</p><div class="mono">manifest proves what changed</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>验证读取</h4><p><span class="inline">read-local-memory.ts</span> 和 export snapshot 用于确认结果。默认只读、小范围、可脱敏；发现异常先停，不要连环写入。</p><div class="mono">read before and after commit</div></div></div>
</div>

<h2>源码锚点</h2>
<div class="card detail">
  <div class="tag">🔬 源码锚点</div>
  <ul>
    <li>批准规格 Part 8 operations：本课覆盖 live loop 外的 seed、migration、export、read、diagnostic 和 operator workflow。</li>
    <li><span class="inline">src/cli/commands/seed.ts</span>、<span class="inline">src/core/seed/input.ts</span>、<span class="inline">src/core/seed/seed-runtime.ts</span>：<span class="inline">openclaw memory-tdai seed</span>、JSON 输入校验 / session 规范化，以及 seed pipeline 运行时。</li>
    <li><span class="inline">src/cli/README.md</span>：CLI 行为、参数和安全使用说明。</li>
    <li><span class="inline">scripts/migrate-sqlite-to-tcvdb/README.md</span>、<span class="inline">cli-entry.ts</span>、<span class="inline">sqlite-to-tcvdb.ts</span>、<span class="inline">config-write.ts</span>、<span class="inline">manifest-write.ts</span>：迁移入口、数据移动、配置写入、manifest pointer 和 <span class="inline">.migrate.bak</span>。</li>
    <li><span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span> 与 <span class="inline">scripts/read-local-memory/read-local-memory.ts</span>：远程导出和本地只读检查。</li>
    <li><span class="inline">scripts/export-diagnostic.sh</span>、<span class="inline">scripts/memory-tencentdb-ctl.sh</span>、<span class="inline">scripts/README.memory-tencentdb-ctl.md</span>：诊断打包，以及 Gateway lifecycle/config helper。</li>
    <li><span class="inline">scripts/install_hermes_memory_tencentdb.sh</span>、<span class="inline">scripts/setup-offload.sh</span>：阅读它们以理解安装/离线化脚本的副作用；本课不提供安装步骤，也不建议把它们当迁移快捷方式。</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ 本课要点</div>
  Seed、迁移、导出、诊断、本地读取和 Gateway 状态检查都是 live loop 外的运维动作。安全顺序是：读文档、限定范围、备份、dry run、检查 manifest / export、再用明确的提交命令执行、最后用只读脚本和 recall/search 验证。
  命令示例必须只含占位路径、占位配置和真实存在的 dry-run / commit 语义，不出现真实 endpoint、token、不存在的 flag 或安装指令。
</div>
""",
    "en": r"""
<p class="lead" style="font-size:1.06rem;color:var(--muted);margin-top:-.6rem">
The memory system does more than run inside the live agent loop. Initial seeding, SQLite to Tencent VectorDB migration, remote snapshot export, safe local reads, and Gateway lifecycle checks should be handled by auditable, reversible commands. This lesson separates the
<span class="inline">openclaw memory-tdai seed</span> CLI, migration scripts, export/read scripts, and the <span class="inline">memory-tencentdb-ctl</span> Gateway helper: read the READMEs and script docs first, then dry run, back up, inspect manifests, commit, and verify.
</p>

<div class="card analogy">
  <div class="tag">🧭 Analogy</div>
  A live conversation is like a restaurant during service; you should not move the warehouse while guests are ordering. Seed, migration, export, and read scripts are closing-time inventory: lock the checklist, take backup photos, rehearse once, inspect the inventory report, move the stock, then sample-check that shelves can be found.
</div>

<h2>Why these actions stay outside the live agent loop</h2>
<div class="cols">
  <div class="col"><h4>Initialization is not chat</h4><p><span class="inline">src/cli/commands/seed.ts</span> accepts an operator-provided seed JSON file; <span class="inline">src/core/seed/input.ts</span> parses, validates, and normalizes sessions; <span class="inline">seed-runtime.ts</span> orchestrates the seed pipeline and waits for L1 capture to idle. This prepares initial memory; it should not pretend to be a user turn.</p></div>
  <div class="col"><h4>Migration is not realtime recall</h4><p><span class="inline">scripts/migrate-sqlite-to-tcvdb</span> moves local SQLite memory toward Tencent VectorDB. Migration needs config snapshots, manifests, dry runs, backups, and idempotent writes, not a hidden side effect inside one recall timeout.</p></div>
  <div class="col"><h4>Diagnostics are not secret dumps</h4><p>Export/read scripts create inspectable local or remote snapshots. They should preserve structure, counts, status, and redacted samples without copying real tokens, endpoints, prompts, or sensitive user content into reports.</p></div>
</div>

<h2>Operational timeline: prove rollback first, then commit</h2>
<div class="timeline">
  <div class="lane"><div class="lane-label">prepare</div><div class="tslot">read docs</div><div class="tslot">choose scope</div><div class="tslot">freeze config</div></div>
  <div class="lane"><div class="lane-label">backup</div><div class="tslot span">copy SQLite / config / existing manifests to BACKUP_DIR_PLACEHOLDER</div></div>
  <div class="lane"><div class="lane-label">dry run</div><div class="tslot">seed JSON validation</div><div class="tslot">migration --dry-run</div><div class="tslot">read-only export</div></div>
  <div class="lane"><div class="lane-label">inspect</div><div class="tslot">manifest</div><div class="tslot">counts</div><div class="tslot">warnings</div><div class="tslot">sample reads</div></div>
  <div class="lane"><div class="lane-label">commit</div><div class="tslot now">run exact reviewed command</div><div class="tslot">write manifest</div></div>
  <div class="lane"><div class="lane-label">verify</div><div class="tslot">local read</div><div class="tslot">search</div><div class="tslot">recall</div><div class="tslot">rollback plan still valid</div></div>
</div>

<h2>Seed write path</h2>
<div class="flow">
  <div class="node"><div class="nt">seed input</div><div class="nd">JSON file only: Format A object or Format B array, with placeholder paths and declared session/user scope.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">input parser</div><div class="nd"><span class="inline">input.ts</span> validates shape, ids, timestamps, required fields, and normalizes sessions.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node hl"><div class="nt">seed runtime</div><div class="nd"><span class="inline">seed-runtime.ts</span> orchestrates the seed pipeline, waits for L1 capture to idle, and expects a fresh output directory; do not assume resume.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">storage adapter</div><div class="nd">SQLite or Tencent VectorDB backend receives checked records.</div></div>
  <div class="arrow">-&gt;</div>
  <div class="node"><div class="nt">verification read</div><div class="nd">read/search confirms expected records without leaking credentials.</div></div>
</div>

<h2>When to use each script or command</h2>
<div class="card warn">
  <div class="tag">⚠️ Confirm real flags first</div>
  The table uses currently known command shapes and placeholder paths, but it does not replace each script README. Note that the OpenClaw CLI namespace remains <span class="inline">memory-tdai</span> even though the plugin brand is <span class="inline">memory-tencentdb</span>. Before running anything, open the matching README / entry file and confirm whether the command is read-only, a preview, or a write. The <span class="inline">seed</span> row is an OpenClaw subcommand (<span class="inline">openclaw memory-tdai seed</span>); <span class="inline">migrate-sqlite-to-tcvdb</span>, <span class="inline">export-tencent-vdb</span>, and <span class="inline">read-local-memory</span> are <span class="inline">package.json</span> bin entries, usually invoked through their npm run scripts, <span class="inline">node ./bin/&lt;name&gt;.mjs</span>, or after symlinking onto PATH, so confirm the bin is on PATH before pasting a bare command name.
</div>
<table class="t">
  <tr><th>Script / command</th><th>When to use</th><th>Inputs</th><th>Outputs</th><th>Safety check</th></tr>
  <tr><td class="mono">openclaw memory-tdai seed --input SEED_FILE_PLACEHOLDER</td><td>Validate and write an initial memory seed JSON file.</td><td>SEED_FILE_PLACEHOLDER (Format A object or Format B array).</td><td>Validation result, rejection reasons, seed pipeline write summary.</td><td>The CLI namespace is <span class="inline">memory-tdai</span>; seed runtime expects a fresh output directory, so do not assume resume.</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --dry-run</td><td>Assess migration from local SQLite to Tencent VectorDB.</td><td><span class="inline">--plugin-data-dir</span> and <span class="inline">--openclaw-config-path</span> (required), plus the TCVDB connection flags <span class="inline">--tcvdb-url</span> / <span class="inline">--tcvdb-username</span> / <span class="inline">--tcvdb-database</span> / <span class="inline">--tcvdb-embedding-model</span> (with <span class="inline">--tcvdb-api-key</span> as a placeholder); <span class="inline">--sqlite-path</span> is optional, defaulting to <span class="inline">vectors.db</span> under the data dir.</td><td>Migration plan, collection checks, manifest draft.</td><td>Back up SQLite first; confirm endpoint / token come only from placeholder config or secure environment.</td></tr>
  <tr><td class="mono">migrate-sqlite-to-tcvdb --yes</td><td>Commit with the same inputs only after dry run, manifest, and backup pass review; do not use nonexistent <span class="inline">--apply</span>.</td><td>The same reviewed config and input snapshot.</td><td>Remote collection writes, final manifest, count summary.</td><td><span class="inline">--apply-config</span> updates config; it is not migration apply. Idempotency comes from migration upsertL0 / upsertL1 calls.</td></tr>
  <tr><td class="mono">export-tencent-vdb --output SNAPSHOT_PATH_PLACEHOLDER</td><td>Create a remote VectorDB diagnostic snapshot.</td><td>Read-only remote config, collection name, redaction rules.</td><td>Structured snapshot or summary file.</td><td>Do not export real credentials; truncate or redact sample content by policy.</td></tr>
  <tr><td class="mono">read-local-memory --data-dir LOCAL_MEMORY_DIR_PLACEHOLDER</td><td>Inspect memory state before debugging recall/search.</td><td>Local memory data directory containing <span class="inline">vectors.db</span>, query filters, limit; <span class="inline">-d</span> is the short form.</td><td>Read-only table stats, matching records, source ids.</td><td>The argument points at a data dir, not one SQLite db file; default to read-only and small limits.</td></tr>
  <tr><td class="mono">TDAI_DATA_DIR=LOCAL_MEMORY_DIR_PLACEHOLDER scripts/memory-tencentdb-ctl.sh status</td><td>Check Gateway lifecycle and configuration status.</td><td>Data dir from fixed paths or environment; no <span class="inline">--config</span> flag.</td><td>Gateway status and config diagnostics.</td><td>It is a Gateway lifecycle/config helper, not the orchestrator for seed, migrate, export, or read scripts.</td></tr>
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
    result = run_seed_or_migration(plan, mode="commit")
    verify_with_read_script(result.expected_records, readonly=True)
    verify_with_search_or_recall(SAFE_QUERY_PLACEHOLDER)</pre>

<h2>What to inspect before running scripts</h2>
<div class="vflow">
  <div class="step"><div class="num">1</div><div class="sc"><h4>Entry arguments</h4><p><span class="inline">cli-entry.ts</span>, shell wrappers, and READMEs should say which arguments are read-only, which write data, and which require dry run. If the arguments are unclear, do not run the script.</p><div class="mono">read docs before scripts</div></div></div>
  <div class="step"><div class="num">2</div><div class="sc"><h4>Config writes</h4><p>Scripts such as <span class="inline">config-write.ts</span> may change runtime config. Save a config copy before updating it, and allow only safe placeholders such as CONFIG_PATH_PLACEHOLDER in output.</p><div class="mono">backup config before update</div></div></div>
  <div class="step"><div class="num">3</div><div class="sc"><h4>Manifest writes</h4><p><span class="inline">manifest-write.ts</span> rewrites the store pointer and creates a <span class="inline">.migrate.bak</span> backup; it provides rollback and audit clues, but do not reference a nonexistent <span class="inline">manifest.id</span>.</p><div class="mono">manifest proves what changed</div></div></div>
  <div class="step"><div class="num">4</div><div class="sc"><h4>Verification reads</h4><p><span class="inline">read-local-memory.ts</span> and export snapshots confirm results. Default to read-only, narrow scope, and redaction; if something looks wrong, stop instead of chaining write runs.</p><div class="mono">read before and after commit</div></div></div>
</div>

<h2>Source anchors</h2>
<div class="card detail">
  <div class="tag">🔬 Source anchors</div>
  <ul>
    <li>Approved spec Part 8 operations: this lesson covers seed, migration, export, read, diagnostic, and operator workflows outside the live loop.</li>
    <li><span class="inline">src/cli/commands/seed.ts</span>, <span class="inline">src/core/seed/input.ts</span>, and <span class="inline">src/core/seed/seed-runtime.ts</span>: <span class="inline">openclaw memory-tdai seed</span>, JSON input validation / session normalization, and the seed pipeline runtime.</li>
    <li><span class="inline">src/cli/README.md</span>: CLI behavior, parameters, and safe usage notes.</li>
    <li><span class="inline">scripts/migrate-sqlite-to-tcvdb/README.md</span>, <span class="inline">cli-entry.ts</span>, <span class="inline">sqlite-to-tcvdb.ts</span>, <span class="inline">config-write.ts</span>, and <span class="inline">manifest-write.ts</span>: migration entry, data movement, config writes, manifest pointer, and <span class="inline">.migrate.bak</span>.</li>
    <li><span class="inline">scripts/export-tencent-vdb/export-tencent-vdb.ts</span> and <span class="inline">scripts/read-local-memory/read-local-memory.ts</span>: remote export and local read-only inspection.</li>
    <li><span class="inline">scripts/export-diagnostic.sh</span>, <span class="inline">scripts/memory-tencentdb-ctl.sh</span>, and <span class="inline">scripts/README.memory-tencentdb-ctl.md</span>: diagnostic bundling and the Gateway lifecycle/config helper.</li>
    <li><span class="inline">scripts/install_hermes_memory_tencentdb.sh</span> and <span class="inline">scripts/setup-offload.sh</span>: read them to understand setup/offload side effects; this lesson gives no installation steps and does not treat them as migration shortcuts.</li>
  </ul>
</div>

<div class="card key">
  <div class="tag">✅ Key points</div>
  Seed, migration, export, diagnostics, local reads, and Gateway status checks are operational actions outside the live loop. The safe order is: read docs, limit scope, back up, dry run, inspect manifest / export, run the explicit commit command, then verify with read-only scripts plus recall/search.
  Command examples must use only placeholder paths, placeholder config, and real dry-run / commit semantics, with no real endpoints, tokens, nonexistent flags, or installation instructions.
</div>
""",
}
