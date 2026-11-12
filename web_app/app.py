from flask import Flask, render_template, request, redirect, url_for
from database import connect_db
from decimal import Decimal

app = Flask(__name__)

@app.route('/')
def dashboard():
    conn = connect_db()
    if conn is None:
        return f"Database Connection Failed!!!"
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Total Books
        cursor.execute("SELECT COUNT(*) FROM books")
        total_books = cursor.fetchone()[0]
        
        # Total Customers
        cursor.execute("SELECT COUNT(*) FROM customers")
        total_customers = cursor.fetchone()[0]
        
        # Total Sales
        cursor.execute("SELECT COUNT(*) FROM sales")
        total_sales = cursor.fetchone()[0]
        
         # Recent Sales (Latest 5 Sales)
        cursor.execute("""
            SELECT
                s.sale_id,
                c.name,
                s.sale_date,
                s.total_amount
            FROM sales s
            JOIN customers c
                ON s.customer_id = c.customer_id
            ORDER BY s.sale_date DESC, s.sale_id DESC
            LIMIT 5;
        """)

        recent_sales = cursor.fetchall()

        return render_template(
            "dashboard.html",
            total_books=total_books,
            total_customers=total_customers,
            total_sales=total_sales,
            recent_sales=recent_sales
            )
    except Exception as e:
        return f"Dashboard Error: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()
    
# View And Search Books
@app.route("/books")
def books():
    conn = connect_db()
    if conn is None:
        return f"Database connection failed!!"
    cursor = None
    try:
        cursor = conn.cursor()
        search = request.args.get("search", "").strip()
        category = request.args.get("category", "").strip()
        query = """
        SELECT book_id, title, author, price, stock, category
        FROM books
        WHERE (title ILike %s OR author ILike %s)
        """
        search_value = f"%{search}%"
        params = [search_value, search_value]

        if category:
            query += " AND category = %s"
            params.append(category)

        query += " ORDER BY book_id"
        
        cursor.execute(query, tuple(params))
        book_list = cursor.fetchall()
        
         # Get all available categories
        cursor.execute("""
            SELECT DISTINCT category
            FROM books
            WHERE category IS NOT NULL
            ORDER BY category;
        """)
        categories = cursor.fetchall()
        
        return render_template(
            "books.html",
            books = book_list,
            search = search,
            categories=categories,
            selected_category=category
        )
    except Exception as e:
        return f"Error: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()
    
# ADD NEW BOOK
@app.route("/books/add", methods=["Post"])
def add_book():
    conn = connect_db()
    if conn is None:
        return f"Database Connection Failed!!"
    cursor = None
    try:
        cursor = conn.cursor()
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        price = request.form["price"]
        stock = request.form["stock"]
        category = request.form["category"].strip()
        
        query = """
        INSERT INTO books (title, author, price, stock, category)
        VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(
            query,
            (title, author, price, stock, category)
        )
        conn.commit()
        return redirect(url_for("books"))
    except Exception as e:
        conn.rollback()
        return f"Error in adding a book: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()

# Edit Book Page
@app.route("/books/edit/<int:book_id>")
def edit_book(book_id):
    conn = connect_db()
    if conn is None:
        return f"Database Connection Failed!!"
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT book_id, title, author, price, stock category
            FROM books
            WHERE book_id = %s;
            """,
            (book_id,)
        )
        book = cursor.fetchone()
        if book is None:
            return f"Book Not Found"
        return render_template("edit_book.html", book=book)
    except Exception as e:
        return f"Error: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()
    
# UPDATE Book
@app.route("/books/update/<int:book_id>", methods=["POST"])
def update_book(book_id):
    conn = connect_db()
    if conn is None:
        return f"Database Connection Failed!!!"
    cursor = None
    
    try:
        
        cursor = conn.cursor()
        title = request.form["title"].strip()
        author = request.form["author"].strip()
        price = request.form["price"]
        stock = request.form["stock"]
        category = request.form["category"].strip()
        
        query = """
        UPDATE books
        SET title = %s,
            author = %s,
            price = %s,
            stock = %s,
            category = %s
        WHERE book_id = %s;
        """
        cursor.execute(
            query,
            (title, author, price, stock, category, book_id)
        )
        conn.commit()
        return redirect(url_for("books"))
    except Exception as e:
        conn.rollback()
        return f"Error in updating book: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()

# DELETE Book
@app.route("/books/delete/<int:book_id>", methods=["POST"])
def delete_book(book_id):
    conn = connect_db()
    if conn is None:
        return f"Database Connection Failed!!!"
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM books WHERE book_id = %s;",
            (book_id,)
        )
        conn.commit()
        return redirect(url_for("books"))
    except Exception as e:
        conn.rollback()
        return f"Error in deleting book: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()
        
