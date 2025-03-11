//+------------------------------------------------------------------+
//|                                            MT5Ext.mqh            |
//+------------------------------------------------------------------+
#property copyright "QuantsPub"
#property version "0.1"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\OrderInfo.mqh>
#include <MT5Ext\utils.mqh>

//
// Handlers functions
//
string GetBrokerServerTime()
{
    string parameters[] = {IntegerToString(TimeCurrent())};
    return MakeMessage("F005", "1", parameters);
}

string GetCheckConnection()
{
    string parameters[] = {"OK"};
    return MakeMessage("F000", "1", parameters);
}

string GetStaticAccountInfo()
{
    string parameters[] = {
        AccountInfoString(ACCOUNT_NAME),
        IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)),
        AccountInfoString(ACCOUNT_CURRENCY),
        IntegerToString(AccountInfoInteger(ACCOUNT_TRADE_MODE)),
        IntegerToString(AccountInfoInteger(ACCOUNT_LEVERAGE)),
        BoolToString((bool)AccountInfoInteger(ACCOUNT_TRADE_ALLOWED)),
        IntegerToString(AccountInfoInteger(ACCOUNT_LIMIT_ORDERS)),
        DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_SO_CALL)),
        DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_SO_SO)),
        AccountInfoString(ACCOUNT_COMPANY)};
    return MakeMessage("F001", "10", parameters);
}

string GetDynamicAccountInfo()
{
    string parameters[] = {
        DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2),
        DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2),
        DoubleToString(AccountInfoDouble(ACCOUNT_PROFIT), 2),
        DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN), 2),
        DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_LEVEL), 2),
        DoubleToString(AccountInfoDouble(ACCOUNT_MARGIN_FREE), 2)};
    return MakeMessage("F002", "6", parameters);
}

string GetInstrumentInfo(string symbol)
{
    string parameters[] = {
        IntegerToString(SymbolInfoInteger(symbol, SYMBOL_DIGITS)),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX), 2),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN), 2),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP), 2),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_POINT), 5),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE), 5),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE), 2),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SWAP_LONG), 2),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_SWAP_SHORT), 2),
        IntegerToString(SymbolInfoInteger(symbol, SYMBOL_TRADE_STOPS_LEVEL)),
        DoubleToString(SymbolInfoDouble(symbol, SYMBOL_TRADE_CONTRACT_SIZE), 2)};
    return MakeMessage("F003", "3", parameters);
}

string GetBrokerInstrumentNames()
{
    string parameters[] = {TerminalInfoString(TERMINAL_NAME)};
    return MakeMessage("F007", "1", parameters);
}

string CheckMarketWatch(string symbol)
{
    bool isWatched = SymbolSelect(symbol, true);
    string parameters[] = {isWatched ? "YES" : "NO"};
    return MakeMessage("F004", "1", parameters);
}

string CheckTradingAllowed(string symbol)
{
    bool tradingAllowed = SymbolInfoInteger(symbol, SYMBOL_TRADE_MODE) != SYMBOL_TRADE_MODE_DISABLED;
    string parameters[] = {tradingAllowed ? "YES" : "NO"};
    return MakeMessage("F008", "1", parameters);
}

string CheckTerminalServerConnection()
{
    string parameters[] = {TerminalInfoInteger(TERMINAL_CONNECTED) ? "CONNECTED" : "DISCONNECTED"};
    return MakeMessage("F011", "1", parameters);
}

string CheckTerminalType()
{
    string parameters[] = {TerminalInfoString(TERMINAL_NAME)};
    return MakeMessage("F012", "1", parameters);
}

