import streamlit as st
import altair as alt
import numpy as np
import pickle
import pandas as pd; import pandas_datareader as web; import numpy as np
import matplotlib.pyplot as plt; 
import yahoofinance as yf
import datetime
basepath = 'C:\\Users\\aumja\\Google Drive\\Learning\\Projects\\StockappStreamlit'
#%%
#symbol='MSFT'
@st.cache(allow_output_mutation=True)
def getdata(symbol):
    stockraw = web.DataReader(symbol, 'yahoo')
    return stockraw
#period=600   
#stockraw = getdata('NFLX')
def processdata(stockraw,period):
    startdt = pd.to_datetime((pd.to_datetime('today')+pd.Timedelta(-period,'d')).strftime('%Y-%m-%d'))
    enddt = pd.to_datetime((pd.to_datetime('today')+pd.Timedelta(1,'d')).strftime('%Y-%m-%d'))
    stockraw = pd.DataFrame(stockraw['Adj Close'])
    stockraw.fillna(method='ffill',limit=1,inplace=True)
    
    EMA200 = stockraw.ewm(200,min_periods=200).mean()
    EMA200.rename(columns=dict(zip(EMA200.columns,[x+'-EMA200' for x in EMA200.columns])),inplace=True)
    
    EMA50 = stockraw.ewm(50,min_periods=200).mean()
    EMA50.rename(columns=dict(zip(EMA50.columns,[x+'-EMA50' for x in EMA50.columns])),inplace=True)
    
    PCTCHG = stockraw.pct_change()
    PCTCHG.rename(columns=dict(zip(PCTCHG.columns,[x+'-PCTCHG' for x in PCTCHG.columns])),inplace=True)
    
    stockraw = stockraw.join(EMA200).join(EMA50).join(PCTCHG) 
    
    stockraw = stockraw[(stockraw.index>startdt)&(stockraw.index<=enddt)]
    return stockraw



#stk='AAL'
def getlatestfinancials(stk):
  
  bsqtr = yf.BalanceSheetQuarterly(stk).to_dfs()

  LatestBsDt = bsqtr['Assets'].loc['Cash And Cash Equivalents'].index[0]

  # Cash balances
  invst = bsqtr['Assets'].loc['Short Term Investments'][0]
  if invst == '-':
    invst = 0
  TotalCash = bsqtr['Assets'].loc['Cash And Cash Equivalents'][0] + invst
  
  # Long term debt
  TotalLtDebt = bsqtr['Liabilities'].loc['Long Term Debt'][0]

  # Total equity
  TotalEquity = bsqtr['Equity'].loc['Total Stockholder Equity'][0]

  # Total revenue TTM
  incqtr = yf.IncomeStatementQuarterly(stk).to_dfs()
  TotalRev = incqtr['Revenue'].loc['Total Revenue'].sum()
  TotalOpInc = incqtr['Operating Expenses'].loc['Operating Income or Loss'].sum()
  TotalNetInc = incqtr['Net Income'].loc['Net Income Applicable To Common Shares'].sum()
  TotalEBIT = incqtr['Income from Continuing Operations'].loc['Earnings Before Interest and Taxes'].sum()
  TotalNetIncContOps = incqtr['Income from Continuing Operations'].loc['Net Income From Continuing Ops'].sum()

  # Cashflow TTM
  cfqtr = yf.CashFlowQuarterly(stk).to_dfs()
  TotalOprCF = cfqtr['Operating activities'].loc['Total cash flow from operating activities'].sum()
  vals=  [stk,LatestBsDt,TotalCash,TotalLtDebt,TotalEquity,TotalRev,TotalOpInc,TotalNetInc,TotalEBIT,TotalNetIncContOps,TotalOprCF]
  heads = ['stock','LatestBsDt','TotalCash','TotalLtDebt','TotalEquity','TotalRev','TotalOpInc','TotalNetInc','TotalEBIT','TotalNetIncContOps','TotalOprCF']
      
  return dict(zip(heads,vals))
#getlatestfinancials('AAL')
  #%%

st.markdown("""
            <div style = 'background-color:#7178ED;padding=15px;'>
            <h2> Welcome to the stock tracker app </h2>
            </div>
            """,unsafe_allow_html=True)

stk = st.sidebar.text_input("Enter stock symbol name").upper()
period=st.sidebar.slider('Enter number of days',min_value=30,max_value=3000,value=600,step=30)
if stk != '':
    stockraw = getdata(stk)
