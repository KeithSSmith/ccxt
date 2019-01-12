# -*- coding: utf-8 -*-

# PLEASE DO NOT EDIT THIS FILE, IT IS GENERATED AND WILL BE OVERWRITTEN:
# https://github.com/ccxt/ccxt/blob/master/CONTRIBUTING.md#how-to-contribute-code

from ccxt.async_support.base.exchange import Exchange
import hashlib
import math
from ccxt.base.errors import ExchangeError
from ccxt.base.errors import BadRequest


class zaif (Exchange):

    def describe(self):
        return self.deep_extend(super(zaif, self).describe(), {
            'id': 'zaif',
            'name': 'Zaif',
            'countries': ['JP'],
            'rateLimit': 2000,
            'version': '1',
            'has': {
                'CORS': False,
                'createMarketOrder': False,
                'fetchOpenOrders': True,
                'fetchClosedOrders': True,
                'withdraw': True,
            },
            'urls': {
                'logo': 'https://user-images.githubusercontent.com/1294454/27766927-39ca2ada-5eeb-11e7-972f-1b4199518ca6.jpg',
                'api': 'https://api.zaif.jp',
                'www': 'https://zaif.jp',
                'doc': [
                    'http://techbureau-api-document.readthedocs.io/ja/latest/index.html',
                    'https://corp.zaif.jp/api-docs',
                    'https://corp.zaif.jp/api-docs/api_links',
                    'https://www.npmjs.com/package/zaif.jp',
                    'https://github.com/you21979/node-zaif',
                ],
                'fees': 'https://zaif.jp/fee?lang=en',
            },
            'fees': {
                'trading': {
                    'percentage': True,
                    'taker': -0.0001,
                    'maker': -0.0005,
                },
            },
            'api': {
                'public': {
                    'get': [
                        'depth/{pair}',
                        'currencies/{pair}',
                        'currencies/all',
                        'currency_pairs/{pair}',
                        'currency_pairs/all',
                        'last_price/{pair}',
                        'ticker/{pair}',
                        'trades/{pair}',
                    ],
                },
                'private': {
                    'post': [
                        'active_orders',
                        'cancel_order',
                        'deposit_history',
                        'get_id_info',
                        'get_info',
                        'get_info2',
                        'get_personal_info',
                        'trade',
                        'trade_history',
                        'withdraw',
                        'withdraw_history',
                    ],
                },
                'ecapi': {
                    'post': [
                        'createInvoice',
                        'getInvoice',
                        'getInvoiceIdsByOrderNumber',
                        'cancelInvoice',
                    ],
                },
                'tlapi': {
                    'post': [
                        'get_positions',
                        'position_history',
                        'active_positions',
                        'create_position',
                        'change_position',
                        'cancel_position',
                    ],
                },
                'fapi': {
                    'get': [
                        'groups/{group_id}',
                        'last_price/{group_id}/{pair}',
                        'ticker/{group_id}/{pair}',
                        'trades/{group_id}/{pair}',
                        'depth/{group_id}/{pair}',
                    ],
                },
            },
            'exceptions': {
                'exact': {
                    'unsupported currency_pair': BadRequest,  # {"error": "unsupported currency_pair"}
                },
                'broad': {
                },
            },
        })

    async def fetch_markets(self, params={}):
        markets = await self.publicGetCurrencyPairsAll()
        result = []
        for p in range(0, len(markets)):
            market = markets[p]
            id = market['currency_pair']
            symbol = market['name']
            base, quote = symbol.split('/')
            precision = {
                'amount': -math.log10(market['item_unit_step']),
                'price': market['aux_unit_point'],
            }
            result.append({
                'id': id,
                'symbol': symbol,
                'base': base,
                'quote': quote,
                'active': True,  # can trade or not
                'precision': precision,
                'limits': {
                    'amount': {
                        'min': self.safe_float(market, 'item_unit_min'),
                        'max': None,
                    },
                    'price': {
                        'min': self.safe_float(market, 'aux_unit_min'),
                        'max': None,
                    },
                    'cost': {
                        'min': None,
                        'max': None,
                    },
                },
                'info': market,
            })
        return result

    async def fetch_balance(self, params={}):
        await self.load_markets()
        response = await self.privatePostGetInfo()
        balances = response['return']
        result = {'info': balances}
        currencies = list(balances['funds'].keys())
        for c in range(0, len(currencies)):
            currency = currencies[c]
            balance = balances['funds'][currency]
            uppercase = currency.upper()
            account = {
                'free': balance,
                'used': 0.0,
                'total': balance,
            }
            if 'deposit' in balances:
                if currency in balances['deposit']:
                    account['total'] = balances['deposit'][currency]
                    account['used'] = account['total'] - account['free']
            result[uppercase] = account
        return self.parse_balance(result)

    async def fetch_order_book(self, symbol, limit=None, params={}):
        await self.load_markets()
        orderbook = await self.publicGetDepthPair(self.extend({
            'pair': self.market_id(symbol),
        }, params))
        return self.parse_order_book(orderbook)

    async def fetch_ticker(self, symbol, params={}):
        await self.load_markets()
        ticker = await self.publicGetTickerPair(self.extend({
            'pair': self.market_id(symbol),
        }, params))
        timestamp = self.milliseconds()
        vwap = ticker['vwap']
        baseVolume = ticker['volume']
        quoteVolume = None
        if baseVolume is not None and vwap is not None:
            quoteVolume = baseVolume * vwap
        last = ticker['last']
        return {
            'symbol': symbol,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'high': ticker['high'],
            'low': ticker['low'],
            'bid': ticker['bid'],
            'bidVolume': None,
            'ask': ticker['ask'],
            'askVolume': None,
            'vwap': vwap,
            'open': None,
            'close': last,
            'last': last,
            'previousClose': None,
            'change': None,
            'percentage': None,
            'average': None,
            'baseVolume': baseVolume,
            'quoteVolume': quoteVolume,
            'info': ticker,
        }

    def parse_trade(self, trade, market=None):
        side = 'buy' if (trade['trade_type'] == 'bid') else 'sell'
        timestamp = trade['date'] * 1000
        id = self.safe_string(trade, 'id')
        id = self.safe_string(trade, 'tid', id)
        price = self.safe_float(trade, 'price')
        amount = self.safe_float(trade, 'amount')
        if not market:
            market = self.markets_by_id[trade['currency_pair']]
        return {
            'id': str(id),
            'info': trade,
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'symbol': market['symbol'],
            'type': None,
            'side': side,
            'price': price,
            'amount': amount,
        }

    async def fetch_trades(self, symbol, since=None, limit=None, params={}):
        await self.load_markets()
        market = self.market(symbol)
        response = await self.publicGetTradesPair(self.extend({
            'pair': market['id'],
        }, params))
        numTrades = len(response)
        if numTrades == 1:
            firstTrade = response[0]
            if not firstTrade:
                response = []
        return self.parse_trades(response, market, since, limit)

    async def create_order(self, symbol, type, side, amount, price=None, params={}):
        await self.load_markets()
        if type == 'market':
            raise ExchangeError(self.id + ' allows limit orders only')
        response = await self.privatePostTrade(self.extend({
            'currency_pair': self.market_id(symbol),
            'action': 'bid' if (side == 'buy') else 'ask',
            'amount': amount,
            'price': price,
        }, params))
        return {
            'info': response,
            'id': str(response['return']['order_id']),
        }

    async def cancel_order(self, id, symbol=None, params={}):
        return await self.privatePostCancelOrder(self.extend({
            'order_id': id,
        }, params))

    def parse_order(self, order, market=None):
        side = 'buy' if (order['action'] == 'bid') else 'sell'
        timestamp = int(order['timestamp']) * 1000
        if not market:
            market = self.markets_by_id[order['currency_pair']]
        price = order['price']
        amount = order['amount']
        return {
            'id': str(order['id']),
            'timestamp': timestamp,
            'datetime': self.iso8601(timestamp),
            'lastTradeTimestamp': None,
            'status': 'open',
            'symbol': market['symbol'],
            'type': 'limit',
            'side': side,
            'price': price,
            'cost': price * amount,
            'amount': amount,
            'filled': None,
            'remaining': None,
            'trades': None,
            'fee': None,
        }

    def parse_orders(self, orders, market=None, since=None, limit=None):
        ids = list(orders.keys())
        result = []
        for i in range(0, len(ids)):
            id = ids[i]
            order = orders[id]
            extended = self.extend(order, {'id': id})
            result.append(self.parse_order(extended, market))
        return self.filter_by_since_limit(result, since, limit)

    async def fetch_open_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = None
        request = {
            # 'is_token': False,
            # 'is_token_both': False,
        }
        if symbol is not None:
            market = self.market(symbol)
            request['currency_pair'] = market['id']
        response = await self.privatePostActiveOrders(self.extend(request, params))
        return self.parse_orders(response['return'], market, since, limit)

    async def fetch_closed_orders(self, symbol=None, since=None, limit=None, params={}):
        await self.load_markets()
        market = None
        request = {
            # 'from': 0,
            # 'count': 1000,
            # 'from_id': 0,
            # 'end_id': 1000,
            # 'order': 'DESC',
            # 'since': 1503821051,
            # 'end': 1503821051,
            # 'is_token': False,
        }
        if symbol is not None:
            market = self.market(symbol)
            request['currency_pair'] = market['id']
        response = await self.privatePostTradeHistory(self.extend(request, params))
        return self.parse_orders(response['return'], market, since, limit)

    async def withdraw(self, code, amount, address, tag=None, params={}):
        self.check_address(address)
        await self.load_markets()
        currency = self.currency(code)
        if code == 'JPY':
            raise ExchangeError(self.id + ' withdraw() does not allow ' + code + ' withdrawals')
        request = {
            'currency': currency['id'],
            'amount': amount,
            'address': address,
            # 'message': 'Hinot ',  # XEM and others
            # 'opt_fee': 0.003,  # BTC and MONA only
        }
        if tag is not None:
            request['message'] = tag
        result = await self.privatePostWithdraw(self.extend(request, params))
        return {
            'info': result,
            'id': result['return']['txid'],
            'fee': result['return']['fee'],
        }

    def nonce(self):
        nonce = float(self.milliseconds() / 1000)
        return '{:.8f}'.format(nonce)

    def sign(self, path, api='public', method='GET', params={}, headers=None, body=None):
        url = self.urls['api'] + '/'
        if api == 'public':
            url += 'api/' + self.version + '/' + self.implode_params(path, params)
        elif api == 'fapi':
            url += 'fapi/' + self.version + '/' + self.implode_params(path, params)
        else:
            self.check_required_credentials()
            if api == 'ecapi':
                url += 'ecapi'
            elif api == 'tlapi':
                url += 'tlapi'
            else:
                url += 'tapi'
            nonce = self.nonce()
            body = self.urlencode(self.extend({
                'method': path,
                'nonce': nonce,
            }, params))
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Key': self.apiKey,
                'Sign': self.hmac(self.encode(body), self.encode(self.secret), hashlib.sha512),
            }
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def handle_errors(self, httpCode, reason, url, method, headers, body, response):
        if response is None:
            return
        #
        #     {"error": "unsupported currency_pair"}
        #
        feedback = self.id + ' ' + body
        error = self.safe_string(response, 'error')
        if error is not None:
            exact = self.exceptions['exact']
            if error in exact:
                raise exact[error](feedback)
            broad = self.exceptions['broad']
            broadKey = self.findBroadlyMatchedKey(broad, error)
            if broadKey is not None:
                raise broad[broadKey](feedback)
            raise ExchangeError(feedback)  # unknown message
        success = self.safe_value(response, 'success', True)
        if not success:
            raise ExchangeError(feedback)
