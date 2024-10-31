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
        self.cursor.execute('SELECT user_id FROM "users" WHERE username=%s OR email=%s', (username, email))
        user_id = self.cursor.fetchone()
        if user_id:
            return None
        self.cursor.execute('INSERT INTO "users" (username, email, password, first_name, last_name, creation_date, last_access_date) VALUES (%s, %s, %s, %s, %s, %s, %s)', (username, email, password, firstname, lastname, formatted_date_time, formatted_date_time))
        self.connection.commit()
        self.cursor.execute('SELECT user_id FROM "users" WHERE username=%s OR email=%s', (username, email))
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
        self.cursor.execute('INSERT INTO "Collection" (name, user_id) VALUES (%s, %s)', (name, user_id))
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
        self.cursor.execute('SELECT book_id FROM "Book" WHERE title=%s', [book_name])
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
                "Collection" c
            LEFT JOIN
                part_of p ON c.collection_id = p.collection_id
            LEFT JOIN
                "Book" b ON p.book_id = b.book_id
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
        self.cursor.execute('SELECT book_id FROM "Book" WHERE title=%s', [book_name])
        book_id = self.cursor.fetchone()
        book_id = str(book_id[0])
        self.cursor.execute('INSERT INTO rates (book_id, user_id, stars) VALUES (%s, %s, %s)', (book_id, user_id, str(rating)))
        self.connection.commit()
        return
    
    def read_book(self, user_id, book_name, start_time, end_time, Pages_read):
        """
        Records a user's reading session by adding an entry to the "Session" table and associating the book with the session in the "has" table.

        Parameters:
            user_id (int): User's ID.
            book_name (str): Title of the book to rate.
            start_time (str): Start time of the reading session.
            end_time (str): End time of the reading session.
            
        """
        self.cursor.execute('SELECT book_id FROM "Book" WHERE title=%s', [book_name])
        book_id = self.cursor.fetchone()[0]
        book_id = str(book_id)
        self.cursor.execute('INSERT INTO "Session" (user_id, start_time, end_time, start_page, end_page) VALUES (%s, %s, %s, %s, %s)', \
            (user_id, start_time, end_time, str(Pages_read)))
        self.connection.commit()
        self.cursor.execute('SELECT session_id FROM "Session" WHERE user_id=%s AND start_time=%s AND end_time=%s AND start_page=%s AND end_page=%s', \
            (user_id, start_time, end_time, str(Pages_read)))
        session_id = self.cursor.fetchone()[0]
        session_id = str(session_id)
        self.cursor.execute('INSERT INTO has (book_id, session_id) VALUES (%s, %s)', (book_id, session_id))
        self.connection.commit()
        return
    
    def search_books(self, search_param, search_value):
        """
        Search for books based on specific parameters. It performs a SQL query on the database.

        Parameters:
            search_page (str): Search parameters (e.g., title, genre, date, author, publisher).
            search_value (str): Value to search for.

        Returns:
            list of tuples: List of books that match the search criteria.
        """
        sql_query = """
        SELECT "Book".book_id, "Book".title,
        "Book".number_of_books, "Book".length,
        W.first_name AS writer_first_name, W.last_name AS writer_last_name,
        P.first_name AS publisher_first_name, P.last_name AS publisher_last_name,
        E.first_name AS editor_first_name, E.last_name AS editor_last_name,
        A.type AS audience_type, G.type AS genre_type,
        edition.release_date,
        rates.stars AS rating
        FROM "Book"
        LEFT JOIN writes ON "Book".book_id = writes.book_id
        LEFT JOIN "Contributor" AS W ON writes.contributor_id = W.contributor_id
        LEFT JOIN publishes ON "Book".book_id = publishes.book_id
        LEFT JOIN "Contributor" AS P ON publishes.contributor_id = P.contributor_id
        LEFT JOIN edits ON "Book".book_id = edits.book_id
        LEFT JOIN "Contributor" AS E ON edits.contributor_id = E.contributor_id
        LEFT JOIN enjoys ON "Book".book_id = enjoys.book_id
        LEFT JOIN "Audience" AS A ON enjoys.audience_id = A.audience_id
        LEFT JOIN classifies_as ON "Book".book_id = classifies_as.book_id
        LEFT JOIN "Genre" AS G ON classifies_as.genre_id = G.genre_id
        LEFT JOIN edition ON "Book".book_id = edition.book_id
        LEFT JOIN rates on "Book".book_id = rates.book_id
        """
        
        order_by = 'ORDER BY "Book".title, edition.release_date;'
        where_clause = ""
        if search_param == "title":
            where_clause = 'WHERE "Book".title= \'' + search_value + '\''
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
        Sorts and filters books on specific parameters.

        Parameters:
            search_param (str): Search parameter (e.g., title, genre, date, author, publisher).
            search_value (str): Value to search for.
            sort_by (str): Field to sort by (e.g., title, publisher, genre, release_year).
            sort_order (str): Sort order (e.g., 'asc' or 'desc').

        Returns:
            list of tuples: List of books that match the search and sorting criteria.
        """
        sql_query = """
        SELECT "Book".book_id, "Book".title,
        "Book".number_of_books, "Book".length,
        W.first_name AS writer_first_name, W.last_name AS writer_last_name,
        P.first_name AS publisher_first_name, P.last_name AS publisher_last_name,
        E.first_name AS editor_first_name, E.last_name AS editor_last_name,
        A.type AS audience_type, G.type AS genre_type,
        edition.release_date,
        rates.stars AS rating
        FROM "Book"
        LEFT JOIN "writes" ON "Book".book_id = writes.book_id
        LEFT JOIN "Contributor" AS W ON writes.contributor_id = W.contributor_id
        LEFT JOIN publishes ON "Book".book_id = Publishes.book_id
        LEFT JOIN "Contributor" AS P ON publishes.contributor_id = P.contributor_id
        LEFT JOIN edits ON "Book".book_id = edits.book_id
        LEFT JOIN "Contributor" AS E ON edits.contributor_id = E.contributor_id
        LEFT JOIN enjoys ON "Book".book_id = enjoys.book_id
        LEFT JOIN "Audience" AS A ON enjoys.audience_id = A.audience_id
        LEFT JOIN classifies_as ON "Book".book_id = classifies_as.book_id
        LEFT JOIN "Genre" AS G ON classifies_as.genre_id = G.genre_id
        LEFT JOIN edition ON "Book".book_id = edition.book_id
        LEFT JOIN rates on "Book".book_id = rates.book_id
        """

        where_clause = ""
        if search_param == "title":
            where_clause = 'WHERE "Book".title=\'' + search_value + '\''
        elif search_param == "genre":
            where_clause = 'WHERE G.type=\'' + search_value + '\''
        elif search_param == "date":
            where_clause = 'WHERE edition.release_date=\'' + search_value + '\''
        elif search_param == "author":
            first_name, last_name = search_value.split(" ")
            where_clause = 'WHERE W.first_name=\'' + first_name + '\'' + ' AND W.last_name=\'' + last_name + '\''
        elif search_param == "publisher":
            first_name, last_name = search_value.split(" ")
            where_clause = 'WHERE P.first_name=\'' + first_name + '\'' + ' AND P.last_name=\'' + last_name + '\''
        order_by_clause = ""
        sort_by = ""
        if sort_order == "desc" or sort_order == "DESC":
            sort_by = 'DESC'
        if sort_by == "title":
            order_by_clause = 'ORDER BY "Book".title' + sort_by
        elif sort_by == "publisher":
            order_by_clause = 'ORDER BY P.first_name, P.last_name' + sort_by
        elif sort_by == "genre":
            order_by_clause = 'ORDER BY G.type' + sort_by
        elif sort_by == "release_year":
            order_by_clause = 'ORDER BY edition.release_date' + sort_by
        self.cursor.execute(sql_query + where_clause + order_by_clause)
        return self.cursor.fetchall()
