import asyncio

async def process_in_chunks(data, chunk_size=100):
    for i in range(0, len(data), chunk_size):
        chunk = data[i:i + chunk_size]
        await asyncio.sleep(0.1)  # Simulate async yield/pause
        yield chunk
