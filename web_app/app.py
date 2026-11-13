from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)

from database import connect_db
from decimal import Decimal
from functools import wraps

from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.secret_key = "bookstore_secret_key_change_later"

def set_toast(message, category="success"):
    session["toast"] = {
        "message": message,
        "category": category
    }

@app.context_processor
def inject_toast():
    return {
        "toast": session.pop("toast", None)
    }

def login_required(route_function):
    @wraps(route_function)
    def wrapper(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("admin_login"))
        return route_function(*args, **kwargs)
    return wrapper

# ADMIN LOGIN
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if "admin_id" in session:
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        # Get login details first
        login_input = request.form.get("login", "").strip()
        password = request.form.get("password", "")

        if not login_input or not password:
            set_toast("Please enter email/phone and password!", "error")
            return render_template(url_for("admin_login.html"))

        conn = connect_db()

        if conn is None:
            return "Database Connection Failed!"

        cursor = None

        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT admin_id, username, email, phone, password_hash
                FROM admins
                WHERE email = %s OR phone = %s;
            """, (login_input, login_input))

            admin = cursor.fetchone()

            if admin and check_password_hash(admin[4], password):

                session["admin_id"] = admin[0]
                session["admin_name"] = admin[1]

                set_toast("Login successful!", "success")

                return redirect(url_for("dashboard"))

            else:
                set_toast("Invalid email/phone or password!", "error")

        except Exception as e:
            conn.rollback()
            return f"Login Error: {e}"

        finally:
            if cursor:
                cursor.close()

            conn.close()

    return render_template("admin_auth.html")

# ADMIN SIGN UP
@app.route("/admin/signup", methods=["POST"])
def admin_signup():

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Validate empty fields
    if not all([username, email, phone, password, confirm_password]):
        set_toast("All fields are required!", "error")
        return redirect(url_for("admin_login"))

    # Validate phone number
    if not phone.isdigit() or len(phone) != 10:
        set_toast("Phone number must be exactly 10 digits!", "error")
        return redirect(url_for("admin_login"))

    # Validate password
    if len(password) < 8:
        set_toast("Password must contain at least 8 characters!", "error")
        return redirect(url_for("admin_login"))

    # Confirm password
    if password != confirm_password:
        set_toast("Passwords do not match!", "error")
        return redirect(url_for("admin_login"))

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        # Check existing email or phone
        cursor.execute("""
            SELECT admin_id
            FROM admins
            WHERE email = %s OR phone = %s;
        """, (email, phone))

        if cursor.fetchone():
            set_toast("Email or phone number already registered!", "error")
            return redirect(url_for("admin_login"))

        # Hash password
        password_hash = generate_password_hash(password)

        # Insert new admin
        cursor.execute("""
            INSERT INTO admins
                (username, email, phone, password_hash)
            VALUES (%s, %s, %s, %s);
        """, (username, email, phone, password_hash))

        conn.commit()

        set_toast("Account created successfully! Please login.", "success")

        return redirect(url_for("admin_login"))

    except Exception as e:
        conn.rollback()
        return f"Sign Up Error: {e}"

    finally:
        if cursor:
            cursor.close()

        conn.close()

# ADMIN LOGOUT
@app.route("/admin/logout")
def admin_logout():

    session.clear()

    set_toast("You have been logged out successfully!", "success")

    return redirect(url_for("admin_login"))

# Dashboard
@app.route('/')
@login_required
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
@login_required
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
            books=book_list,
            search=search,
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
@login_required
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
        cursor.execute(query, (search_value, search_value))
        customer_list = cursor.fetchall()
        return render_template(
            "customers.html",
            customers=customer_list,
            search=search
        )
    except Exception as e:
        return f"Customer Error: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()

# ADD NEW CUSTOMER
@app.route("/customers/add", methods=["POST"])
@login_required
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
@login_required
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
@login_required
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
@login_required
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

# Sales
@app.route("/sales")
@login_required
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
@login_required
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
@login_required
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


# BOOK RENTALS
@app.route("/rentals")
@login_required
def rentals():

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        # Customers for the Rent a Book form
        cursor.execute("""
            SELECT customer_id, name, phone
            FROM customers
            ORDER BY name;
        """)
        customer_list = cursor.fetchall()

        # Only books with available stock can be rented
        cursor.execute("""
            SELECT book_id, title, author, price, stock
            FROM books
            WHERE stock > 0
            ORDER BY title;
        """)
        book_list = cursor.fetchall()

        # Active rentals are shown as Overdue when their due date has passed.
        # Rent is calculated using the number of calendar days since rental_date.
        cursor.execute("""
            SELECT
                r.rental_id,
                c.name,
                c.phone,
                b.title,
                r.rental_date,
                r.due_date,
                r.rental_days,
                r.daily_rent,
                CASE
                    WHEN r.status = 'active' AND CURRENT_DATE > r.due_date
                        THEN 'overdue'
                    ELSE r.status
                END AS display_status,
                CASE
                    WHEN r.status = 'active'
                        THEN r.daily_rent * GREATEST(CURRENT_DATE - r.rental_date, 0)
                    ELSE COALESCE(r.final_rent, 0)
                END AS current_rent,
                b.price AS book_price,
                r.return_date,
                r.purchase_date
            FROM book_rentals r
            JOIN customers c ON c.customer_id = r.customer_id
            JOIN books b ON b.book_id = r.book_id
            ORDER BY
                CASE WHEN r.status = 'active' AND CURRENT_DATE > r.due_date THEN 0
                     WHEN r.status = 'active' THEN 1
                     ELSE 2
                END,
                r.rental_id DESC;
        """)
        rental_list = cursor.fetchall()

        return render_template(
            "rentals.html",
            customers=customer_list,
            books=book_list,
            rentals=rental_list
        )

    except Exception as e:
        return f"Rentals Error: {e}"

    finally:
        if cursor:
            cursor.close()
        conn.close()

# CREATE A NEW BOOK RENTAL
@app.route("/rentals/add", methods=["POST"])
@login_required
def add_rental():

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        customer_id = int(request.form.get("customer_id", "0"))
        book_id = int(request.form.get("book_id", "0"))
        rental_days = int(request.form.get("rental_days", "0"))
        daily_rent = Decimal(request.form.get("daily_rent", "20"))

        if customer_id <= 0 or book_id <= 0:
            raise ValueError("Please select a valid customer and book!")

        if rental_days <= 0:
            raise ValueError("Rental duration must be at least 1 day!")

        if daily_rent <= 0:
            raise ValueError("Daily rent must be greater than zero!")

        # Confirm customer exists
        cursor.execute(
            "SELECT customer_id FROM customers WHERE customer_id = %s;",
            (customer_id,)
        )
        if cursor.fetchone() is None:
            raise ValueError("Customer not found!")

        # Lock the book row so two admins cannot rent the last copy simultaneously
        cursor.execute("""
            SELECT title, stock
            FROM books
            WHERE book_id = %s
            FOR UPDATE;
        """, (book_id,))

        book = cursor.fetchone()

        if book is None:
            raise ValueError("Book not found!")

        title, stock = book

        if stock < 1:
            raise ValueError(f"{title} is currently out of stock!")

        # Create rental. Due date is rental date + selected rental days.
        cursor.execute("""
            INSERT INTO book_rentals
                (customer_id, book_id, rental_date, rental_days, due_date, daily_rent)
            VALUES
                (%s, %s, CURRENT_DATE, %s, CURRENT_DATE + %s, %s);
        """, (customer_id, book_id, rental_days, rental_days, daily_rent))

        # One physical copy is now with the customer
        cursor.execute("""
            UPDATE books
            SET stock = stock - 1
            WHERE book_id = %s;
        """, (book_id,))

        conn.commit()
        set_toast("Book rental created successfully!", "success")
        return redirect(url_for("rentals"))

    except (ValueError, TypeError, ArithmeticError) as e:
        conn.rollback()
        set_toast(str(e), "error")
        return redirect(url_for("rentals"))

    except Exception as e:
        conn.rollback()
        set_toast(f"Error in creating rental: {e}", "error")
        return redirect(url_for("rentals"))

    finally:
        if cursor:
            cursor.close()
        conn.close()

# RETURN A RENTED BOOK
@app.route("/rentals/return/<int:rental_id>", methods=["POST"])
@login_required
def return_rental(rental_id):

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        # Lock the rental row to prevent a duplicate return
        cursor.execute("""
            SELECT book_id, daily_rent, rental_date, status
            FROM book_rentals
            WHERE rental_id = %s
            FOR UPDATE;
        """, (rental_id,))

        rental = cursor.fetchone()

        if rental is None:
            raise ValueError("Rental record not found!")

        book_id, daily_rent, rental_date, status = rental

        if status != "active":
            raise ValueError("This rental is already closed!")

        # The agreed rule: rent keeps increasing until the book is returned.
        cursor.execute("""
            SELECT %s * GREATEST(CURRENT_DATE - %s, 0);
        """, (daily_rent, rental_date))
        final_rent = cursor.fetchone()[0]

        cursor.execute("""
            UPDATE book_rentals
            SET status = 'returned',
                return_date = CURRENT_DATE,
                final_rent = %s
            WHERE rental_id = %s;
        """, (final_rent, rental_id))

        # Returned physical copy becomes available again
        cursor.execute("""
            UPDATE books
            SET stock = stock + 1
            WHERE book_id = %s;
        """, (book_id,))

        conn.commit()
        set_toast(f"Book returned successfully. Final rent: Rs. {final_rent}", "success")
        return redirect(url_for("rentals"))

    except ValueError as e:
        conn.rollback()
        set_toast(str(e), "error")
        return redirect(url_for("rentals"))

    except Exception as e:
        conn.rollback()
        set_toast(f"Error in returning book: {e}", "error")
        return redirect(url_for("rentals"))

    finally:
        if cursor:
            cursor.close()
        conn.close()

# CONVERT AN ACTIVE RENTAL INTO A SALE
@app.route("/rentals/purchase/<int:rental_id>", methods=["POST"])
@login_required
def purchase_rental(rental_id):

    conn = connect_db()

    if conn is None:
        return "Database Connection Failed!"

    cursor = None

    try:
        cursor = conn.cursor()

        # Lock rental and book records during conversion
        cursor.execute("""
            SELECT
                r.customer_id,
                r.book_id,
                r.daily_rent,
                r.rental_date,
                r.status,
                b.price
            FROM book_rentals r
            JOIN books b ON b.book_id = r.book_id
            WHERE r.rental_id = %s
            FOR UPDATE OF r, b;
        """, (rental_id,))

        rental = cursor.fetchone()

        if rental is None:
            raise ValueError("Rental record not found!")

        customer_id, book_id, daily_rent, rental_date, status, book_price = rental

        if status != "active":
            raise ValueError("Only active rentals can be converted into a purchase!")

        # Calculate accumulated rent up to the purchase date
        cursor.execute("""
            SELECT %s * GREATEST(CURRENT_DATE - %s, 0);
        """, (daily_rent, rental_date))
        accumulated_rent = cursor.fetchone()[0]

        # Purchase amount = full book price + accumulated rental charges
        total_amount = book_price + accumulated_rent

        # Add the purchase to the existing Sales module
        cursor.execute("""
            INSERT INTO sales (customer_id, total_amount)
            VALUES (%s, %s)
            RETURNING sale_id;
        """, (customer_id, total_amount))

        sale_id = cursor.fetchone()[0]

        # Store one sale item. Its price includes book price + rental charges,
        # so the existing Sales total and sale-item subtotal remain consistent.
        cursor.execute("""
            INSERT INTO sale_items (sale_id, book_id, quantity, price)
            VALUES (%s, %s, 1, %s);
        """, (sale_id, book_id, total_amount))

        # Mark rental as purchased. Stock is NOT increased because the customer
        # keeps the same physical copy that was already removed at rental time.
        cursor.execute("""
            UPDATE book_rentals
            SET status = 'purchased',
                purchase_date = CURRENT_DATE,
                final_rent = %s
            WHERE rental_id = %s;
        """, (accumulated_rent, rental_id))

        conn.commit()
        set_toast(
            f"Rental converted into sale successfully. Total payable: Rs. {total_amount}",
            "success"
        )
        return redirect(url_for("rentals"))

    except ValueError as e:
        conn.rollback()
        set_toast(str(e), "error")
        return redirect(url_for("rentals"))

    except Exception as e:
        conn.rollback()
        set_toast(f"Error in purchasing rented book: {e}", "error")
        return redirect(url_for("rentals"))

    finally:
        if cursor:
            cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
