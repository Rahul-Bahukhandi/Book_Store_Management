class SaleItem:
    
    def __init__(self, item_id, sale_id, product_id, quantity, price):
        self.item_id = item_id
        self.sale_id = sale_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

# item = SaleItem(1, 1, 5, 2, 300)

# print(item.item_id)
# print(item.sale_id)
# print(item.product_id)
# print(item.quantity)
# print(item.price)