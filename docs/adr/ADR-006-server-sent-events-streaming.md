# ADR-006: Server-Sent Events (SSE) vs WebSockets for AI Response Streaming

## Status
Accepted

## Context & Problem Statement
Large Language Models generate responses incrementally token-by-token. For optimal user experience, visitors should see tokens streamed with sub-second Time-to-First-Token (TTFT) rather than waiting 5–10 seconds for the entire completion.

The two primary protocols for streaming data to modern web clients are:
1. **WebSockets (RFC 6455):** Full-duplex persistent bidirectional socket.
2. **Server-Sent Events (SSE / EventSource, HTML5):** Unidirectional server-to-client streaming over standard HTTP/1.1 or HTTP/2.

## Decision
We select **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse` for streaming AI responses.

## Consequences & Trade-offs

### Positive
* **HTTP/2 Multiplexing:** Operates over standard HTTP connections, sharing existing TCP handshakes and TLS sessions without custom protocol switching (`101 Switching Protocols`).
* **Firewall & Proxy Compatibility:** Fully compatible with enterprise firewalls, CDNs (Firebase Hosting, Cloudflare), and standard HTTP load balancers without special timeout/keepalive configurations.
* **Auto-Reconnection:** Native browser `EventSource` and modern `fetch` stream readers support automatic reconnection and backpressure.
* **Statelessness in Cloud Run:** Serverless containers handle standard streaming HTTP responses gracefully without needing persistent sticky sessions or cross-pod WebSocket state synchronization.

### Negative / Mitigations
* **Unidirectional Only:** Client cannot send upstream messages over the same stream channel.
  * *Evaluation:* Chat interactions are fundamentally request-response loops (visitor sends a prompt, server streams tokens back). Bidirectional full-duplex communication is unnecessary for this workflow.
