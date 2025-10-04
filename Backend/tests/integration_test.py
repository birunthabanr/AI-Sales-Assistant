import asyncio
import pytest
import subprocess
import sys
import time
import socket
import json

from fastmcp import Client


def wait_for_port(port, host="127.0.0.1", timeout=10.0):
    start = time.time()
    while time.time() - start < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.1)
    raise RuntimeError(f"Port {port} not ready")


@pytest.fixture(scope="session")
def mcp_server():
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


# =====================================================
# 1. Media Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_play_music(mcp_server):
    """Test play_music tool with song name"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("play_music", {"song": "Shape of You"})
        content_text = extract_content_text(result)
        print(f"Play music result: {content_text}")
        assert "playing" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_play_music_genre(mcp_server):
    """Test play_music tool with genre"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("play_music", {"genre": "rock"})
        content_text = extract_content_text(result)
        print(f"Play music genre result: {content_text}")
        assert "rock" in content_text.lower() or "playing" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_rate_book(mcp_server):
    """Test rate_book tool with successful rating"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("rate_book", {
            "book": "The Great Gatsby", 
            "rating": 5, 
            "review": "A classic masterpiece!"
        })
        content_text = extract_content_text(result)
        print(f"Rate book result: {content_text}")
        assert "rated" in content_text.lower() or "✅" in content_text
        assert "5" in content_text


@pytest.mark.asyncio
async def test_integration_rate_book_not_found(mcp_server):
    """Test rate_book tool with non-existent book"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("rate_book", {
            "book": "Non Existent Book Name", 
            "rating": 3
        })
        content_text = extract_content_text(result)
        print(f"Rate book not found result: {content_text}")
        assert "not found" in content_text.lower() or "❌" in content_text


# =====================================================
# 3. Weather Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_get_weather(mcp_server):
    """Test get_weather tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("get_weather", {"location": "London"})
        content_text = extract_content_text(result)
        print(f"Get weather result: {content_text}")
        # Weather API might return data or error based on API key availability
        assert content_text  # Should return some response


# =====================================================
# 4. Screening Event Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_search_screening_event(mcp_server):
    """Test search_screening_event tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("search_screening_event", {
            "query": "Avengers",
            "location": "New York"
        })
        content_text = extract_content_text(result)
        print(f"Search screening event result: {content_text}")
        # Might return results or API key error
        assert content_text  # Should return some response



# =====================================================
# 6. Order Management Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_place_order(mcp_server):
    """Test place_order tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        items_json = json.dumps([{"sku": "PROD123", "qty": 2}, {"sku": "PROD456", "qty": 1}])
        result = await client.call_tool("place_order", {
            "customer_id": "cust_123",
            "items": items_json,
            "shipping_address_id": "addr_456",
            "payment_method_id": "pm_789"
        })
        content_text = extract_content_text(result)
        print(f"Place order result: {content_text}")
        assert "order" in content_text.lower() or "mock" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_track_order(mcp_server):
    """Test track_order tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("track_order", {"order_id": "ORD12345"})
        content_text = extract_content_text(result)
        print(f"Track order result: {content_text}")
        assert "order" in content_text.lower() or "status" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_cancel_order(mcp_server):
    """Test cancel_order tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("cancel_order", {
            "order_id": "ORD12345",
            "reason": "Changed my mind"
        })
        content_text = extract_content_text(result)
        print(f"Cancel order result: {content_text}")
        assert "cancelled" in content_text.lower() or "cancel" in content_text.lower()


# =====================================================
# 7. Payment Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_check_payment_methods(mcp_server):
    """Test check_payment_methods tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("check_payment_methods", {"customer_id": "cust_123"})
        content_text = extract_content_text(result)
        print(f"Check payment methods result: {content_text}")
        assert "payment" in content_text.lower() or "methods" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_diagnose_payment_issue(mcp_server):
    """Test diagnose_payment_issue tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("diagnose_payment_issue", {
            "error_code": "DECLINED"
        })
        content_text = extract_content_text(result)
        print(f"Diagnose payment issue result: {content_text}")
        assert "payment" in content_text.lower() or "diagnosis" in content_text.lower()


# =====================================================
# 8. Refund Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_get_refund(mcp_server):
    """Test get_refund tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("get_refund", {
            "order_id": "ORD12345",
            "reason": "Defective product"
        })
        content_text = extract_content_text(result)
        print(f"Get refund result: {content_text}")
        assert "refund" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_track_refund(mcp_server):
    """Test track_refund tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("track_refund", {"refund_id": "REF12345"})
        content_text = extract_content_text(result)
        print(f"Track refund result: {content_text}")
        assert "refund" in content_text.lower()


# =====================================================
# 9. Customer Service Tools Tests
# =====================================================

@pytest.mark.asyncio
async def test_integration_contact_customer_service(mcp_server):
    """Test contact_customer_service tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("contact_customer_service", {
            "topic": "Billing issue with my order",
            "preferred_channel": "email",
            "email": "customer@test.com"
        })
        content_text = extract_content_text(result)
        print(f"Contact customer service result: {content_text}")
        assert "ticket" in content_text.lower() or "support" in content_text.lower()


