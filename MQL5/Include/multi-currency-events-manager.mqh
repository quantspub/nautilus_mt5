#property strict

#include <Arrays\ArrayLong.mqh>
//--- input parameters
#define MCEA_WORKER_REGISTER 9
#define MCEA_WORKER_REGISTER_REPLY 10
#define MCEA_MANAGER_REGISTER 11
#define MCEA_MANAGER_REGISTER_REPLY 12
#define MCEA_WORKER_TICK 13

enum MCEA_MODE{
   MCEA_WORKER,
   MCEA_MANAGER
};

input MCEA_MODE     InpMode=MCEA_WORKER;


class IdSet : public CArrayLong
{
   public: 
   bool Add(const long chart_id)
   {
      for(int i=0;i<this.Total();i++)
         if(this[i] == chart_id)
            return false;
      return CArrayLong::Add(chart_id);
   }
   void clean()
   {
      for(int i=this.Total()-1;i>=0;i--)
         if(!_find(this[i]))
            this.Delete(i);
   }
protected:
   bool _find(long id)
   {
      for(long ch=ChartFirst();ch>=0;ch=ChartNext(ch))
         if(id==ch)
            return true;
      return false;
   }
};

//-- GLOBALS
IdSet workers, managers;
struct Q{long id;datetime time;} queue;
//+------------------------------------------------------------------+
int OnInit()
{
   for(long ch=ChartFirst(); ch>=0; ch=ChartNext(ch))
      if(ch != ChartID())
         if(InpMode==MCEA_WORKER)
            EventChartCustom(ch,MCEA_WORKER_REGISTER,ChartID(),0.0,_Symbol);
         else
            EventChartCustom(ch,MCEA_MANAGER_REGISTER,ChartID(),0.0,_Symbol);
   return(INIT_SUCCEEDED);
}
//+------------------------------------------------------------------+
void OnTick()
{
   if(InpMode==MCEA_WORKER)
   { 
      for(int i=managers.Total()-1;i>=0;i--)
         if(!EventChartCustom(managers[i],MCEA_WORKER_TICK,ChartID(),0.0,TimeToString(
            TimeCurrent(),TIME_DATE|TIME_MINUTES|TIME_SECONDS
         )))
            clean_arrays();
   }
   else if(queue.id >= 0)
   {
      if(TimeCurrent()==queue.time) 
         printf("tick-event coming from %s",ChartSymbol(queue.id));
      queue.id = -1;
   }
   else
   {
      Print("***TICK-EVENT ON THIS CHART***");
   }
}
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
{
   if(InpMode == MCEA_MANAGER)
   {
      if(id==CHARTEVENT_CUSTOM+MCEA_WORKER_REGISTER)
      {
         workers.Add(lparam);
         if(!EventChartCustom(lparam,MCEA_WORKER_REGISTER_REPLY,ChartID(),0.0,_Symbol))
            clean_arrays();
      }
      else if(id==CHARTEVENT_CUSTOM+MCEA_MANAGER_REGISTER_REPLY)
      {
         workers.Add(lparam);
      }
      else if(id==CHARTEVENT_CUSTOM+MCEA_WORKER_TICK)
      {
         queue.id = lparam;
         queue.time = StringToTime(sparam);
         OnTick();
         return;
      }
   } 
   else if(InpMode == MCEA_WORKER)
   {
      if(id==CHARTEVENT_CUSTOM+MCEA_MANAGER_REGISTER)
      {
         managers.Add(lparam);
         if(!EventChartCustom(lparam,MCEA_MANAGER_REGISTER_REPLY,ChartID(),0.0,_Symbol))
            clean_arrays();
      }
      else if(id==CHARTEVENT_CUSTOM+MCEA_WORKER_REGISTER_REPLY)
      {
         managers.Add(lparam);
      }
   }
}
//+------------------------------------------------------------------+

void clean_arrays()
{
   workers.clean();
   managers.clean();
}
