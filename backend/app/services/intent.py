"""Query Intent Classification and Safety Guardrails.

Detects:
1. Adversarial / Prompt Injection attempts (Guardrail)
2. System health / Ping / Diagnostic queries (Ping)
3. Conversational greetings and self-introductions (Greeting)
4. Contact / Recruiter / Hiring inquiries (Contact)
5. Elementary arithmetic / Math questions (Math)
6. Clearly out-of-domain trivia / non-engineering questions (Off-topic)
7. Portfolio technical search (Portfolio)
"""

import re
from enum import Enum
from typing import Tuple, Optional, List, Dict, Any


class IntentType(str, Enum):
    GUARDRAIL = "guardrail"
    PING = "ping"
    GREETING = "greeting"
    CONTACT = "contact"
    OFF_TOPIC_MATH = "off_topic_math"
    OFF_TOPIC_GENERAL = "off_topic_general"
    PORTFOLIO_SEARCH = "portfolio_search"


# 1. Guardrail Patterns
GUARDRAIL_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"delete\s+your",
    r"reveal\s+your",
    r"jailbreak",
    r"you\s+are\s+now\s+in\s+dan\s+mode",
    r"override\s+your",
    r"bypass\s+safety",
]

# 2. System Diagnostic / Ping Patterns
PING_PATTERNS = [
    r"^test+$",
    r"^testing(\s+\d+)?$",
    r"^ping$",
    r"^pong$",
    r"^echo$",
    r"^status$",
    r"^health$",
    r"^check$",
    r"^hello\s+world$",
    r"^can\s+you\s+hear\s+me\??$",
    r"^are\s+you\s+(online|working|there|alive)\??$",
    r"^123+$",
]

# 3. Conversational Greetings / Identity Patterns
GREETING_PATTERNS = [
    r"^hi+$",
    r"^hello+$",
    r"^hey+$",
    r"^heya+$",
    r"^howdy+$",
    r"^sup+$",
    r"^yo+$",
    r"^good\s+(morning|afternoon|evening|day)$",
    r"^greetings$",
    r"^who\s+are\s+you\??$",
    r"^what\s+are\s+you\??$",
    r"^what\s+can\s+you\s+do\??$",
    r"^help$",
    r"^what\s+is\s+this\s+bot\??$",
]

# 4. Contact / Hiring Patterns
CONTACT_PATTERNS = [
    r"how\s+(can|do)\s+i\s+contact\s+(him|brandon)",
    r"how\s+to\s+contact",
    r"contact\s+info",
    r"reach\s+(out\s+to\s+)?brandon",
    r"hire\s+brandon",
    r"is\s+he\s+(open\s+to|looking\s+for)\s+(roles|jobs|work)",
    r"(email|linkedin|github)\s+address",
    r"where\s+is\s+brandon\s+located",
    r"where\s+does\s+brandon\s+live",
    r"where\s+can\s+i\s+(find|see)\s+his\s+resume",
]

# 5. Off-Topic Trivia / General Patterns
OFF_TOPIC_GENERAL_PATTERNS = [
    r"is\s+a\s+hotdog\s+a\s+sandwich",
    r"what\s+is\s+the\s+meaning\s+of\s+life",
    r"tell\s+me\s+a\s+joke",
    r"what('s|\s+is)\s+the\s+weather",
    r"what\s+is\s+the\s+capital\s+of",
    r"recipe\s+for",
    r"who\s+won\s+the\s+(super\s+bowl|world\s+series|world\s+cup|election)",
]


def check_guardrails(query: str) -> bool:
    """Detects prompt injection attempts."""
    q = query.lower().strip()
    return any(re.search(pat, q) for pat in GUARDRAIL_PATTERNS)


