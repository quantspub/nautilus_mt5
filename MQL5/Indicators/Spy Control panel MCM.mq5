//+------------------------------------------------------------------+
//|                                        Spy Control panel MCM.mq5 |
//|                                            Copyright 2010, Lizar |
//|                            https://login.mql5.com/ru/users/Lizar |
//+------------------------------------------------------------------+
#define VERSION       "1.00 Build 3 (26 Dec 2010)"

#property copyright   "Copyright 2010, Lizar"
#property link        "https://login.mql5.com/ru/users/Lizar"
#property version     VERSION
#property description "The spy indicator of MCM Control panel"
#property description "It generates the NewBar and/or NewTick custom events for a chart"

#property indicator_chart_window
  
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


input long                    chart_id;                         // chart id
input ushort                  custom_event_id;                  // event id
input ENUM_CHART_EVENT_SYMBOL flag_event=CHARTEVENT_NO;         // flag with events mask.

MqlDateTime time, prev_time;

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate (const int rates_total,      // size of price[] array
                 const int prev_calculated,  // bars, calculated at the previous call
                 const int begin,            // starting index of data
                 const double& price[]       // array for calculation
   )
  {  
   double price_current=price[rates_total-1];

   TimeCurrent(time);
   
   if(prev_calculated==0)
     {
      EventCustom(CHARTEVENT_INIT,price_current);
      prev_time=time; 
      return(rates_total);
     }
   
//--- new tick
   if((flag_event & CHARTEVENT_TICK)!=0) EventCustom(CHARTEVENT_TICK,price_current);       

//--- check change time
   if(time.min==prev_time.min && 
      time.hour==prev_time.hour && 
      time.day==prev_time.day &&
      time.mon==prev_time.mon) return(rates_total);

//--- new minute
   if((flag_event & CHARTEVENT_NEWBAR_M1)!=0) EventCustom(CHARTEVENT_NEWBAR_M1,price_current);     
   if(time.min%2 ==0 && (flag_event & CHARTEVENT_NEWBAR_M2)!=0)  EventCustom(CHARTEVENT_NEWBAR_M2,price_current);
   if(time.min%3 ==0 && (flag_event & CHARTEVENT_NEWBAR_M3)!=0)  EventCustom(CHARTEVENT_NEWBAR_M3,price_current); 
   if(time.min%4 ==0 && (flag_event & CHARTEVENT_NEWBAR_M4)!=0)  EventCustom(CHARTEVENT_NEWBAR_M4,price_current);      
   if(time.min%5 ==0 && (flag_event & CHARTEVENT_NEWBAR_M5)!=0)  EventCustom(CHARTEVENT_NEWBAR_M5,price_current);     
   if(time.min%6 ==0 && (flag_event & CHARTEVENT_NEWBAR_M6)!=0)  EventCustom(CHARTEVENT_NEWBAR_M6,price_current);     
   if(time.min%10==0 && (flag_event & CHARTEVENT_NEWBAR_M10)!=0) EventCustom(CHARTEVENT_NEWBAR_M10,price_current);      
   if(time.min%12==0 && (flag_event & CHARTEVENT_NEWBAR_M12)!=0) EventCustom(CHARTEVENT_NEWBAR_M12,price_current);      
   if(time.min%15==0 && (flag_event & CHARTEVENT_NEWBAR_M15)!=0) EventCustom(CHARTEVENT_NEWBAR_M15,price_current);      
   if(time.min%20==0 && (flag_event & CHARTEVENT_NEWBAR_M20)!=0) EventCustom(CHARTEVENT_NEWBAR_M20,price_current);      
   if(time.min%30==0 && (flag_event & CHARTEVENT_NEWBAR_M30)!=0) EventCustom(CHARTEVENT_NEWBAR_M30,price_current);      
   if(time.min!=0) {prev_time=time; return(rates_total);}
//--- new hour
   if((flag_event & CHARTEVENT_NEWBAR_H1)!=0) EventCustom(CHARTEVENT_NEWBAR_H1,price_current);
   if(time.hour%2 ==0 && (flag_event & CHARTEVENT_NEWBAR_H2)!=0)  EventCustom(CHARTEVENT_NEWBAR_H2,price_current);
   if(time.hour%3 ==0 && (flag_event & CHARTEVENT_NEWBAR_H3)!=0)  EventCustom(CHARTEVENT_NEWBAR_H3,price_current);      
   if(time.hour%4 ==0 && (flag_event & CHARTEVENT_NEWBAR_H4)!=0)  EventCustom(CHARTEVENT_NEWBAR_H4,price_current);      
   if(time.hour%6 ==0 && (flag_event & CHARTEVENT_NEWBAR_H6)!=0)  EventCustom(CHARTEVENT_NEWBAR_H6,price_current);      
   if(time.hour%8 ==0 && (flag_event & CHARTEVENT_NEWBAR_H8)!=0)  EventCustom(CHARTEVENT_NEWBAR_H8,price_current);      
   if(time.hour%12==0 && (flag_event & CHARTEVENT_NEWBAR_H12)!=0) EventCustom(CHARTEVENT_NEWBAR_H12,price_current);      
   if(time.hour!=0) {prev_time=time; return(rates_total);}
//--- new day
   if((flag_event & CHARTEVENT_NEWBAR_D1)!=0) EventCustom(CHARTEVENT_NEWBAR_D1,price_current);      
 //--- new week
   if(time.day_of_week==1 && (flag_event & CHARTEVENT_NEWBAR_W1)!=0) EventCustom(CHARTEVENT_NEWBAR_W1,price_current);      
 //--- new month
   if(time.day==1 && (flag_event & CHARTEVENT_NEWBAR_MN1)!=0) EventCustom(CHARTEVENT_NEWBAR_MN1,price_current);      
   prev_time=time;
//--- return value of prev_calculated for next call
   return(rates_total);
  }
//+------------------------------------------------------------------+

void EventCustom(ENUM_CHART_EVENT_SYMBOL event,double price)
  {
   EventChartCustom(chart_id,custom_event_id,(long)event,price,_Symbol);
   return;
  }