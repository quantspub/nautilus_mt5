import asyncio
from metatrader5ext.ea.client import EAClient

async def main():
    client = EAClient()

    # Test REST requests
    connection_status = await client.check_connection()
    print(f"Connection status: {connection_status}")

    static_account_info = await client.get_static_account_info()
    print("Static account info:", static_account_info)

    dynamic_account_info = await client.get_dynamic_account_info()
    print("Dynamic account info:", dynamic_account_info)

    last_tick_info = await client.get_last_tick_info()
    print("Last tick info:", last_tick_info)

    broker_server_time = await client.get_broker_server_time()
    print("Broker server time:", broker_server_time)

    instrument_info = await client.get_instrument_info()
    print("Instrument info:", instrument_info) 

    # Start streaming updates
    client.start_stream(callback=lambda data: print(f"\nStreamed data: {data}"))
    input("Press Enter to stop streaming...")
    client.stop_stream()

if __name__ == "__main__":
    asyncio.run(main())
