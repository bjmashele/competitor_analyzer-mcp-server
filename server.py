import re
import threading
import time
from collections import Counter
import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP
import logging


logging.basicConfig(
     format="{asctime} - {levelname} - {message}",
     style="{",
     datefmt="%Y-%m-%d %H:%M",
 )

# Create an MCP server
mcp = FastMCP(
    "competitor_analysis",
    host="127.0.0.1",
    port=8000
)

@mcp.tool()
def validate_company(company_name: str) -> str:
    """
    Validate if the input company name corresponds to a real company using web search.
    Args:
        company_name (str): The name of the company to validate.
    Returns:
        str: Validation result with evidence from search results.
    """
    logging.info(f"[INSIDE TOOL]: validate_company - searching for '{company_name}'")

    try:
        # Perform web search for the company
        search_query = f"{company_name} company business official site"
        results = web_search_tool(search_query)

        # Analyze search results for company evidence
        if is_company_valid_based_on_search(results, company_name):
            return f"[ VALID COMPANY ]: {company_name} (verified via web search)"
        else:
            return f"[NOT valid company]: No substantial evidence found for '{company_name}'"

    except Exception as e:
        logging.error(f"Validation failed: {str(e)}")
        return f"Validation failed: {str(e)}"

def is_company_valid_based_on_search(search_results: str, company_name: str) -> bool:
    """Analyze search results to determine if company is valid"""

    # Convert to lowercase for case-insensitive matching
    results_lower = search_results.lower()
    company_lower = company_name.lower()

    # Evidence indicators
    evidence_count = 0

    # Check for official website patterns
    if f"{company_lower}.com" in results_lower:
        evidence_count += 1
        logging.info(f"Found official domain: {company_lower}.com")

    # Check for "official site" mentions
    if "official site" in results_lower or "official website" in results_lower:
        evidence_count += 1
        logging.info("Found official site mention")

    # Check for company description patterns
    if "company" in results_lower and company_lower in results_lower:
        evidence_count += 1
        logging.info("Found company description")

    # Check for business-related terms
    business_terms = ["corporation", "inc", "ltd", "llc", "business", "enterprise"]
    if any(term in results_lower for term in business_terms):
        evidence_count += 1
        logging.info("Found business terminology")

    # Check for news or Wikipedia mentions
    if "wikipedia" in results_lower or "news" in results_lower:
        evidence_count += 1
        logging.info("Found Wikipedia or news mentions")

    logging.info(f"Total evidence points: {evidence_count}")
    return evidence_count >= 2 

## **************************************************************************** ##

@mcp.tool()
def identify_sector(company_name: str) -> str:
    """
    Determine industry sector using multiple search strategies.
    Args:
        company_name (str): The name of the company.
    Returns:
        str: The sector with confidence indicator.
    """
    print(f"[INSIDE TOOL]: identify_sector - comprehensive analysis for '{company_name}'")

    try:
        all_sectors = []

        # Strategy 1: General company description search
        results1 = web_search_tool(f"what does {company_name} do business industry")
        sectors1 = extract_sectors_advanced(results1, company_name)
        all_sectors.extend(sectors1)

        time.sleep(1)  # Rate limit respect

        # Strategy 2: Wikipedia/LinkedIn style search
        results2 = web_search_tool(f"{company_name} wikipedia linkedin industry type")
        sectors2 = extract_sectors_advanced(results2, company_name)
        all_sectors.extend(sectors2)

        time.sleep(1)

        # Strategy 3: News and financial context
        results3 = web_search_tool(f"{company_name} news financial reports sector")
        sectors3 = extract_sectors_advanced(results3, company_name)
        all_sectors.extend(sectors3)

        # Determine final sector
        final_sector = determine_primary_sector(all_sectors)

        return final_sector if final_sector else "Unknown sector"

    except Exception as e:
        return f"Error identifying sector: {str(e)}"

