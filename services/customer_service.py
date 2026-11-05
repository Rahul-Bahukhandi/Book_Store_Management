from database import connect_db
from tabulate import tabulate


def register_customer(customer):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        INSERT INTO customers (name, email, phone)
        VALUES (%s, %s, %s)
        RETURNING customer_id;
        """

        values = (
            customer.name,
            customer.email,
            customer.phone
        )

        cursor.execute(query, values)

        customer_id = cursor.fetchone()[0]

        conn.commit()

        print("Customer registered successfully!")
        print("Customer ID:", customer_id)

    except Exception as e:

        conn.rollback()
        print("Customer registration failed:", e)

    finally:

        if cursor:
            cursor.close()

        conn.close()


def view_customers():

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        SELECT customer_id, name, email, phone
        FROM customers
        ORDER BY customer_id;
        """

        cursor.execute(query)

        customers = cursor.fetchall()

        if not customers:
            print("No customers registered yet.")
            return

        headers = [
            "Customer ID",
            "Name",
            "Email",
            "Phone"
        ]

        print(tabulate(
            customers,
            headers=headers,
            tablefmt="grid"
        ))

    except Exception as e:

        print("Error fetching customers:", e)

    finally:

        if cursor:
            cursor.close()

        conn.close()


def search_customer(customer_id):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        SELECT customer_id, name, email, phone
        FROM customers
        WHERE customer_id = %s;
        """

        cursor.execute(query, (customer_id,))

        customer = cursor.fetchone()

        if customer:

            print("\nCustomer Found!")
            print("Customer ID:", customer[0])
            print("Name:", customer[1])
            print("Email:", customer[2])
            print("Phone:", customer[3])

        else:

            print("Customer not found!")

    except Exception as e:

        print("Search error:", e)

    finally:

        if cursor:
            cursor.close()

        conn.close()


def update_customer(customer_id):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        # Check customer exists
        cursor.execute(
            """
            SELECT * FROM customers
            WHERE customer_id = %s;
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if not customer:
            print("Customer not found!")
            return

        print("\nCurrent Customer Details:")
        print("Name:", customer[1])
        print("Email:", customer[2])
        print("Phone:", customer[3])

        print("\nEnter Updated Details:")

        name = input("New name: ")
        email = input("New email: ")
        phone = input("New phone: ")

        query = """
        UPDATE customers
        SET name = %s,
            email = %s,
            phone = %s
        WHERE customer_id = %s;
        """

        values = (
            name,
            email,
            phone,
            customer_id
        )

        cursor.execute(query, values)

        conn.commit()

        print("Customer updated successfully!")

    except Exception as e:

        conn.rollback()
        print("Customer update failed:", e)

    finally:

        if cursor:
            cursor.close()

        conn.close()
