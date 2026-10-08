"""Query Intent Classification and Safety Guardrails.

Detects:
1. Adversarial / Prompt Injection attempts (Guardrail)
2. Personal inquiries / Private details (Personal)
3. System health / Ping / Diagnostic queries (Ping)
4. Conversational greetings and self-introductions (Greeting)
5. Contact / Recruiter / Hiring inquiries (Contact)
6. Elementary arithmetic / Math questions (Math)
7. Clearly out-of-domain trivia / non-engineering questions (Off-topic)
8. Portfolio technical search (Portfolio)
"""

import re
from enum import Enum
from typing import Tuple, Optional


class IntentType(str, Enum):
    GUARDRAIL = "guardrail"
    PERSONAL = "personal"
    APPROVED_PERSONAL = "approved_personal"
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

# 2. Protected Personal Information Inquiries (Strictly private; NOT in public docs)
PERSONAL_PATTERNS = [
    # Family, Kids, Children, Relationships (excluding dad jokes)
    r"\b(kid|kids|child|children|son|sons|daughter|daughters|baby|babies)\b",
    r"\b(wife|husband|spouse|partner|married|marry|single|dating|girlfriend|boyfriend|ex-wife|fiance)\b",
    r"\b(family|parents|mom|mother|dad(?![\s\-_]+jokes?)|father|brother|brothers|sister|sisters|relatives)\b",

    # Residential street address is private (general location in Southern California is authorized)
    r"\b(street\s+address|home\s+address|house\s+number|zip\s*code|apartment)\b",

    # Age, Birthday
    r"\bhow\s+old\s+is\s+(he|brandon)\b",
    r"\b(birthday|birth\s*date|date\s+of\s+birth|when\s+was\s+he\s+born|where\s+was\s+he\s+born)\b",
    r"\b(his|brandon\'?s?)\s+age\b",

    # Contact Details (Zero exposure)
    r"\b(phone|cell|mobile)\s*(number)?\b",
    r"\bwhat\s+is\s+(his|brandon\'?s?)\s+(email|phone|number|address|salary|net\s*worth)\b",
    r"\b(his|brandon\'?s?)\s+(email(\s*address)?|phone\s*number|cell\s*phone|contact\s*info)\b",

    # Money / Salary / Compensation
    r"\b(salary|net\s*worth|income|compensation|how\s+much\s+does\s+he\s+(make|earn|get\s*paid))\b",

    # Private Matters & Beliefs
    r"\b(personal|private)\s+(life|info|question|details|matters)\b",
    r"\b(religion|religious|political|politics|faith|church|god)\b",
]

# 3. System Diagnostic / Ping Patterns
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

# 4. Conversational Greetings / Identity Patterns
GREETING_PATTERNS = [
    r"^hi+$",
    r"^hello+$",
    r"^hey+$",
    r"^heya+$",
    r"^howdy+$",
    r"^sup+$",
    r"^yo+$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?what'?s\s+up[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?whats\s+up[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?what\s+is\s+up[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?how\s+are\s+you(\s+doing)?[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?how'?s\s+it\s+going[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?hows\s+it\s+going[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?how\s+is\s+it\s+going[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?what'?s\s+(?:new|happening|good)[\.!\?]*$",
    r"^(?:(?:hey|hi|hello)\s*,?\s*)?whats\s+(?:new|happening|good)[\.!\?]*$",
    r"^good\s+(morning|afternoon|evening|day)$",
    r"^greetings$",
    r"^who\s+are\s+you\??$",
    r"^what\s+are\s+you\??$",
    r"^what\s+can\s+you\s+do\??$",
    r"^help$",
    r"^what\s+is\s+this\s+bot\??$",
]

# 5. Contact / Hiring Patterns
CONTACT_PATTERNS = [
    r"how\s+(can|do)\s+i\s+contact\s+(him|brandon)",
    r"how\s+to\s+contact",
    r"contact\s+info",
    r"reach\s+(out\s+to\s+)?brandon",
    r"hire\s+brandon",
    r"is\s+he\s+(open\s+to|looking\s+for)\s+(roles|jobs|work\b(?!\w))(?!\s+(?:in|at|remotely|hybrid|onsite|office))",
    r"where\s+can\s+i\s+(find|see)\s+his\s+resume",
]

