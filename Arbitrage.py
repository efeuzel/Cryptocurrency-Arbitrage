from websocket import create_connection
import json
from multiprocessing import Process
from multiprocessing import Array
import time
from datetime import date, datetime
from Binance import Binance
from BTCTurk import Btcturk
from telethon.sync import TelegramClient


def binance(dummy, arr):
    ws = create_connection("wss://stream.binance.com:9443/ws/btcusdt@bookTicker")
    message = {"method": "SUBSCRIBE", "params": ["btcusdt@bookTicker"], "id": 1}
    ws.send(json.dumps(message))
    while True:
        try:
            res = json.loads(ws.recv())
            arr[0] = float(res["b"])
            arr[1] = float(res["a"])
            arr[2] = float(res["B"])
            arr[3] = float(res["A"])
        except:
            arr[0] = 0
            arr[1] = 0
            arr[2] = 0
            arr[3] = 0


def btcturk(dummy, arr):
    ws = create_connection("wss://ws-feed-pro.btcturk.com/")
    message = [151, {"type": 151, "channel": 'orderbook', "event": 'BTCUSDT', "join": True}]
    ws.send(json.dumps(message))
    while True:
        try:
            res = json.loads(ws.recv())
            arr[0] = float(res[1]["BO"][0]["P"])
            arr[1] = float(res[1]["AO"][0]["P"])
            arr[2] = float(res[1]["BO"][0]["A"])
            arr[3] = float(res[1]["AO"][0]["A"])
        except:
            arr[0] = 0
            arr[1] = 0
            arr[2] = 0
            arr[3] = 0


def check_for_opp(e1_data, e1, e2_data, e2):
    # This function takes in exchange order book data and returns an opp if found
    # e_data=> 0: bid, 1: ask, 2: bid amount, 3: ask amount

    if e1_data[0] > e2_data[0]:
        max_bid = e1_data[0]
        max_bid_amount = e1_data[2]
        max_bid_exchange = e1
    else:
        max_bid = e2_data[0]
        max_bid_amount = e2_data[2]
        max_bid_exchange = e2

    if e1_data[1] < e2_data[1]:
        min_ask = e1_data[1]
        min_ask_amount = e1_data[3]
        min_ask_exchange = e1
    else:
        min_ask = e2_data[1]
        min_ask_amount = e2_data[3]
        min_ask_exchange = e2

    log_print(
        f'''\n{str(datetime.now())}\n{e1.name} bid: {e1_data[0]:.2f}, ask: {e1_data[1]:.2f} | {e2.name} bid: {e2_data[0]:.2f}, ask: {e2_data[1]:.2f} | Min amount: {(min_ask_amount, max_bid_amount)}''')

    if min_ask > 0:
        profit_ratio = (max_bid * (1 - max_bid_exchange.trade_fee) -
                        min_ask * (1 + min_ask_exchange.trade_fee)) / \
                       min_ask * (1 + min_ask_exchange.trade_fee)
        log_print(f'Profit Ratio: {profit_ratio:0.5f}')
        return {'max_bid': max_bid, 'max_bid_amount': max_bid_amount,
                'max_bid_exchange': max_bid_exchange,
                'min_ask': min_ask, 'min_ask_amount': min_ask_amount,
                'min_ask_exchange': min_ask_exchange,
                'profit_ratio': profit_ratio}
    else:
        log_telegram("Stopped!")


def report_balances(binance, btcturk):
    log_print(f'BINANCE BTC: {binance.btc_free_balance} USDT: {binance.usdt_free_balance}')
    log_print(f'BTCTURK BTC: {btcturk.btc_free_balance} USDT: {btcturk.usdt_free_balance}')
    log_print(
        f'Total BTC: {binance.btc_free_balance + btcturk.btc_free_balance}  Total USDT: {binance.usdt_free_balance + btcturk.usdt_free_balance}')
    log_print(f'BINANCE BTC: {binance.btc_total_balance} USDT: {binance.usdt_total_balance}')
    log_print(f'BTCTURK BTC: {btcturk.btc_total_balance} USDT: {btcturk.usdt_total_balance}')
    log_print(
        f'Total BTC: {binance.btc_total_balance + btcturk.btc_total_balance}  Total USDT: {binance.usdt_total_balance + btcturk.usdt_total_balance}')

def log_print(string):
    print(string)
    log_file.write(f'{str(string)}\n')

def log_telegram(string):
    api_id = 0
    api_hash = ''
    bot_token = ''
    bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

    async def main():
        await bot.send_message(-335391745, string)

    with bot:
        bot.loop.run_until_complete(main())


order_amount = 0.00091
nominal_btc_price = 11800

if __name__ == '__main__':
    binance_data = Array('d', 4)
    p1 = Process(target=binance, args=(0, binance_data))
    p1.start()

    btcturk_data = Array('d', 4)
    p2 = Process(target=btcturk, args=(0, btcturk_data))
    p2.start()

    with open(f'{str(date.today())}_log.txt', 'w+') as log_file:
        binance = Binance(log_file, nominal_btc_price)
        btcturk = Btcturk(log_file, nominal_btc_price)
        initial_total_usd_worth = binance.total_usd_worth + btcturk.total_usd_worth
        log_print(f'Initial total USD worth: {initial_total_usd_worth:0.2f}')

        while True:
            # Safety checks
            if len(btcturk.get_open_orders('BTCUSDT')['data']['bids']) < 2 and \
                    len(btcturk.get_open_orders('BTCUSDT')['data']['asks']) < 2 and \
                    len(binance.get_open_orders('BTCUSDT')) < 2:

                opp = check_for_opp(binance_data, binance, btcturk_data, btcturk)

                # Check if opp is profitable enough dependent on direction
                if (opp['max_bid_exchange'].btc_free_balance >= opp['min_ask_exchange'].btc_free_balance
                    and opp['profit_ratio'] > 0.0001) or \
                        (opp['max_bid_exchange'].btc_free_balance < opp['min_ask_exchange'].btc_free_balance
                         and opp['profit_ratio'] > 0.0003):
                    log_print('Opp is profitable enough')
                    # Check if order is big enough
                    if min(opp['min_ask_amount'], opp['max_bid_amount']) > order_amount:
                        log_print('Opp is big enough')
                        log_telegram('Opp is big enough')
                        # Check if order is there is enough balance
                        if opp['min_ask_exchange'].usdt_free_balance > order_amount * opp['min_ask'] * \
                                (1 + opp['min_ask_exchange'].trade_fee) and opp[
                            'max_bid_exchange'].btc_free_balance > order_amount:
                            log_print('buy trade')
                            opp['min_ask_exchange'].buy_market('BTCUSDT', order_amount, opp['min_ask'])
                            log_print('sell trade')
                            opp['max_bid_exchange'].sell_market('BTCUSDT', order_amount, opp['max_bid'])
                            binance.update_balances()
                            btcturk.update_balances()
                            report_balances(binance, btcturk)
                            log_print(f'New total USD worth: {binance.total_usd_worth + btcturk.total_usd_worth}')
                            log_telegram(f'New total USD worth: {binance.total_usd_worth + btcturk.total_usd_worth}')
                        else:
                            log_print('Not enough balance')
                            log_telegram('Not enough balance')
            else:
                log_print('Safety checks have failed!')
                log_telegram('Safety checks have failed!')
            time.sleep(1)
