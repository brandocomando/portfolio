"""Conversational Synthesizer for Brandon Foster's Portfolio Assistant.

Generates fluid, natural, conversational responses answering questions about
Brandon's engineering background, architecture decisions, and projects.
Strictly protects personal privacy: never reveals email, phone, or private data.
"""

import re
from typing import List, Dict, Any, Optional


def clean_text(text: str) -> str:
    """Removes internal tags and bracketed metadata."""
    text = re.sub(r"\[[A-Z\s\:\&]+\]", "", text)
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

    # 4. Personal Information Inquiries (Kids, Family, Location, Age, Salary, Lifestyle, etc.)
    if any(re.search(pat, q_lower) for pat in [
        r"\b(kid|kids|child|children|son|sons|daughter|daughters|baby|babies)\b",
        r"\b(wife|husband|spouse|partner|married|marry|single|dating|girlfriend|boyfriend|ex-wife|fiance)\b",
        r"\b(family|parents|mom|mother|dad|father|brother|brothers|sister|sisters|relatives)\b",
        r"\bwhere\s+(does|is)\s+(he|brandon)\s+(live|located|from|stay|reside|sleep)\b",
        r"\b(where\s+does\s+he\s+live|where\s+is\s+he\s+located|where\s+is\s+he\s+from|where\s+was\s+he\s+born)\b",
        r"\b(his|brandon\'?s?)\s+(address|home|house|apartment|city|state|zip|neighborhood|town)\b",
        r"\bhow\s+old\s+is\s+(he|brandon)\b",
        r"\b(birthday|birth\s*date|date\s+of\s+birth|when\s+was\s+he\s+born|where\s+was\s+he\s+born)\b",
        r"\b(his|brandon\'?s?)\s+age\b",
        r"\b(phone|cell|mobile)\s*(number)?\b",
        r"\bwhat\s+is\s+(his|brandon\'?s?)\s+(email|phone|number|address|salary|net\s*worth)\b",
        r"\b(his|brandon\'?s?)\s+(email(\s*address)?|phone\s*number|cell\s*phone|contact\s*info)\b",
        r"\b(salary|net\s*worth|income|compensation|how\s+much\s+does\s+he\s+(make|earn|get\s*paid))\b",
        r"\b(personal|private)\s+(life|info|question|details|matters)\b",
        r"\b(hobbies|hobby|favorite\s+food|favorite\s+movie|favorite\s+color|free\s+time|weekend|weekends)\b",
        r"\b(religion|religious|political|politics|faith|church|god)\b",
        r"\b(pet|pets|dog|dogs|cat|cats)\b",
    ]):
        return (
            "I don't know—maybe you should ask him! That personal information is not in his public engineering docs. "
            "You can submit your question and email through the **[Contact Page](#contact)**, and it will be forwarded straight to Brandon's inbox."
        )

    # 5. Contact & Hiring Inquiries (Zero email/phone exposure)
    if any(w in q_lower for w in ["contact", "hire", "email", "reach", "resume"]):
        return (
            "Brandon doesn't publish his direct email or phone number on the site, but you can message him directly "
            "through the **[Contact Page](#contact)**!\n\n"
            "Just submit your question and email, and your message will be forwarded straight to his inbox. "
            "You can also connect with him on [LinkedIn](https://linkedin.com/in/brandocomando) and [GitHub](https://github.com/brandocomando)."
        )

    # 6. Core Technical Topics
    # AI Infrastructure & MLOps
    if any(w in q_lower for w in ["mlops", "ml ops", "ai infra", "ai infrastructure", "agent", "agents", "llm", "llms", "rag", "ollama", "machine learning", "retrieval"]):
        return (
            "Brandon specializes in **AI Infrastructure and MLOps**, bridging cloud platform engineering with production AI systems.\n\n"
            "Key highlights of his work in this space include:\n"
            "• **Autonomous Agent Architectures**: Engineered multi-agent terminal systems like *FirstMate CLI* ('Talk to one agent. Ship with a crew.') and *My Agentic Team*, coordinating local LLMs (via Ollama) with Chrome DevTools Protocol (CDP) for browser automation.\n"
            "• **Hybrid Retrieval & RAG Engines**: Built sub-millisecond retrieval pipelines combining BM25 sparse search with dense vector embeddings via Reciprocal Rank Fusion (RRF), semantic chunking, and metadata filtering—the exact architecture powering this portfolio assistant!\n"
            "• **Evaluation & Quality Gates**: Instituted automated evaluation benchmarks in CI/CD using LLM-as-a-judge patterns to evaluate context recall, MRR, and answer faithfulness.\n\n"
            "Would you like to explore his multi-agent orchestration patterns, local LLM tooling, or RAG evaluation pipelines?"
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

    # Specific Project: FirstMate CLI
    if "firstmate" in q_lower:
        return (
            "**FirstMate CLI** is a terminal orchestration tool Brandon built for multi-agent coding workflows.\n\n"
            "The concept is simple: *'Talk to one agent. Ship with a crew.'* It provides a clean terminal UI and workflow automation "
            "where a lead coordinator agent delegates tasks to specialized sub-agents running in parallel, with decoupled execution contexts. "
            "It's written in Shell/Bash with zero heavy runtime overhead.\n\n"
            "You can check it out on GitHub: [github.com/brandocomando/firstmate](https://github.com/brandocomando/firstmate)!"
        )

    # Specific Project: My Agentic Team
    if any(w in q_lower for w in ["my agentic team", "agentic team", "autonomous agent"]):
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
            "what", "is", "about", "how", "many", "does", "have", "tell", "me", "the", "he", "his",
            "can", "you", "do", "a", "an", "in", "for", "of", "to", "and", "or", "on", "brandon",
            "foster", "with", "any", "are", "there", "has", "had", "would", "could", "should", "some",
            "much", "know", "experience", "work", "worked"
        }
        query_words = [w for w in re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", q_lower) if w not in STOP_WORDS]
        doc_searchable = f"{title.lower()} {content.lower()} {' '.join(top_hit.get('tags', [])).lower()}"

        has_substantive_match = any(w in doc_searchable for w in query_words)
        if query_words and not has_substantive_match:
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
            if any(l.startswith(prefix) for prefix in ["Role:", "Tech Stack:", "Category:", "Summary:", "Skills and Production Proof-Points:"]):
                if l.startswith("Summary:"):
                    intro += f"{l.replace('Summary:', '').strip()}\n\n"
                continue
            cleaned = l.lstrip("•- *").strip()
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