def detect_math(query: str) -> Optional[str]:
    """Detects and calculates elementary arithmetic queries."""
    q_clean = query.lower().strip().rstrip("?").strip()
    # Match patterns like: "5 * 10", "whats 5*10", "what is 25 * 4", "100 / 2"
    m = re.match(
        r"^(?:what\s+is|whats|calculate|solve)?\s*(\d+(?:\.\d+)?)\s*([\+\-\*\/xX])\s*(\d+(?:\.\d+)?)$",
        q_clean,
    )
    if m:
        n1 = float(m.group(1))
        op = m.group(2).lower()
        n2 = float(m.group(3))
        if op == "+":
            res = n1 + n2
        elif op == "-":
            res = n1 - n2
        elif op in ("*", "x"):
            res = n1 * n2
        elif op == "/":
            res = n1 / n2 if n2 != 0 else "undefined"
        else:
            return None

        if isinstance(res, float) and res.is_integer():
            res = int(res)

        op_sym = "×" if op in ("*", "x") else op
        return (
            f"{m.group(1)} {op_sym} {m.group(3)} = **{res}**.\n\n"
            "While I can perform quick calculations, my primary role is as Brandon Foster's "
            "technical portfolio assistant! Feel free to ask about his engineering projects, "
            "Kubernetes architectures, Terraform modules, or Kafka streaming platforms."
        )
    return None


def classify_intent(query: str) -> Tuple[IntentType, Optional[str]]:
    """Classifies user query into an IntentType, returning precomputed answers for non-search intents."""
    q_raw = query.strip()
    q_lower = q_raw.lower()

    # 1. Guardrail Check
    if check_guardrails(q_raw):
        return (
            IntentType.GUARDRAIL,
            "I am Brandon Foster's portfolio assistant, designed to discuss his engineering background, "
            "projects, and architecture experience. I cannot modify my system instructions. "
            "Feel free to ask about Brandon's work with Kubernetes, Terraform, MLOps, or Kafka!",
        )

    # 2. Math Check
    math_resp = detect_math(q_raw)
    if math_resp:
        return (IntentType.OFF_TOPIC_MATH, math_resp)

    # 3. System Diagnostic / Ping Check
    for pat in PING_PATTERNS:
        if re.search(pat, q_lower):
            return (
                IntentType.PING,
                "Systems are fully operational! I am Brandon Foster's AI Assistant, connected to a live "
                "retrieval engine indexing his Platform Engineering, Kubernetes, Terraform, Kafka, and MLOps experience.\n\n"
                "What would you like to know about Brandon's background or projects?",
            )

    # 4. Conversational Greeting Check
    for pat in GREETING_PATTERNS:
        if re.search(pat, q_lower):
            return (
                IntentType.GREETING,
                "Hello! I am Brandon Foster's AI Assistant. I can answer questions and provide architectural deep-dives into Brandon's engineering background, including:\n\n"
                "• **Platform & Cloud Engineering**: Enterprise Terraform module platforms, multi-cloud automation (AWS/GCP), CI/CD pipelines\n"
                "• **Distributed Systems & Kubernetes**: Amazon EKS migrations, ArgoCD GitOps, AWS App Mesh zero-trust mTLS\n"
                "• **Streaming Data Platforms**: Apache Kafka & Confluent Cloud migrations, Schema Registry governance\n"
                "• **AI Infrastructure & MLOps**: Local LLMs (Ollama), autonomous agent architectures, Hybrid RAG pipelines\n"
                "• **FinOps & Cost Optimization**: Strategic rationalization that saved over $10K/month in cloud infrastructure\n\n"
                "What would you like to explore?",
            )

    # 5. Contact / Hiring Check
    for pat in CONTACT_PATTERNS:
        if re.search(pat, q_lower):
            return (
                IntentType.CONTACT,
                "You can connect directly with Brandon Foster:\n\n"
                "• **LinkedIn**: [linkedin.com/in/brandocomando](https://linkedin.com/in/brandocomando)\n"
                "• **GitHub**: [github.com/brandocomando](https://github.com/brandocomando)\n"
                "• **Email**: brandocomando8@gmail.com\n\n"
                "Brandon is an experienced Lead Platform & Distributed Systems Engineer specializing in "
                "Kubernetes, Terraform, Event-Driven Streaming, and MLOps platforms. "
                "Feel free to ask me for a summary of his recent impact or technical competencies!",
            )

    # 6. Off-Topic General Check
    for pat in OFF_TOPIC_GENERAL_PATTERNS:
        if re.search(pat, q_lower):
            return (
                IntentType.OFF_TOPIC_GENERAL,
                "That topic is outside the scope of Brandon Foster's professional engineering portfolio. "
                "I'm dedicated to sharing details about Brandon's technical background, architecture decisions, "
                "and software projects—such as his work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure.\n\n"
                "What would you like to explore regarding his engineering experience?",
            )

    # Default to Portfolio Search
    return (IntentType.PORTFOLIO_SEARCH, None)
