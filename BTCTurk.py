import time, base64, hmac, hashlib, requests, json


class Btcturk:
    name = 'BTCTURK'
    trade_fee = 0.0000

    base = "https://api.btcturk.com"
    method = ""
    uri = base + method

    apiKey = ""
    apiSecret = ""
    apiSecret = base64.b64decode(apiSecret)

    def headers(self):
        stamp = str(int(time.time()) * 1000)
        data = "{}{}".format(self.apiKey, stamp).encode("utf-8")
        signature = hmac.new(self.apiSecret, data, hashlib.sha256).digest()
        signature = base64.b64encode(signature)
        headers = {"X-PCK": self.apiKey, "X-Stamp": stamp, "X-Signature": signature, "Content-Type": "application/json"}
        return headers

    def __init__(self, log_file, nominal_btc_price):
        self.nominal_btc_price = nominal_btc_price
        self.update_balances()
        self.log_file = log_file

    def log_print(self, string):
        print(string)
        self.log_file.write(f'{str(string)}\n')

    def update_balances(self):
        self.btc_total_balance = self.get_total_balance("BTC")
        self.usdt_total_balance = self.get_free_balance("USDT")
        self.btc_free_balance = self.get_free_balance("BTC")
        self.usdt_free_balance = self.get_free_balance("USDT")

        self.total_usd_worth = self.btc_total_balance * self.nominal_btc_price + \
                               self.usdt_total_balance

    def ping(self):
        pass

    def get_server_time(self):
        method = "/api/v2/server/time"
        result = requests.get(url=self.base + method).json()
        return json.dumps(result, indent=2)
        # websocket ile server time'ı kıyasalayacak ileride, kendi saatimiz ile de kıyaslama yapabiliriz.
        pass

    def get_total_balance(self, coin):
        method = "/api/v1/users/balances"
        result = requests.get(url=self.base + method, headers=self.headers()).json()
        balance = json.dumps(result, indent=2)
        # self.log_print(balance)
        if coin == "USDT":
            return float(result["data"][5]["balance"])
        if coin == "BTC":
            return float(result["data"][1]["balance"])

    def get_free_balance(self, coin):
        method = "/api/v1/users/balances"
        result = requests.get(url=self.base + method, headers=self.headers()).json()
        balance = json.dumps(result, indent=2)
        if coin == "USDT":
            return float(result["data"][5]["free"])
        if coin == "BTC":
            return float(result["data"][1]["free"])

    def get_open_orders(self, currency):
        method = "/api/v1/openOrders"
        method = method + "?pairSymbol=" + currency
        result = requests.get(url=self.base + method, headers=self.headers()).json()
        return result

    def get_my_trades(self):
        method = "/api/v1/users/transactions/trade?type=buy&type=sell&symbol=xlm&symbol=try&symbol=usdt"
        result = requests.get(url=self.base + method, headers=self.headers()).json()
        return json.dumps(result, indent=2)

    def buy_market(self, currency, quantity, price):
        method = "/api/v1/order"
        params = {"quantity": quantity, "price": price, "stopPrice": 0,
                  "newOrderClientId": "BtcTurk Python API Test",
                  "orderMethod": "limit", "orderType": "buy", "pairSymbol": currency}
        result = requests.post(url=self.base + method, headers=self.headers(), json=params).json()
        self.log_print(f'Buy order at BTCTurk, Amount: {result}')

    def sell_market(self, currency, quantity, price):
        method = "/api/v1/order"
        params = {"quantity": quantity, "price": price, "stopPrice": 0,
                  "newOrderClientId": "BtcTurk Python API Test",
                  "orderMethod": "limit", "orderType": "sell", "pairSymbol": currency}
        result = requests.post(url=self.base + method, headers=self.headers(), json=params).json()
        self.log_print(f'Sell order at BTCTurk, Amount: {result}')

    def cancel_order(self,order_id):
        method = f'/api/v1/order?id={order_id}'
        result = requests.delete(url=self.base + method, headers=self.headers()).json()
        return json.dumps(result, indent=2)


if __name__ == '__main__':
    log_file = open('BTCTurk_log.txt', 'w')
    b = Btcturk(log_file, nominal_btc_price=11800)
    log_file.close()
    # x = Btcturk()
    print(b.get_total_balance("USDT"))
    print(b.get_total_balance("BTC"))
