//+------------------------------------------------------------------+
//|                                            MT5Ext.mq5            |
//+------------------------------------------------------------------+
#property copyright "QuantsPub"
#property version "0.1"

#include <MT5Ext\MT5Ext.mqh>
#include <MT5Ext\rest-handlers.mqh>
#include <MT5Ext\stream-handlers.mqh>
#include <MT5Ext\utils.mqh>

input ushort REST_SERVER_PORT = 15556;   // REST server for commands
input ushort STREAM_SERVER_PORT = 15557; // Streaming server for real-time data and responses
input int TIMER_INTERVAL = 1;            // Timer interval for the REST server
input bool ONLY_STREAM_MODE = false;     // If enabled, responses will be sent via stream server
input bool DEBUG = false;                // If enabled, debug messages will be printed

datetime lastBarTime = 0;

void OnInit()
{
    StartServers(REST_SERVER_PORT, STREAM_SERVER_PORT, true);

    lastBarTime = iTime(_Symbol, PERIOD_CURRENT, 0);
    EventSetTimer(TIMER_INTERVAL);
}

void OnDeinit(const int reason)
{
    EventKillTimer();

    CloseServers();
}

void OnTimer()
{
    AcceptClients(ONLY_STREAM_MODE, DEBUG);
}

void OnTick()
{
    string symbol = _Symbol;
    string latestTick = GetLatestTick(symbol);
    if (latestTick != "")
    {
        BroadcastStreamData(latestTick);
    }

    // Detect new bar
    datetime currentBarTime = iTime(symbol, PERIOD_CURRENT, 0);
    if (currentBarTime > lastBarTime)
    {
        lastBarTime = currentBarTime;
        string latestBar = GetLatestBar(symbol, currentBarTime);
        if (latestBar != "")
        {
            BroadcastStreamData(latestBar);
        }

        // string noNewBarParameters[1] = {"NO_NEW_BAR"};
        // return MakeMessage("F021", "1", noNewBarParameters);
    }
}


// https://www.mql5.com/en/docs/constants/structures/mqltick
