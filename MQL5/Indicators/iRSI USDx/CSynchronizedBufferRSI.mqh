//+------------------------------------------------------------------+
//|                                       CSynchronizedBufferRSI.mqh |
//|                                            Copyright 2010, Lizar |
//|                            https://login.mql5.com/ru/users/Lizar |
//|                                              Revision 2011.01.03 |
//+------------------------------------------------------------------+

//+------------------------------------------------------------------+
//| CSynchronizedBufferRSI class                                     |
//| Purpose: Class for creation of synchronized RSI buffers          |
//+------------------------------------------------------------------+
class CSynchronizedBufferRSI
  {
   protected:
      string            m_symbol;      // symbol
      ENUM_TIMEFRAMES   m_period;      // period
      int               m_handle;      // handle
      int               m_rsi_period;  // averaging period
      int               m_rsi_count;   // number of bars for the calculation
      bool              m_init_flag;   // initialization flag

   public:
      double   buffer[];               // buffer of the indicator
      //--- class constructor and destructor:
      void CSynchronizedBufferRSI();
      void ~CSynchronizedBufferRSI();
      //--- initialization methods:
      bool Init(int n,string symbol,int rsi_count,int rsi_period);
      //--- data update methods:
      void RefreshBuffer();
      void Refresh(int bar=0);
      //--- returns initialization flag
      bool GetInit()   {return(m_init_flag);}
  };

//+------------------------------------------------------------------+
//| Class constructor                                                |
//| INPUT:  no.                                                      |
//| OUTPUT: no.                                                      |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
void CSynchronizedBufferRSI::CSynchronizedBufferRSI()
  {
   m_init_flag=false;
   m_handle=INVALID_HANDLE;
   m_symbol=_Symbol;
   m_period=_Period;
  }
  
//+------------------------------------------------------------------+
//| Class destructor                                                 |
//| INPUT:  no.                                                      |
//| OUTPUT: no.                                                      |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
void CSynchronizedBufferRSI::~CSynchronizedBufferRSI()
  {
   //--- Release indicator
   if(m_handle!=INVALID_HANDLE) IndicatorRelease(m_handle);  
  }
    
//+------------------------------------------------------------------+
//| Method of initialization of indicator buffer                     |
//| INPUT:  n              - buffer index;                           |
//|         symbol         - symbol;                                 |
//|         rsi_count      - number of bars for the calculation;     |
//|         rsi_period     - averaging period                        |
//| OUTPUT: true  - if successful                                    |
//|         false - if error                                         |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
bool CSynchronizedBufferRSI::Init(int n,string symbol,int rsi_count,int rsi_period)
  {   
   //--- protected data initialization
   m_rsi_count=rsi_count;
   m_symbol=symbol;

   //--- indicator settings:
   ArraySetAsSeries(buffer,true);                     // set indexation as time series
   PlotIndexSetInteger(n,PLOT_DRAW_TYPE,DRAW_LINE);   // draw as a line
   PlotIndexSetInteger(n,PLOT_LINE_STYLE,STYLE_DOT);  // dot style
   PlotIndexSetString (n,PLOT_LABEL,"RSI "+m_symbol); // plot label
        
   //--- RSI indicator initialization
   if(m_handle==INVALID_HANDLE)
     {
      m_handle=iRSI(m_symbol,m_period,rsi_period,PRICE_CLOSE);
      if(m_handle==INVALID_HANDLE)
        {
         Print(__FUNCTION__," ",m_symbol," Error in creation of RSI indicator: ", GetLastError());
         return(false);
        }
     }

   return(true);
  }

//+------------------------------------------------------------------+
//| Initialization/update of the indicator's buffer                  |
//| INPUT:  no.                                                      |
//| OUTPUT: no.                                                      |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
void CSynchronizedBufferRSI::RefreshBuffer()
  {      
   m_init_flag=true;
   ArrayInitialize(buffer,EMPTY_VALUE); 
   for(int bar=m_rsi_count-1; bar>=0; bar--) Refresh(bar);     
   return;
  }
  
//+------------------------------------------------------------------+
//| Refresh method                                                   |
//| INPUT:  bar   - bar index                                        |
//| OUTPUT: no.                                                      |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
void CSynchronizedBufferRSI::Refresh(int bar=0)
  {
   buffer[bar]=EMPTY_VALUE; // initialization of the bar
     
   //--- get bar time of the current chart
   datetime time[1];      
   if(CopyTime(_Symbol,_Period,bar,1,time)!=1) return; // if error, wait for a new tick/bar

   //--- get the data of RSI indicator for the current bar on the chart:
   double value[1];
   if(CopyBuffer(m_handle,0,time[0],time[0],value)!=1) return; // If error, wait for a new tick/bar ...

   buffer[bar]=value[0];
   return;
  }