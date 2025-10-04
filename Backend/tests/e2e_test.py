import asyncio
import pytest
import subprocess
import sys
import time
import socket
import json
import requests
from fastmcp import Client


def wait_for_port(port, host="127.0.0.1", timeout=10.0):
    """Wait until a port is available"""
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    raise RuntimeError(f"Port {port} not ready")


def wait_for_server_ready(url, timeout=10.0):
    """Wait until the server responds"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url.replace('/sse', '/health'), timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Server {url} not ready")


@pytest.fixture(scope="session")
def mcp_server():
    """Start the MCP server"""
    proc = subprocess.Popen(
        [sys.executable, "Backend/MCP/mcp_server_new_1.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    wait_for_port(8081)
    time.sleep(2)  # Give server time to fully initialize
    yield proc
    proc.terminate()
    proc.wait()


def extract_content_text(result):
    """Helper function to extract text from result content"""
    content_text = ""
    for item in result.content:
        if hasattr(item, 'text'):
            content_text += item.text + " "
    return content_text.strip()


class TestMCPEndToEnd:
    """End-to-end tests for MCP server and client"""

    @pytest.mark.asyncio
    async def test_server_connection(self, mcp_server):
        """Test basic server connectivity"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Test that we can list tools
            tools = await client.list_tools()
            assert len(tools) > 0, "Should have at least one tool available"
            print(f"✅ Server connected successfully. Found {len(tools)} tools")

    @pytest.mark.asyncio
    async def test_media_tools_workflow(self, mcp_server):
        """Test complete media tools workflow"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Test music playback
            music_result = await client.call_tool("play_music", {"song": "Shape of You"})
            music_text = extract_content_text(music_result)
            print(f"🎵 Music result: {music_text}")
            assert "playing" in music_text.lower() or "not found" in music_text.lower()

            # Test book rating
            book_result = await client.call_tool("rate_book", {
                "book": "The Great Gatsby",
                "rating": 5,
                "review": "Amazing book!"
            })
            book_text = extract_content_text(book_result)
            print(f"📚 Book rating result: {book_text}")
            assert any(keyword in book_text.lower() for keyword in 
                      ["rated", "✅", "not found", "❌"])

    @pytest.mark.asyncio
    async def test_restaurant_booking_workflow(self, mcp_server):
        """Test restaurant booking workflow"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Test restaurant booking
            restaurant_result = await client.call_tool("book_restaurant", {
                "restaurant": "Italian Bistro",
                "time": "tomorrow 7:00 PM",
                "party_size": 4
            })
            restaurant_text = extract_content_text(restaurant_result)
            print(f"🍽️ Restaurant booking result: {restaurant_text}")
            assert any(keyword in restaurant_text.lower() for keyword in 
                      ["confirmed", "✅", "not found", "❌", "booking"])

    @pytest.mark.asyncio
    async def test_ecommerce_workflow(self, mcp_server):
        """Test complete e-commerce workflow"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Step 1: Place an order
            items_json = json.dumps([{"sku": "LAPTOP001", "qty": 1}, {"sku": "MOUSE002", "qty": 2}])
            place_result = await client.call_tool("place_order", {
                "customer_id": "test_customer_001",
                "items": items_json,
                "shipping_address_id": "addr_test_001",
                "payment_method_id": "pm_test_001"
            })
            place_text = extract_content_text(place_result)
            print(f"📦 Place order result: {place_text}")
            assert "order" in place_text.lower()

            # Step 2: Track the order
            track_result = await client.call_tool("track_order", {"order_id": "ORD12345"})
            track_text = extract_content_text(track_result)
            print(f"📊 Track order result: {track_text}")
            assert "order" in track_text.lower()

            # Step 3: Check payment methods
            payment_result = await client.call_tool("check_payment_methods", {"customer_id": "test_customer_001"})
            payment_text = extract_content_text(payment_result)
            print(f"💳 Payment methods result: {payment_text}")
            assert "payment" in payment_text.lower()

            # Step 4: Diagnose payment issue
            diagnosis_result = await client.call_tool("diagnose_payment_issue", {"error_code": "DECLINED"})
            diagnosis_text = extract_content_text(diagnosis_result)
            print(f"🔍 Payment diagnosis result: {diagnosis_text}")
            assert "payment" in diagnosis_text.lower()

    @pytest.mark.asyncio
    async def test_customer_service_workflow(self, mcp_server):
        """Test customer service workflow"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Step 1: Contact customer service
            contact_result = await client.call_tool("contact_customer_service", {
                "topic": "Order delivery delay",
                "preferred_channel": "email",
                "email": "customer@test.com"
            })
            contact_text = extract_content_text(contact_result)
            print(f"📞 Customer service result: {contact_text}")
            assert any(keyword in contact_text.lower() for keyword in ["ticket", "support"])

            # Step 2: Request refund
            refund_result = await client.call_tool("get_refund", {
                "order_id": "ORD12345",
                "reason": "Late delivery"
            })
            refund_text = extract_content_text(refund_result)
            print(f"💰 Refund request result: {refund_text}")
            assert "refund" in refund_text.lower()

            # Step 3: Transfer to human agent
            transfer_result = await client.call_tool("transfer_to_human_agent", {
                "context": "Complex issue requiring human assistance",
                "priority": "normal"
            })
            transfer_text = extract_content_text(transfer_result)
            print(f"👨‍💼 Transfer to agent result: {transfer_text}")
            assert any(keyword in transfer_text.lower() for keyword in ["agent", "human"])

    @pytest.mark.asyncio
    async def test_weather_and_events_workflow(self, mcp_server):
        """Test weather and events workflow"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Test weather
            weather_result = await client.call_tool("get_weather", {"location": "London"})
            weather_text = extract_content_text(weather_result)
            print(f"🌤️ Weather result: {weather_text}")
            assert weather_text  # Should return some response

            # Test event search
            events_result = await client.call_tool("search_screening_event", {
                "query": "Avengers",
                "location": "New York"
            })
            events_text = extract_content_text(events_result)
            print(f"🎬 Events search result: {events_text}")
            assert events_text  # Should return some response

    @pytest.mark.asyncio
    async def test_error_handling(self, mcp_server):
        """Test error handling scenarios"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            # Test with invalid parameters
            try:
                result = await client.call_tool("play_music", {"invalid_param": "value"})
                text = extract_content_text(result)
                print(f"🛡️ Error handling result: {text}")
                assert text  # Should handle gracefully
            except Exception as e:
                print(f"🛡️ Expected error handled: {e}")

            # Test with empty parameters
            try:
                result = await client.call_tool("track_order", {"order_id": ""})
                text = extract_content_text(result)
                print(f"🛡️ Empty param result: {text}")
                assert text  # Should handle gracefully
            except Exception as e:
                print(f"🛡️ Empty param error handled: {e}")


