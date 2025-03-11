//+------------------------------------------------------------------+
//|                                                         iSpy.mq5 |
//|                                            Copyright 2010, Lizar |
//|                                               lizar-2010@mail.ru |
//+------------------------------------------------------------------+
#define VERSION         "1.00 Build 2 (26 Dec 2010)"

#property copyright   "Copyright 2010, Lizar"
#property link        "https://login.mql5.com/ru/users/Lizar"
#property version     VERSION
#property description "iSpy agent-indicator. If you want to get ticks, attach it to the chart"
#property indicator_chart_window

input long            chart_id=0;        // chart id
input ushort          custom_event_id=0; // event id

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate (const int rates_total,      // size of price[] array
                 const int prev_calculated,  // bars, calculated at the previous call
                 const int begin,            // starting index of data
                 const double& price[]       // array for the calculation
   )
  {
   double price_current=price[rates_total-1];

   //--- Initialization:
   if(prev_calculated==0) 
     { // Generate and send "Initialization" event
      EventChartCustom(chart_id,0,(long)_Period,price_current,_Symbol);
      return(rates_total);
     }
   
   // When the new tick, let's generate the "New tick" custom event
   // that can be processed by Expert Advisor or indicator
   EventChartCustom(chart_id,custom_event_id+1,(long)_Period,price_current,_Symbol);
   
   //--- return value of prev_calculated for next call
   return(rates_total);
  }
//+------------------------------------------------------------------+
