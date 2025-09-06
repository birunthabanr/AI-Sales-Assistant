import asyncio
import aiohttp
import json
import re

async def test_mcp_tools():
    """Test MCP server using proper SSE connection"""
    print("=== Testing MCP Server Tools ===")
    
    MCP_URL = "http://127.0.0.1:8000/sse"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Open SSE connection
            async with session.get(MCP_URL, headers={'Accept': 'text/event-stream'}) as response:
                if response.status == 200:
                    print("✓ Connected to MCP server via SSE")
                    print("Listening for SSE messages... (Press Ctrl+C to stop)")
                    
                    # Read and parse SSE messages
                    buffer = ""
                    async for line in response.content:
                        try:
                            line = line.decode('utf-8').strip()
                            
                            if not line:
                                continue
                                
                            # Handle SSE data lines
                            if line.startswith('data:'):
                                data_content = line[5:].strip()  # Remove 'data:' prefix
                                
                                # Skip empty data or heartbeat messages
                                if not data_content or data_content == ': heartbeat':
                                    continue
                                    
                                try:
                                    data = json.loads(data_content)
                                    print(f"Received JSON: {json.dumps(data, indent=2)}")
                                except json.JSONDecodeError:
                                    print(f"Received non-JSON data: {data_content}")
                                    
                            # Handle SSE event lines
                            elif line.startswith('event:'):
                                event_type = line[6:].strip()  # Remove 'event:' prefix
                                print(f"Event: {event_type}")
                                
                            # Handle SSE comment lines
                            elif line.startswith(':'):
                                comment = line[1:].strip()  # Remove ':' prefix
                                print(f"Comment: {comment}")
                                
                        except UnicodeDecodeError:
                            print(f"Received binary data (length: {len(line)})")
                        except Exception as e:
                            print(f"Error processing line: {e}")
                            print(f"Problematic line: {line}")
                    
                    return True
                else:
                    print(f"✗ Connection failed: {response.status}")
                    return False
                    
    except asyncio.CancelledError:
        print("\nTest cancelled by user")
        return False
    except Exception as e:
        print(f"✗ Error testing MCP tools: {e}")
        return False

if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_tools())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")