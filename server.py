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