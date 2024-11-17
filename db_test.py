# -*- coding: utf-8 -*-
"""
Created on Sat Jul  6 23:23:25 2024

@author: jerem
"""
import photo_database as PD
import os

path = r'D:\album_testing\albums'

# Usage example:
db = PD.PhotoDatabase(os.path.join(path,'photos.db'))
db.compute_missing_hashes()
db.update_missing_dates()
db.rescan_directory(path)

db.print_all_photos()

db.scan_directory(path)

db.list_photos_table_contents()

for root, _, files in os.walk(path):
    for file in files:
        file_path = os.path.join(root, file)
        print(file_path)
        if db.is_image(file_path):
            print('Is Image')
        else:
            print('Is not image')

db.find_files_in_directory(path)

photos = db.get_photos_by_tag('vacation')
tags = db.get_tags_by_photo('/path/to/photo.jpg')
duplicates = db.find_duplicates()
photos_before = db.get_photos_before_date('2020-01-01 00:00:00')
photos_after = db.get_photos_after_date('2020-01-01 00:00:00')
photos_in_range = db.get_photos_by_date_range('2020-01-01 00:00:00', '2021-01-01 00:00:00')
db.close()
