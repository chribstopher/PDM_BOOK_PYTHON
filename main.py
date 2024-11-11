###################################
# File: main.py                   #
# Authors:                        #
#  - Showmik Bhowmik              #
#  - Christopher Rose             #
#  - Micheal                      #
#  - Danny                        #
# Description: The primary script #
# that handles all DB functions   #
###################################
import sys
import hashlib
from getpass import getpass
from connection_and_queries import Connection
from User import User

def help():
    """
    Displays a list of available commands and their descriptions.
    """
    print("join       -- Joins the books platform with a new account")
    print("login      -- Shows the login prompt")
    print("logout     -- Logouts of the current session")
    print("create     -- Creates a new book collection")
    print("list       -- Displays all collections")
    print("add        -- Adds a book to a collection")
    print("remove     -- Removes a book from a collection")
    print("rename     -- Renames an existing book collection")
    print("delete     -- Deletes an existing book collection")
    print("rate       -- Rates a book (1-5 stars)")
    print("read       -- Reads a book from a certain page to a certain page")
    print("profile  -- Check follow and collection info")
    print("follow     -- Follows another user (by email)")
    print("unfollow   -- Unfollows another user (by email)")
    print("search     -- Searches a book based on a search term and a search value")
    print("sort       -- Sorts and searches books")
    print("help       -- Shows a help message")
    print("quit       -- Exits the application")

def hash_password(password):
    """
    Hashes a password using SHA-256.

    Parameters:
        password (str): The plaintext password to be hashed.

    Returns:
        str: The SHA-256 hashed.
    """
    return hashlib.sha256(password.encode()).hexdigest()

def main():
    """
    The main function of the application. The entry point which handles user interaction and command processing.
    """
    ssh_username = input("SSH Username: ")
    ssh_password = input("SSH Password: ")
    try:
        session = Connection(ssh_username, ssh_password)
        user = User(session)
        print("""
                __________________   __________________
            .-/|                  \ /                  |\-.
            ||||                   |                   ||||
            ||||                   |       ~~*~~       ||||
            ||||    --==*==--      |                   ||||
            ||||                   |                   ||||
            ||||                   |                   ||||
            ||||                   |     --==*==--     ||||
            ||||                   |                   ||||
            ||||                   |                   ||||
            ||||                   |                   ||||
            ||||                   |                   ||||
            ||||__________________ | __________________||||
            ||/===================\|/===================\||
            `--------------------~___~-------------------''
            """)
        print("Welcome to the Books Platform!")
        print("Here is a list of useful commands:")
        help()
        while True:
            if user.username is not None:
                command = input(f"{user.username} > ").lower()
            else:
                command = input("> ").lower()
            if command == "login":
                username = input("Username: ")
                password = hash_password(input("Password: "))
                print("Logging you in...")
                user.login(username=username, password=password)
            elif command == "join":
                username = input("Username: ")
                password = hash_password(input("Password: "))
                email = input("Email: ")
                first_name = input("First Name: ")
                last_name = input("Last Name: ")
                print("Creating your account...")
                user.join(username=username, email=email, password=password, first_name=first_name, last_name=last_name)
            elif command == "logout":
                print("Logging you out...")
                user.logout()
            elif command == "create":
                title = input("Collection Title: ")
                print("Creating new book collection...")
                user.create_collection(title)
            elif command == "delete":
                title = input("Collection Title: ")
                print("Deleting collection...")
                user.delete_collection(title)
            elif command == "rename":
                old_title = input("Old Collection Title: ")
                new_title = input("New Collection Title: ")
                print("Renaming collection...")
                user.rename_collection(old_title, new_title)
            elif command == "add":
                book_title = input("Book Title: ")
                collection_title = input("Collection Title: ")
                print("Adding book to collection...")
                user.add_to_collection(book_title, collection_title)
            elif command == "remove":
                book_title = input("Book Title: ")
                collection_title = input("Collection Title: ")
                print("Removing book from collection...")
                user.remove_from_collection(book_title, collection_title)
            elif command == "rate":
                book_title = input("Book Title: ")
                rating = int(input("Rating (1-5 stars): "))
                print("Rating the book...")
                user.rate_book(book_title, rating)
            elif command == "read":
                book_title = input("Which book do you want to read? ")
                book_start_page = int(input("Start page: "))
                book_end_page = int(input("End page: "))
                print("Reading the book...")
                user.read_book(book_title, book_start_page, book_end_page)
            elif command == "profile":
                user.profile()
            elif command == "follow":
                email = input("Please enter the email of the person to follow: ")
                user.follow(email)
            elif command == "unfollow":
                email = input("Please enter the email of the person to unfollow: ")
                user.unfollow(email)
            elif command == "list":
                user.list_collections()
            elif command == "search":
                search_term = input("Please enter the search term[title/release_date/author/publisher/genre]: ")
                search_value = input("Please enter the search value: ")
                user.search(search_term, search_value)
            elif command == "sort":
                search_term = input("Please enter the search term[title/publisher/genre/release_date]: ")
                search_value = input("Please enter the search value: ")
                order_value = input("Please enter the order term[title/publisher/genre/released year]: ")
                order_by = input("Please enter the sort order[asc/desc]: ").lower()
                user.sort(search_term, search_value, order_value, order_by)
            elif command == "help":
                help()
            elif command == "quit":
                print("Thank you for using our application!")
                print("""
                       ---------------------------------
                      /|                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      ||                                |
                      |/---------------------------------
                      | ================================|
                      ----------------------------------- 
                 """)
                break
            else:
                print("Command not recognized. Enter 'help' to see all commands.")
                print("Here is a list of all avaialble commands:")
                help()
    except Exception as e:
        print(e)
        sys.exit()

if __name__ == "__main__":
    main()
