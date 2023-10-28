import yaml

STEAM_FEE = 0.87
INFINITE = float('inf')


class Filter:
    def __init__(self, filter_config_file_path: str):        
        self.filter_config_file_path: str = filter_config_file_path
        self.init_config()

    def init_config(self):
        with open(self.filter_config_file_path, 'r') as f:
            self.config =  yaml.load(f, Loader=yaml.CLoader)
    
    def _reinit_config(func):
        def inner(*args, **kwargs):
            self = args[0]
            self.init_config()
            func(*args, **kwargs)
        return inner

    @_reinit_config    
    def is_game_blacklisted(self, app_id: int) -> bool | None:      
        app_id = int(app_id)
        if app_id in self.config.get('games', {}).get('blacklist', []):
            return True

    def is_game_whitelisted(self, app_id: int) -> bool | None:
        app_id = int(app_id)
        if app_id in self.config.get('games', {}).get('whitelist', []):
            return True

    def is_pagination_start(self, pagination: dict) -> bool | None:
        """
        Returns None if you need to paginate further
        False if you need to turn back
        True if pagination is matched
        """
        key = self.config.get('sorting', {}).get('sort_column', 'price')
        direction = self.config.get('sorting', {}).get('sort_dir', 'asc')
        values = self.config.get('pagination', {}).get(key, {})

        search_key = 'sell_price' if key == 'price' else 'sell_listings'
        search_value = values.get('min', 0) if direction == 'asc' else values.get('max', INFINITE) 
        if key == 'price':
            search_value *= 100

        first_product = pagination['results'][0]
        last_product = pagination['results'][-1]

        if direction == 'asc':
            if first_product[search_key] >= search_value:
                return False
            if first_product[search_key] < search_value and last_product[search_key] >= search_value:
                return True
        else:
            if first_product[search_key] >= search_value:
                return None
            if first_product[search_key] < search_value and last_product[search_key] >= search_value:
                return True
            return False

    def is_pagination_product_good(self, pagination_product: dict) -> bool | None:
        values = self.config.get('pagination', {})
        quantity = values.get('quantity', {})
        min_quantity = quantity.get('min', 0)
        max_quantity = quantity.get('max', INFINITE)

        price = values.get('price', {})
        min_price = price.get('min', 0) * 100
        max_price = price.get('max', INFINITE) * 100

        if min_price <= pagination_product['price'] <= max_price and \
                min_quantity <= pagination_product['quantity'] <= max_quantity:
            return True

    def filter_product(self, product: Product):
        sales_quantity_min = self.config.get('sales_quantity_min', 0)
        sales_quantity_max = self.config.get('sales_quantity_max', INFINITE)
        reject_outlier_coef = self.config.get('reject_outlier_coef', 1)

        # counting sales quantity
        week_history = extract_market_history(product.history.market_history, 7)
        rejected_week_history = product_sales_history_per_days(week_history, reject_outlier_coef)
        weekly_sells = count_sells(rejected_week_history)
        daily_sells = weekly_sells / 7

        if sales_quantity_min < daily_sells <= sales_quantity_max:
            # counting histogram depth
            histogram_depth_coef = self.config.get('histogram_depth_coef', 1)
            order_price_min = self.config.get('order_price_min', 0)
            order_price_max = self.config.get('order_price_max', INFINITE)
            min_profit_percent = self.config.get('min_profit_percent', 0.1)
            analyze_days = self.config.get('analyze_days', 1)
            wts_price_percent = self.config.get('graph_price_percent', 1)

            histogram_str = product.histogram.buy_order_graph
            histogram = json.loads(histogram_str)
            buy_orders = 0
            for order in histogram:
                buy_price = order[0]
                buy_quantity = order[1]
                buy_orders += buy_quantity
                if buy_price < order_price_min or buy_orders >= daily_sells * histogram_depth_coef:
                    break
                elif buy_price > order_price_max:
                    continue

                # counting wts price
                wts_price = round(buy_price / STEAM_FEE / (1 - min_profit_percent / 100), 2)
                history = extract_market_history(product.history.market_history, analyze_days)
                rejected_history = product_sales_history_per_days(history, reject_outlier_coef)
                greater_than_wts_prices = count_prices_greater_than(rejected_history, wts_price)
                greater_than_wts_prices_percent = greater_than_wts_prices / weekly_sells * 100
                if greater_than_wts_prices_percent > wts_price_percent:
                    product.wtb_price = buy_price
                    product.wts_price = wts_price
                    product.history_original = json.dumps(history)
                    product.history_rejected = json.dumps(rejected_history)
                    return product
