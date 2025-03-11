//+------------------------------------------------------------------+
//|                                            stream-handlers.mqh   |
//+------------------------------------------------------------------+
#property copyright "QuantsPub"
#property version "0.1"

#include <MT5Ext\utils.mqh>

string GetLatestTick(const string &symbol)
{
    MqlTick lastTick;
    if (SymbolInfoTick(symbol, lastTick))
    {
        string parameters[5];
        parameters[0] = IntegerToString(lastTick.time);
        parameters[1] = DoubleToString(lastTick.bid, 5);
        parameters[2] = DoubleToString(lastTick.ask, 5);
        parameters[3] = DoubleToString(lastTick.last, 5);
        parameters[4] = IntegerToString(lastTick.volume);
        return MakeMessage("F020", "6", parameters);
    }
    string errorParameters[1] = {"ERROR"};
    return MakeMessage("F020", "1", errorParameters);
}

string GetLatestBar(const string &symbol, datetime currentBarTime)
{
    double open = iOpen(symbol, PERIOD_CURRENT, 0);
    double high = iHigh(symbol, PERIOD_CURRENT, 0);
    double low = iLow(symbol, PERIOD_CURRENT, 0);
    double close = iClose(symbol, PERIOD_CURRENT, 0);
    long volume = iVolume(symbol, PERIOD_CURRENT, 0);

    string parameters[6];
    parameters[0] = IntegerToString(currentBarTime);
    parameters[1] = DoubleToString(open, 5);
    parameters[2] = DoubleToString(high, 5);
    parameters[3] = DoubleToString(low, 5);
    parameters[4] = DoubleToString(close, 5);
    parameters[5] = IntegerToString(volume);
    return MakeMessage("F021", "6", parameters);
}