def extract_sectors_advanced(search_results: str, company_name: str) -> list:
    """Advanced sector extraction with context analysis"""

    results_lower = search_results.lower()
    company_lower = company_name.lower()

    # Extended sector definitions with weighted keywords
    sector_patterns = {
        "Technology": {
            "keywords": ["technology", "software", "hardware", "saas", "cloud", "ai", "artificial intelligence"],
            "weight": 1.0
        },
        "Finance": {
            "keywords": ["financial", "banking", "investment", "fintech", "insurance", "bank"],
            "weight": 1.0
        },
        "Healthcare": {
            "keywords": ["healthcare", "medical", "pharmaceutical", "biotech", "hospital", "health"],
            "weight": 1.0
        },
        "Education": {
            "keywords": ["education", "edtech", "e-learning", "online learning", "educational"],
            "weight": 1.0
        },
        "Retail": {
            "keywords": ["retail", "e-commerce", "online shopping", "marketplace" ],
            "weight": 1.0
        },
        "Manufacturing": {
            "keywords": ["manufacturing", "industrial", "automotive", "electronics", "factory"],
            "weight": 1.0
        },
        "Energy": {
            "keywords": ["energy", "renewable", "oil and gas", "solar" ],
            "weight": 1.0
        }
    }

    found_sectors = []

    # Check for explicit sector mentions
    for sector, pattern in sector_patterns.items():
        for keyword in pattern["keywords"]:
            if keyword in results_lower:
                # Check if this appears to be in context of the company
                if (company_lower in results_lower or
                    any(phrase in results_lower for phrase in [f"is a {keyword}", f"in the {keyword}"])):
                    found_sectors.extend([sector] * int(pattern["weight"] * 2))
                else:
                    found_sectors.extend([sector] * int(pattern["weight"]))

    return found_sectors

def determine_primary_sector(sectors_list: list) -> str:
    """Determine primary sector from list of found sectors"""
    if not sectors_list:
        return ""

    sector_counts = Counter(sectors_list)
    most_common = sector_counts.most_common(1)[0]

    # Only return if we have reasonable confidence
    if most_common[1] >= 2:  # At least 2 mentions
        return most_common[0]
    elif len(sector_counts) == 1 and most_common[1] >= 1:
        return most_common[0]

    return ""


## **************************************************************************** ##

@mcp.tool()
def identify_competitors(sector: str, company_name: str) -> str:
    """
    Identify top 3 competitors using comprehensive web search analysis.
    Args:
        sector (str): The industry sector.
        company_name (str): The name of the company to exclude.
    Returns:
        str: Comma-separated list of top 3 competitors.
    """
    print(f"[INSIDE TOOL]: identify_competitors - analyzing '{sector}' sector excluding '{company_name}'")

    try:
        competitor_candidates = []

        # Query 1: General sector competitors
        results1 = web_search_tool(f"top {sector} companies competitors market share")
        candidates1 = extract_competitors_advanced(results1, company_name, sector)
        competitor_candidates.extend(candidates1)

        time.sleep(1)  # Rate limiting

        # Query 2: Direct competitors of the company
        results2 = web_search_tool(f"who are {company_name} main competitors in {sector}")
        candidates2 = extract_competitors_advanced(results2, company_name, sector)
        competitor_candidates.extend(candidates2)

        time.sleep(1)

        # Query 3: Industry analysis
        results3 = web_search_tool(f"{sector} industry key players leading companies")
        candidates3 = extract_competitors_advanced(results3, company_name, sector)
        competitor_candidates.extend(candidates3)

        # Filter and rank competitors
        final_competitors = rank_competitors(competitor_candidates, company_name)

        if final_competitors:
            top_3 = final_competitors[:3]
            return ", ".join(top_3)
        else:
            return "No competitors identified"

    except Exception as e:
        return f"Error identifying competitors: {str(e)}"

