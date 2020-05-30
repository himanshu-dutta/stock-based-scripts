#!/usr/bin/env python
# coding: utf-8


import os
# import winsound
import numpy as np
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import signal

def keyboardInterruptHandler(signal, frame):
    exit(0)

signal.signal(signal.SIGINT, keyboardInterruptHandler)


notific = 'notify.wav'

if not os.path.exists('Data'):
    os.mkdir('Data')


def notify():
    # None
    # os.system("mpg123 " + notific)
    winsound.PlaySound(notific, winsound.SND_FILENAME)   


class Change:
    def __init__(self,now_mark,then_mark,duration=365,now_factor=100, then_factor=100,drop=True,notify=False):
        self.notify = notify
        self.duration = duration
        self.drop = drop
        self.now = now_mark; self.then = then_mark;self.now_factor = now_factor;
        self.then_factor = then_factor;
    def process(self,data):
        date = None
        i=0
        while True:
            date = (datetime.today() - timedelta(days=self.duration+i)).strftime('%Y-%m-%d')
            if data[data['date'] == date ].any().all(): break
            elif i==31: return False
            else: i+=1
        less = self.now; grt = self.then
        less_f = self.now_factor; grt_f = self.then_factor
        if not self.drop:
            less = self.then; grt = self.now
            less_f = self.then_factor; grt_f = self.now_factor
        date = data[data['date'] == date].index[0]+1
        if len(data[:date][data[less]*(1-(less_f/100.0)) < data[grt]*(grt_f/100.0)]) == len(data[:date]):
            if self.notify: notify()
            return True
        else: return False
    def name(self):
        return 'Change'


class Compare:
    def __init__(self,now_mark,then_mark,agg = False,when=None,date=False,now_factor=100, then_factor=100,drop=True,notify=False):
        self.now_mark = now_mark;self.then_mark = then_mark; self.now_factor = now_factor;
        self.then_factor = then_factor;
        if date and agg: print("Error! Can't use both."); return None;
        if date: self.when = when; self.date = True
        else: self.date = False
        self.agg = agg
        self.drop = drop
        self.notify = notify
    def process(self,data):
        # print(data)
        if self.agg:
            if self.agg == 'max': then = data[self.then_mark].max()
            elif self.agg == 'min': then = data[self.then_mark].min()
            elif self.agg == 'avg': then = data[self.then_mark].mean()
            else: return False
        if self.date:
            i=0
            index=None
            while True:
                index = (datetime.today() - timedelta(days=self.when+i)).strftime('%Y-%m-%d')
                if data[data['date'] == index].any().all(): break
                elif i==31: return False
                else: i+=1
            then = list(data[data['date'] == index][self.then_mark])[0]
        now = data.iloc[0][self.now_mark]
        print('Then:', then)
        print('Now:',now)
        if self.drop:
            check = (now * (self.now_factor/100)) < (then * (self.then_factor/100))
            if check and self.notify: notify()
            return check
        check = (now * (self.now_factor/100)) > (then * (self.then_factor/100))
        if check and self.notify: notify()
        return check
    def name(self):
        return 'Compare'


def Monitor(filters,symbols):
    all_f = []
    fltrs = [np.zeros(1)]*len(filters)
    not_avail = []
    for symbol in symbols:
        try:
            print(symbol)
            stock = yf.Ticker(symbol)
            daily = symbol+ '_daily_' + datetime.today().strftime('%Y%m%d')+'.xlsx'
            intra = symbol+ '_intra_' + datetime.today().strftime('%Y%m%d')+'.xlsx'
            if os.path.exists('Data/'+daily):
                data_daily = pd.read_excel('Data/'+daily)
            else:
                data_daily = stock.history(period='5y',interval='1d')[::-1].reset_index()
                if len(data_daily) == 0: not_avail.append(symbol); continue;
                data_daily = data_daily.loc[:,['Date','Open','Close','High','Low','Volume']]
                with pd.ExcelWriter(os.path.join('Data/'+daily)) as writer:
                    data_daily.to_excel(writer, index=False)
            if os.path.exists('Data/'+intra):
                data_intra = pd.read_excel('Data/'+intra)
            else:       
                data_intra = stock.history(period='1d',interval='1m')[::-1].reset_index()
                if len(data_intra) == 0: continue
                data_intra['Datetime'] = data_intra['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S"')
                data_intra = data_intra.loc[:,['Datetime', 
                                               'Open', 
                                               'Close', 
                                               'High', 
                                               'Low', 
                                               'Volume']]
                data_intra.Datetime
                with pd.ExcelWriter(os.path.join('Data/'+intra)) as writer:
                    data_intra.to_excel(writer, index=False)
