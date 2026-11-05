from database import connect_db
from tabulate import tabulate


def add_book(book):

    conn = connect_db()

    if conn is None:
        return

    try:
        cursor = conn.cursor()

        query = """
        INSERT INTO books (title, author, price, stock, category)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING book_id;
        """

        values = (book.title, book.author, book.price, book.stock, book.category)

        cursor.execute(query, values)

        book_id = cursor.fetchone()[0]

        conn.commit()

        print("Book added successfully!")
        print("Book ID:", book_id)

    except Exception as e:
        conn.rollback()
        print("Error adding book:", e)

    finally:
        cursor.close()
        conn.close()


def view_books():

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        SELECT book_id, title, author, price, stock, category
        FROM books
        ORDER BY book_id;
        """

        cursor.execute(query)

        books = cursor.fetchall()

        if not books:
            print("No books found in the database.")
            return

        headers = ["Book ID", "Title", "Author", "Price", "Stock", "Category"]

        print(tabulate(books, headers=headers, tablefmt="grid"))

    except Exception as e:
        print("Error fetching books:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()


def search_book(book_id):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        query = """
        SELECT * FROM books
        WHERE book_id = %s;
        """

        cursor.execute(query, (book_id,))

        book = cursor.fetchone()

        if book:
            print("\nBook Found!")
            print("Book ID:", book[0])
            print("Title:", book[1])
            print("Author:", book[2])
            print("Price:", book[3])
            print("Stock:", book[4])
            print("Category:", book[5])

        else:
            print("Book not found!")

    except Exception as e:
        print("Search error:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()


def update_book(book_id):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        # Check whether book exists
        cursor.execute("SELECT * FROM books WHERE book_id = %s", (book_id,))

        book = cursor.fetchone()

        if not book:
            print("Book not found!")
            return

        print("\nCurrent Book Details:")
        print("Title:", book[1])
        print("Author:", book[2])
        print("Price:", book[3])
        print("Stock:", book[4])
        print("Category:", book[5])

        print("\nEnter Updated Details")

        title = input("New title: ")
        author = input("New author: ")
        price = float(input("New price: "))
        stock = int(input("New stock: "))
        category = input("New category: ")

        query = """
        UPDATE books
        SET title = %s,
            author = %s,
            price = %s,
            stock = %s,
            category = %s
        WHERE book_id = %s;
        """

        values = (title, author, price, stock, category, book_id)

        cursor.execute(query, values)

        conn.commit()

        print("Book updated successfully!")

    except Exception as e:
        conn.rollback()
        print("Update error:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()


def delete_book(book_id):

    conn = connect_db()

    if conn is None:
        return

    cursor = None

    try:
        cursor = conn.cursor()

        # Check whether book exists
        cursor.execute("SELECT title FROM books WHERE book_id = %s", (book_id,))

        book = cursor.fetchone()

        if not book:
            print("Book not found!")
            return

        # Check whether this book has sales history
        cursor.execute(
            "SELECT 1 FROM sale_items WHERE book_id = %s LIMIT 1", (book_id,)
        )

        if cursor.fetchone():
            print("Cannot delete this book!")
            print("This book is already associated with sales.")
            return

        print("Book:", book[0])

        confirm = input("Are you sure you want to delete? (yes/no): ")

        if confirm.lower() == "yes":

            cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))

            conn.commit()

            print("Book deleted successfully!")

        else:
            print("Delete operation cancelled.")

    except Exception as e:
        conn.rollback()
        print("Delete error:", e)

    finally:
        if cursor:
            cursor.close()

        conn.close()
