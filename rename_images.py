# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 21:34:33 2021

@author: jmatt
"""


from PIL import Image, ImageTk, ImageSequence, ImageOps
import os
import imghdr
import tqdm



def get_date_taken(path):
    return Image.open(path)._getexif()[36867]


root = r'I:test2\to_rename'
rename_to_path = True
rename_to_date = False

dirs_to_process = [root]
img_list = []
ctr = 0
while len(dirs_to_process)>0:
    print('{}: {} files found, {} dirs in queue'.format(ctr,len(img_list),len(dirs_to_process)))
    ctr+=1
    cur_dir = dirs_to_process.pop()
    new_files = [file for file in os.listdir(cur_dir) if os.path.isfile(os.path.join(cur_dir,file))]
    new_files = [os.path.join(cur_dir,file) for file in new_files]
    new_files = [file for file in new_files if imghdr.what(file) != None]
    img_list.extend(new_files)
    
    new_dirs = [item for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
    dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
    
file = img_list[0]
cur_path = ''


for file in tqdm.tqdm(img_list):
    path,fn = os.path.split(file)
    _,new_fn_base = os.path.split(path)
    if path == cur_path:
        ctr+=1
    else:
        ctr = 1
        cur_path = path
        
    ext = fn.split('.')[1]
    if rename_to_path:
        new_fn = '{} {}.{}'.format(new_fn_base,str(ctr).zfill(4),ext)
        os.rename(file,os.path.join(path,new_fn))
        
    if rename_to_date:
        date = get_date_taken(file)
    
img = Image.open(file)
exif = img._getexif()
