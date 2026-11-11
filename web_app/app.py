from flask import Flask, render_template, request, redirect, url_for
from database import connect_db

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

        return render_template(
            "dashboard.html",
            total_books=total_books,
            total_customers=total_customers,
            total_sales=total_sales
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
        customer_list = cursor.fetchall()
        return render_template(
            "customer.html",
            search = search
        )
    except Exception as e:
        return f"Customer Error: {e}"
    finally:
        if cursor:
            cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)