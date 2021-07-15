class Strategy():
    # option setting needed
    def __setitem__(self, key, value):
        self.options[key] = value

    # option setting needed
    def __getitem__(self, key):
        return self.options.get(key, '')

    def __init__(self):
        # strategy property
        self.subscribedBooks = {
            'Binance': {
                'pairs': ['ADA-USDT'],
            },
        }
        self.period =  100*60
        self.options = {}

        # user defined class attribute
        self.last_type = 'buy'
        self.last_cross_status = None
        self.close_price_trace = np.array([])
        self.ma_long = 15
        self.ma_short = 5
        self.UP = 1
        self.DOWN = 2
        self.ratio = 500
        self.notrade = 0
        self.contup = 0
        self.contdown = 0

    def on_order_state_change(self,  order):
        Log("on order state change message: " + str(order) + " order price: " + str(order["price"]))

    def get_current_ma_cross(self):
        s_ma = talib.SMA(self.close_price_trace, self.ma_short)[-1]
        l_ma = talib.SMA(self.close_price_trace, self.ma_long)[-1]
        if np.isnan(s_ma) or np.isnan(l_ma):
            return None
        if s_ma > l_ma:
            return self.UP
        return self.DOWN


    # called every self.period
    def trade(self, information):
        exchange = list(information['candles'])[0]
        pair = list(information['candles'][exchange])[0]
        target_currency = pair.split('-')[0]  #ETH
        base_currency = pair.split('-')[1]  #USDT
        base_currency_amount = self['assets'][exchange][base_currency] 
        target_currency_amount = self['assets'][exchange][target_currency] 
        # add latest price into trace
        close_price = information['candles'][exchange][pair][0]['close']
        self.close_price_trace = np.append(self.close_price_trace, [float(close_price)])
        # only keep max length of ma_long count elements
        self.close_price_trace = self.close_price_trace[-self.ma_long:]
        # calculate current ma cross status
        cur_cross = self.get_current_ma_cross()
        if cur_cross is None:
            return []
        if self.last_cross_status is None:
            self.last_cross_status = cur_cross
            return []
        if self.notrade != 0:
            self.notrade = self.notrade - self.period
        elif self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.UP:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            if self.contup > 1:
                self.contup = self.contup + 1
                return [
                    {
                        'exchange': exchange,
                        'amount': -1*self.contup*self.ratio / close_price,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            self.contup = 1
            return [
                {
                    'exchange': exchange,
                    'amount': -1.5*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'sell' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'wait'
            self.last_cross_status = cur_cross
            if self.contup > 1:
                self.contup = 0
            return [
                {
                    'exchange': exchange,
                    'amount': -0.75*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'sell' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'wait'
            self.last_cross_status = cur_cross
            if self.contup > 1:
                self.contup = 0
            return [
                {
                    'exchange': exchange,
                    'amount': 0.75*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'sell' and cur_cross == self.DOWN and self.last_cross_status == self.DOWN:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            if self.contup > 1:
                self.contup = 0
            return [
                {
                    'exchange': exchange,
                    'amount': 1.5*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'buy' and cur_cross == self.UP and self.last_cross_status == self.UP:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            if self.contdown > 1:
                self.contdown = 0
            return [
                {
                    'exchange': exchange,
                    'amount': -1.5*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'buy' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'wait'
            self.last_cross_status = cur_cross
            if self.contdown > 1:
                self.contdown = 0
            return [
                {
                    'exchange': exchange,
                    'amount': -0.75*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'wait'
            self.last_cross_status = cur_cross
            if self.contdown > 1:
                self.contdown = 0
            return [
                {
                    'exchange': exchange,
                    'amount': 0.75*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'buy' and cur_cross == self.DOWN and self.last_cross_status == self.DOWN:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            if self.contdown > 1:
                self.contdown = self.contdown + 1
                return [
                    {
                        'exchange': exchange,
                        'amount': -1*self.contdown*self.ratio / close_price,
                        'price': -1,
                        'type': 'MARKET',
                        'pair': pair,
                    }
                ]
            return [
                {
                    'exchange': exchange,
                    'amount': 1.5*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'wait' and cur_cross == self.UP and self.last_cross_status == self.UP:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'sell'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -0.75*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'wait' and cur_cross == self.UP and self.last_cross_status == self.DOWN:
            Log('buying 1 unit of ' + str(target_currency))
            self.last_type = 'wait'
            self.notrade = 10*self.period
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': 0,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'wait' and cur_cross == self.DOWN and self.last_cross_status == self.UP:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'wait'
            self.last_cross_status = cur_cross
            self.notrade = 10*self.period
            return [
                {
                    'exchange': exchange,
                    'amount': 0,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        elif self.last_type == 'wait' and cur_cross == self.DOWN and self.last_cross_status == self.DOWN:
            Log('assets before selling: ' + str(self['assets'][exchange][base_currency]))
            self.last_type = 'buy'
            self.last_cross_status = cur_cross
            return [
                {
                    'exchange': exchange,
                    'amount': -0.75*self.ratio / close_price,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        else :
            return [
                {
                    'exchange': exchange,
                    'amount': 0,
                    'price': -1,
                    'type': 'MARKET',
                    'pair': pair,
                }
            ]
        self.last_cross_status = cur_cross

        return []