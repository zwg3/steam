import yaml

INFINITE = float('inf')

class Controller:
    pass


class Filter:
    def __init__(self, filter_config_file_path: str):
        self.filter_config_file_path: str = filter_config_file_path
        # self.config = self.reinit_config()
        #
        # self.games: dict[str, list[int]]
        #
        # # pagination level
        # self.orders_count: list[float]
        # self.cheapest_order_price: list[float]
        #
        # # product level
        # self.mean_sold_week: list[float] | None
        # self.days_analyze_price: int = 7
        # self.history_wts_price_percent: float = 0
        # self.reject_outlier_coef: float = 0
        #
        # # histogram level
        # self.histogram_depth_coef: int = 1
        # self.wtb_order_price: list[float] = [0, INFINITE]
        # self.profit_percent: float = 1.0
        # self.reinit_config()

    def reinit_config(self) -> dict:
        with open(self.filter_config_file_path, 'r') as f:
            return yaml.load(f, Loader=yaml.CLoader)

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
