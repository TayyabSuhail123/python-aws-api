import pytest, asyncio
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from main import app, RunState

@pytest.mark.asyncio
async def test_happy_path():
    transport = ASGITransport(app=app)        
    async with AsyncClient(transport=transport,
                           base_url="http://test") as ac:
        body = {"agent_type": "policy-checker", "user_id": str(uuid4())}
        resp = await ac.post("/agents/run", json=body)
        assert resp.status_code == 202
        run_id = resp.json()["run_id"]

        for _ in range(10):
            status = await ac.get(f"/agents/status/{run_id}")
            if status.json()["state"] == RunState.done.value:
                assert status.json()["result"] in ("approved", "rejected")
                break
            await asyncio.sleep(0.6)
        else:
            pytest.fail("Agent never completed")
