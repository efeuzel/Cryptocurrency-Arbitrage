import time
import hashlib
import requests
import hmac
from urllib.parse import urlencode
import asyncio

class Binance:

    name = 'BINANCE'
    trade_fee = 0.001

    base = "https://api.binance.com/api/v3"
    method = ""
    uri = base+method

    apiKey = ""
    apiSecret = ""

    def __init__(self, log_file, nominal_btc_price):
        self.nominal_btc_price = nominal_btc_price
        self.update_balances()
        self.log_file = log_file


    def log_print(self,string):
        print(string)
        self.log_file.write(f'{str(string)}\n')

    def update_balances(self):
        self.btc_total_balance = self.get_total_balance("BTC")
        self.usdt_total_balance = self.get_total_balance("USDT")
        self.btc_free_balance = self.get_free_balance("BTC")
        self.usdt_free_balance = self.get_free_balance("USDT")
        self.total_usd_worth = self.btc_total_balance * self.nominal_btc_price + \
            self.usdt_total_balance


    def _order(self , currency , quantity , side , price=None):
        params = {}

        if price is not None :
            params["type"] = "LIMIT"
            params["price"] = self._format(price)
            params["timeInForce"] = "GTC"
        else :
            params["type"] = "MARKET"

        params["symbol"] = currency
        params["side"] = side
        params["quantity"] = '%.8f' % quantity

        return params

    def _format(self , price) :
        return "{:.8f}".format(price)


    def _post(self , path , params={}):
        # params.update({"recvWindow" : config.recv_window})
        query = urlencode(self._sign(params))
        url = "%s" % (path)
        header = {"X-MBX-APIKEY" : self.apiKey}
        return requests.post(url , headers = header , data = query , timeout = 30 , verify = True).json()


    def _get(self , path , params={}):
        # params.update({"recvWindow" : config.recv_window})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path , query)
        header = {"X-MBX-APIKEY" : self.apiKey}
        return requests.get(url , headers = header , timeout = 30 , verify = True ).json()

    def _delete(self, path, params={}):
        # params.update({"recvWindow": config.recv_window})
        query = urlencode(self._sign(params))
        url = "%s?%s" % (path, query)
        header = {"X-MBX-APIKEY": self.apiKey}
        return requests.delete(url, headers=header, timeout=30, verify=True).json()

    def _sign(self , params={}):
        data = params.copy()
        ts = int(1000 * time.time())
        data.update({"timestamp" : ts})
        h = urlencode(data)
        b = bytearray()
        b.extend(self.apiSecret.encode())
        signature = hmac.new(b , msg = h.encode('utf-8') , digestmod = hashlib.sha256).hexdigest()
        data.update({"signature" : signature})

        return data

    def ping(self):
        method = "/ping"
        self.log_print(self.base+method)
        url = self.base + method
        return requests.get(url , timeout = 30 , verify = True).json()

    def get_server_time(self):
        method= "/time"
        url = self.base + method
        return requests.get(url , timeout = 30 , verify = True).json()

    def get_total_balance(self, coin):
        method = "/account"
        balance= self._get(self.base + method , {})
        # self.log_print(balance)
        if coin == "BTC":
            return float(balance["balances"][0]["free"])+float(balance["balances"][0]["locked"])
        if coin == "USDT":
             return float(balance["balances"][11]["free"])+float(balance["balances"][11]["locked"])

    def get_free_balance(self,coin):
        method = "/account"
        balance = self._get(self.base + method , {})
        if coin == "BTC" :
             return float(balance["balances"][0]["free"])
        if coin == "USDT" :
             return float(balance["balances"][11]["free"])

    def get_open_orders(self , currency, limit=100) :
        method="/openOrders"
        url = self.base + method
        params = {"symbol" : currency}
        return self._get(url, params)

    def get_my_trades(self , currency , limit=50):
        method="/myTrades"
        url= self.base + method
        params = {"symbol" : currency , "limit" : limit}
        return self._get(url , params)

    async def buy_market(self, currency, quantity, price):
        method = "/order"
        url = self.base + method
        params = self._order(currency, quantity, "BUY", price)
        result = self._post(url, params)
        self.log_print(result)
        self.log_print(f'Price : {result["price"]}, Amount : {result["origQty"]}')
        self.log_print(f'Buy order at BTCTurk, excecuted: {result["executedQty"]}')

    async def sell_market(self, currency, quantity, price):
        method = "/order"
        url=self.base + method
        params = self._order(currency, quantity, "SELL", price)
        result = self._post(url, params)
        self.log_print(result)
        self.log_print(f'Price : {result["price"]}, Amount : {result["origQty"]}')
        self.log_print(f'Sell order at BTCTurk, Amount: {result["executedQty"]}')

    def cancel_all_orders(self, currency):
        method = "/openOrders"
        url = self.base + method
        params = {"symbol": currency}
        result = self._delete(url, params)
        try:
            print("Result : ", result[0]["status"])
        except:
            print("Result : ", "No order to cancel")

    def rebalance(self):
        pass


if __name__ == '__main__':
    log_file = open('Binance_log.txt', 'w')
    x = Binance(log_file, nominal_btc_price=11800)

    print(x.get_total_balance("USDT"))
    print(x.get_total_balance("BTC"))

    asyncio.gather(
        x.sell_market('BTCUSDT', 0.00091, 15000)
    )

    log_file.close()
