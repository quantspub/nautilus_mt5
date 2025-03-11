import asyncio
from nautilus_mt5.ea.client import EAClient

def handle_stream_data(data: str) -> None:
    """Callback function to handle received streaming data."""
    print("Streamed data:", data)

async def main():
    client = EAClient()

    # Start streaming updates
    client.start_stream(callback=handle_stream_data)
    input("Press Enter to stop streaming...")
    client.stop_stream()

if __name__ == "__main__":
    asyncio.run(main())
