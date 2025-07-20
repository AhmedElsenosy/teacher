from app.models.counter import Counter

async def get_next_sequence(name: str):
    counter = await Counter.find_one(Counter.name == name)
    if not counter:
        counter = Counter(name=name, sequence_value=1000 if name == "student_id" else 10035)
        await counter.insert()
    else:
        counter.sequence_value += 1
        await counter.save()
    return counter.sequence_value
 
