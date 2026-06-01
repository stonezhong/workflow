from typing import Callable
import asyncio

async def add(input: dict, logger=Callable[[str],None]) -> dict:
    return {"result": input['x'] + input['y']}


async def mul(input: dict, logger=Callable[[str], None]) -> dict:
    return {"result": input['x'] * input['y']}
