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

