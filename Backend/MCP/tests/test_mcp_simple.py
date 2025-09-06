import asyncio
import aiohttp

async def test_mcp_simple():
    """Simple test to verify MCP server is running"""
    print("=== Testing MCP Server Connection ===")
    
    MCP_URL = "http://127.0.0.1:8000/sse"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(MCP_URL, headers={'Accept': 'text/event-stream'}) as response:
                if response.status == 200:
                    print("✓ MCP Server is running and accessible")
                    print("✓ SSE endpoint is responding")
                    print("\nThe server is ready for MCP client connections")
                    print("Use a proper MCP client (like FastMCPClient) for full testing")
                    return True
                else:
                    print(f"✗ Server returned status: {response.status}")
                    return False
    except Exception as e:
        print(f"✗ Cannot connect to MCP Server: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mcp_simple())