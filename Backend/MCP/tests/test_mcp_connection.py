import asyncio
import aiohttp
import json

async def test_mcp_connection():
    """Test if MCP server is running and responding"""
    try:
        # First, let's find what port your MCP server is running on
        # Since you're using port=0, it chooses a random port
        # We'll need to check the output or modify the server to use a fixed port
        
        # For testing, let's assume it's running on port 8000 (common default)
        # You'll need to change this to match your actual port
        MCP_URL = "http://127.0.0.1:8000/sse"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(MCP_URL) as response:
                if response.status == 200:
                    print("✓ MCP Server is running and responding")
                    return True
                else:
                    print(f"✗ MCP Server returned status: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"✗ Cannot connect to MCP Server: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mcp_connection())