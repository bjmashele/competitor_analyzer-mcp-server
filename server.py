import re
import threading
import time
from collections import Counter
import requests
from bs4 import BeautifulSoup
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP(
    "demo",
    host="127.0.0.1",
    port=8000
)

