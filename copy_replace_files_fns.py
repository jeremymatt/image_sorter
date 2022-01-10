# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 11:07:57 2022

@author: jmatt
"""


import os
from shutil import move



def copy_dirs(src_dir,dst_dir,files_list,known_files,f,prev_str_len):
    items = os.listdir(src_dir)
    source_dirs = [item for item in items if os.path.isdir(os.path.join(src_dir,item))]
    source_files = [item for item in items if os.path.isfile(os.path.join(src_dir,item))]
    new_files = [item for item in source_files if os.path.join(src_dir,item) not in known_files]
    
    for file in new_files:
        
        src_file = os.path.join(src_dir,file)
        string = '{}: {}'.format(str(len(files_list)).zfill(4),src_file)
        print('\r{}{}'.format(string,' '*(prev_str_len-len(string))),end="")
        prev_str_len = len(string)
        
        if file.endswith('jpg'):
            dst_file = os.path.join(dst_dir,'Images',file)
        elif file.endswith('mp4'):
            dst_file = os.path.join(dst_dir,'Videos',file)
        else:
            dst_file = os.path.join(dst_dir,file)
            
        move(src_file,dst_file)
        with open(src_file,'w') as tmp_file:
            tmp_file.write('')
        files_list.append(src_file)
        f.write('{}\n'.format(src_file))
    
    breakhere=1
        
    while len(source_dirs)>0:
        dr = source_dirs.pop()
        src_dir_new = os.path.join(src_dir,dr)
        # dst_dir_new = os.path.join(dst_dir,dr)
        dst_dir_new = dst_dir
        
        if not os.path.isdir(dst_dir_new):
            os.makedirs(dst_dir_new)
        
        copy_dirs(src_dir_new,dst_dir_new,files_list,known_files,f,prev_str_len)
        
        
# dir_list = [item for item in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir,item))]
# for root in dir_list:
    
    
# def collect_files(source_dir,dst_dir):


