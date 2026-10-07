"""Conversational Synthesizer for Brandon Foster's Portfolio Assistant.

Generates fluid, natural, conversational responses answering questions about
Brandon's engineering background, architecture decisions, and projects.
Strictly protects personal privacy: never reveals email, phone, or private data.
"""

import re
import difflib
from typing import List, Dict, Any, Optional

from backend.app.services.intent import detect_approved_personal


def clean_text(text: str) -> str:
    """Removes internal tags, bracketed headers, and metadata."""
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\(GitHub Stars:\s*\d+\)", "", text)
    return text.strip()


PERSONAL_TOPIC_KEYWORDS = {
    "hobby", "hobbies", "personal", "profile", "pizza", "pineapple", "food",
    "cat", "cats", "pet", "pets", "dog", "dogs", "music", "guitar", "band",
    "coffee", "tea", "drink", "hike", "hiking", "camp", "camping", "cook", "cooking",
    "lifestyle", "fun", "preference", "preferences", "workplace", "hybrid", "remote", "office",
    "relocate", "relocation", "location", "live", "living", "california", "orange county", "early bird",
    "night owl", "dad joke", "dad jokes", "color", "season", "emoji", "yosemite"
}


def matches_topic(query: str, targets: List[str], threshold: float = 0.75) -> bool:
    """Fuzzy and substring topic matcher supporting plurals, typos, and variations."""
    q = query.lower().strip()
    for t in targets:
        if t in q:
            return True
    words = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", q)
    for w in words:
        for t in targets:
            if t.startswith(w) or w.startswith(t):
                return True
            if difflib.SequenceMatcher(None, w, t).ratio() >= threshold:
                return True
    return False


def is_affirmative_followup(query: str) -> bool:
    """Checks if a user query is an affirmative continuation like 'yes', 'yea tell me more', 'sure'."""
    q = query.lower().strip().rstrip(".!?,")
    patterns = [
        r"^(?:(?:yes|yea|yeah|yep|yup|sure|ok|okay)\b|tell\s+me\s+more\b|go\s+on\b|continue\b|elaborate\b|more\s+details\b)",
        r"^tell\s+me\s+more(?:\s+about\s+(?:that|this|it))?\b",
        r"^give\s+me\s+more(?:\s+details)?\b",
        r"^(?:i(?:'d|\s+would)?\s+)?(?:love|like|want)\s+to\s+(?:hear|know|learn)\s+more\b",
        r"^sounds\s+good\b",
        r"^let'?s\s+hear\s+it\b",
        r"^sure\s+thing\b",
    ]
    return any(re.match(pat, q) for pat in patterns)


def is_conversational_followup(
    query: str,
    conversation_history: Optional[List[Any]] = None
) -> bool:
    """Detects if query is an affirmative continuation, short topic reply, or follow-up to prior assistant turn."""
    if not conversation_history:
        return False

    if is_affirmative_followup(query):
        return True

    q = query.lower().strip().rstrip(".!?,")
    words = re.findall(r"\b[a-zA-Z0-9_\-]+\b", q)

    # Referential phrases ("the process", "that one", "tell me about that", "how does that work")
    referential_patterns = [
        r"^(?:the|that|this)\s+(?:process|workflow|tooling|system|architecture|part|one|second\s+one|first\s+one|third\s+one)$",
        r"^(?:what\s+about|how\s+about|tell\s+me\s+about)\s+(?:the\s+)?(?:process|workflow|tooling|gitops|security|observability|rag|pipeline|cold\s+starts?)$",
        r"^(?:can\s+you\s+elaborate|can\s+you\s+explain|give\s+me\s+more(?:\s+details)?)$",
        r"^(?:both|all\s+of\s+them|all\s+three|any\s+of\s+them)$",
    ]
    if any(re.match(pat, q) for pat in referential_patterns):
        return True

    # Find last assistant message
    last_asst = ""
    for m in reversed(conversation_history):
        role = m.get("role", "") if isinstance(m, dict) else getattr(m, "role", "")
        content = m.get("content", "") if isinstance(m, dict) else getattr(m, "content", "")
        if role in ("assistant", "model") and content:
            last_asst = content.lower()
            break

    if not last_asst:
        return False

    # Short response (1-4 words) that matches key topics offered in previous assistant turn
    if len(words) <= 4:
        candidate_topics = [
            "process", "migration", "gitops", "workflow", "argocd", "observability", "tooling",
            "security", "mtls", "mesh", "networking", "rag", "retrieval", "medallion", "pipeline",
            "cold start", "cold starts", "scale to zero", "finops", "ci/cd", "runners", "terraform"
        ]
        relevant_candidates = [t for t in candidate_topics if t in last_asst]
        if relevant_candidates and matches_topic(q, relevant_candidates):
            return True

    # Short reply (<= 8 words) that echoes one of the options offered in the assistant's trailing question,
    # e.g. "Would you like ... the CI/CD eval quality gates, or the Terraform setup?" -> "eval gates"
    if len(words) <= 8:
        offered = re.findall(r"[^.!?\n]*\?", last_asst)
        if offered:
            option_words = {
                w for w in re.findall(r"[a-z0-9][a-z0-9/\-]{2,}", offered[-1])
                if w not in _OPTION_STOPWORDS
            }
            reply_words = [w for w in re.findall(r"[a-z0-9][a-z0-9/\-]{2,}", q) if w not in _OPTION_STOPWORDS]
            for rw in reply_words:
                for ow in option_words:
                    if rw == ow or (len(rw) >= 4 and (ow.startswith(rw) or rw.startswith(ow))) \
                            or difflib.SequenceMatcher(None, rw, ow).ratio() >= 0.8:
                        return True

    return False


_OPTION_STOPWORDS = {
    "the", "and", "you", "your", "would", "like", "know", "more", "about", "want", "learn", "hear",
    "explore", "dive", "into", "deeper", "next", "his", "how", "what", "are", "there", "any", "specific",
    "curious", "tell", "with", "for", "that", "this", "does", "did", "can", "next", "patterns",
}


_CONTINUATION_FILLER_WORDS = {
    "yes", "yea", "yeah", "yep", "yup", "sure", "ok", "okay", "please", "pls", "thing",
    "tell", "me", "more", "go", "on", "continue", "elaborate", "details", "detail",
    "about", "that", "this", "it", "the", "a", "an", "of", "on", "sounds", "good", "great",
    "let", "lets", "let's", "hear", "i", "i'd", "id", "would", "love", "like", "want", "to",
    "know", "learn", "give", "can", "you", "explain", "both", "all", "them", "three", "any",
    "and", "so", "cool", "awesome", "interesting", "go", "ahead", "do", "be", "great",
}


def is_generic_continuation(query: str) -> bool:
    """True when the reply carries no topic of its own (e.g. 'yes', 'yea tell me more', 'sure, go on').

    Only these replies should be answered from the previous assistant turn's topic. A reply that names
    a topic ('terraform setup', 'the CI/CD eval gates') must be answered on the topic the user picked.
    """
    words = re.findall(r"[a-z0-9_'\-/]+", query.lower())
    return bool(words) and all(w in _CONTINUATION_FILLER_WORDS for w in words)