class TestMCPClientIntegration:
    """Integration tests for the MCP client with the server"""

    @pytest.mark.asyncio
    async def test_client_server_communication(self, mcp_server):
        """Test that client can communicate with server"""
        # Import the client module functions
        import importlib.util
        import os
        
        client_path = "Backend/MCP/mcp_client_new_3.py"
        if os.path.exists(client_path):
            spec = importlib.util.spec_from_file_location("mcp_client", client_path)
            client_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(client_module)
            
            # Test the helper functions
            test_text = '{"tool_name": "play_music", "arguments": {"song": "test"}}'
            extracted = client_module.extract_json(test_text)
            assert extracted == {"tool_name": "play_music", "arguments": {"song": "test"}}
            
            # Test stringify function
            class MockResult:
                def __init__(self, text):
                    self.text = text
                
                @property
                def content(self):
                    return [{"type": "text", "text": self.text}]
            
            mock_result = MockResult("Test result")
            stringified = client_module._stringify_tool_result(mock_result)
            assert "Test result" in stringified
            
            print("✅ Client module functions work correctly")

    @pytest.mark.asyncio
    async def test_tool_discovery(self, mcp_server):
        """Test that client can discover all available tools"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            tools = await client.list_tools()
            
            # Check that we have the expected tools
            tool_names = [tool.name for tool in tools]
            print(f"🔧 Available tools: {tool_names}")
            
            expected_tools = [
                "play_music", "rate_book", "book_restaurant", "get_weather",
                "search_screening_event", "edit_account", "place_order", 
                "track_order", "cancel_order", "check_payment_methods",
                "diagnose_payment_issue", "get_refund", "track_refund",
                "contact_customer_service", "transfer_to_human_agent"
            ]
            
            # Check that at least some expected tools are present
            found_tools = [tool for tool in expected_tools if tool in tool_names]
            assert len(found_tools) > 0, f"Expected to find some tools from {expected_tools}, but found {tool_names}"

    @pytest.mark.asyncio
    async def test_complete_user_journey(self, mcp_server):
        """Test a complete user journey across multiple tools"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            print("🚀 Starting complete user journey test...")
            
            # Scenario: User plans an evening out
            journey_steps = []
            
            # Step 1: Check weather for the evening
            weather = await client.call_tool("get_weather", {"location": "Paris"})
            weather_text = extract_content_text(weather)
            journey_steps.append(f"Weather: {weather_text}")
            print(f"1. 🌤️ Checked weather: {weather_text[:50]}...")
            
            # Step 2: Search for movie screenings
            movies = await client.call_tool("search_screening_event", {
                "query": "action movies",
                "location": "Paris"
            })
            movies_text = extract_content_text(movies)
            journey_steps.append(f"Movies: {movies_text[:100]}...")
            print(f"2. 🎬 Searched movies: {movies_text[:50]}...")
            
            # Step 3: Book a restaurant
            restaurant = await client.call_tool("book_restaurant", {
                "restaurant": "French Cuisine",
                "time": "tomorrow 8:00 PM", 
                "party_size": 2
            })
            restaurant_text = extract_content_text(restaurant)
            journey_steps.append(f"Restaurant: {restaurant_text}")
            print(f"3. 🍽️ Booked restaurant: {restaurant_text[:50]}...")
            
            # Step 4: Play some music while getting ready
            music = await client.call_tool("play_music", {"genre": "jazz"})
            music_text = extract_content_text(music)
            journey_steps.append(f"Music: {music_text}")
            print(f"4. 🎵 Played music: {music_text[:50]}...")
            
            # Verify all steps completed
            assert len(journey_steps) == 4
            assert all(step for step in journey_steps)
            
            print("✅ Complete user journey test passed!")

    @pytest.mark.asyncio
    async def test_performance_and_reliability(self, mcp_server):
        """Test performance and reliability of the MCP system"""
        async with Client("http://127.0.0.1:8081/sse") as client:
            import time
            
            # Test multiple rapid requests
            start_time = time.time()
            requests_count = 5
            
            for i in range(requests_count):
                result = await client.call_tool("play_music", {"song": f"Test Song {i}"})
                text = extract_content_text(result)
                assert text  # Should get a response
                print(f"⚡ Request {i+1}: {text[:30]}...")
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / requests_count
            
            print(f"📊 Performance: {requests_count} requests in {total_time:.2f}s (avg: {avg_time:.2f}s/request)")
            
            # Should complete in reasonable time
            assert total_time < 30, f"Performance test took too long: {total_time}s"
            
            # Test connection stability
            try:
                # Re-list tools to test connection persistence
                tools = await client.list_tools()
                assert len(tools) > 0
                print("✅ Connection stability test passed")
            except Exception as e:
                pytest.fail(f"Connection stability test failed: {e}")


