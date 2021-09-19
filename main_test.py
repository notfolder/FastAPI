import asyncio
import pytest
from httpx import AsyncClient
import uvicorn
import httpx

from main import app


@pytest.fixture()
async def server():
    ret_app = None
    try:
        async with AsyncClient(app=None, base_url="http://127.0.0.1:5000") as ac:
            response = await ac.get("/")
    except httpx.ConnectError:
        ret_app = app
    return ret_app


@pytest.mark.asyncio
async def test_root(server):
    async with AsyncClient(app=server, base_url="http://127.0.0.1:5000") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


@pytest.mark.asyncio
async def test_task(server):
    async with AsyncClient(app=server, base_url="http://127.0.0.1:5000") as ac:
        response = await ac.post("/task", json={"name": "task1"})
    assert response.status_code == 200
    id = response.json()['id']
    async with AsyncClient(app=server, base_url="http://127.0.0.1:5000") as ac:
        response = await ac.get(f"/task/{id}")
    assert response.status_code == 200
    while True:
        async with AsyncClient(app=server,
                               base_url="http://127.0.0.1:5000") as ac:
            response = await ac.get(f"/task/{id}")
        print(response.json())
        if response.json()['status'] == 'complete':
            break
        await asyncio.sleep(1)


def main():
    asyncio.run(test_task())


if __name__ == "__main__":
    main()
