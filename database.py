import sqlite3
import pandas as pd

def init_db(db_path="photos.db"):
    """Initializes the database and creates the photos table."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filepath TEXT UNIQUE,
            timestamp REAL,
            lat REAL,
            lon REAL,
            cluster_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def insert_photo(db_path, filepath, timestamp, lat, lon):
    """Inserts a single photo's EXIF data into the database."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT OR IGNORE INTO photos (filepath, timestamp, lat, lon) 
            VALUES (?, ?, ?, ?)
        ''', (filepath, timestamp, lat, lon))
        conn.commit()
    finally:
        conn.close()

def get_data_for_clustering(db_path):
    """Returns a Pandas DataFrame of all photos for clustering."""
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT id, filepath, timestamp, lat, lon FROM photos", conn)
    conn.close()
    return df

def update_clusters(db_path, cluster_mappings):
    """Updates the database with the assigned cluster IDs.
       cluster_mappings should be a list of tuples: (cluster_id, id)
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executemany("UPDATE photos SET cluster_id = ? WHERE id = ?", cluster_mappings)
    conn.commit()
    conn.close()
    
def get_clustered_data(db_path):
    """Fetches the final data with assigned clusters to organize files."""
    import sqlite3
    import pandas as pd
    conn = sqlite3.connect(db_path)
    # We added timestamp, lat, and lon to this query
    df = pd.read_sql_query("SELECT filepath, cluster_id, timestamp, lat, lon FROM photos", conn)
    conn.close()
    return df