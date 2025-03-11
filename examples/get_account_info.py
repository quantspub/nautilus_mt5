from metatrader5ext import MetaTrader5Ext, MetaTrader5ExtConfig

config = MetaTrader5ExtConfig()
client = MetaTrader5Ext(config=config)
client.connect()
print(client.is_connected())

print(client.get_accounts())

client.disconnect()
