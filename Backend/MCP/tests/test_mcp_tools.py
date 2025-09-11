import asyncio
import aiohttp
import json

async def test_mcp_tools():
    """Test MCP server tool discovery"""
    try:
        MCP_URL = "http://127.0.0.1:8000/sse"
        
        async with aiohttp.ClientSession() as session:
            # Send initialization message
            init_msg = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {}
                }
            }
            
            async with session.post(MCP_URL, json=init_msg) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✓ MCP Server initialized successfully")
                    print(f"Server capabilities: {json.dumps(data.get('result', {}), indent=2)}")
                    return True
                else:
                    print(f"✗ Initialization failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"✗ Error testing MCP tools: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_mcp_tools())