string GetLastTickInfo(string symbol)
{
    string errorParameters[] = {"ERROR"};

    // Make the symbol uppercase and standardized
    if (!StringToUpper(symbol))
    {
        return MakeMessage("F020", "1", errorParameters);
    }
    SymbolSelect(symbol, true);

    MqlTick lastTick;
    if (SymbolInfoTick(symbol, lastTick))
    {
        string parameters[] = {
            IntegerToString(lastTick.time),
            DoubleToString(lastTick.bid, 5),
            DoubleToString(lastTick.ask, 5),
            DoubleToString(lastTick.last, 5),
            IntegerToString(lastTick.volume),
            IntegerToString(SymbolInfoInteger(symbol, SYMBOL_SPREAD)),
            IntegerToString(lastTick.time_msc),
        };
        return MakeMessage("F020", "6", parameters);
    }
    return MakeMessage("F020", "1", errorParameters);
}

string GetLastXTickFromNow(string symbol, int nbrofticks)
{
    string errorParameters[] = {"ERROR"};

    // Make the symbol uppercase and standardized
    if (!StringToUpper(symbol))
    {
        return MakeMessage("F021", "1", errorParameters);
    }
    SymbolSelect(symbol, true);

    MqlTick ticks[];
    if (CopyTicks(symbol, ticks, COPY_TICKS_ALL, 0, nbrofticks) > 0)
    {
        string parameters[];
        for (int i = 0; i < ArraySize(ticks); i++)
        {
            parameters[i] = IntegerToString(ticks[i].time) + "$" +
                            DoubleToString(ticks[i].ask, 5) + "$" +
                            DoubleToString(ticks[i].bid, 5) + "$" +
                            DoubleToString(ticks[i].last, 5) + "$" +
                            IntegerToString(ticks[i].volume);
        }
        return MakeMessage("F021", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F021", "1", errorParameters);
}

string GetActualBarInfo(string symbol, int timeframe)
{
    string errorParameters[] = {"ERROR"};

    // Make the symbol uppercase and standardized
    if (!StringToUpper(symbol))
    {
        return MakeMessage("F041", "1", errorParameters);
    }
    SymbolSelect(symbol, true);

    MqlRates rates[];
    if (CopyRates(symbol, (ENUM_TIMEFRAMES)timeframe, 0, 1, rates) > 0)
    {
        string parameters[] = {
            IntegerToString(rates[0].time),
            DoubleToString(rates[0].open, 5),
            DoubleToString(rates[0].high, 5),
            DoubleToString(rates[0].low, 5),
            DoubleToString(rates[0].close, 5),
            IntegerToString(rates[0].tick_volume)};
        return MakeMessage("F041", "6", parameters);
    }
    return MakeMessage("F041", "1", errorParameters);
}

string GetSpecificBar(string symbol, int specific_bar_index, ENUM_TIMEFRAMES timeframe)
{
    string errorParameters[] = {"ERROR"};

    // Make the symbol uppercase and standardized
    if (!StringToUpper(symbol))
    {
        return MakeMessage("F045", "1", errorParameters);
    }
    SymbolSelect(symbol, true);

    MqlRates rates[];
    if (CopyRates(symbol, timeframe, specific_bar_index, 1, rates) > 0)
    {
        string parameters[] = {
            symbol,
            IntegerToString(rates[0].time),
            DoubleToString(rates[0].open, 5),
            DoubleToString(rates[0].high, 5),
            DoubleToString(rates[0].low, 5),
            DoubleToString(rates[0].close, 5),
            IntegerToString(rates[0].tick_volume)};
        return MakeMessage("F045", "7", parameters);
    }
    return MakeMessage("F045", "1", errorParameters);
}

string GetLastXBarsFromNow(string symbol, ENUM_TIMEFRAMES timeframe, int nbrofbars)
{
    string errorParameters[] = {"ERROR"};

    // Make the symbol uppercase and standardized
    if (!StringToUpper(symbol))
    {
        return MakeMessage("F042", "1", errorParameters);
    }
    SymbolSelect(symbol, true);

    MqlRates rates[];
    if (CopyRates(symbol, timeframe, 0, nbrofbars, rates) > 0)
    {
        string parameters[];
        for (int i = 0; i < ArraySize(rates); i++)
        {
            parameters[i] = IntegerToString(rates[i].time) + "$" +
                            DoubleToString(rates[i].open, 5) + "$" +
                            DoubleToString(rates[i].high, 5) + "$" +
                            DoubleToString(rates[i].low, 5) + "$" +
                            DoubleToString(rates[i].close, 5) + "$" +
                            IntegerToString(rates[i].tick_volume);
        }
        return MakeMessage("F042", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F042", "1", errorParameters);
}

string GetAllOpenPositions()
{
    string errorParameters[] = {"ERROR"};

    int total = PositionsTotal();
    if (total > 0)
    {
        string parameters[];
        for (int i = 0; i < total; i++)
        {
            ulong ticket = PositionGetTicket(i);
            parameters[i] = IntegerToString(ticket) + "$" +
                            PositionGetString(POSITION_SYMBOL) + "$" +
                            IntegerToString(PositionGetInteger(POSITION_TYPE)) + "$" +
                            IntegerToString(PositionGetInteger(POSITION_MAGIC)) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_VOLUME), 2) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_PRICE_OPEN), 5) + "$" +
                            IntegerToString(PositionGetInteger(POSITION_TIME)) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_SL), 5) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_TP), 5) + "$" +
                            PositionGetString(POSITION_COMMENT) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_PROFIT), 2) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_SWAP), 2) + "$" +
                            DoubleToString(PositionGetDouble(POSITION_COMMISSION), 2);
        }
        return MakeMessage("F061", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F061", "1", errorParameters);
}

