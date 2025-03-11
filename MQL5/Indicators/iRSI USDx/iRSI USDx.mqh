//+------------------------------------------------------------------+
//|                                                    iRSI USDx.mqh |
//|                                            Copyright 2010, Lizar |
//|                            https://login.mql5.com/ru/users/Lizar |
//|                                              Revision 2010.01.03 |
//+------------------------------------------------------------------+

// Structure for serve information on symbol and its wait in the basket
struct stCurrencyWeight
{
   string symbol;   // Symbol
   double weight;   // Weight
};

#include "CSynchronizedBufferRSI.mqh"

//+------------------------------------------------------------------+
//| Class CRSIUSDx                                                   |
//| Purpose: Class, designed for synchronized RSI buffers            |
//| for each symbol of the multicurrency RSI indicator of USD index  |
//+------------------------------------------------------------------+
class CRSIUSDx : public CSynchronizedBufferRSI
  {
   protected:
      double   m_currency_weight;   // weight in the basket
      int      m_currency_base_flag;//  0 - base currency
                                    //  1 - profit currency
                                    // -1 - invalid currency pair
   public:
      //--- initialization methods:
      bool Init(int n,int rsi_count, int rsi_period, string currency_index);
      //--- methods for access to protected data:
      void     SetCurrencyAndWeight(string symbol, double weight);
      double   GetWeight() {return(m_currency_weight);}
      int      GetFlag()   {return(m_currency_base_flag);}
  };
  
//+------------------------------------------------------------------+
//| Method for setting the symbol and weight                         |
//| in multicurrency basket                                          |
//| INPUT:  symbol - symbol                                          |
//|         weight - weight in the basket                            |
//| OUTPUT: no.                                                      |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
void CRSIUSDx::SetCurrencyAndWeight(string symbol, double weight)
  {
   m_symbol=symbol;
   m_currency_weight=weight;
  }
  
//+------------------------------------------------------------------+
//| Method for initialization of RSI indicator                       |
//| INPUT:  n              - buffer index;                           |
//|         currency_index - currency index;                         |
//|         rsi_count      - number of bars for the calculation      |
//|         rsi_period     - averaging period                        |
//| OUTPUT: true  - if successful                                    |
//|         false - if error                                         |
//| REMARK: no.                                                      |
//+------------------------------------------------------------------+
bool CRSIUSDx::Init(int n,int rsi_count, int rsi_period, string currency_index)
  {   
   
   //--- Check the base currency:
   if(currency_index==SymbolInfoString(m_symbol,SYMBOL_CURRENCY_BASE)) m_currency_base_flag=0;
   else if(currency_index==SymbolInfoString(m_symbol,SYMBOL_CURRENCY_PROFIT)) m_currency_base_flag=1;
        else m_currency_base_flag=-1;

   //--- Initialization of the indicator
   Init(n,m_symbol,rsi_count,rsi_period);
   
   return(true);
  }