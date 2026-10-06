"""Conversational Synthesizer for Brandon Foster's Portfolio Assistant.

Generates fluid, natural, conversational responses answering questions about
Brandon's engineering background, architecture decisions, and projects.
Strictly protects personal privacy: never reveals email, phone, or private data.
"""

import re
from typing import List, Dict, Any, Optional


def clean_text(text: str) -> str:
    """Removes internal tags, bracketed headers, and metadata."""
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\(GitHub Stars:\s*\d+\)", "", text)
    return text.strip()


def synthesize_conversational_response(question: str, raw_sources: List[Dict[str, Any]]) -> str:
    """Produces a natural, fluid conversational response strictly grounded in Brandon's experience."""
    q_lower = question.lower().strip()

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
    # Residential street address is private; general location is Southern California
    if any(re.search(pat, q_lower) for pat in [
        r"\b(street\s+address|home\s+address|house\s+number|zip\s*code|apartment)\b"
    ]):
        return (
            "I don't know—maybe you should ask him! Specific residential address information is private. "
            "Brandon is based in Southern California. You can reach out directly through the **[Contact Page](#contact)**."
        )

    if any(re.search(pat, q_lower) for pat in [
        r"\bwhere\s+(?:does\s+he|is\s+he|do\s+you|does\s+brandon)\s+(?:live|reside|based)\b",
        r"\bwhere\s+(?:is\s+brandon|are\s+you)\s+(?:from|located|based)\b",
        r"\b(?:his|brandon\'?s?)\s+location\b",
        r"\bwhere\s+(?:are\s+you|is\s+he)\s+located\b",
    ]):
        return "Brandon lives and is based in **Southern California**."

    # Work Preferences, In-Office, On-Site, Hybrid, Remote, Relocation
    if any(re.search(pat, q_lower) for pat in [
        r"\bwork\s+preference[s]?\b",
        r"\b(?:relocat\w*|willing\s+to\s+relocate|relocation)\b",
        r"\b(?:is\s+he|are\s+you|would\s+he|can\s+he|does\s+he)\s+(?:open\s+to|willing\s+to|do)\s+(?:relocation|relocating|hybrid|remote|in[\s\-_]*office|on[\s\-_]*site|office|work)\b",
        r"\b(?:remote|hybrid|in[\s\-_]*office|on[\s\-_]*site)\s+(?:work|working|preferences?|roles?|opportunities?|job|jobs|arrangement)\b",
        r"\b(?:open\s+to|willing\s+to\s+work|come\s+into)\s+(?:an?\s+|the\s+)?(?:in[\s\-_]*office|on[\s\-_]*site|office)\b",
        r"\b(?:work|working)\s+(?:in[\s\-_]*office|on[\s\-_]*site|in\s+(?:an?\s+|the\s+)?office|onsite)\b",
        r"\b(?:in[\s\-_]*office|on[\s\-_]*site)\s+work\b",
        r"\b(?:remote\s+only|only\s+remote)\b",
        r"\b(?:in[\s\-_]*office|on[\s\-_]*site)\b",
    ]):
        return (
            "Brandon's work preference is **Remote**, but he is open to **hybrid opportunities in Orange County, CA**.\n\n"
            "He is not looking for full-time in-office roles and is **not willing to relocate**."
        )

    # Years of DevOps & Platform Experience
    if any(re.search(pat, q_lower) for pat in [
        r"\bhow\s+many\s+years\s+(?:of\s+)?(?:experience|devops|platform)\b",
        r"\byears\s+of\s+(?:devops|experience|engineering|platform)\b",
        r"\bhow\s+long\s+has\s+he\s+been\s+(?:doing\s+devops|in\s+devops|an\s+engineer)\b",
    ]):
        return (
            "Brandon has **14+ years** of DevOps, Platform Engineering, and distributed systems architecture experience."
        )

    # Former & Current Employers / Career History
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:former|past|previous|current)\s+employer[s]?\b",
        r"\b(?:former|past|previous|current)\s+compan(?:y|ies)\b",
        r"\bwhere\s+(?:has|did)\s+(?:he|brandon|you)\s+work(?:ed)?\b",
        r"\bcompan(?:y|ies)\s+(?:has\s+he|has\s+brandon|he\s+has|brandon\s+has)?\s*work(?:ed)?\b",
        r"\bwork(?:ed)?\s+at\b",
        r"\bwork(?:ed)?\s+for\b",
        r"\b(?:liferay|lakeshore|melrok|persefoni|life360)\b",
        r"\bcurrent\s+(?:company|role|job|employer)\b",
    ]):
        return (
            "Brandon's engineering career spans 14+ years across several companies:\n\n"
            "• **Life360** (Current)\n"
            "• **Persefoni AI**\n"
            "• **Melrok**\n"
            "• **Lakeshore Learning Materials**\n"
            "• **Liferay**\n\n"
            "Would you like to hear more about his architectural initiatives or migrations at any of these companies?"
        )

    # Favorite Color
    if re.search(r"\b(?:favorite|fav)\s+colou?r\b|\bwhat\s+(?:is\s+his|is\s+your)\s+colou?r\b", q_lower):
        return "Brandon's favorite color is **Blue**!"

    # Coffee or Tea
    if any(re.search(pat, q_lower) for pat in [
        r"\bcoffee\s+or\s+tea\b",
        r"\btea\s+or\s+coffee\b",
        r"\b(?:does\s+he\s+drink|do\s+you\s+drink)\s+(?:coffee|tea)\b",
        r"\b(?:favorite|fav)\s+drink\b",
    ]):
        return "**COFFEE!!!!!!** (Hands down—he runs on coffee! ☕)"

    # Cats or Dogs / Pets
    if any(re.search(pat, q_lower) for pat in [
        r"\bcats?\s+or\s+dogs?\b",
        r"\bdogs?\s+or\s+cats?\b",
        r"\b(?:cats|dogs)\s+person\b",
        r"\b(?:does\s+he\s+have|do\s+you\s+have)\s+(?:pets|a\s+pet|cats?|dogs?)\b",
        r"\b(?:his|your)\s+pets?\b",
    ]):
        return "**Cats!!!!!** (Brandon is definitely a cat person! 🐱)"

    # Education & University
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:where\s+did\s+he\s+go\s+to\s+school|where\s+did\s+you\s+go\s+to\s+school)\b",
        r"\b(?:education|college|university|degree|school|alma\s+mater|biola)\b",
        r"\bwhat\s+did\s+he\s+study\b",
    ]):
        return (
            "Brandon attended **Biola University**, graduating with a Bachelor of Science (**BS**) in **Computer Science**."
        )

    # Tabs or Spaces
    if re.search(r"\btabs?\s+or\s+spaces?\b|\bspaces?\s+or\s+tabs?\b", q_lower):
        return "**Tabs**!"

    # Night Owl or Early Bird
    if any(re.search(pat, q_lower) for pat in [
        r"\bnight\s*owl\s+or\s+early\s*bird\b",
        r"\bearly\s*bird\s+or\s+night\s*owl\b",
        r"\bnight\s*owl\b",
        r"\bearly\s*bird\b",
        r"\bmorning\s+person\b",
    ]):
        return "Brandon is an **early bird**! 🌅"

    # Pineapple on Pizza
    if re.search(r"\b(?:pineapple\s+on\s+pizza|pizza\s+with\s+pineapple|pineapple\s+belong\s+on\s+pizza)\b", q_lower):
        return "**YES!** Pineapple definitely belongs on pizza! 🍕🍍"

    # Favorite Season
    if re.search(r"\b(?:favorite|fav)\s+season\b|\bwhich\s+season\b", q_lower):
        return "Brandon's favorite season is **Fall**! 🍂"

    # Dad Jokes
    if re.search(r"\bdad\s+jokes?\b", q_lower):
        return "**All the time!** (Brandon loves a good dad joke! 😄)"

    # Beach or Mountains
    if re.search(r"\bbeach\s+or\s+mountains?\b|\bmountains?\s+or\s+beach\b", q_lower):
        return "**Mountains**! 🏔️"

    # Favorite Place
    if re.search(r"\b(?:favorite|fav)\s+place\b|\byosemite\b", q_lower):
        return "Brandon's favorite place is **Yosemite**! 🏞️"

    # Most Commonly Used Emoji
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:most\s+common(?:ly)?\s+used\s+emoji|favorite\s+emoji|emojis?)\b",
        r"\bwhat\s+emoji\b",
    ]):
        return (
            "Brandon's most commonly used emojis are **ThumbsUp** (👍), **Roger roger** (🫡), and **Facepalm** (🤦)!"
        )

    # Social Profiles (LinkedIn & GitHub)
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:socials?|social\s+media|profiles?|linkedin|github\s+profile)\b"
    ]):
        return (
            "You can find Brandon on [LinkedIn](https://www.linkedin.com/in/brandon-foster) "
            "and check out his open-source work on [GitHub](https://github.com/brandocomando)!"
        )

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

    # Compliance Standards: SOC 2, HIPAA, ISO 27001 & DevSecOps
    if re.search(r"\bsoc\s*2\b|\bsoc2\b|\bhipaa\b|\biso\s*27001\b|\biso27001\b|\bcompliance\b|\baudit\b|\bsecurity\s+standards?\b", q_lower):
        return (
            "Yes! Brandon has direct experience designing cloud security architectures and supplying technical evidence to satisfy "
            "**SOC 2 Type 2**, **HIPAA**, and **ISO 27001** compliance audits.\n\n"
            "Key technical controls and compliance practices he has implemented include:\n"
            "• **Least-Privilege & Identity Governance**: Enforced strict IAM role boundaries, AWS Organizations Service Control Policies (SCPs), "
            "and eliminated static long-lived credentials by adopting Workload Identity Federation (WIF) and keyless OIDC across all CI/CD runners.\n"
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
        return (
            "Brandon has deep, battle-tested expertise in **CI/CD and pipeline engineering**, including architecting "
            "enterprise pipelines completely from scratch.\n\n"
            "Key milestones and architectural patterns include:\n"
            "• **Enterprise Migration from Scratch (100+ Repos)**: As Principal Infrastructure / DevOps Lead, he led the enterprise-wide "
            "migration of over 100 repositories from Bitbucket to GitHub and GitHub Actions. He engineered standardized, reusable "
            "workflow templates, automated linting, container build pipelines, and security scanning (Trivy/Snyk) across thousands of concurrent Linux runners, boosting build reliability to 99.8%.\n"
            "• **Keyless Cloud Security (OIDC / WIF)**: Eliminated static, long-lived cloud credentials across CI runners by implementing "
            "Workload Identity Federation (WIF) and OIDC keyless authentication between GitHub Actions and cloud providers (GCP & AWS).\n"
            "• **Declarative GitOps Delivery**: Paired CI with ArgoCD for continuous delivery into Kubernetes (EKS/GKE), enabling automated canary "
            "rollouts, dynamic horizontal pod autoscaling, and reducing deployment lead times from hours to under 10 minutes.\n"
            "• **MLOps Quality Gates**: Built continuous offline evaluation pipelines running LLM-as-a-judge tests in CI to benchmark retrieval context recall, "
            "MRR, and answer faithfulness before promoting model or retrieval changes.\n\n"
            "Would you like to know more about his reusable workflow design, runner scaling, or GitOps deployment strategies?"
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
        return (
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
        return (
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
        return (
            "Brandon has deep enterprise experience with Apache Kafka and Confluent Cloud. As a Staff Data Infrastructure Engineer, "
            "he led the strategic migration of 40+ microservices from self-hosted AWS MSK to Confluent Cloud—achieving zero customer downtime "
            "and zero message loss throughout the entire cutover.\n\n"
            "Along with the broker cutover, he instituted enterprise Schema Registry governance using Avro and Protobuf contracts "
            "to prevent breaking changes across event schemas, and fully automated Kafka topic provisioning and ACLs with Terraform GitOps pipelines.\n\n"
            "Are you interested in his migration playbook, schema governance, or stream processing architectures?"
        )

    # FinOps & Cloud Cost Optimization
    if any(w in q_lower for w in ["cost", "finops", "save", "saving", "spend", "budget"]):
        return (
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
        return (
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

    # Fallback from retrieved sources (synthesized conversationally)
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
            "much", "know", "experience", "work", "worked", "from", "scratch", "chops"
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
        intro = f"In his work with **{title}**, Brandon has extensive hands-on experience.\n\n"

        for line in raw_lines:
            l = line.strip()
            if not l:
                continue
            if (l.startswith("[") and l.endswith("]")) or re.match(r"^\[.*\]$", l):
                continue
            if any(l.startswith(prefix) for prefix in [
                "Role:", "Tech Stack:", "Category:", "Summary:", "Skills and Production Proof-Points:",
                "Quantified Impact", "Technologies", "Impact Metrics"
            ]):
                if l.startswith("Summary:"):
                    intro += f"{l.replace('Summary:', '').strip()}\n\n"
                continue
            if l.lower() == title.lower() or l.lower() in title.lower():
                continue
            cleaned = l.lstrip("•- *").strip()
            if (cleaned.startswith("[") and cleaned.endswith("]")) or re.match(r"^\[.*\]$", cleaned):
                continue
            if cleaned and len(cleaned) > 10:
                detail_lines.append(f"• {cleaned}")

        response = intro
        if detail_lines:
            response += "Key highlights include:\n" + "\n".join(detail_lines[:3]) + "\n\n"
        response += "Feel free to ask for deeper architectural details, design trade-offs, or specific tooling!"
        return response

    return (
        "I don't know—maybe you should ask him! That question isn't covered in Brandon's engineering portfolio docs, "
        "but you can submit your question and email directly through the **[Contact Page](#contact)** and it will be forwarded straight to him."
    )


# Alias for compatibility
synthesize_grounded_answer = synthesize_conversational_response
