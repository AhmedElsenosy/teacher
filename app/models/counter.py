from beanie import Document
from pydantic import Field

class Counter(Document):
    name: str = Field(...)
    sequence_value: int = Field(...)

    class Settings:
        name = "counters"

async def get_next_id(name: str) -> int:
    counter = await Counter.find_one(Counter.name == name)

    if counter:
        counter.sequence_value += 1
        await counter.save()
        return counter.sequence_value
    else:
        new_counter = Counter(name=name, sequence_value=1)
        await new_counter.insert()
        return 1
