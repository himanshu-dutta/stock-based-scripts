import re
import time
import json
import requests
import pandas as pd
from datetime import datetime, timedelta

api_key = 'YOUR API KEY'

def get_past_data(symbols,api,period=60,delay=5):
    '''
    symbols: list of all the symbols for which you need data.
    api: the api key for iex cloud service.
    period: duration for which data is to be retrieved.
    delay: the gap in minutes for which data is to be retrieved. Set to 5 mins by default.
    '''
    try:
        data = 0
        if type(symbols) != list:
            symbols = [symbols]
        for symbol in symbols:
            print('Collecting data for: {}'.format(symbol))
            for last in range(period):
                date = (datetime.today() - timedelta(days=last)).strftime('%Y%m%d')
                r = requests.get('https://cloud.iexapis.com/stable/stock/'+str(symbol)+'/intraday-prices?'+'exactDate='+date+'&chartInterval='+str(delay)+'&token='+api)
                if len(json.loads(r.text)) == 0: continue
                current = pd.DataFrame(data=json.loads(r.text))
                current.insert(0, column='stock', value=symbol)
                if type(data) == int: data = current
                else: data = data.append(current);
    except:
        date_time = data['date'] + ' ' + data['minute']
        data.insert(1, column='date time', value=date_time)
        data['date time'] = pd.to_datetime(data['date time'])
        data = data.drop(columns=['label','date','minute'])
        # data = data.iloc[:,:10]
    finally:
        data.to_excel('Stocks_'+ (datetime.today() - timedelta(days=last)).strftime('%Y%m%d') + '_' + datetime.today().strftime('%Y%m%d') + '.xlsx')
        return data

def available_stocks(api_key):
    r = requests.get('https://cloud.iexapis.com/beta/ref-data/symbols?token='+api_key)
    if r.status_code != 200: print("Wrong API Key"); return;
    out = pd.DataFrame(data=json.loads(r.text))
    out.to_excel("Available Stocks.xlsx")
    print('Saved available stocks.')
    return list(out['symbol'].values)


if __name__ == '__main__':
    avail = available_stocks(api_key)
    data = get_past_data(avail,api_key,period=5,delay=5)