# 6. Off-Topic Trivia / General Patterns
OFF_TOPIC_GENERAL_PATTERNS = [
    r"is\s+a\s+hotdog\s+a\s+sandwich",
    r"what\s+is\s+the\s+meaning\s+of\s+life",
    r"tell\s+me\s+a\s+joke",
    r"what('s|\s+is)\s+the\s+weather",
    r"what\s+is\s+the\s+capital\s+of",
    r"recipe\s+for",
    r"who\s+won\s+the\s+(super\s+bowl|world\s+series|world\s+cup|election)",
    # World history, presidents, politics, royalty
    r"\b(?:who\s+(?:was|is)\s+(?:the\s+)?(?:\d+(?:st|nd|rd|th)\s+)?(?:president|vice\s+president|prime\s+minister|king|queen|emperor|pope|senator|governor))\b",
    r"\bpresident\s+of\s+(?:the\s+)?(?:us|united\s+states|america)\b",
    # World geography, astronomy, distances
    r"\b(?:capital|population|currency|anthem|flag)\s+of\b",
    r"\b(?:how\s+tall\s+is|height\s+of|how\s+far\s+is|distance\s+(?:to|between)|speed\s+of\s+light|mass\s+of)\b",
    # Famous historical figures & general encyclopedic "who was / who is <name>" (excluding Brandon / assistant)
    r"^who\s+(?:was|is)\s+(?!brandon\b|he\b|this\b|your\b)[a-z]+(?:\s+[a-z]+){1,2}\??$",
    r"\bwho\s+(?:invented|discovered|painted|directed|wrote\s+the\s+book)\b",
    # Science, nature, cooking
    r"\b(?:photosynthesis|quantum\s+physics|black\s+hole|speed\s+of\s+sound|solar\s+system|theory\s+of\s+relativity)\b",
    r"\b(?:how\s+to\s+(?:bake|cook|make)\s+(?:a\s+)?(?:cake|cookies?|bread|pie|soup|pasta|steak))\b",
]

# 7. Arbitrary Code Generation & Homework Patterns (Avoid free ChatGPT coding assistant abuse)
CODE_GENERATION_PATTERNS = [
    r"\b(?:write|create|implement|give\s+me|generate)\s+(?:me\s+)?(?:a\s+)?(?:[a-z0-9_\-]+\s+)?(?:script|function|class|algorithm|code|program)\s+(?:for|to|that)\s+(?:creating|making|building|solving|reversing|calculating|sorting)?\s*(?:a\s+)?(?:linked\s+list|binary\s+tree|bubble\s+sort|quicksort|merge\s+sort|leetcode|fizzbuzz|fibonacci)\b",
    r"\b(?:linked\s+list|binary\s+tree|bubble\s+sort|quicksort|merge\s+sort|fizzbuzz|fibonacci)\s+in\s+(?:python|go|golang|java|c\+\+|javascript|typescript|rust)\b",
    r"\bwrite\s+(?:me\s+)?(?:a\s+)?(?:script|code)\s+for\s+(?:creating|implementing|reversing)\s+(?:a\s+)?(?:linked\s+list|binary\s+tree)\b",
]


def detect_code_generation_request(query: str) -> Optional[str]:
    """Detects attempts to use the portfolio bot as an arbitrary coding tutor or homework script generator."""
    q_lower = query.lower()
    if any(re.search(pat, q_lower) for pat in CODE_GENERATION_PATTERNS):
        return (
            "While Brandon writes plenty of Python and Go, I'm here specifically to discuss his platform engineering "
            "background, system architectures, and projects rather than write custom scripts or solve general programming exercises.\n\n"
            "Feel free to ask about his work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure!"
        )
    return None


def check_guardrails(query: str) -> bool:
    """Detects prompt injection attempts."""
    q = query.lower().strip()
    return any(re.search(pat, q) for pat in GUARDRAIL_PATTERNS)