#             print(data_daily,data_intra)
            data_daily.rename(columns={'Date' : 'date',
                                       'Open':'open',
                                      'High':'high',
                                      'Low':'low',
                                    'Close':'close',
                                    'Volume': 'volumne'}, 
                             inplace=True)

            data_intra.rename(columns={'Datetime' : 'date',
                                       'Open':'open',
                                      'High':'high',
                                      'Low':'low',
                                    'Close':'close',
                                    'Volume': 'volumne'}, 
                             inplace=True)
            # print(data_daily)
            check_all = True
            for fltr in range(len(filters)):
                print('Filter Number', fltr+1)
                if filters[fltr].name() == 'Change':
                    if filters[fltr].process(data_daily):
                        fltrs[fltr] = np.append(fltrs[fltr],symbol)
                    else: check_all = False
                elif filters[fltr].name() == 'Compare' and  filters[fltr].date:
                    if filters[fltr].process(data_daily):
                        fltrs[fltr] = np.append(fltrs[fltr],symbol)
                    else: check_all = False
                else:
                    if filters[fltr].process(data_intra):
                        fltrs[fltr] = np.append(fltrs[fltr],symbol)
                    else: check_all = False
            if check_all:
                all_f.append(symbol)
            a_df = pd.DataFrame(all_f,columns=['Passed Stock'])
            na = pd.DataFrame(not_avail,columns=['Stocks'])
            # na.to_csv('Data/'+'Not Available.csv')
            # a_df.to_csv('Data/'+'Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.csv')
            with pd.ExcelWriter('Data/'+'Not Available.xlsx') as writer:
                na.to_excel(writer,sheet_name='Not Available',index=False)
            with pd.ExcelWriter('Data/'+'1.Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.xlsx') as writer:
                a_df.to_excel(writer,sheet_name='All Filters',index=False)
            with open('Data/'+'1.Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.txt','w') as outfile:
                a_df.to_string(outfile)
            for fltr in range(len(fltrs)):
                f_df= pd.DataFrame(fltrs[fltr][1:],columns=['Passed Stocks'])
                # f_df.to_csv('Data/'+'Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.csv')
                with pd.ExcelWriter('Data/'+'1.Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.xlsx') as writer:
                    f_df.to_excel(writer, sheet_name=('Filter'+str(fltr+1)),index=False)
                with open('Data/'+'1.Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.txt','w') as outfile:
                    f_df.to_string(outfile)
        except KeyboardInterrupt: break
    a_df = pd.DataFrame(all_f,columns=['Passed Stock'])
    not_avail = pd.DataFrame(not_avail,columns=['Stocks'])
    with open('Data/'+'1.Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.txt','w') as outfile:
                a_df.to_string(outfile)
    with pd.ExcelWriter('Data/'+'Not Available.xlsx') as writer:
        not_avail.to_excel(writer,sheet_name='Not Available',index=False)
    with pd.ExcelWriter('Data/'+'1.Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.xlsx') as writer:
        a_df.to_excel(writer,sheet_name='All Filters',index=False)
    for fltr in range(len(fltrs)):
        f_df= pd.DataFrame(fltrs[fltr][1:],columns=['Passed Stocks'])
        with open('Data/'+'1.Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.txt','w') as outfile:
            f_df.to_string(outfile)
        with pd.ExcelWriter('Data/'+'1.Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.xlsx') as writer:
            f_df.to_excel(writer, sheet_name=('Filter'+str(fltr+1)),index=False)
    return None

