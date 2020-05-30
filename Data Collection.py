import pandas as pd
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time
import re


def get_live_data(symbol, interval=3):
    link = 'https://www.finance.yahoo.com/quote/{}?p={}&.tsrc=fin-srch'.format(
        symbol, symbol)
    output = []
    try:
        start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print('Live Stocks for: ', symbol)
        print('%20s  |%20s  |%20s  |%20s  |%20s  |' %
              ('Date', 'Current Value', 'Change', '% Change', 'Market Status'))
        print('%20s  |%20s  |%20s  |%20s  |%20s  |' %
              ('----', '-------------', '------', '---------', '------------'))
        while(True):
            r = requests.get(link)
            if r.status_code != 200:
                print('Wrong Symbol')
                return
            soup = BeautifulSoup(r.text, 'lxml')
            data = soup.find(
                'div', {'class': 'My(6px) Pos(r) smartphone_Mt(6px)'})
            current = data.get_text(separator='\n')
            print(current)
            current = current.split('\n')
            split = re.findall('[-+]?\d*\.\d+|\d+', current[1])

            #Store the values in one record and all the records in the output list.
            rec = []
            rec.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            rec.append(float(current[0].replace(',', '')))
            rec.append(float(split[0].replace(',', '')))
            rec.append(float(split[1].replace(',', '')))
            if 'open' in current[2]:
                rec.append('Open')
            else:
                rec.append('Close')
            output.append(rec)
            print('%20s  |%20.3f  |%20.3f  |%20.3f  |%20s  |' %
                  (rec[0], rec[1], rec[2], rec[3], rec[4]))
            time.sleep(interval)

    except KeyboardInterrupt:
        end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df = pd.DataFrame(data=output, columns=[
                          'Date', 'Current Value', 'Change', '% Change', 'Market Status'])
        #'Googl__25-04-1999 00:25__.csv'
        df.to_csv(symbol + '__' + start + '__' + end+'.csv')
        print('\nSaved current output as: ', symbol +
              '__' + start + '__' + end+'.csv')


def main():
    get_live_data('GOOGL', 5)


if __name__ == '__main__':
    main()
