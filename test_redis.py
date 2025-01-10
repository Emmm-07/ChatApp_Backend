import os
import django
from channels.layers import get_channel_layer
import asyncio

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')  # Replace 'myproject' with your project name
django.setup()

async def test_redis():
    channel_layer = get_channel_layer()
    await channel_layer.send("test_channel", {"type": "test.message", "message": "hello!"})
    response = await channel_layer.receive("test_channel")
    print(response)

asyncio.run(test_redis())
