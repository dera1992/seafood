from decimal import Decimal
from django.conf import settings
from foodCreate.models import Products


class Cart(object):

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0,
                                      'price': str(product.price)}

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def remove(self, product):
        product_id = str(product.id)
        if product_id in self.cart:
            # self.cart[product_id]['quantity'] -= 1
            # # If the quantity is now 0, then delete the item
            # if self.cart[product_id]['quantity'] == 0:
            del self.cart[product_id]
            self.save()

    def __iter__(self):

        product_ids = [int(product_id) for product_id in self.cart.keys()]
        products = Products.objects.filter(id__in=product_ids)
        products_map = {product.id: product for product in products}
        for product_id, item in self.cart.items():
            product = products_map.get(int(product_id))
            if product:
                item['product'] = product
            item_price = Decimal(item['price'])
            item['price'] = item_price
            item['total_price'] = item_price * item['quantity']
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.session.modified = True

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
