
class Book:

    def __init__(self, title, author, price, stock, category):
        self.title = title
        self.author = author
        self.price = price
        self.stock = stock
        self.category = category

    def display_details(self):
        print("Book Title:", self.title)
        print("Author:", self.author)
        print("Price:", self.price)
        print("Stock:", self.stock)
        print("Category:", self.category)

# book = Book(
#     "Python Basics",
#     "John Smith",
#     450,
#     10,
#     "Programming"
# )

# book.display_details()