def detect_math(query: str) -> Optional[str]:
    """Detects and calculates elementary arithmetic queries."""
    q_clean = query.lower().strip().rstrip("?").strip()
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
            "While I can perform quick calculations, my focus is Brandon Foster's engineering portfolio. "
            "For general questions or problem solving, tools like **ChatGPT** or **Claude** are great resources!\n\n"
            "Feel free to ask me about Brandon's work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure."
        )


def is_query_about_brandon(query: str) -> bool:
    """Determines whether a query is directed at / about Brandon Foster rather than general off-topic trivia."""
    q_lower = query.lower().strip()

    # Explicit name mentions
    if re.search(r"\b(brandon|foster|brandocomando)\b", q_lower):
        return True

    # Third-person pronouns referring to Brandon
    if re.search(r"\b(he|him|his|himself)\b", q_lower):
        return True

    # Second-person queries directed at the portfolio assistant representing Brandon
    if re.search(
        r"\b(your\s+(?:experience|background|career|role|resume|cv|portfolio|contact|email|phone|skills?|projects?|work|job|location|address|salary))\b",
        q_lower,
    ):
        return True
    if re.search(
        r"\b(?:are|do|can|would|have)\s+you\s+(?:work|located|based|open\s+to|willing\s+to|have|build|use|know|code)\b",
        q_lower,
    ):
        return True

    # Career / personal attributes often asked about a candidate without explicit pronouns
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:work\s+preferences?|relocat\w*|salary\s+expectations?|clearance|security\s+clearance)\b",
        r"\b(?:years\s+of\s+(?:experience|devops|engineering|platform))\b",
        r"\b(?:former|past|previous|current)\s+(?:employer|company|job)\b",
        r"\b(?:contact\s+info|reach\s+out|send\s+(?:a\s+)?message|hire\b)",
        r"\b(?:resume|curriculum\s+vitae|cv)\b",
    ]):
        return True

    return False

