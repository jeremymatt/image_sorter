# -*- coding: utf-8 -*-
"""
Created on Sat Jul  6 23:20:57 2024

@author: jerem
"""
import os
import sqlite3
import hashlib
import re
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
from tqdm import tqdm  # Ensure you have tqdm installed: pip install tqdm

class PhotoDatabase:
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        if not os.path.exists(db_path):
            self.initialize_database()
            self.scan_directory(os.path.dirname(db_path))
        else:
            self.initialize_database()  # Ensure the database schema is correct

    def initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                md5_hash TEXT UNIQUE,
                album TEXT,
                date_taken TEXT,
                setting TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_name TEXT UNIQUE NOT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS photo_tags (
                photo_id INTEGER,
                tag_id INTEGER,
                FOREIGN KEY (photo_id) REFERENCES photos (id),
                FOREIGN KEY (tag_id) REFERENCES tags (id),
                UNIQUE (photo_id, tag_id)
            )
        ''')
        self.conn.commit()

        # Create indexes for fast access
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_photos_md5_hash ON photos (md5_hash)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_photos_file_path ON photos (file_path)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_photos_date_taken ON photos (date_taken)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_tags_tag_name ON tags (tag_name)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_photo_tags_photo_id ON photo_tags (photo_id)')
        self.cursor.execute('CREATE INDEX IF NOT EXISTS idx_photo_tags_tag_id ON photo_tags (tag_id)')
        self.conn.commit()

    def scan_directory(self, directory):
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self.is_image(file_path):
                    self.cursor.execute('''
                        INSERT OR IGNORE INTO photos (file_path, date_taken)
                        VALUES (?, NULL)
                    ''', (file_path,))
        self.conn.commit()

    def is_image(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.IMAGE_EXTENSIONS

    def get_date_taken(self, file_path):
        # Try to get the date taken from the image's EXIF data
        try:
            with Image.open(file_path) as img:
                exif_data = img._getexif()
                if exif_data:
                    for tag, value in exif_data.items():
                        decoded = TAGS.get(tag, tag)
                        if decoded == 'DateTimeOriginal':
                            return value.replace(':', '-', 2)
        except Exception as e:
            print(f"Error reading EXIF data from {file_path}: {e}")

        # Try to parse the filename
        file_name = os.path.basename(file_path)
        match = re.match(r'(\d{4}-\d{2}-\d{2})[ _](\d{2}[-.]\d{2}[-.]\d{2})', file_name)
        if match:
            date_str = match.group(1) + ' ' + match.group(2).replace('-', ':').replace('.', ':')
            try:
                return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass

        # Fallback to file's last modified date
        return datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')

    def update_missing_dates(self):
        self.cursor.execute('''
            SELECT id, file_path FROM photos WHERE date_taken IS NULL
        ''')
        rows = self.cursor.fetchall()
        for row in tqdm(rows, desc="Updating missing dates"):
            photo_id, file_path = row
            date_taken = self.get_date_taken(file_path)
            self.cursor.execute('''
                UPDATE photos SET date_taken = ? WHERE id = ?
            ''', (date_taken, photo_id))
        self.conn.commit()

    def compute_missing_hashes(self):
        self.cursor.execute('''
            SELECT id, file_path FROM photos WHERE md5_hash IS NULL OR md5_hash = ''
        ''')
        rows = self.cursor.fetchall()
        for row in tqdm(rows, desc="Computing missing hashes"):
            photo_id, file_path = row
            md5_hash = self.compute_md5(file_path)
            self.cursor.execute('''
                UPDATE photos SET md5_hash = ? WHERE id = ?
            ''', (md5_hash, photo_id))
        self.conn.commit()

    def compute_md5(self, file_path):
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def rescan_directory(self, directory):
        current_files = set()
        for root, _, files in os.walk(directory):
            for file in files:
                if self.is_image(file):
                    current_files.add(os.path.join(root, file))

        self.cursor.execute('SELECT file_path FROM photos')
        db_files = {row[0] for row in self.cursor.fetchall()}

        new_files = current_files - db_files
        missing_files = db_files - current_files

        for file_path in new_files:
            self.cursor.execute('''
                INSERT OR IGNORE INTO photos (file_path, date_taken)
                VALUES (?, NULL)
            ''', (file_path,))
        
        for file_path in missing_files:
            self.cursor.execute('''
                DELETE FROM photos WHERE file_path = ?
            ''', (file_path,))
        
        self.conn.commit()

    def find_files_in_directory(self, directory):
        self.cursor.execute('''
            SELECT file_path FROM photos WHERE file_path LIKE ?
        ''', (f'{directory}%',))
        return self.cursor.fetchall()

    def add_tag(self, tag_name):
        self.cursor.execute('''
            INSERT OR IGNORE INTO tags (tag_name)
            VALUES (?)
        ''', (tag_name,))
        self.conn.commit()

    def tag_photo(self, file_path, tag_name):
        self.cursor.execute('''
            SELECT id FROM photos WHERE file_path = ?
        ''', (file_path,))
        photo_id = self.cursor.fetchone()[0]

        self.cursor.execute('''
            SELECT id FROM tags WHERE tag_name = ?
        ''', (tag_name,))
        tag_id = self.cursor.fetchone()[0]

        self.cursor.execute('''
            INSERT OR IGNORE INTO photo_tags (photo_id, tag_id)
            VALUES (?, ?)
        ''', (photo_id, tag_id))
        self.conn.commit()

    def get_photos_by_tag(self, tag_name):
        self.cursor.execute('''
            SELECT p.file_path
            FROM photos p
            JOIN photo_tags pt ON p.id = pt.photo_id
            JOIN tags t ON t.id = pt.tag_id
            WHERE t.tag_name = ?
        ''', (tag_name,))
        return self.cursor.fetchall()

    def get_tags_by_photo(self, file_path):
        self.cursor.execute('''
            SELECT t.tag_name
            FROM tags t
            JOIN photo_tags pt ON t.id = pt.tag_id
            JOIN photos p ON p.id = pt.photo_id
            WHERE p.file_path = ?
        ''', (file_path,))
        return self.cursor.fetchall()

    def find_duplicates(self):
        self.cursor.execute('''
            SELECT file_path, md5_hash, COUNT(*)
            FROM photos
            GROUP BY md5_hash
            HAVING COUNT(*) > 1
        ''')
        return self.cursor.fetchall()

    def get_photos_by_date_range(self, start_date, end_date):
        self.cursor.execute('''
            SELECT file_path
            FROM photos
            WHERE date_taken BETWEEN ? AND ?
        ''', (start_date, end_date))
        return self.cursor.fetchall()

    def get_photos_before_date(self, date):
        self.cursor.execute('''
            SELECT file_path
            FROM photos
            WHERE date_taken < ?
        ''', (date,))
        return self.cursor.fetchall()

    def get_photos_after_date(self, date):
        self.cursor.execute('''
            SELECT file_path
            FROM photos
            WHERE date_taken > ?
        ''', (date,))
        return self.cursor.fetchall()

    def print_all_photos(self):
        self.cursor.execute('SELECT * FROM photos')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    def print_all_tags(self):
        self.cursor.execute('SELECT * FROM tags')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    def print_all_photo_tags(self):
        self.cursor.execute('SELECT * FROM photo_tags')
        rows = self.cursor.fetchall()
        for row in rows:
            print(row)

    def close(self):
        self.conn.close()

