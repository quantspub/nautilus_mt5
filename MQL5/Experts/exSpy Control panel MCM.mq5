//+------------------------------------------------------------------+
//|                                      exSpy Control panel MCM.mq5 |
//|                                            Copyright 2010, Lizar |
//|                            https://login.mql5.com/ru/users/Lizar |
//+------------------------------------------------------------------+
#define VERSION       "1.00 Build 1 (28 Dec 2010)"

#property copyright   "Copyright 2010, Lizar"
#property link        "https://login.mql5.com/ru/users/Lizar"
#property version     VERSION
#property description "Example of Spy agent of MCM Control panel"

//+------------------------------------------------------------------+
//| Enumeration of the events,                                       |
//| It allows to define the available events                         |
//| The events can be combined using the "|" char (OR operation)     |
//+------------------------------------------------------------------+
enum ENUM_CHART_EVENT_SYMBOL
  {
   CHARTEVENT_INIT      =0,          // "Initialization" event
   CHARTEVENT_NO        =0,          // No events

   CHARTEVENT_NEWBAR_M1 =0x00000001, // "New bar" event on M1 chart
   CHARTEVENT_NEWBAR_M2 =0x00000002, // "New bar" event on M2 chart
   CHARTEVENT_NEWBAR_M3 =0x00000004, // "New bar" event on M3 chart
   CHARTEVENT_NEWBAR_M4 =0x00000008, // "New bar" event on M4 chart
   
   CHARTEVENT_NEWBAR_M5 =0x00000010, // "New bar" event on M5 chart
   CHARTEVENT_NEWBAR_M6 =0x00000020, // "New bar" event on M6 chart
   CHARTEVENT_NEWBAR_M10=0x00000040, // "New bar" event on M10 chart
   CHARTEVENT_NEWBAR_M12=0x00000080, // "New bar" event on M12 chart
   
   CHARTEVENT_NEWBAR_M15=0x00000100, // "New bar" event on M15 chart
   CHARTEVENT_NEWBAR_M20=0x00000200, // "New bar" event on M20 chart
   CHARTEVENT_NEWBAR_M30=0x00000400, // "New bar" event on M30 chart
   CHARTEVENT_NEWBAR_H1 =0x00000800, // "New bar" event on H1 chart
   
   CHARTEVENT_NEWBAR_H2 =0x00001000, // "New bar" event on H2 chart
   CHARTEVENT_NEWBAR_H3 =0x00002000, // "New bar" event on H3 chart
   CHARTEVENT_NEWBAR_H4 =0x00004000, // "New bar" event on H4 chart
   CHARTEVENT_NEWBAR_H6 =0x00008000, // "New bar" event on H6 chart
   
   CHARTEVENT_NEWBAR_H8 =0x00010000, // "New bar" event on H8 chart
   CHARTEVENT_NEWBAR_H12=0x00020000, // "New bar" event on H12 chart
   CHARTEVENT_NEWBAR_D1 =0x00040000, // "New bar" event on D1 chart
   CHARTEVENT_NEWBAR_W1 =0x00080000, // "New bar" event on W1 chart
     
   CHARTEVENT_NEWBAR_MN1=0x00100000, // "New bar" event on MN1 chart
   CHARTEVENT_TICK      =0x00200000, // "New tick" event
   
   CHARTEVENT_ALL       =0xFFFFFFFF, // All events
  };

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {   
   if(iCustom("GBPUSD",PERIOD_M1,"Spy Control panel MCM",ChartID(),0,CHARTEVENT_TICK|CHARTEVENT_NEWBAR_M5)==INVALID_HANDLE) 
      { Print("Error in setting of spy on GBPUSD"); return(true);}
   if(iCustom("EURUSD",PERIOD_M1,"Spy Control panel MCM",ChartID(),1,CHARTEVENT_NEWBAR_M1|CHARTEVENT_TICK)==INVALID_HANDLE) 
      { Print("Error in setting of spy on EURUSD"); return(true);}
   if(iCustom("USDJPY",PERIOD_M1,"Spy Control panel MCM",ChartID(),2,CHARTEVENT_TICK)==INVALID_HANDLE) 
      { Print("Error in setting of spy on USDJPY"); return(true);}
   if(iCustom("USDCHF",PERIOD_M1,"Spy Control panel MCM",ChartID(),2,CHARTEVENT_TICK)==INVALID_HANDLE) 
      { Print("Error in setting of spy on USDJPY"); return(true);}
   if(iCustom("USDSEK",PERIOD_M1,"Spy Control panel MCM",ChartID(),2,CHARTEVENT_TICK)==INVALID_HANDLE) 
      { Print("Error in setting of spy on USDJPY"); return(true);}
   if(iCustom("USDCAD",PERIOD_M1,"Spy Control panel MCM",ChartID(),2,CHARTEVENT_TICK)==INVALID_HANDLE) 
      { Print("Error in setting of spy on USDJPY"); return(true);}
      
   Print("Spy agents ok, waiting for events...");
   //---
   return(0);
  }
  
//+------------------------------------------------------------------+
//| The Standard event handler.                                      |
//| See MQL5 Reference for the details.                              |
//|                                                                  |
//| In this case it is used for decoding of spy messages, sent by    |
//| iSPY Control panel MCM indicator.                                |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,         // event id
                  const long&   lparam, // event flag
                                        // the flag is a bit mask of ENUM_CHART_EVENT_SYMBOL enumeration.
                  const double& dparam, // price
                  const string& sparam  // symbol
                 )
  {
   if(id>=CHARTEVENT_CUSTOM)      
     {
      Print(TimeToString(TimeCurrent(),TIME_SECONDS)," -> id=",id-CHARTEVENT_CUSTOM,":  ",sparam," ",EnumToString((ENUM_CHART_EVENT_SYMBOL)lparam)," price=",dparam);
     }
  }
 
