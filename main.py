from database import connect_db

from menus.book_menu import BookMenu
from menus.customer_menu import CustomerMenu
from menus.sales_menu import SalesMenu

class BookStoreApp:

    def __init__(self):

        self.book_menu = BookMenu()
        self.customer_menu = CustomerMenu()
        self.sales_menu = SalesMenu()
<<<<<<< HEAD
=======
        
>>>>>>> feature/sales
    def run(self):

        # Check database connection
        conn = connect_db()

        if conn is None:
            print("Application cannot start without database!")
            return

        conn.close()

        # print("Database connection verified!")

        while True:

            print("\n================================")
            print("     BOOK STORE MANAGEMENT")
            print("================================")

            print("1. Book Management")
            print("2. Customer Management")
            print("3. Sales Management")
            print("0. Exit")

            choice = input("Enter your choice: ")

            if choice == "1":

                self.book_menu.run()

            elif choice == "2":

                self.customer_menu.run()
                
            elif choice == "3":
                self.sales_menu.run()

            elif choice == "0":

                print("Thank you for visiting!")
                break

            else:

                print("Invalid choice!")


if __name__ == "__main__":

    app = BookStoreApp()
    app.run()

