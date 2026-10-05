# ADR-005: Workload Identity Federation (WIF) vs Long-Lived Service Account Keys

## Status
Accepted

## Context & Problem Statement
CI/CD automation in GitHub Actions requires authentication to Google Cloud Platform to:
1. Run `terraform plan` and `terraform apply`
2. Push container images to Google Artifact Registry
3. Deploy new revisions to Google Cloud Run
4. Upload Gold MLOps artifacts to Google Cloud Storage

The legacy approach generates a static JSON Service Account Key downloaded from GCP IAM and stored in GitHub repository secrets.

**Risks of Static Service Account Keys:**
* Long-lived credentials subject to credential leakage and exfiltration.
* Lack of automated key rotation, violating zero-trust and CIS GCP Foundation benchmarks.
* Overly broad permissions frequently granted to a single static key.

## Decision
We implement **GCP Workload Identity Federation (WIF)** with OpenID Connect (OIDC):
1. Configure a Workload Identity Pool and Workload Identity Provider in GCP IAM backed by `https://token.actions.githubusercontent.com`.
2. Configure attribute condition filtering strictly restricting token exchange to repository `repo:brandocomando/portfolio:*`.
3. GitHub Actions requests a short-lived, cryptographically signed OIDC JWT token per job execution.
4. GCP STS (Security Token Service) validates the GitHub JWT and issues a temporary OAuth2 access token with a 1-hour expiration.

## Consequences & Trade-offs

### Positive
* **Zero Secret Storage:** No static service account keys stored in GitHub repository secrets or local machines.
* **Granular Least Privilege:** Different GitHub workflows (e.g. PR verification vs production merge) can be mapped to different service accounts with scoped permissions.
* **Auditability:** Every token exchange is explicitly logged in Google Cloud Cloud Audit Logs with the exact GitHub workflow run ID, actor, and commit SHA.

### Negative / Mitigations
* **Initial Setup Overhead:** Requires configuring IAM pools, providers, and attribute mappings in Terraform before the first CI pipeline can authenticate.
  * *Mitigation:* Automated via a repeatable Terraform module (`infra/modules/iam_wif`) and a one-time bootstrap bash script.