# Customers
@app.route("/customers")
def customers():
    conn = connect_db()
    if conn is None:
        return "Database Conncetion Failed!!!"
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Get Search Value
        search = request.args.get("search", "").strip()
        
        # Fetch customers
        query = """
        SELECT customer_id, name, email, phone
        FROM customers
        WHERE name ILIKE %s
            OR phone ILIKE %s
        ORDER BY customer_id;
        """
        search_value = f"%{search}%"
        cursor.execute(query, (search_value,search_value))
        customer_list = cursor.fetchall()
        return render_template(
            "customers.html",
            customers = customer_list,
            search = search
        )
    except Exception as e:
        return f"Customer Error: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()

# ADD NEW CUSTOMER
@app.route("/customers/add", methods=["POST"])
def add_customer():

    conn = connect_db()

    if conn is None:
        return f"Database Connection Failed!!"

    cursor = None

    try:
        cursor = conn.cursor()

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        # Validate phone number
        if not phone.isdigit() or len(phone) != 10:
            return "Phone number must be exactly 10 digits!"

        query = """
        INSERT INTO customers (name, email, phone)
        VALUES (%s, %s, %s);
        """

        cursor.execute(query, (name, email, phone))

        conn.commit()

        return redirect(url_for("customers"))

    except Exception as e:
        conn.rollback()
        return f"Error in adding customer: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()

