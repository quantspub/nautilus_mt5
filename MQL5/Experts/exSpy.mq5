//+------------------------------------------------------------------+
//|                                                        exSpy.mq5 |
//|                                            Copyright 2010, Lizar |
//|                            https://login.mql5.com/ru/users/Lizar |
//+------------------------------------------------------------------+
#define VERSION       "1.00 Build 1 (26 Dec 2010)"

#property copyright   "Copyright 2010, Lizar"
#property link        "https://login.mql5.com/ru/users/Lizar"
#property version     VERSION
#property description "The Expert Advisor shows the work of iSPY indicator"

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {   
   if(iCustom("GBPUSD",PERIOD_M1,"iSpy",ChartID(),0)==INVALID_HANDLE) 
      { Print("Error in setting of spy on GBPUSD"); return(true);}
   if(iCustom("EURUSD",PERIOD_M1,"iSpy",ChartID(),1)==INVALID_HANDLE) 
      { Print("Error in setting of spy on EURUSD"); return(true);}
   if(iCustom("USDJPY",PERIOD_M1,"iSpy",ChartID(),2)==INVALID_HANDLE) 
      { Print("Error in setting of spy on USDJPY"); return(true);}
      
   Print("Spys ok, waiting for data...");
   //---
   return(0);
  }
  
//+------------------------------------------------------------------+
//| The Standard event handler.                                      |
//| See MQL5 Reference for the details.                              |
//|                                                                  |
//| In this case it is used for decoding of spy messages, sent by    |
//| iSPY spy indicator                                               |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,         // event id:
                                        // if id-CHARTEVENT_CUSTOM=0 - "initialization" event
                  const long&   lparam, // chart period
                  const double& dparam, // price
                  const string& sparam  // symbol
                 )
  {
   if(id>=CHARTEVENT_CUSTOM)      
     {
      Print(TimeToString(TimeCurrent(),TIME_SECONDS)," -> id=",id-CHARTEVENT_CUSTOM,":  ",sparam," ",EnumToString((ENUM_TIMEFRAMES)lparam)," price=",dparam);
     }
  }
//+------------------------------------------------------------------+
