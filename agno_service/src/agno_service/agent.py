import os

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

CLICKHOUSE_MCP_ENV = {
    "CLICKHOUSE_HOST": os.environ.get("CLICKHOUSE_HOST", "clickhouse.clickhouse.svc.cluster.local"),
    "CLICKHOUSE_PORT": os.environ.get("CLICKHOUSE_PORT", "8123"),
    "CLICKHOUSE_USER": os.environ.get("CLICKHOUSE_USER", "default"),
    "CLICKHOUSE_PASSWORD": os.environ.get("CLICKHOUSE_PASSWORD", ""),
    "CLICKHOUSE_SECURE": os.environ.get("CLICKHOUSE_SECURE", "false"),
}

INSTRUCTIONS = (
    "You answer natural-language questions about NYC taxi trip data "
    "(table nyc_taxi.trips_small) by querying ClickHouse through the "
    "available MCP tools. Only run read-only SELECT queries; never run "
    "DDL or DML statements. Answer in plain text, no markdown tables."
)


async def build_agent() -> Agent:
    mcp_tools = MCPTools(
        command="uv run --frozen --package agno-service mcp-clickhouse",
        env=CLICKHOUSE_MCP_ENV,
    )
    await mcp_tools.connect()
    return Agent(
        model=Claude(id="claude-sonnet-5"),
        tools=[mcp_tools],
        instructions=INSTRUCTIONS,
        markdown=False,
    )