def extract_competitors_advanced(search_results: str, exclude_company: str, sector: str) -> list:
    """Advanced competitor extraction with context awareness"""

    exclude_lower = exclude_company.lower()
    sector_lower = sector.lower()
    results_lower = search_results.lower()

    competitors = []

    # Known company patterns in different sectors
    sector_companies = {
        "technology": ["microsoft", "apple", "amazon", "meta", "google", "ibm", "oracle", "intel"],
        "finance": ["jpmorgan", "bank of america", "goldman sachs", "morgan stanley", "citi", "wells fargo"],
        "healthcare": ["johnson & johnson", "pfizer", "merck", "novartis", "roche", "abbvie"],
        "education": ["great learning", "coursera", "udemy", "edx", "khan academy", "byju's", "pluralsight"],
        "retail": ["walmart", "target", "amazon", "home depot", "costco", "best buy"],
        "automotive": ["toyota", "ford", "general motors", "honda", "bmw", "mercedes-benz"]
    }

    # Look for known companies in this sector
    if sector_lower in sector_companies:
        for company in sector_companies[sector_lower]:
            if (company in results_lower and
                company != exclude_lower and
                company not in competitors):
                competitors.append(company.title())

    # Extract from list patterns
    list_patterns = [
        r'(?:competitors|companies|players):? ([^\.]+)',
        r'(?:including|such as) ([^\.]+)',
        r'top \d+ ([^:]+) companies',
    ]

    for pattern in list_patterns:
        matches = re.findall(pattern, search_results, re.IGNORECASE)
        for match in matches:
            # Split and clean potential company names
            potential_companies = re.split(r',|\band\b|\bor\b|;', match)
            for comp in potential_companies:
                comp = comp.strip()
                if (is_likely_company_name(comp) and
                    comp.lower() != exclude_lower and
                    comp not in competitors):
                    competitors.append(comp)

    # Extract from numbered/bulleted lists
    numbered_pattern = r'\b\d+\.\s*([A-Z][a-zA-Z\s&]+?)(?=\.|\n|$)'
    matches = re.findall(numbered_pattern, search_results)
    for match in matches:
        comp = match.strip()
        if (is_likely_company_name(comp) and
            comp.lower() != exclude_lower and
            comp not in competitors):
            competitors.append(comp)

    return competitors

def is_likely_company_name(text: str) -> bool:
    """Check if text looks like a company name"""
    if not text or len(text) < 2:
        return False

    # Exclude common non-company words
    non_company_words = {
        'the', 'and', 'or', 'but', 'with', 'for', 'from', 'that', 'this',
        'these', 'those', 'their', 'other', 'some', 'such', 'including',
        'etc', 'etc.', 'among', 'various', 'several', 'many'
    }

    words = text.lower().split()
    if any(word in non_company_words for word in words):
        return False

    # Should start with capital letter and have reasonable length
    return (text[0].isupper() and
            len(text) <= 50 and
            any(c.isalpha() for c in text))

def rank_competitors(competitor_candidates: list, exclude_company: str) -> list:
    """Rank competitors by frequency and relevance"""
    if not competitor_candidates:
        return []

    exclude_lower = exclude_company.lower()

    # Filter out the excluded company and clean the list
    filtered_competitors = [
        comp for comp in competitor_candidates
        if comp.lower() != exclude_lower and comp.strip()
    ]

    if not filtered_competitors:
        return []

    # Count occurrences and return most frequent
    competitor_counts = Counter(filtered_competitors)
    return [comp for comp, count in competitor_counts.most_common()] 

## **************************************************************************** ##

@mcp.tool()
def browse_page(url: str, instructions: str) -> str:
    """
    Browse a webpage and extract information based on instructions using web scraping.
    Args:
        url (str): The URL to browse.
        instructions (str): Instructions for what information to extract.
    Returns:
        str: Extracted information or error message.
    """
    print(f"[INSIDE TOOL]: browse_page - scraping {url} for '{instructions}'")

    try:
        # Validate and prepare URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Fetch webpage content
        content = fetch_webpage_content(url)
        if not content:
            return f"Failed to fetch content from {url}"

        # Extract relevant text based on instructions
        extracted_text = extract_relevant_content(content, instructions)

        return extracted_text if extracted_text else "No relevant content found based on the instructions"

    except Exception as e:
        return f"Error browsing page: {str(e)}"

