import sqlite3


def createdatabase():

    # Connect to SQLite database (or create if not exists)
    conn = sqlite3.connect('database.db')

    # Create a cursor object to execute SQL queries
    cursor = conn.cursor()

    # Create "Location" table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Location (
            CamID INTEGER PRIMARY KEY AUTOINCREMENT,
            IPaddrs TEXT,
            lattitude REAL,
            longitude REAL,
            AccLoc TEXT,
            HospName TEXT,
            HopsMailID TEXT
        )
    ''')

    # Create "ControlRoom" table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ControlRoom (
            id INTEGER PRIMARY KEY,
            name TEXT,
            mail TEXT,
            password TEXT
        )
    ''')

    # Create "Accidentlog" table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Accidentlog (
            ACCID INTEGER PRIMARY KEY,
            DayDatetime TEXT NOT NULL,
            location TEXT NOT NULL,
            Hospital TEXT NOT NULL
        )
    ''')

    # Commit changes and close connection
    conn.commit()
    conn.close()

    return("Database and tables created successfully.")