# EDIT CUSTOMER PAGE
@app.route("/customers/edit/<int:customer_id>")
def edit_customer(customer_id):

    conn = connect_db()

    if conn is None:
        return f"Database Connection Failed!!"

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT customer_id, name, email, phone
            FROM customers
            WHERE customer_id = %s;
            """,
            (customer_id,)
        )

        customer = cursor.fetchone()

        if customer is None:
            return "Customer Not Found"

        return render_template(
            "edit_customers.html",
            customer=customer
        )

    except Exception as e:
        return f"Error: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()

# UPDATE CUSTOMER
@app.route("/customers/update/<int:customer_id>", methods=["POST"])
def update_customer(customer_id):

    conn = connect_db()

    if conn is None:
        return f"Database Connection Failed!!"

    cursor = None

    try:
        cursor = conn.cursor()

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()

        # Validate phone number
        if not phone.isdigit() or len(phone) != 10:
            return "Phone number must be exactly 10 digits!"

        query = """
        UPDATE customers
        SET name = %s,
            email = %s,
            phone = %s
        WHERE customer_id = %s;
        """

        cursor.execute(
            query,
            (name, email, phone, customer_id)
        )

        conn.commit()

        return redirect(url_for("customers"))

    except Exception as e:
        conn.rollback()
        return f"Error in updating customer: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()

# DELETE CUSTOMER
@app.route("/customers/delete/<int:customer_id>", methods=["POST"])
def delete_customer(customer_id):

    conn = connect_db()

    if conn is None:
        return f"Database Connection Failed!!"

    cursor = None

    try:
        cursor = conn.cursor()

        # Check customer sales history
        cursor.execute(
            """
            SELECT sale_id
            FROM sales
            WHERE customer_id = %s
            LIMIT 1;
            """,
            (customer_id,)
        )

        if cursor.fetchone():
            return "Cannot delete customer because sales records exist!"

        cursor.execute(
            "DELETE FROM customers WHERE customer_id = %s;",
            (customer_id,)
        )

        conn.commit()

        return redirect(url_for("customers"))

    except Exception as e:
        conn.rollback()
        return f"Error in deleting customer: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()

@app.route("/sales")
def sales():

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        # Get filter values from URL
        search = request.args.get("search", "").strip()
        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")

        # Customer dropdown
        cursor.execute("""
            SELECT customer_id, name
            FROM customers
            ORDER BY name;
        """)
        customer_list = cursor.fetchall()

        # Available books dropdown
        cursor.execute("""
            SELECT book_id, title, author, price, stock
            FROM books
            WHERE stock > 0
            ORDER BY title;
        """)
        book_list = cursor.fetchall()

        # Build sales history filters
        query = """
            SELECT
                s.sale_id,
                c.name,
                s.sale_date,
                s.total_amount
            FROM sales s
            JOIN customers c
                ON s.customer_id = c.customer_id
        """

        conditions = []
        params = []

        # Search by Sale ID or Customer Name
        if search:
            conditions.append("""
                (
                    s.sale_id::text ILIKE %s
                    OR c.name ILIKE %s
                )
            """)
            search_value = f"%{search}%"
            params.extend([search_value, search_value])

        # Filter by start date
        if start_date:
            conditions.append("s.sale_date::date >= %s")
            params.append(start_date)

        # Filter by end date
        if end_date:
            conditions.append("s.sale_date::date <= %s")
            params.append(end_date)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY s.sale_id DESC;"

        cursor.execute(query, tuple(params))
        sales_list = cursor.fetchall()

        return render_template(
            "sales.html",
            customers=customer_list,
            books=book_list,
            sales=sales_list,
            search=search,
            start_date=start_date,
            end_date=end_date
        )

    except Exception as e:
        return f"Sales Error: {e}"

    finally:
        if cursor:
            cursor.close()

        conn.close()
        
# ADD NEW SALE
@app.route("/sales/add", methods=["POST"])
def add_sale():

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!!"

    cursor = None

    try:
        cursor = conn.cursor()

        # 1. Get Customer ID
        customer_id = request.form["customer_id"]

        # 2. Get Book IDs and Quantities
        book_ids = request.form.getlist("book_id[]")
        quantities = request.form.getlist("quantity[]")

        if not book_ids or len(book_ids) != len(quantities):
            return "Please select at least one book and quantity!"

        # 3. Validate and combine duplicate books
        selected_books = {}

        for book_id, quantity in zip(book_ids, quantities):

            book_id = int(book_id)
            quantity = int(quantity)

            if quantity <= 0:
                return "Quantity must be greater than zero!"

            selected_books[book_id] = (
                selected_books.get(book_id, 0) + quantity
            )

        # 4. Check Customer Exists
        cursor.execute(
            "SELECT customer_id FROM customers WHERE customer_id = %s;",
            (customer_id,)
        )

        if cursor.fetchone() is None:
            return "Customer Not Found!"

        # 5. Check Books and Available Stock
        total_amount = Decimal("0.00")
        sale_items = []

        for book_id, quantity in sorted(selected_books.items()):

            cursor.execute(
                """
                SELECT title, price, stock
                FROM books
                WHERE book_id = %s
                FOR UPDATE;
                """,
                (book_id,)
            )

            book = cursor.fetchone()

            if book is None:
                raise ValueError(f"Book ID {book_id} not found!")

            title, price, stock = book

            if quantity > stock:
                raise ValueError(
                    f"Insufficient stock for {title}. "
                    f"Available stock: {stock}"
                )

            item_total = price * quantity
            total_amount += item_total

            sale_items.append(
                (book_id, quantity, price)
            )

        # 6. Insert Sale Record
        cursor.execute(
            """
            INSERT INTO sales (customer_id, total_amount)
            VALUES (%s, %s)
            RETURNING sale_id;
            """,
            (customer_id, total_amount)
        )

        sale_id = cursor.fetchone()[0]

        # 7. Insert Sale Items and Update Stock
        for book_id, quantity, price in sale_items:

            cursor.execute(
                """
                INSERT INTO sale_items
                    (sale_id, book_id, quantity, price)
                VALUES (%s, %s, %s, %s);
                """,
                (sale_id, book_id, quantity, price)
            )

            cursor.execute(
                """
                UPDATE books
                SET stock = stock - %s
                WHERE book_id = %s;
                """,
                (quantity, book_id)
            )

        # 8. Save Transaction
        conn.commit()

        return redirect(url_for("sales"))

    except Exception as e:
        conn.rollback()
        return f"Error in creating sale: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()

# VIEW SALE DETAILS
@app.route("/sales/<int:sale_id>")
def view_sale_details(sale_id):

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                s.sale_id,
                s.sale_date,
                s.total_amount,
                c.name,
                c.email,
                c.phone
            FROM sales s
            JOIN customers c
                ON s.customer_id = c.customer_id
            WHERE s.sale_id = %s;
        """, (sale_id,))

        sale = cursor.fetchone()

        if sale is None:
            return "Sale not found!"

        cursor.execute("""
            SELECT
                b.title,
                b.author,
                si.quantity,
                si.price,
                (si.quantity * si.price) AS subtotal
            FROM sale_items si
            JOIN books b
                ON si.book_id = b.book_id
            WHERE si.sale_id = %s;
        """, (sale_id,))

        sale_items = cursor.fetchall()

        return render_template(
            "sale_details.html",
            sale=sale,
            sale_items=sale_items
        )

    except Exception as e:
        return f"Sale Details Error: {e}"

    finally:
        if cursor:
            cursor.close()

        conn.close()
       
if __name__ == '__main__':
    app.run(debug=True)