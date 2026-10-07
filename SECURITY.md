# Security Policy

Security, least privilege, and defense-in-depth are foundational architectural priorities for Brandon Foster's portfolio and associated cloud infrastructure.

## Supported Versions

Only the latest commit on the `main` branch deployed to the production environment is actively supported and monitored for security issues.

| Version / Branch | Supported |
| :--- | :--- |
| `main` (Production Deployment) | :white_check_mark: |
| Historical releases & experimental branches | :x: |

---

## Reporting a Vulnerability

If you believe you have discovered a security vulnerability in this repository or the live deployed infrastructure, please report it responsibly. **Do not create public GitHub issues, discussions, or pull requests for security vulnerabilities.**

### How to Report

Please submit a private report using **GitHub Private Vulnerability Reporting**:
1. Navigate to the repository's [Security Advisories](https://github.com/brandocomando/portfolio/security/advisories) tab.
2. Click **Report a vulnerability**.
3. Fill in the advisory details, potential impact, and reproduction steps.

This ensures the report is triaged privately and securely. For non-technical inquiries or if you are unable to use GitHub Private Vulnerability Reporting, you may connect via [LinkedIn](https://linkedin.com/in/brando-foster).

### Information to Include

To help triage and resolve the issue quickly, please include:
- A clear description of the vulnerability and potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Affected endpoints, files, or cloud components (e.g., Cloud Run API routes, Firebase Auth token validation, Firestore security rules).
- Any proposed remediations or patches (conceptual; see [CONTRIBUTING.md](CONTRIBUTING.md)).

---

## Scope & Architectural Context

This application runs on Google Cloud Platform (GCP) and Firebase with a scale-to-zero serverless architecture.

### In Scope
- Cryptographic bypasses or vulnerabilities in Firebase Auth JWT verification.
- Server-Side Request Forgery (SSRF) or Local File Inclusion (LFI).
- Injection flaws (command injection, Firestore NoSQL injection).
- Insecure direct object references (IDOR) or unauthorized data access in Firestore.
- Secret exposure or credential leakage in git history or CI/CD pipelines.
- Workload Identity Federation (WIF) / OIDC misconfigurations enabling unauthorized role assumption.

### Out of Scope
- Distributed Denial of Service (DDoS) or volumetric traffic flooding against rate-limited endpoints.
- Spamming public recruiter lead forms or token-bucket rate limiter exhaustion without proof of technical compromise.
- Theoretical issues without demonstrable impact or working PoC.
- Attacks requiring physical device access or social engineering (phishing).
- Vulnerabilities in third-party services (GitHub, Google Cloud, Firebase) outside this project's administrative configuration.

---

## Response & Disclosure Process

1. **Acknowledgment:** Vulnerability reports will be acknowledged within **48 hours**.
2. **Investigation & Triage:** The issue will be investigated and severity assessed.
3. **Remediation:** A fix will be developed, tested, and deployed to production.
4. **Coordinated Disclosure:** We kindly request that you maintain confidentiality until a fix has been deployed to production.

---

## Safe Harbor

Any security research conducted in good faith that respects visitor privacy, avoids data destruction or system degradation, and complies with this policy will be considered authorized. We will not pursue legal action against researchers acting in accordance with these guidelines.
