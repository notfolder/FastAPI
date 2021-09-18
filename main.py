import asyncio
import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from logging import config
from typing import List
from multiprocessing import Pool
import logging

import uvicorn
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

config.dictConfig(yaml.load(open("logging.yml").read(),
                            Loader=yaml.SafeLoader))

queue: List[dict] = []

log = logging.getLogger('process')


class Item(BaseModel):
    name: str


def getLogger(id: str):
    log = logging.getLogger(f'process.{id}')
    handler = logging.FileHandler(f'./log/log-{id}.log')
    fmt = yaml.load(
        open("logging.yml").read(),
        Loader=yaml.SafeLoader)['formatters']['simple_fmt']['format']
    handler.setFormatter(logging.Formatter(fmt))
    log.addHandler(handler)
    return log


def sub_proccess_f(id: str, n: int):
    log = getLogger(id)
    log.info(f'start: {id}-{n}')
    time.sleep(2)
    log.info(f'end: {id}-{n}')


def process_f(id: str):
    log = getLogger(id)
    log.info(f'start: {id}')
    with Pool(2) as p:
        log.info(
            p.starmap(sub_proccess_f, [(id, 1), (id, 2), (id, 3), (id, 4)]))
    #time.sleep(5)
    log.info(f'end: {id}')
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

    loop = asyncio.get_event_loop()
    executor = ProcessPoolExecutor(max_workers=1)
    result = await loop.run_in_executor(executor,
                                        partial(process_f, task['id']))
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
    log.info(id)
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
