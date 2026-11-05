
from models.book import Book

from services.book_service import (
    add_book,
    view_books,
    search_book,
    update_book,
    delete_book
)


class BookMenu:

    def run(self):

        while True:

            print("\n========== BOOK MANAGEMENT ==========")
            print("1. Add New Book")
            print("2. View All Books")
            print("3. Search Book")
            print("4. Update Book")
            print("5. Delete Book")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ")

            if choice == "1":

                title = input("Enter book title: ")
                author = input("Enter author: ")
                price = float(input("Enter price: "))
                stock = int(input("Enter stock: "))
                category = input("Enter category: ")

                book = Book(title, author, price, stock, category)

                add_book(book)

            elif choice == "2":
                view_books()

            elif choice == "3":

                book_id = int(input("Enter Book ID: "))
                search_book(book_id)

            elif choice == "4":

                book_id = int(input("Enter Book ID: "))
                update_book(book_id)

            elif choice == "5":

                book_id = int(input("Enter Book ID: "))
                delete_book(book_id)

            elif choice == "0":
                break

            else:
                print("Invalid choice!")
