import pytest
from fastmcp import Client
from Backend.MCP.mcp_server_new_1 import mcp

@pytest.mark.asyncio
async def test_play_music():
    async with Client(mcp) as client:
        result = await client.call_tool("play_music", {"song": "Shape of You", "artist": "Ed Sheeran"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_rate_book():
    async with Client(mcp) as client:
        result = await client.call_tool("rate_book", {"book": "1984", "rating": 5, "review": "Excellent read"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_search_screening_event():
    async with Client(mcp) as client:
        result = await client.call_tool("search_screening_event", {"query": "Spider-Man", "location": "New York", "date": "tomorrow"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_edit_account():
    async with Client(mcp) as client:
        result = await client.call_tool("edit_account", {"account_id": "ACC1234", "email": "newemail@example.com", "full_name": "John Doe"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_place_order():
    async with Client(mcp) as client:
        items = '[{"sku": "PROD123", "qty": 2}, {"sku": "PROD456", "qty": 1}]'
        result = await client.call_tool("place_order", {"customer_id": "CUST001", "items": items, "shipping_address_id": "ADDR001", "payment_method_id": "PM001"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_track_order():
    async with Client(mcp) as client:
        result = await client.call_tool("track_order", {"order_id": "ORD001"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_cancel_order():
    async with Client(mcp) as client:
        result = await client.call_tool("cancel_order", {"order_id": "ORD001", "reason": "Changed my mind"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_check_payment_methods():
    async with Client(mcp) as client:
        result = await client.call_tool("check_payment_methods", {"customer_id": "CUST001"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_diagnose_payment_issue():
    async with Client(mcp) as client:
        result = await client.call_tool("diagnose_payment_issue", {"order_id": "ORD001", "error_code": "DECLINED"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_get_refund():
    async with Client(mcp) as client:
        items = '[{"sku": "PROD123", "qty": 1}]'
        result = await client.call_tool("get_refund", {"order_id": "ORD001", "items": items, "reason": "Defective product"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_track_refund():
    async with Client(mcp) as client:
        result = await client.call_tool("track_refund", {"refund_id": "REF001"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_contact_customer_service():
    async with Client(mcp) as client:
        result = await client.call_tool("contact_customer_service", {"topic": "Billing issue", "preferred_channel": "email", "customer_id": "CUST001", "email": "test@example.com"})
        content = result.content
        assert content is not None
        print(content)

@pytest.mark.asyncio
async def test_transfer_to_human_agent():
    async with Client(mcp) as client:
        result = await client.call_tool("transfer_to_human_agent", {"context": "Issue with order cancellation", "priority": "urgent"})
        content = result.content
        assert content is not None
        print(content)
