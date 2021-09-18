import asyncio
import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


@pytest.mark.asyncio
async def test_task():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/task", json={"name": "task1"})
    assert response.status_code == 200
    id = response.json()['id']
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get(f"/task/{id}")
    assert response.status_code == 200
    while True:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get(f"/task/{id}")
        print(response.json())
        if response.json()['status'] == 'complete':
            break
        await asyncio.sleep(1)


def main():
    asyncio.run(test_task())


if __name__ == "__main__":
    main()
