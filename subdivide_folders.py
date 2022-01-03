# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 21:56:38 2021

@author: jmatt
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Nov  9 21:34:33 2021

@author: jmatt
"""


from PIL import Image, ImageTk, ImageSequence, ImageOps
import os
import imghdr
import tqdm
from shutil import move
import numpy as np



def get_date_taken(path):
    return Image.open(path)._getexif()[36867]

file_limit = 1000

root = r'P:test3'
rename_to_path = True
rename_to_date = False

dirs_to_process = [root]
ctr = 0
while len(dirs_to_process)>0:
    print('\r{}: {} dirs in queue                                     '.format(ctr,len(dirs_to_process)),end='')
    ctr+=1
    cur_dir = dirs_to_process.pop()
    
    items = os.listdir(cur_dir)
    new_dirs = [item for item in items if os.path.isdir(os.path.join(cur_dir,item))]
    dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
    num_items = len(items) - len(new_dirs)
    if num_items>file_limit:
        root = os.path.split(cur_dir)[0]
        cd_name = os.path.split(cur_dir)[1]
        num_sub_folders = int(num_items/file_limit)
        if num_items%file_limit > 0:
            num_sub_folders += 1
        
        for i in range(num_sub_folders):
            dir_to_make = os.path.join(root,cd_name,"{}-{}".format(cd_name,str(i+1).zfill(2)))
            if not os.path.isdir(dir_to_make):
                os.makedirs(dir_to_make)
        
        new_files = [file for file in items if os.path.isfile(os.path.join(cur_dir,file))]
        
        dest_files = []
        for ind,file in enumerate(new_files):
            folder_num = str(int(np.ceil((ind+1)/file_limit))).zfill(2)
            dest_dir_name = '{}-{}'.format(cd_name,folder_num)
            dest_files.append(os.path.join(root,cd_name,dest_dir_name,file))
            
        new_files = [os.path.join(cur_dir,file) for file in new_files]
        
        moves = list(zip(new_files,dest_files))
        
        for ind,move_paths in enumerate(moves):
            print('\r{}: {} dirs in queue. moving {}/{}               '.format(ctr,len(dirs_to_process),ind,num_items),end='')
            source,dest = move_paths
            move(source,dest)
        
