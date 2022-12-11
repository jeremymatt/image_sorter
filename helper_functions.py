# -*- coding: utf-8 -*-
"""
Created on Thu May 26 11:05:28 2022

@author: jerem
"""

import pandas as pd
import hashlib
import os
from pathlib import Path
import tqdm


chr_lst = list(r'abcdefghijklmnopqrstuvwxyz0123456789-_|(). ')

for char in chr_lst[:26]:
    chr_lst.append(char.upper())

def clear_special_characters(string):
    path,fn = os.path.split(string)
    new_fn = [char for char in list(fn) if char in chr_lst]
    new_fn = ''.join(new_fn)
    new_string = os.path.join(path,new_fn)
    return new_string

def get_file_list(root,dirs_to_ignore = []):
    dirs_to_process = set()
    dirs_to_process.add(root)
    
    files_to_hash = set()
    print("\n")
    ctr = 0
    while len(dirs_to_process)>0:
        ctr+=1
        cur_dir = dirs_to_process.pop()
        print("\r{}: {} remaining.  Processing: {}".format(str(ctr).zfill(3),len(dirs_to_process),cur_dir))
        dir_list = os.listdir(cur_dir)
        dir_list = [os.path.join(cur_dir,item) for item in dir_list]
        new_dirs = set([item for item in dir_list if (os.path.isdir(item))])
        dir_len = len(new_dirs)
        breakhere=1
        best = [item for item in new_dirs if item.split('\\')[-1] == 'best']
        if len(best)>0:
            breakhere=1
        new_dirs = set([item for item in new_dirs if not item in dirs_to_ignore])
        if dir_len != len(new_dirs):
            print('dropped {} dirs'.format(dir_len-len(new_dirs)))
        dirs_to_process = dirs_to_process.union(new_dirs)
        
        new_files = set([item for item in dir_list if os.path.isfile(item)])
        files_to_hash = files_to_hash.union(new_files)
        
    # if extensions != None:
    #     files_to_hash = [item for item in files_to_hash if item.split('.')[1].lower() in extensions]

    return files_to_hash



def get_dir_tree(cur_dir,dir_list,str_len,dirs_to_ignore = []):
    
    # print('str_len: {}, cur_len: {}, delta: {}'.format(str_len,len(cur_dir_string),str_len-len(cur_dir_string)))
    
    
    dirs = [os.path.join(cur_dir,item) for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
    for item in dirs:
        cur_dir_string = 'Processing: {}'.format(cur_dir)
        print("\r{}{}".format(cur_dir_string,' '*(len(cur_dir_string)-str_len)),end="")
        str_len = len(cur_dir_string)
        dir_list.append(item)
        get_dir_tree(item,dir_list,str_len,dirs_to_ignore)
    return dir_list


def add_hash_to_dict(hash_dict,file_hash,file):
    
    if file_hash in hash_dict.keys():
        hash_dict[file_hash].append(file)
    else:
        hash_dict[file_hash] = [file]
    