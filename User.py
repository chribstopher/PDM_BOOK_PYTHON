import datetime
from getpass import getpass
from connection_and_queries import Connection

class User:
    def __init__(self, connection: Connection):
        """
        Initializes a User object.

        Parameters:
            connection (Connection): An instance of the Connection class for database interaction.
        
        Attributes:
            connection (Connection): The database connection.
            user_id (int): The user's ID, initialized as None.
            username (str): The user's username, initialized as None.
            collections (list): A list of collections associated with the user, initialized as None.
        """
        self.connection = connection
        self.user_id = None
        self.username = None
        self.collections = None
    
    def login(self, username: str, password: str):
        """
        Logs in a user with the provided username and password.

        Parameters:
            username (str): The user's username.
            password (str): The hashed user's password.
        """
        if self.username is not None:
            print("You are already logged in.")
            return
        try:
            user_id = self.connection.login(username, password)
        except Exception as e:
            print(e)
            return
        if not user_id:
            print("Invalid username or password.")
            return
        self.user_id = user_id
        self.username = username
        print(f'Welcome {self.username}! Logged in successfully :)')
        
    def join(self, username, email, password, first_name, last_name):
        """
        Creates a new user account and logs in.

        Parameters:
            username (str): The user's username for the new account.
            email (str): The user's email address.
            password (str): The hashed user's password.
            first_name (str): The user's first name.
            last_name (str): The user's last name.
        """
        try:
            user_id = self.connection.join(username, email, password, first_name, last_name)
        except Exception as e:
            print(e)
            return
        if not user_id:
            print("User already exists.")
            return
        self.user_id = user_id
        self.username = username
        print(f'Welcome {self.username}! You have successfully joined the Books platform :)')
        
    def logout(self):
        """
        Logs out the currently logged-in user.
        """
        if self.user_id:
            self.username = None
            self.user_id = None
            print("Logged out successfully.")
        else:
            print("You are not logged in.")
            
    def create_collection(self, title):
        """
        Creates a new book collection for the user.

        Parameters:
            title (str): The title of the new collection.
        """
        if self.username == None:
            print("Please log in to create a collection.")
            return
        self.connection.create_collection(self.user_id, title)
        print(f'Collection "{title}" created successfully.')
    
    def delete_collection(self, title):
        """
        Deletes an existing book collection.

        Parameters:
            title (str): The title of the collection to be deleted.
        """
        try:
            if self.username is None:
                print("Please log in to delete a collection.")
                return
            self.connection.delete_collection(self.user_id, title)
            print(f'Collection "{title}" deleted successfully.')
        except FileNotFoundError:
            print(f"You do not have permission to delete this collection.")
        
    def rename_collection(self, old_title, new_title):
        """
        Renames an existing book collection.

        Parameters:
            old_title (str): The current title of the collection.
            new_title (str): The new title for the collection.
        """
        try:
            if self.username is None:
                print("Please log in to rename a collection.")
                return
            self.connection.modify_collection_name(self.user_id, old_name=old_title, new_name=new_title)
            print(f'Collection "{old_title}" renamed to "{new_title} successfully.')
        except:
            print("You do not have permission to rename this collection.")
        
    def add_to_collection(self, book_title, collection_title):
        """
        Adds a book to a user's collection.

        Parameters:
            book_title (str): The title of the book to be added.
            collection_title (str): The title of the collection to add the book to.
        """
        if self.username is None:
            print("Please log in to add a book to a collection.")
            return
        result = self.connection.add_book_to_collection(self.user_id, book_title, collection_title)
        if result is False:
            print("Collection doesn't exist.")
        else:
            print(f'Book "{book_title}" added to collection "{collection_title}" successfully.')
    
    def remove_from_collection(self, book_title, collection_title):
        """
        Removes a book from a user's collection.

        Parameters:
            book_title (str): The title of the book to be removed.
            collection_title (str): The title of the collection to remove the book from.  
        """
        if self.username is None:
            print("Please log in to remove a book from a collection.")
            return
        self.connection.remove_book_from_collection(self.user_id, book_title, collection_title)
        print(f'Book "{book_title}" removed from collection "{collection_title}" successfully.')
    
    def rate_book(self, book_title, rating):
        """
        Rates a book with a given rating.

        Parameters:
            book_title (str): The title of the book to be rated.
            rating (int): The rating (1-5 stars) to assign to the book.
        """
        if self.username is None:
            print("Please log in to rate a book.")
            return
        self.connection.rate_a_book(self.user_id, book_title, rating)
        print(f'Book "{book_title}" has been rated {rating} stars.')

    def read_book(self, book_title, start_page, end_page):
        """
        Records reading activity for a book.

        Parameters:
            book_title (str): The title of the book being read.
            start_page (int): The starting page number.
            end_page (int): The ending page number.
        """
        if self.username is None:
            print("Please log in to read a book.")
            return
        reading_time_minutes = (end_page - start_page) * 3 # assuming each page takes 3 minutes to read
        start_time = datetime.datetime.now()
        end_time = datetime.datetime.now() + datetime.timedelta(minutes=reading_time_minutes)
        self.connection.read_book(self.user_id, book_title, start_time, end_time, start_page, end_page)
        print(f'Book "{book_title}" has been read from page {start_page} to page {end_page}. It took {reading_time_minutes} minutes to read.')
        
    def follow(self, email):
        """
        Follows another user by email.

        Parameters:
            email (str): The email address of the user to follow.
        """
        if self.username is None:
            print("Please log in to follow users.")
            return
        result = self.connection.follow(self.user_id, email)
        if result:
            print(f'"{self.username}" followed {email} successfully :)')
    
    def unfollow(self, email):
        """
        Unfollows another user by email.

        Parameters:
            email (str): The email address of the user to unfollow.
        """
        if self.username is None:
            print("Please log in to unfollow users.")
            return
        result = self.connection.unfollow(self.user_id, email)
        if result:
             print(f'"{self.username}" unfollowed {email} successfully :(')

    def list_collections(self):
        """
        Lists all book collections associated with the user.
        """
        if self.username is None:
            print("Please log in to view your collections.")
            return
        print(f'Listing all collections for {self.username}...')
        self.collections = self.connection.get_collections(self.user_id)
        for collection in self.collections:
            print(f"{str(collection)}\n")
            
    def search(self, search_term, search_value):
        """
        Searches for books based on a seach term and value.

        Parameters:
            search_term (str): The search term (e.g., title, release_date).
            search_value (str): The value to search for.
        """
        print(f'Searching for books related to {search_value} containing {search_term}...')
        search_results = self.connection.search_books(search_term, search_value)
        for result in search_results:
            print(f"{result}")
            
    def sort(self, search_term, search_value, order_value, order_by):
        """
        Sorts and searches for books.

        Parameters:
            search_term (str): The search term (e.g., title, release_date).
            search_value (str): The value to search for.
            order_value (str): The field to order by (e.g., title, publisher).
            order_by (str): The sort order ('asc' or 'desc').
        """
        print(f'Sorting books related to {search_value} containing {search_term} by {order_value} in {order_by} order...')
        search_results = self.connection.sort_books(search_term, search_value, order_value, order_by)
        for result in search_results:
            print(f"{result}")