def LiveMonitor(filters,symbols,notify_all=True):
    while True:
        all_f = []
        fltrs = [np.zeros(1)]*len(filters)
        for symbol in symbols:
            try:
                print(symbol)
                stock = yf.Ticker(symbol)
                daily = symbol+ '_daily_' + datetime.today().strftime('%Y%m%d')+'.xlsx'
                intra = symbol+ '_intra_' + datetime.today().strftime('%Y%m%d')+'.xlsx'
                prev_data = 0
                if os.path.exists('Data/'+daily):
                    data_daily = pd.read_excel('Data/'+daily)
                    data_daily = data_daily.reset_index()
                else:
                    data_daily = stock.history(period='5y',interval='1d')[::-1].reset_index()
                    data_daily = data_daily.loc[:,['Date','Open','Close','High','Low','Volume']]
                    with pd.ExcelWriter(os.path.join('Data/'+daily)) as writer:
                        data_daily.to_excel(writer, index=False)
                data_intra = stock.history(period='1d',interval='1m')[::-1].reset_index()
                if len(data_intra) == 0 : continue
                data_intra = data_intra.loc[:,['Datetime','Open','Close','High','Low','Volume']]
                data_intra['Datetime'] = data_intra['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S"')
                if len(data_intra) == 0: continue
                with pd.ExcelWriter(os.path.join('Data/'+intra)) as writer:
                    data_intra.to_excel(writer, index=False)
                data_daily.rename(columns={'Date' : 'date',
                                        'Open':'open',
                                        'High':'high',
                                        'Low':'low',
                                        'Close':'close',
                                        'Volume': 'volumne'}, 
                                inplace=True)

                data_intra.rename(columns={'Datetime' : 'date',
                                        'Open':'open',
                                        'High':'high',
                                        'Low':'low',
                                        'Close':'close',
                                        'Volume': 'volumne'}, 
                                inplace=True)
                check_all = True
                for fltr in range(len(filters)):
                    filters[fltr].notify = False
                    if filters[fltr].name() == 'Compare' and filters[fltr].date:
                        print('Filter: ', fltr+1)
                        if filters[fltr].process(data_daily):
                            fltrs[fltr] = np.append(fltrs[fltr],symbol)
                            if not notify_all: notify()
                        else: check_all = False
                    elif filters[fltr].name() == 'Compare':
                        print('Filter: ', fltr+1)
                        if filters[fltr].process(data_intra):
                            fltrs[fltr] = np.append(fltrs[fltr],symbol)
                            if not notify_all: notify()
                        else: check_all = False
                    f_df= pd.DataFrame(fltrs[fltr][1:],columns=['Passed Stocks'])
                    # f_df.to_csv('Data/'+'Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.csv')
                    with pd.ExcelWriter('Data/'+'1.Filter_'+str(fltr+1)+'_'+datetime.today().strftime('%Y%m%d')+'.xlsx') as writer:
                        f_df.to_excel(writer, sheet_name=('Filter'+str(fltr+1)),index=False)
                if check_all:
                    all_f.append(symbol)
                    if notify_all: notify()
                    a_df = pd.DataFrame(all_f,columns=['Passed Stock'])
                    with open('Data/'+'1.Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.txt','w') as outfile:
                        a_df.to_string(outfile)
                    with pd.ExcelWriter('Data/'+'1.Filter_'+'_'+datetime.today().strftime('%Y%m%d')+'.xlsx') as writer:
                        a_df.to_excel(writer,sheet_name='All Filters',index=False)
            except KeyboardInterrupt: exit 
    return None


symbols_file = 'input.txt'


filters = [
    #Filter1
    #Each Day's close value is checked with day's open value, for last 365 days, and it checks that the
    #close value doesn't drop below 5% of open value, that's why drop is False.
    # open*0.95 < close*1 for 365 days
    Change('close','open',duration = 1,then_factor=80,drop=False,notify=False),
    #Filter2
    #It checks that the open value now does not drop below the value of the ticker, 
    # 7 days ago, times 1.1(110%).
    # 1.1 * [Close 7 days ago] < [Open now]
    Compare('open','close',when=7,date = True,then_factor=110,drop=False,notify=False),
	
    #Filter3
    #Checks that the closing value of ticker now, drops less than the closing value 30 days ago times 1.2(120%)
    # 1.2 * [Close 30 days ago] > [Open now]
    #Compare('open','close',when=30,date = True,then_factor=120,drop=True,notify=False),
	
	# 1.2 * [Close 30 days ago] < [Open now]
	Compare('open','close',when=30,date = True,then_factor=120,drop=False,notify=False),
	
    #Filter4
    #Checks that the close value of each day, for past 7 days, doesn't drop below 1%.
    # open*0.99 < close*1 for last 7 days
    Change('close','open',duration = 7,then_factor=1,drop=False,notify=False),
	
    #Filter5
    #Checks that the close value of each day, for past 30 days, doesn't drop below 2%.
    # open*0.98 < close*1 for last 30 days
    Change('close','open',duration = 30,then_factor=2,drop=False,notify=False),
	
    #Filter6
    #Checks for a stock to drop in price such that, 1.03(103%) times current open price is less than maximum
    #of the day.
    # 1.03 * [Current Open Price] < [Max Open Price today]
    Compare('open','open',agg='max',now_factor=103,drop=True,notify=False),
	
	#Filter7
    # 1.05 * [Close 120 days ago] < [Open now]
    Compare('open','close',when=90,date = True,then_factor=105,drop=False,notify=False),
]


# #Run in background
# if not os.path.exists('Data'):
#     os.mkdir('Data')
# command = "nohup python3 'Stock Monitor.py' -u &\nkill -9 {}".format(os.getpid())
# with open('Command.txt','w') as file:
#     file.write(command)



symbols = pd.read_table(symbols_file,header=None)
symbols = symbols[0].tolist()
# symbols = ['Googl','Goog']

Monitor(filters,symbols)


LiveMonitor(filters,symbols,notify_all=True)