#if st.sidebar.checkbox("Get chart"):
    st.write("Selected stock: {}".format(stk))
    stockdata = processdata(stockraw,period)
    stockdata.reset_index(inplace=True)
    minprice = stockdata['Adj Close'].min()
    maxprice = stockdata['Adj Close'].max()
    #st.write(stockdata.tail(10))
    stockdata1=pd.melt(stockdata,id_vars=['Date'],value_vars=['Adj Close','Adj Close-EMA50','Adj Close-EMA200'])
    lst = stockdata1.sort_values(by=['Date','variable'],ascending=False)['value'].tolist()
    #st.markdown('Cyan:<span style=  "background-color:#00FEFE">CYANTEXT</span>',unsafe_allow_html=True)
    clprice = lst[2]
    ema50 = lst[0]
    ema200 = lst[1]
    if (clprice>ema200) & (clprice>ema50):
        col = "background-color:#0CFF00" # GREEN
    elif (clprice>ema200) & (clprice<ema50):
        col = "background-color:#FFC300" # ORANGE
    elif (clprice<ema200) & (clprice<ema50):
        col =  "background-color:#62F67D"
    elif (clprice<ema200) & (clprice>ema50):
        col= "background-color:#F70C16" # RED
    else:
        col = "background-color:#FBFF00" # YELLOS
        
    st.markdown("""
                Closing price: <span style= {}>**{:.2f}**</span>, 
                50 EMA: <span style= {}>**{:.2f}**</span>, 
                200 EMA: <span style= {}>**{:.2f}**</span>
                """.format(col,clprice,col,ema50,col,ema200),unsafe_allow_html=True)
    #st.write(stockdata.tail(20))
    #st.markdown("### Latest data:")
    st.markdown("### Plotted chart")
    c = alt.Chart(stockdata1).mark_line().encode(x='Date',
                 y=alt.Y('value',scale=alt.Scale(domain=[minprice,maxprice],clamp=True)),
                 #color=alt.Color('variable',legend=alt.Legend(orient='bottom',title='')),
                 color=alt.Color('variable',legend=alt.Legend(orient='bottom',title='')),
                 strokeDash='variable').interactive()
    
    st.altair_chart(c,use_container_width=True)


if st.sidebar.checkbox("Get Financials"):  
    dffin = pd.read_excel('C:\\Users\\aumja\\Google Drive\\Investment\\Analysis\\StockchartsUS\stockfinancials.xlsx')
    dffin.columns=['Company Name','Symbol','Industry','Financials as of','Revenue','EBIT','Operating Income','Net Income','Net Income from Continuing Operations','Total Operating Cashflow','Total Long Term Debt']
    st.table(dffin[dffin.Symbol==stk].T)
    #dffin.assign(tmp='').set_index('tmp',inplace=True)
    #st.table(dffin[dffin.Symbol==stk][dffin.columns[:4]])
    #st.table(dffin[dffin.Symbol==stk][dffin.columns[4:9]])
    #st.table(dffin[dffin.Symbol==stk][dffin.columns[9:12]])

if st.sidebar.checkbox("Enter/view comments"):
    #prevcomments = {'NFLX':['2020-08-10','My previous comments here'],'MSFT':['2020-08-10','My previous comments']}
    comments = pickle.load(open(basepath+'stockcomments.pkl','rb'))
    comment = comments.get(stk,'')
    txtarea = st.sidebar.text_area("Comments",value=comment)
    comments[stk] = txtarea
    pickle.dump(comments,open(basepath+'stockcomments.pkl','wb'))

#dfvirtualtrades = pd.DataFrame(None,columns=['Symbol','Quantity','Buydt','Buyprice','Selldt','Sellprice','stoploss','traderationale','CMP','Netgain'])
#dfvirtualtrades.to_pickle(basepath+'virtualtrades.pkl')

if st.sidebar.checkbox("Enter trade in virtual portfolio"):
    dfvirtualtrades = pd.read_pickle(basepath+'virtualtrades.pkl')   
    numrecords = len(dfvirtualtrades)
    #stk = 'MSFT'
    stoploss = st.sidebar.number_input('Enter stoploss',value=0)
    rationale = st.sidebar.text_input('Enter trade rationale',value='')
    st.write("Existing trades on "+stk)
    trades = st.write(dfvirtualtrades[dfvirtualtrades['Symbol']==stk])
    if st.sidebar.button("Buy"):
        cmp = round(stockraw.tail(1)['Adj Close'][0],2)
        currdt = stockraw.tail(1).index[0].strftime('%m/%d/%Y')
        qty = round(10000/cmp,0)
        dfvirtualtrades.loc[numrecords+1] = [stk,qty,currdt,cmp,np.NaN,np.NaN,stoploss,rationale,np.NaN,np.NaN]
        trades = st.write(dfvirtualtrades[dfvirtualtrades['Symbol']==stk])
        dfvirtualtrades.to_pickle(basepath+'virtualtrades.pkl')
    if st.sidebar.button("Sell"):
        cmp = round(stockraw.tail(1)['Adj Close'][0],2)
        currdt = stockraw.tail(1).index[0].strftime('%m/%d/%Y')
        qty = round(10000/cmp,0)
        dfvirtualtrades.loc[numrecords+1] = [stk,qty,np.NaN,np.NaN,currdt,cmp,stoploss,rationale,np.NaN,np.NaN]
        trades = st.write(dfvirtualtrades[dfvirtualtrades['Symbol']==stk])
        dfvirtualtrades.to_pickle(basepath+'virtualtrades.pkl')
                           
    