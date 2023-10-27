import yaml

INFINITE = float('inf')


class Filter:
    def __init__(self, filter_config_file_path: str):
        self.filter_config_file_path: str = filter_config_file_path
        self.config = self.reinit_config()

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
