# ADR-007: Multi-Tier Token Bucket Rate Limiting & Recruiter Lead Capture

## Status
Accepted

## Context & Problem Statement
Exposing an LLM chat endpoint publicly introduces two significant business risks:
1. **Financial Exhaustion / Denial-of-Wallet (DoW):** Automated bots or malicious actors repeatedly invoking the AI endpoint, running up API consumption and compute bills.
2. **Missed Opportunity for Recruiter Engagement:** High-value visitors (engineering hiring managers, technical recruiters) may interact with the portfolio and leave without providing contact information.

## Decision
We implement a **Two-Tier Token Bucket Rate Limiter** integrated with **Firebase Authentication & Firestore Lead Capture**:

1. **Anonymous Tier (Zero Friction):**
   * Identified by client IP (retrieved from `X-Forwarded-For` with trusted proxy validation) or client session token.
   * **Allowance:** 5 queries per rolling 24-hour window.
   * **Purpose:** Allows visitors to immediately test the agent without friction.
2. **Authenticated Tier (Lead Unlocked):**
   * Identified by verified Firebase Authentication JWT (Google OAuth, GitHub OAuth, or Email).
   * **Allowance:** 30 queries per rolling 24-hour window.
   * **Activation:** When anonymous quota is exhausted (or on demand), the UI displays a clean modal: *"Unlock 30 questions/day and connect with Brandon by signing in with Google or GitHub."*
3. **Multi-Channel Lead Capture & Contact Forwarding:**
   * Upon successful JWT verification in FastAPI, visitor identity (Name, Email, Photo URL, Provider, Timestamp) and user questions are upserted into **Google Cloud Firestore** (Free Tier: 20k writes/day).
   * For explicit contact inquiries submitted via the Contact modal, the service routes through a multi-channel pipeline (`backend/app/services/firestore_service.py`):
     - **Firestore Record:** Stored in the `contact_submissions` collection with review status.
     - **Real-Time Webhooks:** Asynchronously posts formatted alerts to Discord or Slack.
     - **Direct SMTP Forwarding:** Transmits authenticated emails with TLS (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`).
     - **Resend API Failover:** Transmits via Resend's REST API (`RESEND_API_KEY`) if configured.
     - **Secret Management:** Sensitive credentials (`SMTP_PASSWORD`, `RESEND_API_KEY`, `LEAD_NOTIFICATION_WEBHOOK_URL`) are stored in Google Cloud Secret Manager and mounted as environment variables at runtime in Cloud Run, keeping IaC state and application code completely keyless.

## Consequences & Trade-offs

### Positive
* **Budget Security:** Hard daily quota limits per IP/UID ensure total monthly Gemini API costs remain capped under \$1–\$2 even under sustained traffic.
* **Lead Conversion:** Converts passive site visitors into verified recruiter contacts.
* **Reliable Contact Delivery:** Multi-channel alerting (Firestore + Webhook + SMTP + Resend) ensures recruiter inquiries are never dropped even if an individual notification provider experiences an outage.
* **Security Architecture Demonstration:** Proves proficiency in OAuth2/OIDC token verification in Python and keyless secret management via GCP Secret Manager without external middleware bottlenecks.

### Negative / Mitigations
* **Shared IP Collisions:** Users on shared enterprise proxies (corporate VPNs) share the 5-query anonymous limit.
  * *Mitigation:* Signing in with 1-click Google or GitHub authentication immediately bypasses the IP bucket and grants dedicated user-specific quotas.