def synthesize_conversational_response(
    question: str,
    raw_sources: List[Dict[str, Any]],
    conversation_history: Optional[List[Dict[str, str]]] = None
) -> str:
    """Produces a natural, fluid conversational response strictly grounded in Brandon's experience."""
    q_lower = question.lower().strip()

    # 0. Multi-turn Continuations and Contextual Followups
    if conversation_history and is_conversational_followup(question, conversation_history):
        last_asst = ""
        last_user = ""
        for m in reversed(conversation_history):
            role = m.get("role", "")
            content = m.get("content", "")
            if role in ("assistant", "model") and not last_asst:
                last_asst = content
            elif role == "user" and not last_user:
                last_user = content
            if last_asst and last_user:
                break

        hist_text = (last_asst + " " + last_user).lower()
        generic = is_generic_continuation(question)
        if any(w in hist_text for w in [
            "hybrid rag", "medallion", "cold start", "scale-to-zero", "scale to zero",
            "portfolio platform", "portfolio assistant", "cloud run", "gemini flash", "this platform",
            "finops-optimized cloud portfolio"
        ]):
            # Options offered by the platform answers: check what the USER picked first.
            if matches_topic(q_lower, ["terraform", "opentofu", "iac", "infrastructure as code"]):
                return (
                    "Here's how the **Terraform setup** for this platform is organized:\n\n"
                    "• **Small, single-purpose modules** (`infra/modules/`): `apis`, `artifact_registry`, `cloud_run`, `firestore`, `iam_wif`, and `secrets`—each with its own variables, outputs, and pinned provider versions.\n"
                    "• **Thin environment roots** (`infra/envs/dev` and `infra/envs/prod`): each environment just composes the modules, with remote state in a GCS backend and explicit `depends_on` ordering behind API enablement.\n"
                    "• **Secrets never touch code**: the Gemini API key lives in Secret Manager, the Cloud Run service account is granted accessor rights, and the key is injected as an environment variable at runtime—never in tfvars or the container image.\n"
                    "• **Keyless IaC pipelines**: `terraform-ci` runs `terraform fmt -check`, a Trivy IaC security scan, and `terraform validate` on pull requests; `terraform-cd` applies production on merge to `main`, authenticating through Workload Identity Federation (zero JSON service account keys).\n\n"
                    "Would you like to dig into the Workload Identity Federation setup or how Cloud Run is configured to scale to zero?"
                )
            if matches_topic(q_lower, ["ci/cd", "cicd", "eval", "evals", "evaluation", "quality gate", "gates", "github actions", "deploy"]):
                return (
                    "Here's how the **CI/CD eval quality gates** protect this assistant:\n\n"
                    "• **Rebuild on every change**: the MLOps workflow re-runs the Medallion pipeline (Bronze → Silver → Gold) so the retrieval index is always rebuilt from source data, never hand-edited.\n"
                    "• **Continuous evaluation benchmark**: `evaluate_agent.py` replays a golden dataset of questions against the fresh index, measuring Top-3 retrieval hit rate, Mean Reciprocal Rank (MRR), expected-keyword recall, and adversarial (prompt-injection) deflection rate.\n"
                    "• **Hard gates**: the build fails if Top-3 hit rate drops below **85%** or MRR below **0.70**, or if guardrail deflection regresses—so a retrieval regression can't ship silently.\n"
                    "• **Auditable artifacts**: every run archives the Gold index and the evaluation report.\n"
                    "• **Backend & infra gates**: the backend pipeline runs the pytest suite before deploying the container to Cloud Run, and Terraform changes go through fmt/Trivy/validate before apply—all using keyless OIDC auth.\n\n"
                    "Would you like to hear about the Terraform setup or the scale-to-zero FinOps design?"
                )
            if matches_topic(q_lower, ["rate limit", "rate-limit", "rate limiting", "token bucket", "quota", "throttle"]):
                return (
                    "Here's how **rate limiting** protects the LLM budget on this platform:\n\n"
                    "• **Tiered quotas**: anonymous visitors get 5 questions per 24 hours (keyed by client IP), and signed-in visitors get 30 per 24 hours (keyed by Firebase UID).\n"
                    "• **Sliding-window limiter**: requests are tracked as timestamps per key in memory, with periodic cleanup, so there's no Redis or database to pay for.\n"
                    "• **Lead capture**: hitting the anonymous limit nudges visitors to sign in, and conversations are recorded in Firestore as lead interactions.\n\n"
                    "Would you like to explore the scale-to-zero FinOps design or the CI/CD eval quality gates?"
                )
            if matches_topic(q_lower, ["finops", "cost", "costs", "idle", "budget", "cheap", "pricing"]):
                return (
                    "Here's the **scale-to-zero FinOps design** behind this platform:\n\n"
                    "• **Scale-to-zero compute**: the FastAPI backend runs on Cloud Run with `min-instances: 0`, so when nobody is chatting there are no CPU or memory charges—**$0/month idle**.\n"
                    "• **No database bill for search**: the hybrid retrieval index is loaded into container memory at startup instead of paying for a managed vector database.\n"
                    "• **Static frontend on a CDN**: the React app is served from Firebase Hosting's global CDN on the free tier.\n"
                    "• **Serverless state**: Firestore and Firebase Auth are pay-per-use, and per-visitor rate limits cap LLM spend.\n"
                    "• **Fast cold starts**: a slim multi-stage Docker image and index pre-warming in the FastAPI lifespan keep cold starts under ~2 seconds, so scaling to zero doesn't hurt the experience.\n\n"
                    "Would you like to know more about the Terraform setup or the CI/CD eval quality gates?"
                )
            if matches_topic(q_lower, ["rag", "retrieval", "rrf", "hybrid", "dense", "bm25"]):
                return (
                    "Here is a deeper architectural look into the **In-Memory Hybrid RAG engine (Dense + BM25 RRF)**:\n\n"
                    "• **Zero-Database In-Memory Architecture**: Rather than paying for an expensive managed vector database (like Pinecone or Cloud SQL Vector), this service loads a pre-computed, signed Gold retrieval index directly into container memory on startup.\n"
                    "• **Reciprocal Rank Fusion (RRF)**: When a query arrives, it calculates Okapi BM25 keyword scores alongside cosine similarity against 384-dimensional dense semantic embeddings, merging them with RRF (k=60).\n"
                    "• **Sub-10ms Latency**: In-memory execution provides sub-10ms retrieval latency with zero database hosting fees and zero external network hops!\n\n"
                    "Would you like to know more about the Medallion data pipeline or how cold starts are handled on Cloud Run?"
                )
            elif matches_topic(q_lower, ["medallion", "lakehouse", "pipeline", "bronze", "silver", "gold"]):
                return (
                    "Here is a deeper look into the **Medallion Data Lakehouse (Bronze → Silver → Gold)** pipeline:\n\n"
                    "• **Bronze Stage**: Ingests raw YAML/JSON profile data and GitHub REST API metadata, enforcing Pydantic v2 schemas and recording cryptographic SHA-256 hashes.\n"
                    "• **Silver Stage**: Semantically chunks achievements with strict quality gates, validates token lengths, and normalizes technical taxonomy.\n"
                    "• **Gold Stage**: Vectorizes chunks with dense embeddings, builds the Okapi BM25 inverted index, and bundles the search assets with SHA-256 integrity verification.\n\n"
                    "Would you like to explore the in-memory RAG retriever or cold start optimization next?"
                )
            elif matches_topic(q_lower, ["cold start", "scale to zero", "startup", "latency"]):
                return (
                    "Here is how **cold start latency is minimized** while maintaining scale-to-zero FinOps efficiency:\n\n"
                    "• **Scale-to-Zero ($0 Idle Cost)**: Cloud Run is configured with `min-instances: 0` so no compute charges accrue when the site is idle.\n"
                    "• **Multi-Stage Lightweight Docker Container**: Utilizes a slim Python base image, stripping build-time dependencies to keep the image size minimal.\n"
                    "• **Lifespan Pre-Warming**: The Gold retrieval index is deserialized and pre-warmed during the FastAPI lifespan startup event, keeping cold starts under 2 seconds.\n\n"
                    "Would you like to learn more about the Hybrid RAG engine or Medallion data pipeline?"
                )
            if generic:
                return (
                    "Here is a deeper architectural look into the **Hybrid RAG engine, Medallion data pipeline, and cold start optimization** "
                    "powering this platform:\n\n"
                    "• **In-Memory Hybrid RAG (Dense + BM25 RRF)**:\n"
                    "  Rather than paying for an expensive managed vector database (like Pinecone or Cloud SQL Vector), this service loads a "
                    "  pre-computed, signed Gold retrieval index directly into container memory on startup. When a query arrives, it calculates "
                    "  BM25 keyword scores alongside cosine similarity against 384-dimensional dense semantic embeddings, merging them with "
                    "  Reciprocal Rank Fusion (RRF). Retrieval latency is **sub-10ms** with zero database hosting fees!\n\n"
                    "• **Medallion Data Lakehouse (Bronze → Silver → Gold)**:\n"
                    "  The offline data pipeline validates raw YAML/JSON profile data using Pydantic v2 schemas (Bronze), chunks achievements "
                    "  semantically with strict quality gates (Silver), and vectorizes and hashes the index bundle (Gold) with SHA-256 verification.\n\n"
                    "• **Cold Start & FinOps Optimization**:\n"
                    "  Cloud Run is configured with `min-instances: 0` to achieve $0 idle cost. To minimize cold start latency when traffic arrives, "
                    "  the container utilizes a lightweight multi-stage Docker build, lazy dependency loading, and pre-warms the index during "
                    "  FastAPI lifespan initialization—keeping cold starts under 2 seconds.\n\n"
                    "Would you like to know more about the GitHub Actions CI/CD deployment or the rate-limiting token bucket architecture?"
                )
        elif generic and any(w in hist_text for w in ["bitbucket", "github actions", "runner", "workflow design", "ci/cd", "oidc", "wif"]):
            return (
                "Here are the deeper architectural details on Brandon's workflow design, runner scaling, and GitOps delivery:\n\n"
                "• **Reusable Workflow Architecture**: He standardized reusable GitHub Actions workflows across 100+ repositories with automated linting, container builds, and security gates (Trivy/Snyk), boosting build reliability to 99.8%.\n"
                "• **Dynamic Runner Autoscaling**: Engineered autoscaling self-hosted Linux runners orchestrated to absorb hundreds of concurrent CI job spikes, cutting queue times to near-zero while optimizing runner compute costs.\n"
                "• **Declarative GitOps Delivery**: Paired GitHub Actions with ArgoCD so container image pushes trigger automated syncs, canary testing, and instant rollbacks on anomaly detection.\n"
                "• **Keyless Cloud Auth (OIDC / WIF)**: Eliminated static credentials across CI runners by implementing Workload Identity Federation between GitHub Actions, AWS, and GCP.\n\n"
                "Would you like to explore his security validation gates or how he implemented MLOps eval quality gates in CI?"
            )
        elif any(w in hist_text for w in ["eks", "kubernetes", "migration", "argocd", "ecs"]):
            if matches_topic(q_lower, ["process", "migration", "cutover", "strategy", "dns"]):
                return (
                    "Here is a deep dive into the **zero-downtime migration process** Brandon architected from AWS ECS to Amazon EKS:\n\n"
                    "• **Dual-Running Infrastructure & Ingress**: Provisioned parallel EKS clusters alongside production ECS tasks, configuring AWS ALB Ingress Controllers and target groups to mirror routing rules across both environments.\n"
                    "• **Phased Weighted DNS Cutover**: Leveraged Amazon Route 53 weighted record sets to gradually shift live production traffic (1% → 10% → 50% → 100%) between ECS and EKS backends while continuously monitoring real-time error rates, HTTP latency, and saturation.\n"
                    "• **Automated Rollback & Health Validation**: Maintained instant DNS failback mechanisms throughout each wave, validating service telemetry before decommissioning legacy ECS services.\n"
                    "• **Zero Customer Disruption**: Migrated over 30 mission-critical microservices without a single second of customer-facing downtime.\n\n"
                    "Would you like to explore the ArgoCD GitOps delivery pipeline or his custom Kubernetes ingress observability tooling next?"
                )
            elif matches_topic(q_lower, ["gitops", "workflow", "argocd", "delivery"]):
                return (
                    "Here are the details on Brandon's **ArgoCD GitOps workflow and continuous delivery** architecture:\n\n"
                    "• **Multi-Cluster ApplicationSets**: Implemented ArgoCD ApplicationSets managing multi-cluster and multi-environment Helm charts with Kustomize overlays, eliminating drift and manual kubectl executions.\n"
                    "• **Automated Sync & Canary Deployments**: Paired GitHub Actions container image publishing with declarative ArgoCD auto-syncs, integrating canary deployments with metric-based automated rollbacks on failure.\n"
                    "• **Radically Reduced Lead Times**: Slashed production deployment lead times from several hours down to under 10 minutes while improving auditability.\n\n"
                    "Would you like to know more about the migration cutover process or the custom Go ingress observability exporter?"
                )
            elif matches_topic(q_lower, ["observability", "tooling", "prometheus", "monitoring", "exporter", "metric"]):
                return (
                    "Here are the details on Brandon's **Kubernetes observability tooling and custom controller development**:\n\n"
                    "• **Custom Go Controller (`prometheus-ingress-status-exporter`)**: Authored a lightweight Go controller that dynamically discovers Ingress endpoints across namespaces, probes HTTP/TCP reachability, and exports synthetic health metrics to Prometheus.\n"
                    "• **Datadog & APM Integration**: Configured cluster-wide Datadog agents and OpenTelemetry sidecars to correlate ingress latency with microservice application traces.\n"
                    "• **Actionable SLO Alerting**: Built high-signal alerts in PagerDuty and Slack based on multi-window burn rates, eliminating alarm fatigue for platform and product engineers.\n\n"
                    "Would you like to dive deeper into the zero-downtime migration process or the ArgoCD GitOps architecture?"
                )
            elif matches_topic(q_lower, ["security", "mtls", "mesh", "networking", "cert", "acm", "envoy"]):
                return (
                    "Here are deeper architectural details on Brandon's **zero-trust security and service mesh architecture**:\n\n"
                    "• **Automated mTLS & ACM Certificate Rotation**: Deployed Envoy sidecar proxies across Kubernetes pods with AWS App Mesh, "
                    "enforcing cryptographically verified mutual TLS (mTLS) with automated zero-downtime certificate rotation via AWS Certificate Manager (ACM).\n"
                    "• **Network Isolation & Ingress Security**: Hardened Kubernetes network topologies using strict security groups, PrivateLink endpoints, "
                    "and dynamic Ingress rate limiting and TLS termination.\n"
                    "• **Distributed Tracing & Auditing**: Configured Envoy proxies to inject and propagate distributed tracing context (OpenTelemetry/W3C) "
                    "for granular audit logs and traffic path analysis across microservices.\n\n"
                    "Would you like to explore the zero-downtime migration cutover or the ArgoCD GitOps pipeline?"
                )
            if generic:
                return (
                    "Here are the deeper architectural details on his EKS migration, GitOps workflows, and observability tooling:\n\n"
                    "• **Zero-Downtime Migration Playbook**: Executed a phased dual-running strategy using DNS weight shifts via Route 53 and ALB ingress controllers, transitioning 30+ services from ECS to EKS with zero customer impact.\n"
                    "• **ArgoCD Declarative GitOps**: Configured multi-cluster ApplicationSets managing Helm charts and Kustomize overlays, eliminating manual kubectl interventions and reducing deploy lead times from hours to under 10 minutes.\n"
                    "• **Custom Go Ingress Observability**: Authored `prometheus-ingress-status-exporter` to continuously probe ingress availability and export metrics directly to Prometheus and Datadog.\n"
                    "• **Karpenter Dynamic Compute**: Replaced static EC2 node groups with Karpenter autoscaling and Spot instance fleets, cutting thousands in idle compute costs.\n\n"
                    "Are there specific Kubernetes networking, security (mTLS), or storage patterns you'd like to dive into?"
                )
        elif generic and any(w in hist_text for w in ["app mesh", "service mesh", "mtls", "envoy"]):
            return (
                "Here are deeper architectural details on Brandon's zero-trust service mesh implementation:\n\n"
                "• **Automated mTLS & ACM Certificate Rotation**: Envoy proxies run as sidecars alongside microservice containers in Kubernetes, "
                "enforcing mutual TLS authentication with automated certificate lifecycle management via AWS Certificate Manager (ACM).\n"
                "• **Traffic Shaping & Resilience**: Implemented fine-grained canary traffic routing, circuit breakers, and connection timeouts "
                "at the mesh layer to prevent cascading microservice outages.\n"
                "• **Distributed Tracing Context Propagation**: Configured Envoy to automatically propagate W3C `traceparent` headers to OpenTelemetry "
                "and Datadog APM, enabling end-to-end distributed latency tracing across the entire cluster.\n\n"
                "Are there specific mesh networking or security controls you'd like to dive into?"
            )
        elif generic and any(w in hist_text for w in ["kafka", "confluent", "msk", "streaming"]):
            return (
                "Here are the deeper architectural details on his Kafka & Confluent Cloud platform work:\n\n"
                "• **Zero-Downtime MSK Cutover**: Implemented MirrorMaker2 replication between AWS MSK and Confluent Cloud, enabling seamless consumer offset translation and zero message drop during cluster migration.\n"
                "• **Schema Registry Governance**: Enforced Avro and Protobuf schema compatibility checks directly in CI, preventing breaking schema mutations across event streams.\n"
                "• **Terraform GitOps for Kafka**: Automated topic creation, retention configurations, and ACL policies declaratively through Terraform pipelines.\n\n"
                "Would you like to hear more about his stream processing patterns or event throughput?"
            )
        elif generic and any(w in hist_text for w in ["terraform", "opentofu", "iac"]):
            return (
                "Here are key patterns in Brandon's enterprise Terraform module architecture:\n\n"
                "• **Modular Golden Templates**: Standardized multi-tier modules for VPCs, EKS clusters, and RDS databases shared across 20+ engineering teams with semantic versioning.\n"
                "• **Custom Go Provider Authoring**: Authored `terraform-provider-neo4j` using the HashiCorp Terraform Plugin SDK to declaratively manage graph databases alongside standard cloud resources.\n"
                "• **Keyless OIDC Cloud Auth**: Integrated Workload Identity Federation in GitHub Actions to eliminate all long-lived AWS IAM access keys and GCP service account JSON keys.\n\n"
                "Would you like to know more about his CI/CD validation gates or drift detection?"
            )
        elif generic and any(w in hist_text for w in ["cost", "finops", "save", "saving", "budget"]):
            return (
                "Here are more details on Brandon's FinOps cost optimization strategies:\n\n"
                "• **Karpenter Dynamic Spot Compute**: Implemented Karpenter autoscaling on EKS, utilizing diversified Spot instance pools to reduce idle compute costs by over $6,500/month.\n"
                "• **Storage & Database Optimization**: Right-sized over-provisioned Aurora RDS instances, converted gp2 EBS volumes to gp3, and instituted automated S3 lifecycle tiering.\n"
                "• **Serverless FinOps Portfolio**: Architected this portfolio platform on Cloud Run and Firebase Hosting with scale-to-zero compute, costing $0/month while idle."
            )

    # 1. Greetings & Warm-ups
    if re.search(r"^(hi+|hello+|hey+|howdy+|sup+|greetings)\b", q_lower):
        return (
            "Hey! I'm Brandon Foster's AI assistant. I'm here to chat about his platform engineering, "
            "Kubernetes, Terraform, Kafka, and MLOps work. Feel free to ask about his recent projects, "
            "architecture decisions, or tech stack—what can I help you with today?"
        )

    # 2. System pings & Diagnostics
    if re.search(r"^(test+|testing|ping|pong|status|health|check|echo)\b", q_lower):
        return (
            "Systems are up and running smoothly! I'm Brandon's AI assistant, connected and ready to chat. "
            "Feel free to ask about his background, past migrations, or any of his open-source projects."
        )

    # 3. Arithmetic / Math
    math_match = re.match(
        r"^(?:what\s+is|whats|calculate|solve)?\s*(\d+(?:\.\d+)?)\s*([\+\-\*\/xX])\s*(\d+(?:\.\d+)?)$",
        q_lower.rstrip("?").strip(),
    )
    if math_match:
        n1 = float(math_match.group(1))
        op = math_match.group(2).lower()
        n2 = float(math_match.group(3))
        res = n1 + n2 if op == "+" else (n1 - n2 if op == "-" else (n1 * n2 if op in ("*", "x") else (n1 / n2 if n2 != 0 else "undefined")))
        if isinstance(res, float) and res.is_integer():
            res = int(res)
        op_sym = "×" if op in ("*", "x") else op
        return (
            f"{math_match.group(1)} {op_sym} {math_match.group(3)} is **{res}**!\n\n"
            "While I can do quick math, I'm really here to chat about Brandon Foster's engineering experience. "
            "If you have non-engineering questions or personal inquiries, I don't know—maybe you should ask him! "
            "You can submit your question and email through the **[Contact Page](#contact)** and it will be forwarded directly to him."
        )

    # 4. Approved Personal Information & Preferences (Explicitly authorized from personal.yaml)
    approved_personal_resp = detect_approved_personal(question)
    if approved_personal_resp:
        return approved_personal_resp

    # 5. Strictly Protected Personal Information Inquiries (Kids, Family, Age, Salary, Private matters)
    # ONLY the approved data above may be shared. Everything else is strictly private!
    if any(re.search(pat, q_lower) for pat in [
        r"\b(kid|kids|child|children|son|sons|daughter|daughters|baby|babies)\b",
        r"\b(wife|husband|spouse|partner|married|marry|single|dating|girlfriend|boyfriend|ex-wife|fiance)\b",
        r"\b(family|parents|mom|mother|dad|father|brother|brothers|sister|sisters|relatives)\b",
        r"\bhow\s+old\s+is\s+(he|brandon)\b",
        r"\b(birthday|birth\s*date|date\s+of\s+birth|when\s+was\s+he\s+born|where\s+was\s+he\s+born)\b",
        r"\b(his|brandon\'?s?)\s+age\b",
        r"\b(phone|cell|mobile)\s*(number)?\b",
        r"\bwhat\s+is\s+(his|brandon\'?s?)\s+(email|phone|number|address|salary|net\s*worth)\b",
        r"\b(his|brandon\'?s?)\s+(email(\s*address)?|phone\s*number|cell\s*phone|contact\s*info)\b",
        r"\b(salary|net\s*worth|income|compensation|how\s+much\s+does\s+he\s+(make|earn|get\s*paid))\b",
        r"\b(personal|private)\s+(life|info|question|details|matters)\b",
        r"\b(religion|religious|political|politics|faith|church|god)\b",
    ]):
        return (
            "I don't know—maybe you should ask him! That personal information is not in his public docs. "
            "You can submit your question and email through the **[Contact Page](#contact)**, and it will be forwarded straight to Brandon's inbox."
        )

    # 6. Contact & Hiring Inquiries (Zero email/phone exposure)
    if any(w in q_lower for w in ["contact", "hire", "email", "reach", "resume"]):
        return (
            "Brandon doesn't publish his direct email or phone number on the site, but you can message him directly "
            "through the **[Contact Page](#contact)**!\n\n"
            "Just submit your question and email, and your message will be forwarded straight to his inbox. "
            "You can also connect with him on [LinkedIn](https://www.linkedin.com/in/brandon-foster) and [GitHub](https://github.com/brandocomando)."
        )

    # 6. Core Technical Topics
    # Verification & Achievement Validation Engine ("did he really do this?", "did he actually build...", "is this true?")
    is_verification = bool(re.search(
        r"\b(?:did\s+he\s+(?:really|actually)|did\s+brandon\s+(?:really|actually)|is\s+(?:this|that|it)\s+(?:true|real|accurate)|really\s+do\s+this|actually\s+do\s+this|has\s+he\s+actually)\b",
        q_lower
    ))

    # Upstream Forks / External Projects (FirstMate & WezTerm Agent Deck)
    if any(w in q_lower for w in ["firstmate", "first mate", "agent deck", "agentdeck", "wezterm agent deck"]):
        return (
            "Both **FirstMate CLI** and **WezTerm Agent Deck** are forks and experimental adaptations of upstream "
            "open-source projects and should **not** be considered Brandon's original work.\n\n"
            "For Brandon's original agentic AI architecture and developer tooling, check out **My Agentic Team**—his "
            "local-first autonomous agent platform integrating Ollama, Chrome DevTools Protocol (CDP) automation, "
            "and sub-50ms inference decisions: [github.com/brandocomando/my_agentic_team](https://github.com/brandocomando/my_agentic_team)."
        )

    # Specific Project: My Agentic Team
    if any(w in q_lower for w in ["my agentic team", "agentic team"]):
        return (
            "**My Agentic Team** is Brandon's local-first compilation of autonomous AI agents designed to automate daily developer workflows.\n\n"
            "It leverages local LLM inference (via Ollama), Chrome DevTools Protocol (CDP) for browser automation, and the sub-50ms Laya decision engine. "
            "It demonstrates how to coordinate multi-agent teams reliably without relying exclusively on expensive cloud API roundtrips.\n\n"
            "You can explore the repository here: [github.com/brandocomando/my_agentic_team](https://github.com/brandocomando/my_agentic_team)."
        )

    # Specific Project: Prometheus Ingress Exporter
    if any(w in q_lower for w in ["prometheus", "ingress exporter", "status exporter"]):
        return (
            "The **Prometheus Ingress Status Exporter** is a Kubernetes controller Brandon wrote in Go using `client-go`.\n\n"
            "It dynamically watches Ingress resources across namespaces, runs synthetic HTTP/HTTPS health checks against host rules and TLS configs, "
            "and exports Prometheus-compatible latency percentiles, status codes, and availability metrics. It gives platform and SRE teams "
            "instant cluster-wide edge health observability.\n\n"
            "It's open-source at [github.com/brandocomando/prometheus-ingress-status-exporter](https://github.com/brandocomando/prometheus-ingress-status-exporter)."
        )

    # Temporal & Stateful Workflow Orchestration
    if re.search(r"\btemporal\b|\bworkflow\s+orchestrat\w*\b|\bcadence\b", q_lower):
        return (
            "Brandon understands the architecture and programming model of **Temporal** conceptually—including "
            "event sourcing, deterministic execution replay, activity workers, and durable execution timers.\n\n"
            "In production, his distributed workflow and asynchronous coordination experience has primarily centered on "
            "**event-driven streaming with Apache Kafka & Confluent Cloud**, **AWS SQS/SNS**, **AWS Step Functions**, and **Celery**.\n\n"
            "Given his deep background in Go and Python systems engineering, event-driven microservices, and distributed coordination, "
            "he can rapidly adopt Temporal or Cadence for stateful, long-running business workflows.\n\n"
            "Are you exploring Temporal for microservice orchestration or asynchronous task processing?"
        )

    # Pulumi & AWS CDK (Programmatic Infrastructure as Code)
    if re.search(r"\bpulumi\b|\b(?:aws\s+)?cdk\b|\bprogrammatic\s+iac\b", q_lower):
        return (
            "Brandon understands programmatic Infrastructure as Code concepts (defining cloud topologies using TypeScript, "
            "Python, or Go SDKs, construct trees, and state management) and can ramp up on **Pulumi** or **AWS CDK** rapidly.\n\n"
            "His primary production expertise is in declarative **Terraform / OpenTofu**, where he engineered a centralized enterprise "
            "module platform used by over 20 engineering squads across AWS, GCP, Datadog, Snowflake, and Confluent Cloud.\n\n"
            "Furthermore, he has authored native custom Terraform providers in Go (`terraform-provider-neo4j`) using the Terraform Plugin SDK, "
            "giving him deep low-level mastery of cloud provider APIs, state reconciliation loops, and CRUD lifecycles.\n\n"
            "Are you evaluating a migration between Terraform and Pulumi/CDK?"
        )

    # FluxCD / Flux (GitOps)
    if re.search(r"\bflux(?:cd)?\b", q_lower):
        return (
            "Brandon's primary production GitOps platform is **ArgoCD** (where he architected multi-cluster ApplicationSets, "
            "automated canary deployments, image updates, and cut deployment lead times from hours to under 10 minutes).\n\n"
            "However, he understands **FluxCD**'s architecture, including its controller reconciliation loops, GitRepository / OCIRepository "
            "sources, Kustomize controller patterns, and Helm release management.\n\n"
            "Because his GitOps philosophy centers on declarative desired state in Git, immutable versioning, automated drift detection, "
            "and zero direct cluster mutations, his skills translate seamlessly between ArgoCD and FluxCD.\n\n"
            "What GitOps patterns or tools does your team utilize?"
        )

    # Developer Portals (Backstage / Port) & IDP
    if re.search(r"\bbackstage\b|\bport(?:\.io)?\b|\bidp\b|\binternal\s+developer\s+portal\b|\bsoftware\s+catalog\b", q_lower) and not re.search(r"\bport\s+\d+\b", q_lower):
        return (
            "Brandon has extensive experience building **Internal Developer Platform (IDP) tooling and paved roads**:\n\n"
            "• **Developer Tooling & CLIs**: Authored high-performance developer CLIs, SDKs, and automation tooling in Go and Python.\n"
            "• **Paved Roads & Golden Paths**: Standardized opinionated microservice boilerplates, reusable GitHub Actions workflows, "
            "and Docker Compose local development stacks that cut developer onboarding from days to under 2 hours.\n"
            "• **Developer Portals (Backstage / Port)**: While he hasn't had the organizational opportunity to fully roll out a formal "
            "developer portal using Backstage or Port yet, he has a solid architectural understanding of their service catalogs, Scorecards, "
            "and Software Templates—and is actively looking forward to leading an IDP rollout!\n\n"
            "Are you looking to build or mature an Internal Developer Platform for your engineering teams?"
        )

    # Streamlit & Customer Support Internal Tooling
    if re.search(r"\bstreamlit\b|\bcustomer\s+(?:support|service)\b", q_lower):
        return (
            "Yes! Brandon engineered an internal **Streamlit** self-service web application used by customer service teams to diagnose and resolve common customer issues quickly.\n\n"
            "Key engineering and architectural highlights:\n"
            "• **Faster Issue Resolution**: Streamlined troubleshooting workflows into an intuitive self-service portal, drastically reducing time-to-resolution for customer-facing support tickets.\n"
            "• **Least-Privilege Security Posture**: Enforced strict role-based access controls (RBAC) so support representatives could safely remediate issues via audited APIs without granting them direct access to production databases or underlying infrastructure.\n"
            "• **Standardized Remediation Playbooks**: Replaced manual, error-prone database queries with validated, automated resolution workflows.\n\n"
            "Would you like to explore his other internal developer platform tooling or Python backend services?"
        )

    # Distributed NoSQL: Cassandra & Aerospike
    if re.search(r"\bcassandra\b|\baerospike\b", q_lower):
        return (
            "Yes! Brandon has direct, hands-on production experience operating **Aerospike** and **Apache Cassandra** "
            "distributed NoSQL databases for high-throughput, low-latency (sub-10ms) key-value and wide-column workloads.\n\n"
            "Alongside his work modernizing event streaming on Confluent Cloud / Apache Kafka, he operated these distributed NoSQL "
            "stores to handle high-velocity write throughput and low-latency reads. He has also engineered systems with PostgreSQL, "
            "AWS Aurora, Redis (ElastiCache), DynamoDB, and graph databases (authoring `terraform-provider-neo4j` in Go).\n\n"
            "Would you like to hear more about his distributed data store experience or event-driven data architectures?"
        )

    # Analytical Data Warehouses & Lakehouses: ClickHouse, Redshift, Snowflake
    if re.search(r"\bclickhouse\b|\bredshift\b|\bsnowflake\b|\blakehouse\b|\bdata\s*warehous\w*\b", q_lower):
        return (
            "For analytical data warehousing and lakehouses, Brandon's primary production expertise is with **Snowflake** and **Databricks**, "
            "where he managed data lakehouse infrastructure, role-based access control (RBAC), and automated provisioning with Terraform.\n\n"
            "While he has not operated ClickHouse or Amazon Redshift as his primary analytical stores, the dimensional modeling, columnar query "
            "concepts, and streaming ingestion patterns (via Kafka, Confluent Cloud, and S3) translate directly.\n\n"
            "Additionally, for high-throughput operational workloads, he has hands-on production experience with distributed NoSQL databases "
            "including **Aerospike** and **Apache Cassandra**.\n\n"
            "What kind of analytical or data platform architecture does your team run?"
        )

    # Databricks, Spark, Airflow, Kubeflow, Ray
    if re.search(r"\bdatabricks\b|\bspark\b|\bairflow\b|\bkubeflow\b|\bray\b", q_lower):
        return (
            "Brandon has hands-on experience with **Databricks** and **Apache Spark** data lakehouse pipelines, managing role-based access control, "
            "compute clusters, and provisioning them via Terraform alongside Snowflake and Kafka.\n\n"
            "In workflow and data pipeline orchestration, he has worked with DAG pipelines (Airflow) and offline MLOps evaluation in CI/CD. "
            "While he understands the architectures of distributed ML frameworks like **Kubeflow** and **Ray** (for distributed training and model serving), "
            "his primary hands-on ML engineering has focused on local LLM inference engines (Ollama, Laya sub-50ms decision loops), autonomous multi-agent "
            "systems (*My Agentic Team*), and hybrid RAG retrieval pipelines with automated LLM-as-a-judge CI/CD quality gates.\n\n"
            "Are you evaluating him for data platform engineering or MLOps infrastructure?"
        )

    # AWS SageMaker & Managed ML Platforms
    if re.search(r"\bsagemaker\b", q_lower):
        return (
            "Brandon understands the architecture and operational lifecycle of **AWS SageMaker**—including notebook instances, "
            "training jobs, model registries, and multi-model real-time endpoints.\n\n"
            "In production, his AI and ML platform engineering has primarily centered on:\n"
            "• **Containerized Inference Microservices**: Packaging model runtimes into lightweight Docker containers deployed onto Amazon EKS and serverless Google Cloud Run with FastAPI.\n"
            "• **Local LLM Inference Runtimes**: Orchestrating local model execution with Ollama, GGUF quantization, and the sub-50ms Laya decision engine for autonomous agent workflows (*My Agentic Team*).\n"
            "• **Infrastructure as Code & Governance**: Provisioning and securing cloud ML resources and IAM least-privilege execution roles declaratively via Terraform.\n\n"
            "Because of his deep background across AWS, Docker, Kubernetes, and MLOps evaluation pipelines, he can configure, secure, and operationalize SageMaker workloads seamlessly. Are you evaluating him for an AWS ML platform or MLOps engineering role?"
        )

    # Runtime Security & Falco (eBPF / Syscall Threat Detection)
    if re.search(r"\bfalco\b|\bruntime\s+security\b|\bruntime\s+threat\b|\bebpf\s+security\b", q_lower):
        return (
            "Yes! Brandon has hands-on production experience implementing **Falco** for Kubernetes runtime security and threat detection:\n\n"
            "• **Kubernetes DaemonSet Deployment**: Deployed and maintained Falco DaemonSets across Kubernetes clusters to monitor Linux kernel syscalls and container execution in real time.\n"
            "• **Anomaly Detection & Threat Alerting**: Configured rule sets to detect privilege escalations, unauthorized shell spawns inside production containers, unexpected outbound network connections, and sensitive file mutations (`/etc/passwd`, `/etc/shadow`).\n"
            "• **Defense-in-Depth DevSecOps**: Paired runtime monitoring with automated CI/CD container image scanning (Trivy/Snyk), admission controllers, least-privilege IAM/WIF, and end-to-end mTLS via AWS App Mesh.\n\n"
            "Would you like to hear more about his DevSecOps compliance automation or zero-trust networking architecture?"
        )

    # Compliance Standards: SOC 2, HIPAA, ISO 27001 & DevSecOps
    if re.search(r"\bsoc\s*2\b|\bsoc2\b|\bhipaa\b|\biso\s*27001\b|\biso27001\b|\bcompliance\b|\baudit\b|\bsecurity\s+standards?\b", q_lower):
        return (
            "Yes! Brandon has direct experience designing cloud security architectures and supplying technical evidence to satisfy "
            "**SOC 2 Type 2**, **HIPAA**, and **ISO 27001** compliance audits.\n\n"
            "Key technical controls and compliance practices he has implemented include:\n"
            "• **Least-Privilege & Identity Governance**: Enforced strict IAM role boundaries and eliminated static long-lived credentials "
            "by adopting Workload Identity Federation (WIF) and keyless OIDC across all CI/CD runners.\n"
            "• **Runtime Threat Detection**: Implemented Falco DaemonSets on Kubernetes for real-time syscall monitoring, container anomaly alerts, and privilege escalation detection.\n"
            "• **Zero-Trust Network Encryption**: Enforced end-to-end mutual TLS (mTLS) with automated ACM certificate rotation across Kubernetes "
            "microservices via AWS App Mesh and Envoy proxy.\n"
            "• **Supply Chain & Vulnerability Gates**: Automated container scanning (Trivy, Snyk), Software Bill of Materials (SBOM), and static "
            "analysis in CI/CD pipelines to block vulnerable dependencies before production deployment.\n"
            "• **Audit Evidence Collection & Continuous Monitoring**: Automated cloud compliance tracking with AWS Config, Security Hub, KMS envelope "
            "encryption, and immutable audit logging.\n\n"
            "Would you like to discuss his compliance automation or cloud security controls in greater detail?"
        )

    # Certifications & CKA (Certified Kubernetes Administrator)
    if re.search(r"\bcka\b|\bckad\b|\bcks\b|\bcert(?:ification)?s?\b|\bcertified\b", q_lower):
        return (
            "Brandon values real-world, battle-tested production engineering experience over paper credentials. "
            "He **previously held the CKA (Certified Kubernetes Administrator)** certification and let it lapse in favor of continuous, "
            "deep hands-on production Kubernetes engineering.\n\n"
            "In production, his Kubernetes expertise goes well beyond standard administration:\n"
            "• **Zero-Downtime Migration**: Architected and led the migration of 30+ mission-critical microservices from legacy ECS to Amazon EKS.\n"
            "• **Custom Operators in Go**: Authored custom Kubernetes controllers using `client-go` (`prometheus-ingress-status-exporter`) to monitor Ingress health and export latency metrics.\n"
            "• **Production Ecosystem**: Expert with ArgoCD GitOps, Helm chart authoring, Karpenter dynamic Spot autoscaling, AWS App Mesh mTLS, and CRDs.\n\n"
            "Are you looking for hands-on Kubernetes architecture or cluster administration expertise?"
        )

    # Observability, SRE & Reliability Engineering (Datadog, OpenTelemetry, Grafana, SLOs)
    if re.search(r"\bsre\b|\bslo(?:s)?\b|\bsli(?:s)?\b|\berror\s+budget\b|\bincident\s+management\b|\bpostmortem\b|\bopentelemetry\b|\botel\b|\bgrafana\b|\bdatadog\b", q_lower):
        return (
            "Brandon integrates Site Reliability Engineering (SRE) principles directly into platform engineering:\n\n"
            "• **Observability & Telemetry**: Authored custom Go controllers (`prometheus-ingress-status-exporter`) dynamically probing Ingress health and latency. "
            "Configured Datadog APM tracing, synthetic monitoring, and Terraform-managed dashboards. Utilized OpenTelemetry (OTel) for distributed trace context propagation (W3C traceparent).\n"
            "• **SLOs & Error Budgets**: Defined Service-Level Indicators (SLIs) and Service-Level Objectives (SLOs) paired with error budgets to balance deployment velocity with system reliability.\n"
            "• **Incident Management & Postmortems**: Championed blameless postmortem culture and automated runbooks to cut recurring operational toil by 40%, alongside leading on-call rotations for mission-critical platforms.\n\n"
            "Would you like to know more about his observability stack or SRE operational practices?"
        )

    # Developer Experience & Paved Roads
    if re.search(r"\bpaved\s+road(?:s)?\b|\bgolden\s+path(?:s)?\b|\bdeveloper\s+experience\b|\bdevex\b|\bdeveloper\s+tooling\b", q_lower):
        return (
            "Brandon strongly champions **adoption-first platform engineering** and the philosophy that 'the easy path is the safe path.'\n\n"
            "Key achievements include:\n"
            "• **Golden Path Templates & CLIs**: Designed opinionated service boilerplates and authored high-performance developer CLIs in Go and Python.\n"
            "• **Rapid Onboarding**: Standardized local developer environments using Docker Compose, cutting new microservice onboarding from days to under 2 hours.\n"
            "• **Self-Service & Safety**: Automated PR preview environments, reusable CI/CD workflows, and integrated vulnerability scanning (Trivy/Snyk) to boost developer velocity with 99.8% build reliability.\n\n"
            "Are you looking to scale developer productivity and platform self-service on your team?"
        )


    # AI Infrastructure & MLOps
    if any(w in q_lower for w in ["mlops", "ml ops", "ai infra", "ai infrastructure", "agent", "agents", "llm", "llms", "rag", "ollama", "machine learning", "retrieval"]):
        return (
            "Brandon specializes in **AI Infrastructure and MLOps**, bridging cloud platform engineering with production AI systems.\n\n"
            "Key highlights of his work in this space include:\n"
            "• **Autonomous Agent Architectures**: Engineered *My Agentic Team*, coordinating local LLMs (via Ollama) with Chrome DevTools Protocol (CDP) for browser automation and sub-50ms inference decisions with Laya.\n"
            "• **Hybrid Retrieval & RAG Engines**: Built sub-millisecond retrieval pipelines combining BM25 sparse search with dense vector embeddings via Reciprocal Rank Fusion (RRF), semantic chunking, and metadata filtering—the exact architecture powering this portfolio assistant!\n"
            "• **Evaluation & Quality Gates**: Instituted automated evaluation benchmarks in CI/CD using LLM-as-a-judge patterns to evaluate context recall, MRR, and answer faithfulness.\n\n"
            "Would you like to explore his multi-agent orchestration patterns, local LLM tooling, or RAG evaluation pipelines?"
        )

    # Jenkins & Traditional CI/CD Tooling
    if "jenkins" in q_lower:
        return (
            "Yes, Brandon has hands-on experience with **Jenkins** and traditional CI/CD pipelines alongside modern platforms "
            "like GitHub Actions and ArgoCD.\n\n"
            "Throughout his infrastructure and platform engineering career, he has managed Jenkins build environments, automated "
            "agent runner scaling on Linux and Docker, and configured multi-stage build, test, and container packaging pipelines. "
            "In his enterprise leadership work, he transitioned squads from legacy CI setups (including Bitbucket and Jenkins) to modern "
            "GitHub Actions and ArgoCD GitOps pipelines—authoring reusable workflow templates, automated vulnerability scanning (Trivy/Snyk), "
            "and keyless OIDC authentication that achieved 99.8% build reliability across 100+ repositories.\n\n"
            "His core CI/CD philosophy—pipeline-as-code, ephemeral container runners, immutable artifacts, and fast feedback loops—applies "
            "equally across Jenkins, GitHub Actions, or GitLab CI.\n\n"
            "Are you looking to modernize a Jenkins setup or wondering how his pipeline experience fits your engineering stack?"
        )

    # GitLab CI / CircleCI / Other CI Tooling
    if any(w in q_lower for w in ["gitlab", "circleci", "travis", "tekton", "spinnaker", "teamcity", "bamboo"]):
        return (
            "While Brandon's primary production focus has centered on **GitHub Actions**, **Bitbucket Pipelines**, and **ArgoCD GitOps**, "
            "his deep CI/CD and platform engineering background translates directly across modern CI runners including GitLab CI and CircleCI.\n\n"
            "He specializes in designing declarative pipelines-as-code, runner autoscaling on Kubernetes and Linux, multi-stage container builds, "
            "and keyless cloud authentication (OIDC/WIF). As Principal Infrastructure Lead, he modernized over 100 repositories to standardized "
            "reusable pipelines with 99.8% build reliability.\n\n"
            "Would you like to know more about his pipeline architectures, automated testing gates, or runner scaling?"
        )

    # Keyless Cloud Auth & Workload Identity Federation (OIDC / WIF)
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:keyless\s+(?:cloud\s+)?auth(?:entication)?|oidc|wif|workload\s+identity\s+federation)\b",
        r"\b(?:eliminat\w*|remov\w*|replac\w*)\s+static\s+(?:credentials?|keys?|secrets?)\b",
        r"\bstatic\s+credentials?\b",
    ]):
        confirm = "**Yes, Brandon really did this!** In fact, eliminating static credentials was one of his highest-impact security and platform initiatives.\n\n" if is_verification else ""
        return (
            f"{confirm}"
            "As Principal Infrastructure / DevOps Lead, Brandon eliminated all long-lived static credentials across CI runners "
            "by implementing **Workload Identity Federation (WIF)** and **OpenID Connect (OIDC)** keyless authentication between "
            "GitHub Actions and cloud providers (both AWS and GCP).\n\n"
            "**How he architected it:**\n"
            "• **Ephemeral Token Exchange**: When a GitHub Actions workflow executes, the runner requests a short-lived OIDC JSON Web Token (JWT) signed by GitHub's certificate authority.\n"
            "• **Direct Cloud Trust**: Cloud IAM (AWS STS `AssumeRoleWithWebIdentity` and GCP Workload Identity Pools) cryptographically validates the JWT against GitHub's issuer URL and audience, exchanging it for temporary, scoped cloud credentials that automatically expire in minutes.\n"
            "• **Strict Least-Privilege Scoping**: IAM policies and role trust boundaries are locked down to specific GitHub repositories, branches (e.g., `main`), or deployment environments—preventing unauthorized forks or pull requests from assuming roles.\n"
            "• **Zero Static Keys**: Completely eliminated AWS Access Keys (`AKIA...`) and GCP Service Account JSON keys from CI runners and repository secrets, removing the primary attack vector for credential leaks.\n"
            "• **100% Codified via Terraform**: All IAM trust policies, WIF pools, and provider bindings were deployed declaratively via Terraform across all cloud accounts.\n\n"
            "He also applied this exact same architecture to this portfolio—deploying Cloud Run and Firebase from GitHub Actions with zero static keys.\n\n"
            "Would you like to know more about how he structured the IAM trust policies or the Terraform automation?"
        )

    # Enterprise Bitbucket to GitHub Migration (100+ Repos)
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:migrat\w*|move\w*)\s+(?:from\s+)?bitbucket\b",
        r"\bbitbucket\s+(?:to\s+github|migration)\b",
        r"\b100\+\s+(?:repos|repositories)\b",
        r"\b100\s+(?:repos|repositories)\b",
    ]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "As Principal Infrastructure / DevOps Lead, Brandon led the enterprise-wide migration of over 100 repositories "
            "from legacy Bitbucket to GitHub and GitHub Actions completely from scratch.\n\n"
            "Key engineering achievements during this migration:\n"
            "• **Standardized Reusable Workflows**: Designed central, modular GitHub Actions workflows for linting, container builds, "
            "and security scanning (Trivy/Snyk) across all engineering squads.\n"
            "• **Autoscaling Linux Runners**: Orchestrated high-performance self-hosted Linux runners to absorb hundreds of concurrent CI job spikes, "
            "driving build reliability to 99.8% and cutting queue times to near-zero.\n"
            "• **Keyless Security & GitOps**: Embedded Workload Identity Federation (WIF/OIDC) and connected CI to ArgoCD for continuous delivery into Kubernetes.\n\n"
            "Would you like to know more about his reusable workflow design or how he managed team onboarding?"
        )

    # CI/CD & Pipeline Engineering
    if any(re.search(pat, q_lower) for pat in [
        r"\bci[\s\-_/]*cd\b",
        r"\bcicd\b",
        r"\bpipelines?\b",
        r"\bpiplines?\b",
        r"\bgithub\s+actions\b",
        r"\bbitbucket\b",
        r"\bjenkins\b",
        r"\bgitlab\b",
        r"\bcircleci\b",
        r"\btekton\b",
        r"\bspinnaker\b",
    ]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "Brandon has deep, battle-tested expertise in **CI/CD and pipeline engineering**, having architected enterprise-scale "
            "delivery platforms completely from scratch.\n\n"
            "As Principal Infrastructure Lead, he migrated over 100 repositories from Bitbucket to GitHub Actions, engineering reusable "
            "modular workflow templates, automated linting, container builds, and security scanning (Trivy/Snyk) across thousands of concurrent "
            "Linux runners with 99.8% build reliability.\n\n"
            "To harden security, he eliminated static cloud credentials across runners by implementing keyless Workload Identity Federation (OIDC) "
            "with AWS and GCP. He then paired continuous integration with ArgoCD GitOps for automated, declarative deployments to Kubernetes, "
            "reducing release lead times from hours to under 10 minutes.\n\n"
            "Would you like to know more about his reusable workflow templates, runner autoscaling, or GitOps deployment strategies?"
        )

    # Cloud Providers: Azure, Oracle Cloud (OCI) & Multi-Cloud
    if re.search(r"\bazure\b|\boracle\b|\boci\b", q_lower):
        return (
            "Brandon's primary cloud expertise is focused on **AWS** and **GCP**, where he manages multi-account organizations, "
            "EKS/GKE clusters, serverless Cloud Run, and large-scale Terraform automation.\n\n"
            "However, he also understands multi-cloud and cloud-agnostic architectures across **Microsoft Azure** (AKS, Azure DevOps, Blob Storage) "
            "and **Oracle Cloud Infrastructure (OCI)**. Because he architects infrastructure declaratively using **Terraform / OpenTofu** "
            "and containerized workloads on Kubernetes, his patterns for networking, IAM least-privilege, GitOps delivery, and distributed "
            "observability translate directly to Azure and OCI.\n\n"
            "Are you evaluating him for an Azure, Oracle, or hybrid cloud infrastructure environment?"
        )

    # Configuration Management: Ansible / Chef / Puppet
    if any(w in q_lower for w in ["ansible", "puppet", "chef"]):
        return (
            "Brandon has worked with configuration management tools like **Ansible** for host provisioning and Linux system automation, "
            "though his primary modern focus is immutable infrastructure using **Terraform / OpenTofu**, Docker multi-stage container builds, "
            "and declarative Kubernetes/GitOps configurations.\n\n"
            "He pairs systems automation with POSIX Bash and Go daemons for high-reliability platform tooling.\n\n"
            "What kind of infrastructure automation setup does your team use?"
        )

    # Kubernetes & GitOps
    if any(w in q_lower for w in ["kubernetes", "eks", "k8s", "argocd", "gitops"]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "Brandon has extensive hands-on experience with Kubernetes, especially leading enterprise migrations and GitOps adoption.\n\n"
            "As Lead Platform Engineer, he architected and led the zero-downtime migration of over 30 mission-critical microservices "
            "from legacy AWS ECS to Amazon EKS. To streamline delivery, he introduced ArgoCD for declarative GitOps, which slashed "
            "deployment lead times from hours down to under 10 minutes.\n\n"
            "On the networking and security side, he rolled out AWS App Mesh with Envoy proxies across clusters to enforce zero-trust "
            "mTLS encryption with automated ACM certificate rotation. He also authored a custom Go controller (`prometheus-ingress-status-exporter`) "
            "to dynamically discover Ingress endpoints and export health metrics to Prometheus, and used Karpenter with Spot instances "
            "to cut thousands in idle cluster compute costs.\n\n"
            "Are you curious about the migration process, the GitOps workflow, or his observability tooling?"
        )

    # Terraform & Infrastructure as Code
    if any(w in q_lower for w in ["terraform", "opentofu", "iac"]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "Terraform is one of Brandon's strongest core skills. He designed and maintained a centralized Terraform module platform "
            "used by over 20 engineering squads across AWS, GCP, Datadog, Snowflake, and Confluent Cloud.\n\n"
            "Beyond authoring standard reusable modules, he's built custom native Terraform providers in Go (like `terraform-provider-neo4j`) "
            "using the Terraform Plugin SDK. In CI/CD, he eliminated static cloud credentials entirely by configuring Workload Identity Federation "
            "(OIDC) in GitHub Actions so that workflows authenticate dynamically.\n\n"
            "Even this portfolio platform is 100% Terraform-managed, orchestrating Cloud Run, Firebase Hosting, and Artifact Registry with zero static keys.\n\n"
            "Are there specific infrastructure patterns or cloud providers you'd like to hear more about?"
        )

    # Kafka & Event Streaming
    if any(w in q_lower for w in ["kafka", "confluent", "streaming", "msk"]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "Brandon has deep enterprise experience with Apache Kafka and Confluent Cloud. As a Staff Data Infrastructure Engineer, "
            "he led the strategic migration of 40+ microservices from self-hosted AWS MSK to Confluent Cloud—achieving zero customer downtime "
            "and zero message loss throughout the entire cutover.\n\n"
            "Along with the broker cutover, he instituted enterprise Schema Registry governance using Avro and Protobuf contracts "
            "to prevent breaking changes across event schemas, and fully automated Kafka topic provisioning and ACLs with Terraform GitOps pipelines.\n\n"
            "Are you interested in his migration playbook, schema governance, or stream processing architectures?"
        )

    # FinOps & Cloud Cost Optimization
    if any(w in q_lower for w in ["cost", "finops", "save", "saving", "spend", "budget"]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "Brandon led cloud infrastructure cost rationalization initiatives that eliminated over **$10,000/month** in cloud waste "
            "across enterprise AWS environments!\n\n"
            "The biggest win came from revamping Kubernetes compute: by implementing Karpenter dynamic autoscaling and Spot instance fleets, "
            "he reduced idle compute costs by over $6,500/month alone. He also right-sized over-provisioned Aurora RDS databases, "
            "upgraded EBS storage volumes to gp3, and instituted automated S3 lifecycle tiering.\n\n"
            "To make sure costs didn't regress, he integrated Datadog FinOps tagging and automated anomaly alerts. Even this portfolio platform "
            "is designed strictly for FinOps—it runs scale-to-zero on Cloud Run and Firebase Hosting so it incurs $0/month while idle."
        )

    # AWS App Mesh & Service Mesh
    if any(w in q_lower for w in ["service mesh", "app mesh", "mtls", "envoy"]):
        confirm = "**Yes, Brandon really did this!** " if is_verification else ""
        return (
            f"{confirm}"
            "Brandon architected zero-trust service mesh security across Kubernetes using AWS App Mesh and Envoy proxy.\n\n"
            "He enforced end-to-end mutual TLS (mTLS) encryption for all inter-service communication with automated certificate "
            "rotation via AWS Certificate Manager (ACM). He also configured fine-grained traffic routing, circuit breakers, and distributed "
            "tracing propagation so platform teams gained deep visibility into service dependencies with zero code changes."
        )

    # Programming Languages: Python
    if "python" in q_lower:
        return (
            "Yes, Brandon works with Python regularly—primarily across AI infrastructure, MLOps, and backend microservices.\n\n"
            "In his AI and agent projects, he's used Python with local LLMs (via Ollama) and Chrome DevTools Protocol automation "
            "(like in `My Agentic Team`). He's built hybrid search retrieval pipelines combining BM25 sparse indexing with dense vector embeddings, "
            "and built asynchronous APIs with FastAPI and Pydantic v2. He also uses Python extensively for CI/CD eval quality gates "
            "(using LLM-as-a-judge to test faithfulness, relevancy, and context recall).\n\n"
            "He also writes Go and Bash when he needs raw performance or low-level systems tooling. What kind of stack are you evaluating him for?"
        )

    # Programming Languages: Go / Golang
    if re.search(r"\b(go|golang)\b", q_lower):
        return (
            "Brandon uses Go (Golang) extensively for systems engineering, Kubernetes operators, and developer tooling.\n\n"
            "Key projects include:\n"
            "• **Prometheus Ingress Status Exporter**: A custom Go controller using Kubernetes `client-go` that dynamically discovers Ingress endpoints and exports latency and availability metrics to Prometheus.\n"
            "• **Terraform Provider for Neo4j**: A native Go plugin using the Terraform Plugin SDK to manage Neo4j graph database topologies declaratively.\n"
            "• Concurrent CLI daemons and system automation utilizing Go routines and channels for high concurrency.\n\n"
            "Would you like to hear more about how he structured his Kubernetes controllers or custom providers?"
        )


    # General Bio / Who is Brandon
    if any(w in q_lower for w in ["who is brandon", "about brandon", "overview", "background", "summary"]):
        return (
            "Brandon Foster is a Lead Platform & Distributed Systems Engineer specializing in cloud-native platforms, "
            "Kubernetes, Infrastructure as Code (Terraform), event-driven streaming (Kafka/Confluent), and AI infrastructure.\n\n"
            "Throughout his career, he has led large-scale microservices migrations to Amazon EKS, built centralized Terraform platforms "
            "for dozens of squads, modernized enterprise Kafka streaming, and engineered local-first AI agent workflows. "
            "He also focuses heavily on FinOps, having saved over $10K/month in cloud infrastructure optimizations.\n\n"
            "What areas of his background or projects would you like to explore?"
        )

    # Code Authorship & AI Collaboration
    if any(re.search(pat, q_lower) for pat in [
        r"\b(write|wrote)\s+(?:any\s+of\s+)?(?:your|the|this)\s+code\b",
        r"\ball\s+ai\b",
        r"\bdid\s+ai\s+write\b",
        r"\bwho\s+wrote\s+(?:your|the|this)\s+code\b",
        r"\bis\s+(?:this\s+)?code\s+ai\b",
        r"\bai\s+generated\b",
        r"\bdid\s+he\s+write\b",
    ]):
        return (
            "Brandon architected and engineered this entire platform, utilizing modern AI as an agentic pair-programmer "
            "and force multiplier.\n\n"
            "Key aspects of how this codebase was developed:\n"
            "• **Human-Led Architecture & Direction**: Brandon designed the overall system topology—the scale-to-zero GCP architecture, "
            "the Medallion data lakehouse, the in-memory hybrid retrieval engine (Dense + BM25 RRF), and multi-tier rate limiting.\n"
            "• **Agentic AI Pair-Programming**: He directed advanced coding agents (such as Google Antigravity and Gemini) to rapidly "
            "implement features and boilerplate, while personally conducting code reviews, defining domain schemas, and directing refactoring.\n"
            "• **Engineering Rigor & Quality Gates**: Every line of code is verified by over 36 automated unit and integration tests, "
            "TypeScript type checking, strict linter rules, and offline continuous evaluation gates (LLM-as-a-judge benchmarking retrieval "
            "context recall and faithfulness) running in CI/CD.\n\n"
            "So while AI accelerated the implementation under his direction, the architectural vision, engineering standards, prompt engineering, "
            "and quality gates are 100% Brandon's!"
        )

    # How Brandon Built this AI Assistant
    if any(re.search(pat, q_lower) for pat in [
        r"\bhow\s+(?:did\s+he|was|were\s+you)\s+(?:make|build|create|program)\s+(?:you|this\s+(?:bot|assistant|ai|portfolio|app|website))\b",
        r"\bhow\s+(?:do\s+you|does\s+this\s+(?:bot|ai|assistant|app|site|platform))\s+work\b",
        r"\bhow\s+were\s+you\s+(?:built|made|created)\b",
    ]):
        return (
            "I am Brandon's custom AI portfolio assistant, built as a full-stack, scale-to-zero RAG (Retrieval-Augmented Generation) "
            "application on Google Cloud!\n\n"
            "Here is how Brandon engineered my architecture:\n"
            "• **Backend & Hybrid Retrieval**: Powered by an asynchronous FastAPI service on Google Cloud Run. I use an in-memory Hybrid "
            "Retrieval engine that merges BM25 keyword search with 384-dimensional dense semantic embeddings using Reciprocal Rank Fusion (RRF)—"
            "delivering vector search precision with zero database hosting costs.\n"
            "• **LLM Streaming**: My answers stream token-by-token via Google Gemini Flash (with a deterministic conversational synthesizer "
            "fallback for offline testing and resilience).\n"
            "• **Guardrails & Privacy**: Multi-layer intent classification intercepts prompt injections, calculates math, and enforces strict "
            "privacy guardrails so personal contact info is never exposed.\n"
            "• **Medallion Data Lakehouse**: Brandon built a Medallion pipeline (Bronze raw JSON → Silver Pydantic validation & semantic chunking "
            "→ Gold signed hybrid index) that compiles his career achievements and technical projects into semantic chunks.\n"
            "• **Frontend**: A reactive single-page app built with React, Vite, and Tailwind CSS hosted globally on Firebase Hosting's CDN.\n\n"
            "Would you like to know more about the scale-to-zero FinOps design, the CI/CD eval quality gates, or the Terraform setup?"
        )

    # Scale-to-Zero GCP Infrastructure & Portfolio Architecture
    if any(re.search(pat, q_lower) for pat in [
        r"\bscale[\s\-_]*to[\s\-_]*zero\b",
        r"\b(?:tell\s+me\s+about\s+)?(?:this\s+(?:portfolio|repo|platform|website|project|app|infra|codebase)|portfolio\s+platform)\b",
    ]):
        return (
            "This portfolio platform is engineered specifically around strict **FinOps principles** to achieve **$0/month in idle "
            "infrastructure costs** while maintaining production performance and security!\n\n"
            "Key architectural components include:\n"
            "• **Scale-to-Zero Compute (Cloud Run)**: The FastAPI backend runs containerized on Google Cloud Run configured with "
            "`min-instances: 0` and `max-instances: 10`. When no visitors are active, the container scales completely to zero so you never pay "
            "for idle CPU or memory.\n"
            "• **Global Edge Delivery (Firebase Hosting)**: The React SPA frontend is served statically via Firebase Hosting's worldwide CDN cache, "
            "providing sub-50ms page loads with generous free-tier bandwidth.\n"
            "• **Serverless Lead Capture & Auth (Firestore & Firebase Auth)**: Visitor rate limiting and recruiter lead captures are recorded "
            "in Firestore, paired with Firebase Authentication for recruiter verification.\n"
            "• **Keyless CI/CD (Workload Identity Federation)**: GitHub Actions deploys infrastructure and container builds to GCP using OpenID "
            "Connect (OIDC) Workload Identity Federation—completely eliminating static service account JSON keys.\n"
            "• **100% Terraform IaC**: The entire platform—IAM roles, Cloud Run services, Artifact Registry, and Firebase Hosting—is declared "
            "and deployed declaratively via Terraform.\n\n"
            "Are you curious about the hybrid RAG engine, the Medallion data pipeline, or how cold starts are handled?"
        )

    # Fallback from retrieved sources (synthesized conversationally)
    if raw_sources:
        # Filter out personal profile chunk for technical or non-personal inquiries
        if not any(kw in q_lower for kw in PERSONAL_TOPIC_KEYWORDS):
            filtered_sources = [s for s in raw_sources if s.get("id") != "chunk-personal-profile"]
            if filtered_sources:
                raw_sources = filtered_sources
            elif any(s.get("id") == "chunk-personal-profile" for s in raw_sources):
                # Only personal chunk was retrieved for a non-personal query
                raw_sources = []

    if raw_sources:
        top_hit = raw_sources[0]
        title = top_hit.get("title", "").replace("Experience: ", "").replace("Project: ", "").replace("Skills: ", "")
        content = clean_text(top_hit.get("content", ""))

        # Check substantive query relevance:
        # Ignore common filler and the author's own name so off-topic queries don't match the bio chunk
        STOP_WORDS = {
            "what", "is", "about", "how", "hows", "whats", "many", "does", "have", "tell", "me", "the", "he", "his",
            "can", "you", "do", "a", "an", "in", "for", "of", "to", "and", "or", "on", "brandon",
            "foster", "with", "any", "are", "there", "has", "had", "would", "could", "should", "some",
            "much", "know", "experience", "work", "worked", "from", "scratch", "chops",
            "yes", "yeah", "yea", "yep", "yup", "no", "nope", "please", "more", "also", "like"
        }
        normalized_q = re.sub(r"\bci[\s\-_/]+cd\b", "cicd", q_lower)
        normalized_q = re.sub(r"\bpipline(s)?\b", r"pipeline\1", normalized_q)
        query_words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", normalized_q) if w not in STOP_WORDS]
        normalized_doc = re.sub(
            r"\bci[\s\-_/]+cd\b",
            "cicd",
            f"{title.lower()} {content.lower()} {' '.join(top_hit.get('tags', [])).lower()}"
        )

        has_substantive_match = any(w in normalized_doc for w in query_words)
        if query_words and not has_substantive_match:
            TECH_INDICATORS = {
                "experience", "tool", "tools", "stack", "tech", "technology", "technologies",
                "database", "db", "framework", "library", "platform", "cloud", "infra",
                "infrastructure", "language", "pipeline", "pipelines", "ci", "cd", "cicd", "k8s", "docker",
                "container", "containers", "deploy", "deployment", "service", "services", "architecture", "engineer",
                "engineering", "developer", "code", "devops", "mlops", "sre", "monitoring", "metrics",
                "observability", "api", "backend", "system", "systems", "cluster", "server",
                "software", "skills", "skill", "proficient", "know", "use", "using", "used", "work", "worked",
                "build", "built", "manage", "managed", "chops", "run", "running", "orchestrat", "stream",
                "streaming", "data", "storage", "security", "audit", "compliance"
            }
            is_technical_query = any(ind in q_lower for ind in TECH_INDICATORS)
            if is_technical_query:
                return (
                    "While Brandon hasn't highlighted direct production use of that specific technology in his portfolio, "
                    "his core expertise is focused on **Platform Engineering, Kubernetes, Terraform, Confluent Kafka, CI/CD, and MLOps**.\n\n"
                    "He has a proven track record of rapidly adopting adjacent technologies and applying foundational distributed systems principles. "
                    "If you'd like to ask Brandon directly about his experience in that area or discuss how his background maps to your team's stack, "
                    "you can submit your question and email through the **[Contact Page](#contact)** and it will be forwarded straight to him!"
                )
            return (
                "I don't know—maybe you should ask him! That question isn't covered in Brandon's engineering portfolio docs. "
                "You can submit your question and email directly through the **[Contact Page](#contact)** and it will be forwarded straight to him."
            )

        # Parse content into clean conversational highlights
        raw_lines = content.split("\n")
        detail_lines = []
        is_personal_chunk = (top_hit.get("id") == "chunk-personal-profile")
        if is_verification:
            intro = f"**Yes, Brandon really did this!** In his work with **{title}**, he directly engineered this initiative in production.\n\n"
        elif is_personal_chunk:
            intro = "Regarding Brandon's background and personal preferences:\n\n"
        else:
            intro = f"In his work with **{title}**, Brandon has extensive hands-on experience.\n\n"

        for line in raw_lines:
            l = line.strip()
            if not l:
                continue
            if (l.startswith("[") and l.endswith("]")) or re.match(r"^\[.*\]$", l):
                continue
            if any(l.startswith(prefix) for prefix in [
                "Role:", "Tech Stack:", "Category:", "Summary:", "Overview:", "Tagline:",
                "Repository:", "Live Demo:", "Skills and Production Proof-Points:",
                "Quantified Impact", "Technologies", "Impact Metrics",
                "Key Architectural Highlights", "Highlights", "Key Highlights"
            ]):
                if l.startswith("Summary:"):
                    intro += f"{l.replace('Summary:', '').strip()}\n\n"
                elif l.startswith("Overview:"):
                    intro += f"{l.replace('Overview:', '').strip()}\n\n"
                continue
            if l.lower() == title.lower() or l.lower() in title.lower():
                continue
            cleaned = l.lstrip("•- *").strip()
            if (cleaned.startswith("[") and cleaned.endswith("]")) or re.match(r"^\[.*\]$", cleaned):
                continue
            if any(cleaned.startswith(prefix) for prefix in [
                "Role:", "Tech Stack:", "Category:", "Summary:", "Overview:", "Tagline:",
                "Repository:", "Live Demo:", "Key Architectural Highlights", "Highlights", "Key Highlights"
            ]):
                continue
            if cleaned and len(cleaned) > 5:
                detail_lines.append(f"• {cleaned}")

        response = intro
        if detail_lines:
            matching_lines = [l for l in detail_lines if any(qw in l.lower() for qw in query_words)]
            other_lines = [l for l in detail_lines if not any(qw in l.lower() for qw in query_words)]
            if is_personal_chunk and matching_lines:
                selected_lines = matching_lines[:3]
            else:
                selected_lines = (matching_lines + other_lines)[:3]
            lead_in = "Specifically, here is how he implemented it in production:\n" if is_verification else "Key highlights include:\n"
            response += lead_in + "\n".join(selected_lines) + "\n\n"
        response += "Feel free to ask for deeper architectural details, design trade-offs, or specific tooling!"
        return response

    return (
        "I don't know—maybe you should ask him! That question isn't covered in Brandon's engineering portfolio docs, "
        "but you can submit your question and email directly through the **[Contact Page](#contact)** and it will be forwarded straight to him."
    )


# Alias for compatibility
synthesize_grounded_answer = synthesize_conversational_response
