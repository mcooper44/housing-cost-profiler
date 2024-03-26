import sqlite3

DBSCHEMA = ('''CREATE TABLE Listing
            (LID INTEGER NOT NULL PRIMARY KEY, Bedrooms TEXT, Bathrooms TEXT,
            Sqft TEXT, AgreeType TEXT, Price INTEGER)''',
            '''CREATE TABLE Address (LID INTEGER, StreetAddress TEXT,
            City TEXT, Prov TEXT, PCode TEXT, HType TEXT, FullStr TEXT,
            FOREIGN KEY(LID) REFERENCES Listing(LID))''',
            '''CREATE TABLE Description
            (LID INTEGER, Description TEXT, FOREIGN KEY(LID) REFERENCES
            Listing(LID))''',
            '''CREATE TABLE url (LID INTEGER, URL TEXT, FOREIGN KEY(LID)
            REFERENCES Listing(LID))''',
            '''CREATE TABLE Features
            (LID INTEGER, Parking INTEGER, Furnished INTEGER, Smoking INTEGER,
            Air INTEGER, Pets INTEGER, FOREIGN KEY(LID) REFERENCES
            Listing(LID))''',
            '''CREATE TABLE Utilities (LID INTEGER, Hydro INTEGER, Water
            INTEGER, Heat INTEGER, FOREIGN KEY(LID) REFERENCES
            Listing(LID))''',
            '''CREATE TABLE Amenities (LID INTEGER, Item TEXT, FOREIGN
            KEY(LID) REFERENCES Listing(LID))''',
            '''CREATE TABLE Appliances (LID INTEGER, Appliance TEXT, FOREIGN
            KEY(LID) REFERENCES Listing(LID))''',
           '''CREATE TABLE Space (LID INTEGER, OutDoorSpace TEXT, FOREIGN
            KEY(LID REFERENCES Listing(LID)''')

class Database():
    '''
    for interacting with databases
    path_name is the location and name of the databse to connect with
    or create

    connect() method establishes a database and/or connection to one
    '''

    def __init__(self, path_name):
        self.path_name = path_name
        self.conn = None
        self.cur = None


    def connect(self, first_time=False, strings=None):
        '''
        establishes connection to database stored in the .path_name attribute
        if the first_time flag is set
        it will attempt to create tables with strings contained in a list or
        tuple held in the 'strings' parameter
        '''

        try:
            self.conn = sqlite3.connect(self.path_name)
            self.cur = self.conn.cursor()
            print(f'Database.connect: database connection open to {self.path_name}')

            if first_time == True and any(strings):
                for string in strings:
                    self.cur.execute(string)
                    print(f'executing: {string}')
                    self.conn.commit()
            elif first_time == True and not any(strings):
                print('no strings provided to provision tables')

        except Exception as e:
            print('could not establish connection to database')
            print(e)

    def insert(self, data_struct, echo=False):
        '''
        takes a dictionary 'data_struct' of
        'table name': ([(values_to_write,)], # list of tuple(s)
                       '(?, [...])') # string tuple with a ? for each
                                     # to insert

        and iterates through the data structure inserting values
        into the tables used as keys in dictionary
        '''
        for table_name in data_struct.keys():
            # lookup the values to insert i.e [(1,2,3),(4,5,6)]
            # and a tuple representing the number of columns
            # i.e. '(?, ?, ?)'
            lst_of_tples, flds = data_struct.get(table_name, (None,None))
            wr_str = f'INSERT OR IGNORE INTO {table_name} VALUES {flds}'
            if all((lst_of_tples,flds)):
                for tple_to_insert in lst_of_tples:
                    if echo: print(f'writing {tple_to_insert} into {table_name}')
                    self.cur.execute(wr_str, tple_to_insert)
                    self.conn.commit()

    def o2m_insert(self, visit, many):
        '''
        handles the one to many table insert for the database
        '''
        self.cur.execute(*visit)

        pk = self.cur.lastrowid

        for s in many:
            if any((s)):
                try:
                    s1, s2 = s
                    self.cur.execute(s1,(pk,*s2))
                    self.conn.commit()
                except Exception as insert_fail:
                    print(f'{s1} with values {s2}')
                    print('yielded...')
                    print(insert_fail)

    def lookup(self, target, table, row, paramater):
        '''
        http://www.sqlitetutorial.net/sqlite-between/
        '''
        ex_string = f'SELECT {target} FROM {table} WHERE {row}{parameter}'
        self.cur.execute(ex_string)
        rows = self.cur.fetchall()
        return rows

    def update(self, string, tple):
        '''
        executes sql string with values tple
        to update a table
        '''
        if all((string,tple)):
            try:
                self.cur.execute(string, tple)
                self.conn.commit()
                return True
            except Exception as error:
                return error
        else:
            print('input for SQL update operation is none')
            return False

    def lookup_string(self, string, tple):
        '''
        executes sql string with values tple
        if tple != None asuming it a fetchone scenario
        if tple = None, assuming it is a fetchall scenario
        '''
        rows = None
        if tple:
            try:
                self.cur.execute(string, tple)
                rows = self.cur.fetchone()
            except:
                print(f'could not lookup {tple} with {string}')
        else:
            self.cur.execute(string)
            rows = self.cur.fetchall()

        if not rows: print(f'WARNING: NO DATABASE RESULT\nfrom {string}')

        return rows

    def close(self):
        '''
        closes the db connection

        '''
        name = self.path_name
        try:
            self.conn.close()
            print(f'connection to {name} closed')
        except:
            print('could not close connection')

class k_interface:
    def __init__(self, dbase):
        self.database = dbase
        pass


