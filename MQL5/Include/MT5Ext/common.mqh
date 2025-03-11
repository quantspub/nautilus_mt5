// Constants
#define NO_VALID_ID -1
#define MAX_MSG_LEN 0xFFFFFF // 16Mb - 1byte

// Unset values
#define UNSET_INTEGER 2147483647
#define UNSET_DOUBLE DBL_MAX
#define UNSET_LONG 9223372036854775807
#define UNSET_DECIMAL 1.7976931348623157E308
#define DOUBLE_INFINITY DBL_MAX
#define INFINITY_STR "Infinity"

// Type aliases
typedef int TickerId;
typedef int OrderId;
typedef string TagValueList[];

// Enums
enum FaDataType {
    FA_NONE,
    FA_GROUPS,
    FA_PROFILES,
    FA_ALIASES
};

enum MarketDataType {
    MARKET_DATA_NONE,
    MARKET_DATA_REALTIME,
    MARKET_DATA_FROZEN,
    MARKET_DATA_DELAYED,
    MARKET_DATA_DELAYED_FROZEN
};

enum Liquidities {
    LIQUIDITY_NONE,
    LIQUIDITY_ADDED,
    LIQUIDITY_REMOVED,
    LIQUIDITY_ROUNDED_OUT
};

// Custom classes
class BarData {
public:
    string date;
    double open;
    double high;
    double low;
    double close;
    double volume;
    double wap;
    int barCount;

    BarData() : open(0.0), high(0.0), low(0.0), close(0.0), volume(UNSET_DECIMAL), wap(UNSET_DECIMAL), barCount(0) {}

    string ToString() {
        return StringFormat("Date: %s, Open: %s, High: %s, Low: %s, Close: %s, Volume: %s, WAP: %s, BarCount: %s",
            date, FloatToString(open), FloatToString(high), FloatToString(low), FloatToString(close),
            DoubleToString(volume), DoubleToString(wap), IntegerToString(barCount));
    }
};

class RealTimeBar {
public:
    int time;
    int endTime;
    double open_;
    double high;
    double low;
    double close;
    double volume;
    double wap;
    int count;

    RealTimeBar(int _time = 0, int _endTime = -1, double _open = 0.0, double _high = 0.0, double _low = 0.0, double _close = 0.0, double _volume = UNSET_DECIMAL, double _wap = UNSET_DECIMAL, int _count = 0)
        : time(_time), endTime(_endTime), open_(_open), high(_high), low(_low), close(_close), volume(_volume), wap(_wap), count(_count) {}

    string ToString() {
        return StringFormat("Time: %s, Open: %s, High: %s, Low: %s, Close: %s, Volume: %s, WAP: %s, Count: %s",
            IntegerToString(time), FloatToString(open_), FloatToString(high), FloatToString(low), FloatToString(close),
            DoubleToString(volume), DoubleToString(wap), IntegerToString(count));
    }
};

class HistogramData {
public:
    double price;
    double size;

    HistogramData() : price(0.0), size(UNSET_DECIMAL) {}

    string ToString() {
        return StringFormat("Price: %s, Size: %s", FloatToString(price), DoubleToString(size));
    }
};

class NewsProvider {
public:
    string code;
    string name;

    NewsProvider() : code(""), name("") {}

    string ToString() {
        return StringFormat("Code: %s, Name: %s", code, name);
    }
};

class DepthMktDataDescription {
public:
    string exchange;
    string secType;
    string listingExch;
    string serviceDataType;
    int aggGroup;

    DepthMktDataDescription() : aggGroup(UNSET_INTEGER) {}

    string ToString() {
        return StringFormat("Exchange: %s, SecType: %s, ListingExchange: %s, ServiceDataType: %s, AggGroup: %s",
            exchange, secType, listingExch, serviceDataType, IntegerToString(aggGroup));
    }
};

class SmartComponent {
public:
    int bitNumber;
    string exchange;
    string exchangeLetter;

    SmartComponent() : bitNumber(0), exchange(""), exchangeLetter("") {}

    string ToString() {
        return StringFormat("BitNumber: %d, Exchange: %s, ExchangeLetter: %s", bitNumber, exchange, exchangeLetter);
    }
};

