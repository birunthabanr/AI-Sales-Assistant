# tests/test_add_to_playlist.py
import pytest

pytestmark = pytest.mark.asyncio

async def test_add_to_playlist(mcp_client):
    params = {
        "user_id": "123",
        "playlist_name": "Focus Mix",
        "song_title": "Time",
        "artist": "Hans Zimmer",
    }
    result = await mcp_client.call_tool("add_to_playlist", **params)
    text = result.content.text
    assert isinstance(text, str)
    assert "playlist" in text.lower()
