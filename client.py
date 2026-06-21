import os
from dotenv import load_dotenv
from smolagents import (
    OpenAIServerModel,
    MCPClient,
    CodeAgent,
    DuckDuckGoSearchTool,
    ToolCallingAgent,
    tool,
    PromptTemplates,
    PlanningPromptTemplate,
    ManagedAgentPromptTemplate,
    FinalAnswerPromptTemplate,
)

# Load environment variables from the .env file (if present)
load_dotenv()

# Access environment variables as if they came from the actual environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# LLM Setup - Using the "gpt-4o-mini" model as LLM
model = OpenAIServerModel(model_id="gpt-4o-mini")

system_prompt = (
    """
    You are an expert Competitive Analysis Agent. Given a single company name, perform the following tasks:
    - Validate that it is a real company using available validation tools or web search.
    - Determine its primary industry sector using sector identification tools or web search.
    - Identify its top three competitors (excluding the company itself) using competitor discovery tools or web search.
    - Gather real-time strategy data—such as pricing, marketing, product offerings, recent quarterly earnings reports, press releases, and authentic news articles—accessible on websites using browsing or search tools.
    Analyze the collected data to compare strategies and generate a formatted report with actionable insights to help the input company outperform its competitors. Focus exclusively on the provided company and its top three competitors; do not expand to additional entities.
    """
)

planning_prompts = PlanningPromptTemplate(
    initial_facts=(
        """
        Key facts about the input company and its top three competitors from initial research:
        {facts}
        """
    ),
    initial_plan=(
        """
        Step-by-step plan:
        1. Validate the single input company name.
        2. Determine the sector for the input company.
        3. Identify the top 3 competitors for the input company.
        4. Gather strategy data on the input company and its top 3 competitors.
        5. Analyze strategies and generate a comparison table.
        6. Propose actionable insights for the input company.
        """
    ),
    update_facts_pre_messages="Reassess facts with new information, focusing on the input company and its competitors:",
    update_facts_post_messages="Updated facts considered for the single-company analysis.",
    update_plan_pre_messages="Revise the analysis plan based on new data, maintaining focus on one company:",
    update_plan_post_messages="Analysis plan revised for targeted competitive insights."
)

managed_agent_prompts = ManagedAgentPromptTemplate(
    task="""
    Your task is to analyze the strategies of the top 3 competitors relative to the single input company {task_description} and
    produce a comparison table with actionable insights tailored to helping {task_description} outperform them.
    """,
    report="Generate a detailed, focused report based on the task results for {task_description}: {results}"
)

final_answer_prompts = FinalAnswerPromptTemplate(
    pre_messages="""
    Based on the analysis of the input company and its top three competitors,
    prepare a beautifully formatted report with a comparison table and actionable insights to drive competitive advantage.
    """,
    post_messages="Ensure the response is clear, concise, professionally presented, and centered on the single input company.",
    final_answer_template=(
        """
        Provide a Markdown report for the input company with sections:
        Executive Summary (overview of competitive position),
        Comparison Table (strategies across the input company and top 3 competitors),
        Actionable Insights (specific recommendations to outperform competitors).
        """
    )
)

prompt_templates = PromptTemplates(
    system_prompt=system_prompt,
    planning=planning_prompts,
    managed_agent=managed_agent_prompts,
    final_answer=final_answer_prompts
)


# Initialize search tool 
web_search_tool = DuckDuckGoSearchTool(max_results=5, rate_limit=2.0)