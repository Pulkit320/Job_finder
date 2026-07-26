import re
from bs4 import BeautifulSoup

INDIA_CITIES_AND_TERMS = [
    "india", "bengaluru", "bangalore", "mumbai", "delhi", "gurugram",
    "gurgaon", "hyderabad", "noida", "pune", "chennai", "kolkata",
    "ahmedabad", "kochi", "trivandrum"
]

SENIOR_TITLE_KEYWORDS = [
    "senior", "sr.", "sr ", "staff", "principal", "lead", "head of",
    "director", "vp", "architect", "manager", "manager,", "chief", "5+", "7+", "8+"
]

ENTRY_AND_2027_TITLE_KEYWORDS = [
    "2027", "batch of 2027", "class of 2027", "2027 batch", "2027 graduate",
    "junior", "jr.", "jr ", "entry level", "entry-level", "associate",
    "fresher", "freshers", "graduate", "0-1", "0-2", "1-2", "trainee",
    "intern", "internship", "co-op", "early career"
]

def clean_html(html_content: str) -> str:
    if not html_content:
        return ""
    soup = BeautifulSoup(html_content, "lxml")
    for script_or_style in soup(["script", "style", "header", "footer", "nav"]):
        script_or_style.decompose()
    text = soup.get_text(separator=" ")
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    return " ".join(chunk for chunk in chunks if chunk)

def parse_work_type(title: str, location: str, description: str) -> str:
    combined = f"{title} {location} {description}".lower()
    if "remote" in combined or "work from home" in combined or "wfh" in combined:
        if "hybrid" in combined:
            return "Hybrid"
        return "Remote"
    elif "hybrid" in combined:
        return "Hybrid"
    elif "onsite" in combined or "on-site" in combined or "in-office" in combined or "office" in combined:
        return "Onsite"
    return "Unknown"

def is_india_location(location: str, description: str = "") -> bool:
    if not location:
        return False
    loc_lower = location.lower().strip()
    
    for term in INDIA_CITIES_AND_TERMS:
        if re.search(r"\b" + re.escape(term) + r"\b", loc_lower):
            return True
            
    if re.search(r"(?:,\s*in\b|\bin\s*,|\(in\))", loc_lower):
        return True

    desc_lower = description.lower()[:300] if description else ""
    if "not specified" in loc_lower or not loc_lower:
        if any(re.search(r"\b" + re.escape(t) + r"\b", desc_lower) for t in INDIA_CITIES_AND_TERMS):
            return True

    return False

def is_entry_level(title: str, description: str = "") -> bool:
    title_lower = title.lower().strip()
    desc_lower = description.lower()
    
    # 2027 Graduating Batch & Student roles are ALWAYS accepted
    if any(k in title_lower or k in desc_lower for k in ["2027", "batch of 2027", "class of 2027", "2027 graduate", "2027 batch"]):
        return True

    # Rejection rule: If title contains senior/lead/staff/principal/architect
    if any(skw in title_lower for skw in SENIOR_TITLE_KEYWORDS):
        return False
        
    # Explicit entry level / student / intern tags in title
    if any(ekw in title_lower for ekw in ENTRY_AND_2027_TITLE_KEYWORDS):
        return True
        
    # Rejection rule: 5+ years experience required in description
    if any(req in desc_lower for req in ["5+ years", "6+ years", "7+ years", "8+ years", "5-7 years"]):
        return False
        
    return True

def parse_experience_level(title: str, description: str) -> str:
    combined = f"{title} {description}".lower()
    if "2027" in combined or "batch of 2027" in combined:
        return "2027 Graduating Batch / Student"
    if not is_entry_level(title, description):
        return "Senior Level"
    return "Entry Level"

def parse_salary(text: str) -> str:
    if not text:
        return "Not specified"
    salary_patterns = [
        r"(\$\d{2,3}(?:,\d{3})*(?:\s*-\s*\$\d{2,3}(?:,\d{3})*)?\s*(?:/yr|/year|k|K|per year)?)",
        r"(\d+\s*-\s*\d+\s*(?:LPA|lpa|Lacs|Lakhs))",
        r"(€\d{2,3}(?:,\d{3})*(?:\s*-\s*€\d{2,3}(?:,\d{3})*)?\s*k?)",
        r"(£\d{2,3}(?:,\d{3})*(?:\s*-\s*£\d{2,3}(?:,\d{3})*)?\s*k?)",
        r"(₹\d{1,2}(?:,\d{2,3})*(?:\s*-\s*₹\d{1,2}(?:,\d{2,3})*)?\s*(?:LPA|L|Lacs)?)",
    ]
    for pattern in salary_patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return "Not specified"

def filter_internships(title: str) -> bool:
    title_lower = title.lower()
    is_internship = any(k in title_lower for k in ["intern", "internship", "co-op", "trainee", "2027"])
    
    if not is_internship:
        return True  # Not an internship, keep

    # Keep internships / 2027 student roles if title relates to engineering or AI or tech
    allowed_core_titles = [
        "software engineer", "ai engineer", "prompt engineer", "machine learning",
        "developer", "sde", "data engineer", "frontend", "backend", "full stack", "2027"
    ]
    if any(core in title_lower for core in allowed_core_titles):
        return True
    
    return False
