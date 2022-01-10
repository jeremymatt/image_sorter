# -*- coding: utf-8 -*-
"""
Created on Fri Jan  7 10:18:58 2022

@author: jmatt
"""

import settings
import copy_replace_files_fns as CR

import os

from shutil import move



source_dir_root = settings.copy_move_source_dir

source_dir_name = os.path.split(source_dir_root)[1]
root = os.path.split(source_dir_root)[0]

dest_dir_root = os.path.join(root,'{}_new-files'.format(source_dir_name))

if settings.to_copy == 'all':
    dirs_to_copy = [item for item in os.listdir(source_dir_root) if os.path.isdir(os.path.join(source_dir_root,item))]
else:
    dirs_to_copy = settings.to_copy
    
dr = dirs_to_copy[0]
for dr in dirs_to_copy:
    sub_dirs = [item for item in os.listdir(os.path.join(source_dir_root,dr)) if (item not in settings.dirs_to_ignore) and (os.path.isdir(os.path.join(source_dir_root,dr,item)))]
    sdr = sub_dirs[0]
    files_list = []
    known_list_fn = os.path.join(source_dir_root,dr,settings.store_table_locn,'.copied_files')
    if not os.path.isdir(os.path.join(source_dir_root,dr,settings.store_table_locn)):
        os.makedirs(os.path.join(source_dir_root,dr,settings.store_table_locn))
    if os.path.isfile(known_list_fn):
        with open(known_list_fn,'r') as f:
            known_files = f.readlines()
        known_files = [file.strip() for file in known_files]
    else:
        known_files = []
        
    with open(known_list_fn,'a') as f:
         
        for sdr in sub_dirs:
            print('\n')
            src_dir_start = os.path.join(source_dir_root,dr,sdr)
            dst_dir_start = os.path.join(dest_dir_root,dr)
            if not os.path.isdir(dst_dir_start):
                os.makedirs(dst_dir_start)
            if not os.path.isdir(os.path.join(dst_dir_start,'Images')):
                os.makedirs(os.path.join(dst_dir_start,'Images'))
            if not os.path.isdir(os.path.join(dst_dir_start,'Videos')):
                os.makedirs(os.path.join(dst_dir_start,'Videos'))
            prev_str_len = 0
            CR.copy_dirs(src_dir_start,dst_dir_start,files_list,known_files,f,prev_str_len)
            
    # files = [file for file in os.listdir(dst_dir_start) if os.path.isdir(os.path.join(dst_dir_start,file))]
    # images
        
        
        
        
        
        
        # if not os.path.isdir(dst_dir):
        #     os.makedirs(dst_dir)
            
        # files = 
    
    
    


