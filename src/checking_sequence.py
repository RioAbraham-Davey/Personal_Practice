import asyncio

async def first_routine():
    print("First routine is running")

async def second_routine():
    print("Second routine is running")

async def third_routine():
    print("Third routine is running")

async def fourth_routine():
    print("Fourth routine is running")

async def fifth_routine():
    print("Fifth routine is running")

async def sixth_routine():
    print("Sixth routine is running")

async def seventh_routine():
    print("Seventh routine is running")

loop = asyncio.new_event_loop()
asyncio.create_task(fourth_routine())
asyncio.create_task(fifth_routine())
asyncio.create_task(first_routine())
asyncio.create_task(second_routine())
asyncio.create_task(third_routine())
asyncio.create_task(sixth_routine())
asyncio.create_task(seventh_routine())
loop.run_forever()