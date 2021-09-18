import asyncio
import pytest
from httpx import AsyncClient
from multiprocessing import Process
import uvicorn
import time

from main import app


async def root_tester(app):
    async with AsyncClient(app=app, base_url="http://127.0.0.1:5000") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"Hello": "World"}


@pytest.mark.asyncio
async def test_root():
    root_tester(app)


async def run_server():
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")


@pytest.fixture
async def server():
    proc = Process(target=run_server, args=(), daemon=True)
    proc.start()
    yield
    proc.kill()


@pytest.mark.asyncio
async def test_root_server(server):
    await asyncio.sleep(1)
    await root_tester(None)


@pytest.mark.asyncio
async def test_task():
    async with AsyncClient(app=app, base_url="http://127.0.0.1:5000") as ac:
        response = await ac.post("/task", json={"name": "task1"})
    assert response.status_code == 200
    id = response.json()['id']
    async with AsyncClient(app=app, base_url="http://127.0.0.1:5000") as ac:
        response = await ac.get(f"/task/{id}")
    assert response.status_code == 200
    while True:
        async with AsyncClient(app=app,
                               base_url="http://127.0.0.1:5000") as ac:
            response = await ac.get(f"/task/{id}")
        print(response.json())
        if response.json()['status'] == 'complete':
            break
        await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_task_server(server):
    await test_task()


@pytest.mark.asyncio
async def test_task_server(server):
    await test_task()


# class RemoteTestApp(asynctest.TestCase):
#     async def setUp(self):
#         self.proc = Process(target=uvicorn.run,
#                             args=(app.api,),
#                             kwargs={
#                                 "host": "127.0.0.1",
#                                 "port": 5000,
#                                 "log_level": "info"},
#                             daemon=True)
#         self.proc.start()
#         await asyncio.sleep(0.1)  # time for the server to start

#     async def tearDown(self):
#         """ Shutdown the app. """
#         self.proc.terminate()

#     async def test_root(self):
#         async with AsyncClient(app=app, base_url="http://127.0.0.1:5000") as ac:
#             response = await ac.get("/")
#         assert response.status_code == 200
#         assert response.json() == {"Hello": "World"}


def main():
    asyncio.run(test_task())


if __name__ == "__main__":
    main()
