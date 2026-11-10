from services.sale_services import(
    create_sale,
    view_sales,
<<<<<<< HEAD
    view_sale_details,
=======
    view_sale_bills,
>>>>>>> feature/sales
)

class SalesMenu:

    def run(self):

        while True:

            print("\n========== SALES MANAGEMENT ==========")
            print("1. Create New Sale")
            print("2. View All Sales")
<<<<<<< HEAD
            print("3. View Sale Details")
=======
            print("3. View Sale Bills")
>>>>>>> feature/sales
            print("4. Back to Main Menu")

            choice = input("\nEnter your choice: ")

            if choice == "1":
                create_sale()

            elif choice == "2":
                view_sales()

            elif choice == "3":

                try:
                    sale_id = int(input("Enter Sale ID: "))
<<<<<<< HEAD
                    view_sale_details(sale_id)
=======
                    view_sale_bills(sale_id)
>>>>>>> feature/sales

                except ValueError:
                    print("Please enter a valid Sale ID!")

            elif choice == "4":
                print("Returning to Main Menu...")
                break

            else:
                print("Invalid choice! Please try again.")
def sales_menu():

    while True:

        print("\n========== SALES MANAGEMENT ==========")
        print("1. Create New Sale")
        print("2. View All Sales")
        print("3. View Sale Details")
        print("4. Back to Main Menu")

        choice = input("\nEnter your choice: ")

        if choice == "1":
            create_sale()

        elif choice == "2":
            view_sales()

        elif choice == "3":

            try:
                sale_id = int(input("Enter Sale ID: "))
<<<<<<< HEAD
                view_sale_details(sale_id)
=======
                view_sale_bills(sale_id)
>>>>>>> feature/sales

            except ValueError:
                print("Please enter a valid Sale ID!")

        elif choice == "4":
            print("Returning to Main Menu...")
            break

        else:
            print("Invalid choice! Please try again.")
