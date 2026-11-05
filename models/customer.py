
class Customer:

    def __init__(self, name, email, phone):
        self.name = name
        self.email = email
        self.phone = phone

    def display_details(self):

        print("Customer Name:", self.name)
        print("Email:", self.email)
        print("Phone:", self.phone)

# customer = Customer(
#     "Rahul Sharma",
#     "rahul@gmail.com",
#     "9876543210"
# )

# customer.display_details()