import sqlite3

# open connection to database
conn = sqlite3.connect('database.db')

# create cursor object
cursor = conn.cursor()

# execute drop table statement
cursor.execute('DROP TABLE youtube_object;')

# commit changes
conn.commit()

# close connection
conn.close()
