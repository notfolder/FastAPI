from typing import List
from fastapi import FastAPI
import uvicorn
import uuid
import asyncio
from pydantic import BaseModel
import time
from concurrent.futures import ProcessPoolExecutor
from functools import partial

app = FastAPI()

queue: List[dict] = []


class Item(BaseModel):
    name: str


def process_f(id: int):
    print(id)
    time.sleep(5)
    return id


async def run_next_task():
    current = get_current_task()
    if current is not None:
        await current

    task = get_next_task()
    if task is None:
        return
    task['status'] = 'processing'
    # main task
    #with Pool(2) as p:
    #    print(p.map(process_f, [1, 2, 3]))

    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor(max_workers=2)
    result = await asyncio.gather(*[
        loop.run_in_executor(executor, partial(process_f, 1)),
        loop.run_in_executor(executor, partial(process_f, 2)),
    ])
    task['result'] = result

    #await asyncio.sleep(5)

    task['status'] = 'complete'


def get_current_task():
    task = [x for x in queue if x['status'] == 'processing']
    if len(task) == 0:
        return None
    return task[0]


def get_next_task():
    task = [x for x in queue if x['status'] == 'waiting']
    if len(task) == 0:
        return None
    return task[0]


def get_task(id: str):
    task = [x for x in queue if x['id'] == id]
    if len(task) == 0:
        return None
    return task[0]


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/task")
async def post_task(item: Item):
    id = str(uuid.uuid4())
    print(id)
    async_task = asyncio.get_event_loop().create_task(run_next_task())
    task = {
        "id": id,
        "name": item.name,
        "task": async_task,
        "status": "waiting"
    }
    queue.append(task)
    return {"id": id}


@app.get("/task/{id}")
async def get_task_status(id: str):
    task = get_task(id)
    return {'id': task['id'], 'status': task['status']}


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=5000, log_level="info")