class TickAttrib {
public:
    bool canAutoExecute;
    bool pastLimit;
    bool preOpen;

    TickAttrib() : canAutoExecute(false), pastLimit(false), preOpen(false) {}

    string ToString() {
        return StringFormat("CanAutoExecute: %d, PastLimit: %d, PreOpen: %d", canAutoExecute, pastLimit, preOpen);
    }
};

class TickAttribBidAsk {
public:
    bool bidPastLow;
    bool askPastHigh;

    TickAttribBidAsk() : bidPastLow(false), askPastHigh(false) {}

    string ToString() {
        return StringFormat("BidPastLow: %d, AskPastHigh: %d", bidPastLow, askPastHigh);
    }
};

class TickAttribLast {
public:
    bool pastLimit;
    bool unreported;

    TickAttribLast() : pastLimit(false), unreported(false) {}

    string ToString() {
        return StringFormat("PastLimit: %d, Unreported: %d", pastLimit, unreported);
    }
};

class FamilyCode {
public:
    string accountID;
    string familyCodeStr;

    FamilyCode() : accountID(""), familyCodeStr("") {}

    string ToString() {
        return StringFormat("AccountId: %s, FamilyCodeStr: %s", accountID, familyCodeStr);
    }
};

class PriceIncrement {
public:
    double lowEdge;
    double increment;

    PriceIncrement() : lowEdge(0.0), increment(0.0) {}

    string ToString() {
        return StringFormat("LowEdge: %s, Increment: %s", FloatToString(lowEdge), FloatToString(increment));
    }
};

class HistoricalTick {
public:
    int time;
    double price;
    double size;

    HistoricalTick() : time(0), price(0.0), size(UNSET_DECIMAL) {}

    string ToString() {
        return StringFormat("Time: %s, Price: %s, Size: %s", IntegerToString(time), FloatToString(price), DoubleToString(size));
    }
};

class HistoricalTickBidAsk {
public:
    int time;
    TickAttribBidAsk tickAttribBidAsk;
    double priceBid;
    double priceAsk;
    double sizeBid;
    double sizeAsk;

    HistoricalTickBidAsk() : time(0), priceBid(0.0), priceAsk(0.0), sizeBid(UNSET_DECIMAL), sizeAsk(UNSET_DECIMAL) {}

    string ToString() {
        return StringFormat("Time: %s, TickAttriBidAsk: %s, PriceBid: %s, PriceAsk: %s, SizeBid: %s, SizeAsk: %s",
            IntegerToString(time), tickAttribBidAsk.ToString(), FloatToString(priceBid), FloatToString(priceAsk),
            DoubleToString(sizeBid), DoubleToString(sizeAsk));
    }
};

class HistoricalTickLast {
public:
    int time;
    TickAttribLast tickAttribLast;
    double price;
    double size;
    string exchange;
    string specialConditions;

    HistoricalTickLast() : time(0), price(0.0), size(UNSET_DECIMAL), exchange(""), specialConditions("") {}

    string ToString() {
        return StringFormat("Time: %s, TickAttribLast: %s, Price: %s, Size: %s, Exchange: %s, SpecialConditions: %s",
            IntegerToString(time), tickAttribLast.ToString(), FloatToString(price), DoubleToString(size), exchange, specialConditions);
    }
};

class HistoricalSession {
public:
    string startDateTime;
    string endDateTime;
    string refDate;

    HistoricalSession() : startDateTime(""), endDateTime(""), refDate("") {}

    string ToString() {
        return StringFormat("Start: %s, End: %s, Ref Date: %s", startDateTime, endDateTime, refDate);
    }
};

class WshEventData {
public:
    int conId;
    string filter;
    bool fillWatchlist;
    bool fillPortfolio;
    bool fillCompetitors;
    string startDate;
    string endDate;
    int totalLimit;

    WshEventData() : conId(UNSET_INTEGER), fillWatchlist(false), fillPortfolio(false), fillCompetitors(false), totalLimit(UNSET_INTEGER) {}

    string ToString() {
        return StringFormat("WshEventData. ConId: %s, Filter: %s, Fill Watchlist: %d, Fill Portfolio: %d, Fill Competitors: %d",
            IntegerToString(conId), filter, fillWatchlist, fillPortfolio, fillCompetitors);
    }
};
