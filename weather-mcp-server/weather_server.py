from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Weather MCP Server")

@mcp.tool()
def hell_weather(name: str = "World") -> str:
    """シンプルな挨拶を返すツール"""
    return f"Hello, {name}! Welcome to Weather MCP Server!"

@mcp.tool()
def server_info() -> dict:
    """サーバ情報を返すツール"""
    return {
        "name": "Weather MCP Server",
        "version": "1.0.0",
        "description": "天気予報情報を提供するMCPサーバ（開発中）"
    }

if __name__ == "__main__":
    print("Starting MCP Server...")
    mcp.run(transport="streamable-http")