string GetAllClosedPositions()
{
    string errorParameters[] = {"ERROR"};

    int total = HistoryDealsTotal();
    if (total > 0)
    {
        string parameters[];
        for (int i = 0; i < total; i++)
        {
            ulong ticket = HistoryDealGetTicket(i);
            parameters[i] = IntegerToString(ticket) + "$" +
                            HistoryDealGetString(ticket, DEAL_SYMBOL) + "$" +
                            IntegerToString(HistoryDealGetInteger(ticket, DEAL_TYPE)) + "$" +
                            IntegerToString(HistoryDealGetInteger(ticket, DEAL_MAGIC)) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_VOLUME), 2) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_PRICE), 5) + "$" +
                            IntegerToString(HistoryDealGetInteger(ticket, DEAL_TIME)) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_SL), 5) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_TP), 5) + "$" +
                            HistoryDealGetString(ticket, DEAL_COMMENT) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_PROFIT), 2) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_SWAP), 2) + "$" +
                            DoubleToString(HistoryDealGetDouble(ticket, DEAL_COMMISSION), 2);
        }
        return MakeMessage("F063", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F063", "1", errorParameters);
}

string GetAllDeletedOrders()
{
    string errorParameters[] = {"ERROR"};
    if (!HistorySelect(0, TimeCurrent()))
    {
        // GetLastError();
        return MakeMessage("F065", "1", errorParameters);
    }

    int total = HistoryOrdersTotal();
    if (total > 0)
    {
        string parameters[];
        for (int i = 0; i < total; i++)
        {
            ulong ticket = OrderGetTicket(i);
            parameters[i] = IntegerToString(ticket) + "$" +
                            OrderGetString(ORDER_SYMBOL) + "$" +
                            IntegerToString(OrderGetInteger(ORDER_TYPE)) + "$" +
                            IntegerToString(OrderGetInteger(ORDER_MAGIC)) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_VOLUME_INITIAL), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_VOLUME_CURRENT), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_PRICE_OPEN), 5) + "$" +
                            IntegerToString(OrderGetInteger(ORDER_TIME_SETUP)) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_SL), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_TP), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_PRICE_CURRENT), 5) + "$" +
                            IntegerToString(OrderGetInteger(ORDER_TIME_DONE)) + "$" +
                            OrderGetString(ORDER_COMMENT);
        }
        return MakeMessage("F065", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F065", "1", errorParameters);
}