def fetch_webpage_content(url: str) -> str:
    """Fetch webpage content with proper headers"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse HTML and extract main text content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()

        # Get text from main content areas
        main_content = soup.find_all(['main', 'article', 'div', 'p'])
        text_parts = []

        for element in main_content:
            text = element.get_text(strip=True)
            if text and len(text) > 20:  # Only include substantial text
                text_parts.append(text)

        return ' '.join(text_parts[:5000])  # Limit length

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_relevant_content(content: str, instructions: str) -> str:
    """Extract content relevant to the instructions"""
    content_lower = content.lower()
    instructions_lower = instructions.lower()

    # Split content into sentences for better matching
    sentences = [s.strip() for s in content.split('.') if s.strip()]

    relevant_sentences = []

    # Simple keyword matching based on instructions
    for sentence in sentences:
        sentence_lower = sentence.lower()

        # Check if sentence contains words from instructions
        instruction_words = set(instructions_lower.split())
        sentence_words = set(sentence_lower.split())

        # Count matching words
        matching_words = instruction_words.intersection(sentence_words)

        # If substantial match, include the sentence
        if len(matching_words) >= 1 and len(sentence) > 10:
            relevant_sentences.append(sentence)

    # If no specific matches found, return first few sentences as summary
    if not relevant_sentences and sentences:
        return '. '.join(sentences[:5]) + '...'

    return '. '.join(relevant_sentences[:10])  # Limit to top 10 relevant sentences 


@mcp.tool()
def generate_report(company_name: str, context: str) -> str:
    """
    Generate a competitive analysis report with a comparison table and actionable insights for the input company.
    Args:
        company_name: The name of the company to analyze.
        context: Retrieved context from tools.
    Returns:
        str: Formatted report.
    """
    print("[INSIDE TOOL]: generate_report")

    # Parse competitors from context instead of using static placeholders
    competitors = extract_competitors_from_context(context)

    # Build dynamic competitor rows
    competitor_rows = ""
    for i, competitor in enumerate(competitors[:3]):  # Top 3 competitors
        competitor_rows += f"| {competitor} | - | - | - | - |\n"

    # If no competitors found, use placeholders but indicate this
    if not competitor_rows:
        competitor_rows = "| Competitor A | - | - | - | - |\n| Competitor B | - | - | - | - |\n| Competitor C | - | - | - | - |"

    # Simple template-based report (NO LLM calls) with dynamic data
    report_template = f"""
# Competitive Analysis Report: {company_name}

## Executive Summary
Analysis of {company_name}'s competitive position based on available market data.

## Competitor Comparison

| Competitor | Strategy Type | Key Tactics | Strengths | Weaknesses |
|------------|---------------|-------------|-----------|------------|
{competitor_rows}

## Actionable Insights for {company_name}
- Develop differentiated positioning in the market
- Focus on unique value propositions
- Optimize operational efficiencies
- Enhance customer engagement strategies

*Report generated from context data. Fill in specific details based on comprehensive market research.*
"""

    return report_template.strip()

def extract_competitors_from_context(context: str) -> list:
    """Extract competitor names from context string"""
    competitors = []

    # Look for comma-separated competitor lists
    if ", " in context:
        potential_competitors = context.split(", ")
        for comp in potential_competitors:
            if comp and len(comp) > 2 and comp[0].isupper():
                competitors.append(comp)

    # Look for known competitor patterns
    import re
    competitor_patterns = [
        r'competitors?[:\s]+([^\.\n]+)',
        r'top.*companies?[:\s]+([^\.\n]+)',
    ]

    for pattern in competitor_patterns:
        matches = re.findall(pattern, context, re.IGNORECASE)
        for match in matches:
            # Split by common separators
            found_comps = re.split(r',|\band\b', match)
            competitors.extend([comp.strip() for comp in found_comps if comp.strip()])

    return list(set(competitors))[:5]  # Remove duplicates and limit