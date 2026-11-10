
from models.customer import Customer

from services.customer_service import (
    register_customer,
    view_customers,
    search_customer,
    update_customer
)


class CustomerMenu:

    def run(self):

        while True:

            print("\n========== CUSTOMER MANAGEMENT ==========")
            print("1. Register Customer")
            print("2. View All Customers")
            print("3. Search Customer")
            print("4. Update Customer")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ")

            if choice == "1":

                name = input("Enter customer name: ")
                email = input("Enter customer email: ")
                
                while True:
                    phone = input("Enter customer phone: ")
                    if len(phone) == 10 and phone.isdigit():
                        break
                    else:
                        print("Invalid phone number! Please enter a 10-digit number.")
                
                customer = Customer(name, email, phone)
                
                register_customer(customer)

            elif choice == "2":
                view_customers()

            elif choice == "3":

                customer_id = int(input("Enter Customer ID: "))
                search_customer(customer_id)

            elif choice == "4":

                customer_id = int(input("Enter Customer ID: "))
                update_customer(customer_id)

            elif choice == "0":
                break

            else:
                print("Invalid choice!")
