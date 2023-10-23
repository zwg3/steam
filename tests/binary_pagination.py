from ..controller import Filter

if __name__ == '__main__':
    filter = Filter('')
    filter.config = {
        'sorting': {
            'sort_column': 'price',
            'sort_dir': 'desc',
        },
        'pagination': {
            'quantity': {
                'min': 50,
                'max': 2000,
            },
            'price': {
                'min': 1,
                'max': 1,
            }
        }
    }
    print(filter.is_pagination_start({
        'results': [
            {
                'sell_listings': 25,
                'sell_price': 100
            },
            {
                'sell_listings': 50,
                'sell_price': 250
            }
        ]
    }))
