from database import connect_db
from tabulate import tabulate


def select_customer():

    conn = connect_db()

    if conn is None:
        return None

    cursor = None

    try:
        cursor = conn.cursor()
        phone = input("Enter customer phone number:")

        query = """
        SELECT customer_id, name, email, phone
        FROM customers
        where phone = %s;"""

        cursor.execute(query, (phone,))

        customer = cursor.fetchone()

        if customer:
            print("\nCustomer Found: ")
            headers = ["Customer ID", "Name", "Email", "Phone"]
            print(tabulate([customer], headers=headers, tablefmt="grid"))
            return customer[0]  # Return customer ID

        else:
            print("Customer not found! Please register first.")
            return None

    except Exception as e:
        print("Customer Search Failed:", e)

    finally:
        if cursor:
            cursor.close()
        conn.close()


def view_available_books():

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        SELECT book_id, title, author, price, stock, category
        FROM books
        WHERE stock > 0
        ORDER BY book_id;
        """

        cursor.execute(query)

        books = cursor.fetchall()

        if books:

            headers = ["Book ID", "Title", "Author", "Price", "Stock", "Category"]
            print("\n========== AVAILABLE BOOKS ==========")
            print(tabulate(books, headers=headers, tablefmt="grid"))

        else:
            print("No books available in stock.")

    except Exception as e:
        print("Unable to display available books:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()


def create_sale():

    # Step 1: Select Customer
    customer_id = select_customer()

    if customer_id is None:
        return None

    # Step 2: Display Available Books
    view_available_books()

    conn = connect_db()

    if conn is None:
        return
    cursor = None

    try:
        cursor = conn.cursor()

        cart = {}

        # Step 3: Select Multiple Books
        while True:
            book_input = input("\nEnter Book ID(or 'done' to finish): ").strip()
            if book_input.lower() == "done":
                break

            try:
                book_id = int(book_input)
            except ValueError:
                print("Please enter a valid Book ID!")
                continue
            if book_id in cart:
                print("This book is already in your cart!")
                continue

            query = """
            SELECT book_id, title, price, stock
            FROM books
            WHERE book_id = %s AND stock > 0;
            """
            cursor.execute(query, (book_id,))
            book = cursor.fetchone()

            if book is None:
                print("Book Not Found!")
                continue

            book_id, title, price, stock = book

            if stock <= 0:
                print("This book is out of stock!")
                continue

            # Step 4: Enter Quantity
            try:
                quantity = int(input("Enter Quantity:"))
            except ValueError:
                print("Please enter a valid quantity!")
                continue

            if quantity <= 0:
                print("Quantity must be greater than 0!")
                continue

            if quantity > stock:
                print("Insufficient stock!")
                print("Available Stock: ", stock)
                continue

            cart[book_id] = {"title": title, "price": price, "quantity": quantity}
            print(f"{title} added to cart succesfully!")

            # Step 5: Check Whether a cart is empty or not
            if not cart:
                conn.rollback()
                print("No Books Selected! Sale Cancelled.")

            # Step 6: Lock Selected books and verify latest stock.
            # Sorting ID's helps accquire locks in a consistent order.

            for book_id in sorted(cart):
                query = """
                SELECT title, price, stock
                FROM books
                WHERE book_id = %s
                FOR UPDATE;
                """

                cursor.execute(query, (book_id,))
                book = cursor.fetchone()

                if book is None:
                    raise Exception(f"Book with ID {book_id} no longer exists!")
                title, price, stock = book
                quantity = cart[book_id]["quantity"]

                if quantity > stock:
                    raise Exception(
                        f"Insufficient Stock for {title}." f"Avialable: {stock}"
                    )
                # Use the latest database price
                cart[book_id]["title"] = title
                cart[book_id]["price"] = price

            # Step 7: Calculate Total Amount
            total_amount = sum(
                item["price"] * item["quantity"] for item in cart.values()
            )

            # Step 8: Insert Main Sale Record
            query = """
            INSERT INTO sales (customer_id, sale_date, total_amount)
            VALUES (%s, CURRENT_TIMESTAMP, %s)
            RETURNING sale_id;
            """

            cursor.execute(query, (customer_id, total_amount))

            sale_id = cursor.fetchone()[0]

            # Step 9: Insert sale items and update stock
            for book_id, item in cart.items():
                quantity = item["quantity"]
                price = item["price"]

                query = """
                INSERT INTO sale_items
                (sale_id, book_id, quantity, price)
                VALUES (%s, %s, %s, %s);
                """

                cursor.execute(query, (sale_id, book_id, quantity, price))

                query = """
                UPDATE books
                SET stock = stock - %s
                WHERE book_id = %s AND stock >= %s;
                """

                cursor.execute(query, (quantity, book_id, quantity))

                if cursor.rowcount != 1:
                    raise Exception("Unable to update book stock!")

        # Step 10: Get Custoemer Details
        query = """
        SELECT name, phone
        FROM customers
        WHERE customer_id = %s;
        """

        cursor.execute(query, (customer_id,))
        customer = cursor.fetchone()

        if customer is None:
            raise Exception("Customer details not Found!")

        # Step 11: Commit Transaction
        conn.commit()

        # Step 12: Generate Bill
        print("\n" + "=" * 50)
        print("=============BOOK STORE BILL=============")
        print("=" * 50)

        print("Sale ID:", sale_id)
        print("Customer Name:", customer[0])
        print("Customer Phone:", customer[1])

        bill_headers = ["Book ID", "Title", "Quantity", "Price", "Subtotal"]

        bill_rows = []

        for book_id, item in cart.items():

            subtotal = item["price"] * item["quantity"]

            bill_rows.append(
                [book_id, item["title"], item["quantity"], item["price"], subtotal]
            )
        print(tabulate(bill_rows, headers=bill_headers, tablefmt="grid"))

        print("\nTotal Amount:", total_amount)
        print("=" * 50)
        print("       Thank you for shopping!")
        print("=" * 50)

    except Exception as e:

        conn.rollback()
        print("\nSale Failed:", e)
        print("All database changes have been rolled back.")

    finally:

        if cursor:
            cursor.close()

        conn.close()


def view_sales():

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        SELECT sale_id, customer_id, sale_date, total_amount
        FROM sales
        ORDER BY sale_id DESC;
        """

        cursor.execute(query)

        sales = cursor.fetchall()

        if sales:
            headers = ["Sale ID", "Customer ID", "Sale Date", "Total Amount"]

            print("\n========== SALES HISTORY ==========")

            print(tabulate(sales, headers=headers, tablefmt="grid"))

        else:
            print("\nNo sales records found!")

    except Exception as e:
        print("Unable to display sales:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()


def view_sale_bills(sale_id):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        # Get sale and customer information
        query = """
        SELECT
            s.sale_id,
            s.sale_date,
            c.name,
            c.phone,
            s.total_amount
        FROM sales s
        JOIN customers c
            ON s.customer_id = c.customer_id
        WHERE s.sale_id = %s;
        """

        cursor.execute(query, (sale_id,))

        sale = cursor.fetchone()

        if sale is None:
            print("\nSale record not found!")
            return

        # Get purchased book details
        query = """
        SELECT
            si.book_id,
            b.title,
            si.quantity,
            si.price,
            (si.quantity * si.price) AS subtotal
        FROM sale_items si
        JOIN books b
            ON si.book_id = b.book_id
        WHERE si.sale_id = %s;
        """

        cursor.execute(query, (sale_id,))

        items = cursor.fetchall()

        # Display bill
        print("\n" + "=" * 50)
        print("              BOOK STORE BILL")
        print("=" * 50)

        print("Sale ID:", sale[0])
        print("Sale Date:", sale[1])
        print("Customer Name:", sale[2])
        print("Customer Phone:", sale[3])

        headers = ["Book ID", "Title", "Quantity", "Price", "Subtotal"]

        if items:
            print("\nPurchased Books:")
            print(tabulate(items, headers=headers, tablefmt="grid"))

        else:
            print("\nNo book details found for this sale.")

        print("\nTotal Amount:", sale[4])
        print("=" * 50)

    except Exception as e:
        print("Unable to display sale details:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()
