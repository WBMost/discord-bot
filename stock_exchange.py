import json
from traceback import format_exc
from datetime import datetime
import requests
import pandas as pd
from web_scraping import Market_Watcher_Scraper

api_url = 'https://www.alphavantage.co/query?'

api_key = 'ECTRAJQ3Q5XKH28M'

def info(mes):
    print(f'INFO - {mes}')
def error(mes):
    print(f'ERROR - {mes}')

class StockExchanger():
    def __init__(self):
        self.mws = Market_Watcher_Scraper()

    def create_file(self,user_id):
        file = {
            'balance': 1000.00,
            'stocks':{},
            'history':[]
        }
        with open(f'stockExchange/{user_id}.json','w') as w:
            json.dump(file,w)

    def write_to_file(self,user_id,data):
        with open(f'stockExchange/{user_id}.json','w') as w:
            json.dump(data,w)

    def get_user_data(self,user_id):
        with open(f'stockExchange/{user_id}.json','r') as w:
            data = json.loads(w.read())
        return data

    def read_balance(self,user_id):
        data = self.get_user_data(user_id)
        return float(round(data['balance'],2))

    def read_stocks(self,user_id):
        data = self.get_user_data(user_id)
        data = data['stocks']
        to_delete = []
        for ticker in data:
            print(ticker)
            if data[ticker][1] < 0.01:
                to_delete.append(ticker)
                continue
            resp = self.stock_price(ticker)
            data[ticker] = [data[ticker][0],round(data[ticker][0]*resp, 2)]
        if to_delete:
            for tick in to_delete:
                del data[tick]
            data2 = self.get_user_data(user_id)
            data2['stocks'] = data
            self.write_to_file(user_id, data2)
        return pd.DataFrame.from_dict(data=data, orient='index', columns=['ticker','total_value']).sort_values(by='total_value',ascending=False)


    def read_history(self,user_id):
        data = self.get_user_data(user_id)
        df = pd.DataFrame(data=data['history'],columns=['transaction_type','symbol','cost_per_share','total_cost','start_balance','end_balance'])
        return df


    def purchase(self,user_id,ticker,value):
        if value < 0.01:
            return 66
        value = round(value,2)
        data = self.get_user_data(user_id)
        start_balance = data['balance']
        if data['balance'] < value:
            return 66
        resp = self.stock_price(ticker)
        data['balance'] -= value
        new_shares = round(value/resp, 2)
        if ticker in data['stocks']:
            data['stocks'][ticker][0] += new_shares
        else:
            data['stocks'][ticker] = [new_shares,resp]
        # columns = transaction_type, cost_per_share, total_cost, start_balance, end_balance
        data['history'].insert(0,['PURCHASE',ticker,resp,value,start_balance,data['balance']])
        self.write_to_file(user_id,data)

    def sell(self,user_id,ticker,value):
        if value < 0.01:
            return 66
        resp = self.stock_price(ticker)
        data = self.get_user_data(user_id)
        start_balance = data['balance']
        if ticker in data['stocks']:
            current_value = data['stocks'][ticker][0] * resp
            if value > current_value:
                return 66
            else:
                data['balance'] += value
                sold_shares = value/resp
                data['stocks'][ticker][0] -= sold_shares
        # columns = transaction_type, cost_per_share, total_cost, start_balance, end_balance
        data['history'].insert(0,['SALE',ticker,resp,value,start_balance,data['balance']])
        self.write_to_file(user_id,data)
    
    def search_symbol(self,keyword):
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': keyword,
            'apikey': api_key,
        }
        r = requests.get(url=api_url,params=params).json()
        return r['bestMatches']
    
    def business_info(self,ticker):
        params = {
            'function': 'OVERVIEW',
            'symbol': ticker,
            'apikey': api_key,
        }
        r = requests.get(url=api_url,params=params).json()
        return r

    def stock_price(self,ticker):
        r = self.mws.get_price(ticker)
        return r

    def preview_stock(self,ticker):
        ticker = ticker.upper()
        info(f'attempting to gather data {ticker}')
        stock = self.business_info(ticker)
        if 'Name' not in stock:
            data = {
                'Name': 'Could not process request through API',
                'Recommendation':'Please try again later or ask about a different symbol...'
            }
            return data
        data = {
            'Name':stock['Name'],
            'Sector': stock['Sector'],
            'Industry': stock['Industry'],
            'Exchange': stock['Exchange'],
            'Current Price':self.stock_price(ticker),
            'EPS':stock['EPS'],
            'PEG Ratio': stock['PEGRatio'],
            '52 week high/low': stock['52WeekHigh'] + '/' +stock['52WeekLow'],
            'Recommendation':self.mws.get_recommendation(ticker)
        }
        return data

if __name__ == '__main__':
    se = StockExchanger()
    userID = 'test_account'
    print(se.search_symbol('apple'))