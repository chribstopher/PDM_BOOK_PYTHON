import datetime
import psycopg2
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
from constants import DATABASE_NAME

class Connection:
    def __init__(self, ssh_username, ssh_password):
        """
        Initializes the Connection object with SSH tunnel and database connection.

        Parameters:
            ssh_username (str): SSH username for connecting to the remote server.
            ssh_password (str): SSH password for connecting to the remote server.

        Raises:
            ConnectionError: If there is an error while connecting using SSH.
        """
        try:
            self.server = SSHTunnelForwarder (
                ('starbug.cs.rit.edu', 22),
                ssh_username = ssh_username,
                ssh_password = ssh_password,
                remote_bind_address = ('127.0.0.1', 5432),
                allow_agent = False,
                ssh_config_file = None,
                ssh_pkey = None,
            )
            self.server.start()
        except BaseSSHTunnelForwarderError as e:
            raise ConnectionError("Error while connecting using ssh: ", e)

        parameters = {
            'database' : DATABASE_NAME,
            'user' : ssh_username,
            'password' : ssh_password,
            'host' : '127.0.0.1',
            'port' : self.server.local_bind_port,
        }
        self.connection = psycopg2.connect(**parameters)
        self.cursor = self.connection.cursor()
        self.collectioncursor = self.connection.cursor()

    def close(self):
        """
        Closes the database connection and SSH tunnel.
        """
        self.cursor.close()
        self.connection.close()
        self.server.stop()
        
    def __exit__(self):
        """
        Ensures the connection is properly closed when exiting a context.
        """
        self.close()

    def join(self, username, email, password, firstname, lastname):
        """
        Registers a new user and adds their information to the "Users" table.

        Parameters:
            username (str): User's username.
            email (str): User's email address.
            password (str): User's password.
            firstname (str): User's first name.
            lastname (str): User's last name.

        Returns:
            tuple: User ID if registration is successful, None if user already exists.
        """
        formatted_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if the username already exists
        self.cursor.execute('SELECT user_id FROM "users" WHERE username=%s', (username,))
        user_id = self.cursor.fetchone()
        if user_id:
            return None  # User already exists

        # Get the next user_id by finding the current max user_id
        self.cursor.execute('SELECT MAX(user_id) FROM users')
        max_user_id = self.cursor.fetchone()[0]
        user_id = 1 if max_user_id is None else max_user_id + 1

        # Insert into the users table
        print("Inserting into users table")
        self.cursor.execute(
            'INSERT INTO "users" (username, user_id, password, first_name, last_name, creation_date, last_access_date) VALUES (%s, %s, %s, %s, %s, %s, %s)',
            (username, user_id, password, firstname, lastname, formatted_date_time, formatted_date_time)
        )

        # Insert into the user_email table
        print("Inserting into user email table")
        self.cursor.execute(
            'INSERT INTO "user_email" (user_id, email) VALUES (%s, %s)',
            (user_id, email)
        )

        # Commit the transaction
        self.connection.commit()

        # Retrieve and return the newly created user_id
        self.cursor.execute('SELECT user_id FROM "users" WHERE username=%s', (username,))
        return self.cursor.fetchone()

    def login(self, username, password):
        """
        Logs in a user and updates their last access date.

        Parameters:
            username (str): User's username.
            password (str): User's password.

        Returns:
            tuple: User ID if login is successful, None if login fails.
        """
        formatted_date_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute('SELECT user_id FROM "users" WHERE username=%s AND password=%s', (username, password))
        user_id = self.cursor.fetchone()
        self.cursor.execute('UPDATE "users" SET last_access_date=%s WHERE user_id=%s', (formatted_date_time, user_id))
        self.connection.commit()
        return user_id
    
    def create_collection(self, user_id, name):
        """
        Creates a new collection for a user into the "Collection" table.

        Parameters:
            user_id (int): User's ID.
            name (str): Name of the collection.
        """
        # Get the next user_id by finding the current max user_id
        self.cursor.execute('SELECT MAX(collection_id) FROM collection')
        max_collection_id = self.cursor.fetchone()[0]
        collection_id = 1 if max_collection_id is None else max_collection_id + 1
        self.cursor.execute('INSERT INTO "collection" (collection_id, name, user_id) VALUES (%s, %s, %s)', (collection_id, name, user_id))
        self.connection.commit()
        return
        
    def delete_collection(self, user_id, name):
        """
        Deletes a user's collection.

        Parameters:
            user_id (int): User's ID.
            name (str): Name of the collection.

        Raises:
            FileNotFoundError: If the collection does not exist.
        """
        self.cursor.execute('SELECT * FROM "collection" WHERE user_id=%s AND name=%s', (user_id, name))
        result = self.cursor.fetchone()
        if result is None:
            raise FileNotFoundError
        self.cursor.execute('SELECT collection_id FROM "collection" WHERE user_id=%s AND name=%s', (user_id, name))
        collection_id = self.cursor.fetchone()
        self.cursor.execute('DELETE FROM part_of WHERE collection_id=%s', collection_id)
        self.cursor.execute('DELETE FROM "collection" WHERE user_id=%s AND name=%s', (user_id, name))
        self.connection.commit()
        return
    
    def modify_collection_name(self, user_id, old_name, new_name):
        """
        Renames the name of a user's collection.

        Parameters:
            user_id (int): User's ID.
            old_name (str): Current name of the collection.
            new_name (str): New name for the collection.
        
        Raises:
            FileNotFoundError: If the collection does not exist.
        """
        self.cursor.execute('SELECT * FROM "collection" WHERE user_id=%s AND name=%s', (user_id, old_name))
        result= self.cursor.fetchone()
        if result is None:
            raise FileNotFoundError
        self.cursor.execute('UPDATE "collection" SET name=%s WHERE user_id=%s AND name=%s', (new_name, user_id, old_name))
        self.connection.commit()
        return
    
    def add_book_to_collection(self, user_id, book_name, collection_name):
        """
        Adds a book to a user's collection.

        Parameters:
            user_id (int): User's ID.
            book_name (str): Title of the book to be added.
            collection_name (str): Name of the collection to add the book to.
        """
        self.cursor.execute('SELECT book_id FROM "book" WHERE title=%s', [book_name])
        book_id = self.cursor.fetchone()
        book_id = str(book_id[0])
        self.cursor.execute('SELECT collection_id FROM "collection" WHERE name=%s AND user_id=%s', (collection_name, user_id))
        collection_id = self.cursor.fetchone()
        if collection_id is None:
            return False
        self.cursor.execute('INSERT INTO part_of (book_id, collection_id) VALUES (%s, %s)', (book_id, collection_id))
        self.connection.commit()
        return True
    
    def remove_book_from_collection(self, user_id, book_name, collection_name):
        """
        Removes a book from a user's collection.

        Parameters:
            user_id (int): User's ID.
            book_name (str): Title of the book to be removed from the collection.
            collection_name (str): Name of the collection from which to remove the book.
        """
        self.cursor.execute('SELECT book_id FROM "book" WHERE title=%s', [book_name])
        book_id = self.cursor.fetchone()
        book_id = str(book_id[0])
        self.cursor.execute('SELECT collection_id FROM "collection" WHERE name=%s AND user_id=%s', (collection_name, user_id))
        collection_id = self.cursor.fetchone()
        self.cursor.execute('DELETE FROM part_of WHERE book_id=%s AND collection_id=%s', (book_id, collection_id))
        self.connection.commit()
        return
    
    def get_collections(self, user_id):
        """
        Gets a list of collections for a user.

        Parameters:
            user_id (int): User's ID.

        Returns:
            list of tuples: A list of collections with their names, book counts, and total page counts.
        """
        uid = user_id[0]
        collection_sql_stmnt = f"""
            SELECT
                c.name AS "Collection Name",
                COUNT(p.book_id) AS "Number of Books",
                SUM(b.length) AS "Length (Pages)"
            FROM
                "collection" c
            LEFT JOIN
                part_of p ON c.collection_id = p.collection_id
            LEFT JOIN
                "book" b ON p.book_id = b.book_id
            WHERE
                c.user_id = {uid}
            GROUP BY
                c.collection_id, c.name
            ORDER BY
                c.name;
        """
        
        self.cursor.execute(collection_sql_stmnt)
        return self.cursor.fetchall()
    

    def rate_a_book(self, user_id, book_name, rating):
        """
        Rates a book by adding their rating to the "rates" table.

        Parameters:
            user_id (int): User's ID.
            book_name (str): Title of the book to rate.
            rating (int): User's rating for the book.
        """
        self.cursor.execute('SELECT book_id FROM "book" WHERE title=%s', [book_name])
        book_id = self.cursor.fetchone()
        book_id = str(book_id[0])
        self.cursor.execute('INSERT INTO rating (book_id, user_id, stars) VALUES (%s, %s, %s)', (book_id, user_id, str(rating)))
        self.connection.commit()
        return

    def read_book(self, user_id, book_name, start_time, end_time, start_page, end_page):
        """
        Records a user's reading session by adding an entry to the "Session" table and associating the book with the session in the "has" table.

        Parameters:
            user_id (int): User's ID.
            book_name (str): Title of the book to rate.
            start_time (str): Start time of the reading session.
            end_time (str): End time of the reading session.
            start_page (int): The starting page number.
            end_page (int): The ending page number.
        """
        # Get the next session_id
        self.cursor.execute('SELECT MAX(session_id) FROM reading_session')
        max_session_id_result = self.cursor.fetchone()
        max_session_id = max_session_id_result[0] if max_session_id_result and max_session_id_result[
            0] is not None else 0
        session_id = max_session_id + 1

        # Calculate pages read
        Pages_read = end_page - start_page

        # Get the book_id for the specified book name
        self.cursor.execute('SELECT book_id FROM "book" WHERE title=%s', (book_name,))
        book_id_result = self.cursor.fetchone()
        if not book_id_result:
            print(f"Error: Book '{book_name}' not found in the database.")
            return
        book_id = book_id_result[0]

        # Insert into reading_session table
        self.cursor.execute(
            'INSERT INTO reading_session (session_id, user_id, start_time, end_time, pages_read) VALUES (%s, %s, %s, %s, %s)',
            (session_id, user_id, start_time, end_time, Pages_read)
        )
        self.connection.commit()

        # Verify the session was created and fetch the session_id
        self.cursor.execute(
            'SELECT session_id FROM reading_session WHERE user_id=%s AND start_time=%s AND end_time=%s AND pages_read=%s',
            (user_id, start_time, end_time, Pages_read)
        )
        session_id_result = self.cursor.fetchone()
        if not session_id_result:
            print("Error: Unable to retrieve session_id after insertion.")
            return
        session_id = session_id_result[0]

        # Insert into book+session table (associative table for book and session relationship)
        self.cursor.execute(
            'INSERT INTO "book+session" (book_id, session_id) VALUES (%s, %s)',
            (book_id, session_id)
        )
        self.connection.commit()

        print(f"Book '{book_name}' has been read from page {start_page} to page {end_page}.")

    def follow(self, follower_id, email):
        """
        Adds a new row to the following table, where the follower follows the user identified by email.

        Parameters:
            follower_id (int): The user_id of the person doing the following.
            email (str): The email of the user to be followed.

        Returns:
            bool: True if the follow operation was successful, False if the user with the provided email was not found.
        """
        try:
            # Step 1: Find the user_id associated with the provided email
            self.cursor.execute('SELECT user_id FROM user_email WHERE email = %s', (email,))
            result = self.cursor.fetchone()

            if result is None:
                # No user found with the provided email
                print(f"No user found with email {email}.")
                return False

            followee_id = result[0]

            # Step 2: Insert the follower and followee relationship into the following table
            self.cursor.execute(
                'INSERT INTO following (follower, followee) VALUES (%s, %s)',
                (follower_id, followee_id)
            )

            # Commit the transaction
            self.connection.commit()
            print(f"You are now following user with email {email}.")
            return True

        except Exception as e:
            print(f"An error occurred while trying to follow: {e}")
            self.connection.rollback()  # Roll back in case of an error
            return False

    def unfollow(self, follower_id, email):
        """
        Removes a row from the following table, where the follower stops following the user identified by email.

        Parameters:
            follower_id (int): The user_id of the person doing the unfollowing.
            email (str): The email of the user to be unfollowed.

        Returns:
            bool: True if the unfollow operation was successful, False if the user with the provided email was not found.
        """
        try:
            # Step 1: Find the user_id associated with the provided email
            self.cursor.execute('SELECT user_id FROM user_email WHERE email = %s', (email,))
            result = self.cursor.fetchone()

            if result is None:
                # No user found with the provided email
                print(f"No user found with email {email}.")
                return False

            followee_id = result[0]

            # Step 2: Delete the follower and followee relationship from the following table
            self.cursor.execute(
                'DELETE FROM following WHERE follower = %s AND followee = %s',
                (follower_id, followee_id)
            )

            # Commit the transaction
            self.connection.commit()
            print(f"You have unfollowed user with email {email}.")
            return True

        except Exception as e:
            print(f"An error occurred while trying to unfollow: {e}")
            self.connection.rollback()  # Roll back in case of an error
            return False

    def search_books(self, search_param, search_value):
        """
        Search for books based on specific parameters. It performs a SQL query on the database.

        Parameters:
            search_page (str): Search parameters (e.g., title, genre, date, author, publisher).
            search_value (str): Value to search for.

        Returns:
            list of tuples: List of books that match the search criteria.
        """

        # "book".number_of_books,
        sql_query = """
        SELECT "book".book_id, "book".title,
        "book".length,
        W.first_name AS writer_first_name, W.last_name AS writer_last_name,
        P.first_name AS publisher_first_name, P.last_name AS publisher_last_name,
        E.first_name AS editor_first_name, E.last_name AS editor_last_name,
        A.type AS audience_type, G.type AS genre_type,
        edition.release_date,
        rating.stars AS rating
        FROM "book"
        LEFT JOIN writes ON "book".book_id = writes.book_id
        LEFT JOIN "contributor" AS W ON writes.contributor_id = W.contributor_id
        LEFT JOIN publishes ON "book".book_id = publishes.book_id
        LEFT JOIN "contributor" AS P ON publishes.contributor_id = P.contributor_id
        LEFT JOIN edits ON "book".book_id = edits.book_id
        LEFT JOIN "contributor" AS E ON edits.contributor_id = E.contributor_id
        LEFT JOIN enjoys ON "book".book_id = enjoys.book_id
        LEFT JOIN "audience" AS A ON enjoys.audience_id = A.audience_id
        LEFT JOIN classifies_as ON "book".book_id = classifies_as.book_id
        LEFT JOIN "genre" AS G ON classifies_as.genre_id = G.genre_id
        LEFT JOIN edition ON "book".book_id = edition.book_id
        LEFT JOIN rating on "book".book_id = rating.book_id
        """
        
        order_by = 'ORDER BY "book".title, edition.release_date;'
        where_clause = ""
        if search_param == "title":
            where_clause = 'WHERE "book".title= \'' + search_value + '\''
        elif search_param == "genre":
            where_clause = 'WHERE G.type= \'' + search_value + '\''
        elif search_param == "date":
            where_clause = 'WHERE edition.release_date= \'' +  search_value + '\''
        elif search_param == "author":
            first_name, last_name = search_value.split(" ")
            where_clause= 'WHERE W.first_name=\'' + first_name + '\' AND W.last_name=\'' + last_name + '\''
        elif search_param == "publisher":
            first_name, last_name = search_value.split(" ")
            where_clause= 'WHERE P.first_name=\'' + first_name + '\' AND P.last_name=\'' + last_name + '\''
        self.cursor.execute(sql_query + where_clause + order_by)
        return self.cursor.fetchall()

    def sort_books(self, search_param, search_value, sort_by, sort_order):
        """
        Sorts and filters books on specific parameters, with support for multiple editions.

        Parameters:
            search_param (str): Search parameter (e.g., title, genre, date, author, publisher).
            search_value (str): Value to search for.
            sort_by (str): Field to sort by (e.g., title, publisher, genre, release_year).
            sort_order (str): Sort order (e.g., 'asc' or 'desc').

        Returns:
            list of tuples: List of books that match the search and sorting criteria.
        """
        sql_query = """
        SELECT "book".book_id, "book".title,
               "book".length,
               W.writer_names AS writer_names,  -- Aggregated writer names
               P.first_name AS publisher_first_name, P.last_name AS publisher_last_name,
               E.first_name AS editor_first_name, E.last_name AS editor_last_name,
               A.audience_type, G.genre_type,
               edition.release_date,
               rating.stars AS rating
        FROM "book"
        LEFT JOIN (
            SELECT writes.book_id, array_agg(C.first_name || ' ' || C.last_name) AS writer_names
            FROM "writes"
            JOIN "contributor" AS C ON writes.contributor_id = C.contributor_id
            GROUP BY writes.book_id
        ) AS W ON "book".book_id = W.book_id
        LEFT JOIN (
            SELECT publishes.book_id, C.first_name, C.last_name
            FROM "publishes"
            JOIN "contributor" AS C ON publishes.contributor_id = C.contributor_id
            GROUP BY publishes.book_id, C.first_name, C.last_name
        ) AS P ON "book".book_id = P.book_id
        LEFT JOIN (
            SELECT edits.book_id, C.first_name, C.last_name
            FROM "edits"
            JOIN "contributor" AS C ON edits.contributor_id = C.contributor_id
            GROUP BY edits.book_id, C.first_name, C.last_name
        ) AS E ON "book".book_id = E.book_id
        LEFT JOIN (
            SELECT enjoys.book_id, array_agg(A.type) AS audience_type
            FROM "enjoys"
            JOIN "audience" AS A ON enjoys.audience_id = A.audience_id
            GROUP BY enjoys.book_id
        ) AS A ON "book".book_id = A.book_id
        LEFT JOIN (
            SELECT classifies_as.book_id, array_agg(G.type) AS genre_type
            FROM "classifies_as"
            JOIN "genre" AS G ON classifies_as.genre_id = G.genre_id
            GROUP BY classifies_as.book_id
        ) AS G ON "book".book_id = G.book_id
        LEFT JOIN "edition" ON "book".book_id = edition.book_id
        LEFT JOIN "rating" ON "book".book_id = rating.book_id
        """

        # Construct the WHERE clause based on search parameters
        where_clause = ""
        if search_param == "title":
            where_clause = f"WHERE book.title = '{search_value}'"
        elif search_param == "genre":
            where_clause = f"WHERE '{search_value}' = ANY(G.genre_type)"
        elif search_param == "date":
            where_clause = f"WHERE edition.release_date = '{search_value}'"
        elif search_param == "author":
            first_name, last_name = search_value.split(" ")
            where_clause = f"WHERE '{first_name} {last_name}' = ANY(W.writer_names)"
        elif search_param == "publisher":
            where_clause = f"WHERE P.first_name = '{first_name}' AND P.last_name = '{last_name}'"

        # Construct the ORDER BY clause
        if sort_order.lower() == "desc":
            sort_order = "DESC"
        else:
            sort_order = "ASC"

        order_by_clause = ""
        if sort_by == "title":
            order_by_clause = f"ORDER BY book.title {sort_order}"
        elif sort_by == "publisher":
            order_by_clause = f"ORDER BY P.first_name {sort_order}, P.last_name {sort_order}"
        elif sort_by == "genre":
            order_by_clause = f"ORDER BY G.genre_type {sort_order}"
        elif sort_by == "release_year":
            order_by_clause = f"ORDER BY edition.release_date {sort_order}"

        # Final SQL execution
        sql_query += " " + where_clause + " " + order_by_clause
        self.cursor.execute(sql_query)
        return self.cursor.fetchall()