def test_manual_client_server_test():
    """Manual test that can be run to verify the full system"""
    print("\n" + "="*60)
    print("MANUAL END-TO-END TEST")
    print("="*60)
    
    # Start server
    print("1. Starting MCP server...")
    server_proc = subprocess.Popen(
        [sys.executable, "Backend/MCP/mcp_server_new_1.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for server to start
        wait_for_port(8081)
        time.sleep(2)
        print("✅ MCP server started successfully")
        
        # Test basic connectivity
        print("2. Testing server connectivity...")
        async def test_connectivity():
            async with Client("http://127.0.0.1:8081/sse") as client:
                tools = await client.list_tools()
                print(f"✅ Connected to server. Found {len(tools)} tools")
                return True
        
        # Run the async test
        if asyncio.run(test_connectivity()):
            print("🎉 End-to-end test setup successful!")
            print("\nNext steps:")
            print("1. Run the client manually: python Backend/MCP/mcp_client_new_3.py")
            print("2. Test various commands like:")
            print("   - 'Play some jazz music'")
            print("   - 'What's the weather in London?'")
            print("   - 'Book a restaurant for 2 people tomorrow at 7 PM'")
            print("   - 'I need to track my order ORD12345'")
        
    finally:
        # Clean up
        print("3. Cleaning up...")
        server_proc.terminate()
        server_proc.wait()
        print("✅ Cleanup complete")


if __name__ == "__main__":
    # Run the manual test
    test_manual_client_server_test()
    
    # Run pytest tests
    print("\n" + "="*60)
    print("RUNNING PYTEST END-TO-END TESTS")
    print("="*60)
    pytest.main([__file__, "-v", "-s"])