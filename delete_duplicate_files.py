# -*- coding: utf-8 -*-
"""
Created on Thu May 26 11:04:15 2022

@author: jerem
"""

import pandas as pd
import hashlib
import os
from pathlib import Path
import tqdm
import helper_functions as HF
import settings
import sys


if settings.delete_if_previously_hashed:
    print('*****')
    print('WARNING: program set to delete any files in {} that have previously been hashed')
    print('         Only continue if directory is a new download that has never been hashed')
    print('*****\n')
    response = input('Enter "yes_delete" to continue with deletion\n>> ')
    
    if response != "yes_delete":
        sys.exit()


cur_dir = settings.cur_dir
dirs_to_ignore = settings.dup_dirs_to_ignore
dir_list = [cur_dir]
str_len = 0


dir_list = HF.get_dir_tree(cur_dir,dir_list,str_len,dirs_to_ignore)

priority_dict = {}
user_priority_dict = {}
ctr = 1000

for priority,directory in settings.dir_priority:
    priority_dict[priority] = directory
    user_priority_dict[priority] = [directory,1]
    
for directory in tqdm.tqdm(dir_list,desc = 'Creating priority dictionary'):
    root_priority = None
    for key in user_priority_dict.keys():
        cur_dir,cur_count = user_priority_dict[key]
        if directory.startswith(cur_dir):
            if root_priority == None:
                root_priority = key
            else:
                prev_dir,prev_count = user_priority_dict[root_priority]
                if cur_dir.startswith(prev_dir):
                    root_dir = key
                    
    if root_priority == None:
        priority_dict[ctr] = directory
        ctr += 1
    else:
        root_dir,root_count = user_priority_dict[root_priority]
        cur_priority = root_priority-(0.00001*root_count)
        priority_dict[cur_priority] = directory
        user_priority_dict[root_priority][1] += 1
        
print_priority_dict = True
folder_priority_dict = {}
keys = list(priority_dict.keys())
keys.sort()
for key in keys:
    folder_priority_dict[priority_dict[key]] = key
    if print_priority_dict:
        print('{} : {}'.format(str(key).ljust(10,'.'),priority_dict[key]))
        

# cur_dir = dir_list[2]
hash_dict = {}

master_hash_set = set()
if os.path.isfile(settings.master_hash_list):
    with open(settings.master_hash_list,'r') as f:
        for line in f.readlines():
            master_hash_set.add(line.strip())
else:
    with open(settings.master_hash_list,'w') as f:
        f.write('')

ctr = 0
for cur_dir in tqdm.tqdm(dir_list,desc='hashing files'):
    files = {os.path.join(cur_dir,item) for item in os.listdir(cur_dir) if (os.path.join(cur_dir,item) not in dir_list) & (not item.endswith('hsh_txt_file'))}
    
    cur_dir_hashes = []
    
    hsh_fn = os.path.join(cur_dir,'.hsh_txt_file')
    
    file_mode = 'w'
    
    if os.path.isfile(hsh_fn) and not settings.redo_hashes:
        file_mode = 'a'
        with open(hsh_fn,'r') as f:
            lines = f.readlines()
            
        for line in lines:
            file_hash,file = line.strip().split('(*)(*)')
            if file in files:
                HF.add_hash_to_dict(hash_dict, file_hash, file)
                cur_dir_hashes.append((file_hash,file))
                files.remove(file)
                master_hash_set.add(file_hash)
            
        #check for correct # of files, drop into hash dict
    # else:
    with open(hsh_fn,file_mode) as f:
    
        for file in files:
            file_hash = hashlib.md5(open(file,'rb').read()).hexdigest()
            
            hashed_previously = file_hash in master_hash_set
            
            if not hashed_previously:
                master_hash_set.add(file_hash)
                    
            
            if (settings.delete_if_previously_hashed) & (hashed_previously):
                print('removing : {}'.format(file))
                os.remove(file)
            else:
                
                try:
                    f.write('{}(*)(*){}\n'.format(file_hash,file))
                except:
                    new_file = HF.clear_special_characters(file)
                    os.rename(os.path.join(cur_dir,file),os.path.join(cur_dir,new_file))
                    file = new_file
                    f.write('{}(*)(*){}\n'.format(file_hash,file))
                    
                HF.add_hash_to_dict(hash_dict, file_hash, file)
                cur_dir_hashes.append((file_hash,file))
            
            
    with open(hsh_fn,'w') as f:            
        for file_hash,file in cur_dir_hashes:
            ctr+=1
            f.write('{}(*)(*){}\n'.format(file_hash,file))

print('\nfound {} files\n'.format(ctr))

ctr = 0   
errors = []   
# key = list(hash_dict.keys())[-5]  
# len(hash_dict[key])   
for key in tqdm.tqdm(hash_dict.keys()):
    if len(hash_dict[key]) > 1:
        del_list = []
        for item in hash_dict[key]:
            # find_priority = True
            
            path,fn = os.path.split(item)
            
            if path in folder_priority_dict.keys():
                del_list.append((folder_priority_dict[path],item))
            else:
                print('DIR NOT FOUND IN PRIORITY LIST: {}'.format(item))
                break
                        
        del_list.sort(reverse=False)
            # print(del_list)
            
        for priority,item in del_list[1:]:
            if settings.delete_dups:
                try:
                    os.remove(item)
                    hash_dict[key].remove(item)
                    ctr += 1
                except:
                    errors.append((priority,item))
            else:
                print('to remove: {}'.format(item))
      
print('\nremoved {} files'.format(ctr))

folder_dict = {}
for key in tqdm.tqdm(hash_dict.keys(),desc = 'building path dict for hash file generation'):
    for item in hash_dict[key]:
        path,fn = os.path.split(item)
        if path in folder_dict.keys():
            folder_dict[path].append((key,fn))
            folder_dict[path].sort(reverse=False)
        else:
            folder_dict[path] = [(key,fn)]

empty_dirs = []
for path in tqdm.tqdm(dir_list,desc='removing hash text files from empty dirs'):
    if path not in folder_dict.keys():
        empty_dirs.append(path)
        
for path in tqdm.tqdm(empty_dirs,desc='removing empty dirs'):
    if os.path.isfile(os.path.join(path,'.hsh_txt_file')):
        os.remove(os.path.join(path,'.hsh_txt_file'))
        
for path in tqdm.tqdm(folder_dict.keys(),desc = 'Writing hash text files'):
    with open(os.path.join(path,'.hsh_txt_file'),'w') as f:
        for file_hash,fn in folder_dict[path]:
            f.write('{}(*)(*){}\n'.format(file_hash,os.path.join(path,fn)))

with open(settings.master_hash_list,'w') as f:
    for hsh in master_hash_set:
        f.write('{}\n'.format(hsh))
                
                
                
                
                
                
                
                