string GetAllPendingOrders()
{
    string errorParameters[] = {"ERROR"};

    int total = OrdersTotal();
    if (total > 0)
    {
        string parameters[];
        for (int i = 0; i < total; i++)
        {
            ulong ticket = OrderGetTicket(i);
            parameters[i] = IntegerToString(ticket) + "$" +
                            OrderGetString(ORDER_SYMBOL) + "$" +
                            IntegerToString(OrderGetInteger(ORDER_TYPE)) + "$" +
                            IntegerToString(OrderGetInteger(ORDER_MAGIC)) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_VOLUME_INITIAL), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_VOLUME_CURRENT), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_PRICE_OPEN), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_SL), 5) + "$" +
                            DoubleToString(OrderGetDouble(ORDER_TP), 5) + "$" +
                            OrderGetString(ORDER_COMMENT);
        }
        return MakeMessage("F060", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F060", "1", errorParameters);
}

string GetAllClosedPositionsWithinWindow(datetime date_from, datetime date_to)
{
    string errorParameters[] = {"ERROR"};

    int total = HistoryDealsTotal();
    if (total > 0)
    {
        string parameters[];
        for (int i = 0; i < total; i++)
        {
            ulong ticket = HistoryDealGetTicket(i);
            datetime deal_time = (datetime)HistoryDealGetInteger(ticket, DEAL_TIME);
            if (deal_time >= date_from && deal_time <= date_to)
            {
                parameters[i] = IntegerToString(ticket) + "$" +
                                HistoryDealGetString(ticket, DEAL_SYMBOL) + "$" +
                                IntegerToString(HistoryDealGetInteger(ticket, DEAL_TYPE)) + "$" +
                                IntegerToString(HistoryDealGetInteger(ticket, DEAL_MAGIC)) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_VOLUME), 2) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_PRICE), 5) + "$" +
                                IntegerToString(deal_time) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_SL), 5) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_TP), 5) + "$" +
                                HistoryDealGetString(ticket, DEAL_COMMENT) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_PROFIT), 2) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_SWAP), 2) + "$" +
                                DoubleToString(HistoryDealGetDouble(ticket, DEAL_COMMISSION), 2);
            }
        }
        return MakeMessage("F062", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F062", "1", errorParameters);
}

string GetAllDeletedPendingOrdersWithinWindow(datetime date_from, datetime date_to)
{
    string errorParameters[] = {"ERROR"};

    int total = HistoryOrdersTotal();
    if (total > 0)
    {
        string parameters[];
        for (int i = 0; i < total; i++)
        {
            ulong ticket = OrderGetTicket(i);
            datetime order_time = (datetime)OrderGetInteger(ORDER_TIME_SETUP);
            if (order_time >= date_from && order_time <= date_to)
            {
                parameters[i] = IntegerToString(ticket) + "$" +
                                OrderGetString(ORDER_SYMBOL) + "$" +
                                IntegerToString(OrderGetInteger(ORDER_TYPE)) + "$" +
                                IntegerToString(OrderGetInteger(ORDER_MAGIC)) + "$" +
                                DoubleToString(OrderGetDouble(ORDER_VOLUME_INITIAL), 5) + "$" +
                                DoubleToString(OrderGetDouble(ORDER_VOLUME_CURRENT), 5) + "$" +
                                DoubleToString(OrderGetDouble(ORDER_PRICE_OPEN), 5) + "$" +
                                IntegerToString(order_time) + "$" +
                                DoubleToString(OrderGetDouble(ORDER_SL), 5) + "$" +
                                DoubleToString(OrderGetDouble(ORDER_TP), 5) + "$" +
                                DoubleToString(OrderGetDouble(ORDER_PRICE_CURRENT), 5) + "$" +
                                IntegerToString(OrderGetInteger(ORDER_TIME_DONE)) + "$" +
                                OrderGetString(ORDER_COMMENT);
            }
        }
        return MakeMessage("F064", IntegerToString(ArraySize(parameters)), parameters);
    }
    return MakeMessage("F064", "1", errorParameters);
}