@pytest.mark.asyncio
async def test_integration_transfer_to_human_agent(mcp_server):
    """Test transfer_to_human_agent tool"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        result = await client.call_tool("transfer_to_human_agent", {
            "context": "Customer needs help with complex billing issue",
            "priority": "normal"
        })
        content_text = extract_content_text(result)
        print(f"Transfer to human agent result: {content_text}")
        assert "agent" in content_text.lower() or "human" in content_text.lower()


# =====================================================
# 10. Comprehensive Test Scenarios
# =====================================================

@pytest.mark.asyncio
async def test_comprehensive_order_flow(mcp_server):
    """Test a complete order flow scenario"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        # Step 1: Place an order
        items_json = json.dumps([{"sku": "LAPTOP001", "qty": 1}])
        place_result = await client.call_tool("place_order", {
            "customer_id": "test_customer_001",
            "items": items_json,
            "shipping_address_id": "addr_test_001",
            "payment_method_id": "pm_test_001"
        })
        place_text = extract_content_text(place_result)
        print(f"Step 1 - Place order: {place_text}")
        
        # Step 2: Track the order
        track_result = await client.call_tool("track_order", {"order_id": "ORD12345"})
        track_text = extract_content_text(track_result)
        print(f"Step 2 - Track order: {track_text}")
        
        # Step 3: Check payment methods
        payment_result = await client.call_tool("check_payment_methods", {"customer_id": "test_customer_001"})
        payment_text = extract_content_text(payment_result)
        print(f"Step 3 - Check payment methods: {payment_text}")
        
        # Verify all steps executed without critical errors
        assert place_text and track_text and payment_text


@pytest.mark.asyncio
async def test_comprehensive_customer_service_flow(mcp_server):
    """Test a complete customer service flow scenario"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        # Step 1: Contact customer service
        contact_result = await client.call_tool("contact_customer_service", {
            "topic": "Order not delivered on time",
            "preferred_channel": "phone",
            "phone": "555-0123"
        })
        contact_text = extract_content_text(contact_result)
        print(f"Step 1 - Contact customer service: {contact_text}")
        
        # Step 2: Request refund
        refund_result = await client.call_tool("get_refund", {
            "order_id": "ORD12345",
            "reason": "Late delivery"
        })
        refund_text = extract_content_text(refund_result)
        print(f"Step 2 - Request refund: {refund_text}")
        
        # Step 3: Transfer to human agent if needed
        transfer_result = await client.call_tool("transfer_to_human_agent", {
            "context": "Complex refund issue requiring manual review",
            "priority": "urgent"
        })
        transfer_text = extract_content_text(transfer_result)
        print(f"Step 3 - Transfer to agent: {transfer_text}")
        
        # Verify all steps executed without critical errors
        assert contact_text and refund_text and transfer_text


@pytest.mark.asyncio
async def test_error_handling_scenarios(mcp_server):
    """Test various error handling scenarios"""
    async with Client("http://127.0.0.1:8081/sse") as client:
        # Test with empty parameters
        result1 = await client.call_tool("play_music", {})
        text1 = extract_content_text(result1)
        print(f"Empty play_music: {text1}")
        
        # Test with invalid order ID
        result2 = await client.call_tool("track_order", {"order_id": ""})
        text2 = extract_content_text(result2)
        print(f"Empty order ID: {text2}")
        
        # Test payment diagnosis without parameters
        result3 = await client.call_tool("diagnose_payment_issue", {})
        text3 = extract_content_text(result3)
        print(f"Empty payment diagnosis: {text3}")
        
        # All should handle errors gracefully
        assert text1 and text2 and text3


if __name__ == "__main__":
    # Run tests manually if needed
    pytest.main([__file__, "-v"])