def detect_approved_personal(query: str) -> Optional[str]:
    """System-1 Fast Path: Calibrated deterministic routing for authorized personal profile facts & trivia.

    Serves verified facts from personal.yaml instantly (<5ms) with zero LLM API cost, zero token burn,
    and no vector search latency. Escalates unhandled/technical questions to System-2 (Gemini Flash).
    """
    q_lower = query.lower().strip()

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

    # Specific query about Los Angeles / LA
    if re.search(r"\b(?:los\s+angeles|\bla\b)\b", q_lower) and any(w in q_lower for w in ["work", "working", "job", "hybrid", "commute", "commuting", "office", "onsite", "in-office", "role", "open", "willing"]):
        return (
            "Brandon is **not open to working in or commuting to Los Angeles (LA)**.\n\n"
            "His work preference is **Remote**, though he is open to **hybrid opportunities in Orange County, CA**. He is also not willing to relocate."
        )

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
        r"\borange\s+county\b",
    ]):
        return (
            "Brandon's work preference is **Remote**, but he is open to **hybrid opportunities in Orange County, CA** (specifically **not Los Angeles / LA**).\n\n"
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

    # Coffee Preparation / How he drinks coffee
    if any(re.search(pat, q_lower) for pat in [
        r"\bhow\s+(?:does\s+he|do\s+you|does\s+brandon)\s+(?:like|take|make|brew|drink)\s+(?:his\s+|your\s+)?coffee\b",
        r"\b(?:what\s+kind\s+of|what\s+type\s+of)\s+coffee\b",
        r"\b(?:black|french\s+press)\s+coffee\b",
        r"\bhow\s+(?:is\s+his|is\s+your)\s+coffee\b",
        r"\bcoffee\s+preparation\b",
    ]):
        return "Brandon drinks his coffee **black, brewed with a French press**! ☕ (Hands down, he runs on coffee and prefers it over tea)."

    # Coffee or Tea Binary Preference
    if any(re.search(pat, q_lower) for pat in [
        r"\bcoffee\s+or\s+tea\b",
        r"\btea\s+or\s+coffee\b",
        r"\b(?:does\s+he|do\s+you|does\s+brandon)\s+(?:prefer|choose)\s+(?:coffee|tea)\b",
        r"\b(?:does\s+he|do\s+you|does\s+brandon)\s+(?:drink|like|love)\s+tea\b",
        r"\b(?:favorite|fav)\s+(?:morning\s+)?drink\b",
        r"\b(?:do\s+you|does\s+he)\s+drink\s+coffee\b",
    ]):
        if "tea" in q_lower and "coffee" not in q_lower:
            return "Brandon runs on **COFFEE!!!!!!** ☕ (not much of a tea drinker)."
        return "**COFFEE!!!!!!** (Hands down—he runs on coffee and prefers it over tea! ☕)"

    # Cats or Dogs Binary Preference
    if any(re.search(pat, q_lower) for pat in [
        r"\bcats?\s+or\s+dogs?\b",
        r"\bdogs?\s+or\s+cats?\b",
        r"\b(?:is\s+he|are\s+you)\s+(?:a\s+)?(?:cat|dog)\s+(?:person|lover)\b",
        r"\b(?:cat|dog)\s+person\b",
        r"\b(?:does\s+he|do\s+you|does\s+brandon)\s+prefer\s+(?:cats?|dogs?)\b",
        r"\b(?:does\s+he|do\s+you|does\s+brandon)\s+(?:like|prefer)\s+(?:cats?\s+or\s+dogs?|dogs?\s+or\s+cats?)\b",
    ]):
        if "dog" in q_lower and "cat" not in q_lower:
            return "Brandon is definitely a cat person (**Cats!!!!!** 🐱), rather than dogs!"
        return "**Cats!!!!!** (Brandon is definitely a cat person! 🐱)"

    # Education & University (College / Degree / Alma Mater)
    if not re.search(r"\b(?:high\s+school|elementary|middle\s+school|grade\s+school|gpa|grades?|sat|act)\b", q_lower):
        if any(re.search(pat, q_lower) for pat in [
            r"\bwhere\s+did\s+(?:he|brandon|you)\s+go\s+to\s+(?:school|college|university)\b",
            r"\b(?:what\s+is\s+his|what\s+is\s+your|what\s+is\s+brandon\'?s?)\s+(?:education|degree|alma\s+mater)\b",
            r"\bwhat\s+(?:college|university)\s+did\s+(?:he|brandon|you)\s+(?:go\s+to|attend)\b",
            r"\b(?:what\s+degree\s+does\s+he\s+have|does\s+he\s+have\s+a\s+degree)\b",
            r"\bwhat\s+did\s+(?:he|brandon|you)\s+study\b",
            r"\bbiola\s*(?:university)?\b",
            r"\b(?:his|brandon\'?s?)\s+(?:college|university|alma\s+mater|degree)\b",
        ]):
            return (
                "Brandon attended **Biola University**, graduating with a Bachelor of Science (**BS**) in **Computer Science**."
            )

    # Tabs or Spaces
    if re.search(r"\btabs?\s+or\s+spaces?\b|\bspaces?\s+or\s+tabs?\b", q_lower):
        return "**Tabs**!"

    # Night Owl or Early Bird Binary Preference
    if any(re.search(pat, q_lower) for pat in [
        r"\bnight\s*owl\s+or\s+early\s*bird\b",
        r"\bearly\s*bird\s+or\s+night\s*owl\b",
        r"\b(?:is\s+he|are\s+you|does\s+he\s+consider\s+himself)\s+(?:an?\s+)?(?:early\s*bird|night\s*owl|morning\s+person)\b",
    ]):
        return "Brandon is an **early bird**! 🌅"

    # Pineapple on Pizza
    if re.search(r"\b(?:pineapple\s+on\s+pizza|pizza\s+with\s+pineapple|pineapple\s+belong\s+on\s+pizza)\b", q_lower):
        return "**YES!** Pineapple definitely belongs on pizza! 🍕🍍"

    # Favorite Season
    if re.search(r"\b(?:favorite|fav)\s+season\b|\bwhich\s+season\b", q_lower):
        return "Brandon's favorite season is **Fall**! 🍂"

    # Dad Jokes Preference
    if not re.search(r"\b(?:tell|give|say|share|crack)\s+(?:me\s+)?(?:a\s+)?dad\s+joke\b", q_lower):
        if any(re.search(pat, q_lower) for pat in [
            r"\b(?:does\s+he|do\s+you|does\s+brandon)\s+(?:like|tell|love|enjoy)\s+dad\s+jokes?\b",
            r"\bdad\s+jokes?\s+(?:all\s+the\s+time|fan|enthusiast)?\??$",
        ]):
            return "**All the time!** (Brandon loves a good dad joke! 😄)"

    # Beach or Mountains
    if re.search(r"\bbeach\s+or\s+mountains?\b|\bmountains?\s+or\s+beach\b", q_lower):
        return "**Mountains**! 🏔️"

    # Favorite Place
    if any(re.search(pat, q_lower) for pat in [
        r"\b(?:favorite|fav)\s+(?:place|destination|spot|park|vacation)\b",
        r"\bwhere\s+(?:is\s+his|is\s+your)\s+favorite\s+place\b",
    ]):
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

    # Personal Hobbies (Hiking, Camping, Cooking)
    is_open_ended_hobby = bool(
        re.search(r"^(?:where|what|which|how|why)\b", q_lower) and
        not re.search(r"\b(?:what\s+are\s+(?:his|your|brandon\'?s?)\s+hobbies|what\s+hobbies)\b", q_lower)
    )
    if not is_open_ended_hobby:
        if any(re.search(pat, q_lower) for pat in [
            r"\b(?:what\s+are\s+his|what\s+are\s+your|what\s+are\s+brandon\'?s?)\s+hobbies\b",
            r"\b(?:does\s+he|do\s+you)\s+have\s+(?:any\s+)?hobbies\b",
            r"\bhobb(?:y|ies)\??$",
            r"\b(?:what\s+does\s+he\s+do\s+(?:in\s+his\s+free\s+time|for\s+fun|outside\s+of\s+work))\b",
            r"\bwhat\s+(?:are\s+his\s+interests|does\s+he\s+do\s+outside\s+work)\b",
            r"\b(?:does\s+he\s+like\s+to\s+|does\s+he\s+enjoy\s+)(?:hike|hiking|camp|camping|cook|cooking)\b",
            r"\b(?:does\s+he|do\s+you)\s+(?:hike|camp|cook)\??$",
        ]):
            if "cook" in q_lower and not any(w in q_lower for w in ["hike", "camp", "hobb"]):
                return "Yes! Outside of engineering, **Cooking** is one of Brandon's favorite hobbies (along with **Hiking** and **Camping**)! 🍳🥾⛺"
            if "camp" in q_lower and not any(w in q_lower for w in ["hike", "cook", "hobb"]):
                return "Yes! Brandon loves **Camping** and spending time outdoors in nature, alongside **Hiking** and **Cooking**! ⛺🥾🍳"
            if "hike" in q_lower and not any(w in q_lower for w in ["camp", "cook", "hobb"]):
                return "Yes! Brandon loves **Hiking** in the mountains (his favorite place is Yosemite!), along with **Camping** and **Cooking**! 🥾🏔️⛺"
            return (
                "Outside of platform engineering, Brandon's favorite hobbies are:\n\n"
                "• **Hiking** 🥾 (he loves the mountains and trails, especially Yosemite!)\n"
                "• **Camping** ⛺ (spending time outdoors in nature)\n"
                "• **Cooking** 🍳\n\n"
                "Would you like to explore his technical background or architecture projects?"
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

    # 2. Personal Inquiries (Zero personal contact info exposure)
    for pat in PERSONAL_PATTERNS:
        if re.search(pat, q_lower):
            return (
                IntentType.PERSONAL,
                "I don't know—maybe you should ask him! That personal information is not in his public docs. "
                "You can submit your question and email through the **[Contact Page](#contact)**, and it will be forwarded straight to Brandon's inbox.",
            )

    # 3. Approved Personal Information & Preferences (System 1 Fast Path)
    approved_personal_resp = detect_approved_personal(q_raw)
    if approved_personal_resp:
        return (IntentType.APPROVED_PERSONAL, approved_personal_resp)

    # 4. Math Check
    math_resp = detect_math(q_raw)
    if math_resp:
        return (IntentType.OFF_TOPIC_MATH, math_resp)

    # 4. System Diagnostic / Ping Check
    for pat in PING_PATTERNS:
        if re.search(pat, q_lower):
            return (
                IntentType.PING,
                "Systems are fully operational! I am Brandon Foster's AI Assistant, connected to a live "
                "retrieval engine indexing his Platform Engineering, Kubernetes, Terraform, Kafka, and MLOps experience.\n\n"
                "What would you like to know about Brandon's background or projects?",
            )

    # 5. Conversational Greeting Check
    for pat in GREETING_PATTERNS:
        if re.search(pat, q_lower):
            if re.search(r"\b(?:what'?s\s+up|whats\s+up|what\s+is\s+up|how\s+are\s+you|how'?s\s+it\s+going|hows\s+it\s+going)\b", q_lower):
                greeting_intro = "Not much, just ready to help! I am Brandon Foster's AI Assistant."
            else:
                greeting_intro = "Hello! I am Brandon Foster's AI Assistant."
            return (
                IntentType.GREETING,
                f"{greeting_intro} I can answer questions and provide architectural deep-dives into Brandon's engineering background, including:\n\n"
                "• **Platform & Cloud Engineering**: Enterprise Terraform module platforms, multi-cloud automation (AWS/GCP), CI/CD pipelines\n"
                "• **Distributed Systems & Kubernetes**: Amazon EKS migrations, ArgoCD GitOps, AWS App Mesh zero-trust mTLS\n"
                "• **Streaming Data Platforms**: Apache Kafka & Confluent Cloud migrations, Schema Registry governance\n"
                "• **AI Infrastructure & MLOps**: Local LLMs (Ollama), autonomous agent architectures, Hybrid RAG pipelines\n"
                "• **FinOps & Cost Optimization**: Strategic rationalization that saved over $10K/month in cloud infrastructure\n\n"
                "What would you like to explore?",
            )

    # 6. Contact / Hiring Check (Zero email/phone exposure)
    is_workplace_query = bool(re.search(
        r"\b(remote|hybrid|in[\s\-_]*office|on[\s\-_]*site|office|la|los\s+angeles|orange\s+county|relocat\w*|preference[s]?)\b",
        q_lower
    ))
    if not is_workplace_query:
        for pat in CONTACT_PATTERNS:
            if re.search(pat, q_lower):
                return (
                    IntentType.CONTACT,
                "Brandon doesn't publish his direct email or phone number on the site, but you can message him directly "
                "through the **[Contact Page](#contact)**!\n\n"
                "Just submit your question and email, and your message will be forwarded straight to his inbox. "
                "You can also connect on [LinkedIn](https://www.linkedin.com/in/brandon-foster) or [GitHub](https://github.com/brandocomando).",
            )

    # 7. Arbitrary Code Generation & Homework Solver Check
    code_gen_resp = detect_code_generation_request(q_raw)
    if code_gen_resp:
        return (IntentType.OFF_TOPIC_GENERAL, code_gen_resp)

    # 8. Off-Topic General Check
    for pat in OFF_TOPIC_GENERAL_PATTERNS:
        if re.search(pat, q_lower):
            if is_query_about_brandon(q_raw):
                return (
                    IntentType.OFF_TOPIC_GENERAL,
                    "I don't know—maybe you should ask Brandon directly! That's outside the scope of Brandon Foster's professional engineering portfolio. "
                    "You can submit your question and email directly through the **[Contact Page](#contact)** and it will be forwarded straight to him.\n\n"
                    "Or feel free to ask about his work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure!",
                )
            return (
                IntentType.OFF_TOPIC_GENERAL,
                "That's not something I'm configured to answer! As Brandon Foster's portfolio assistant, I'm focused specifically on his platform engineering background, architectures, and projects. "
                "For general questions or trivia, you might want to ask **ChatGPT** or **Claude**!\n\n"
                "Feel free to ask about Brandon's work with Kubernetes, Terraform, Confluent Kafka, or AI infrastructure!",
            )

    # Default to Portfolio Search
    return (IntentType.PORTFOLIO_SEARCH, None)
