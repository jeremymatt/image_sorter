# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 21:32:49 2021

@author: jmatt
"""

import os
import hashlib
import tqdm

from shutil import copy

class backup_dirs:
    def __init__(self,from_dir,to_dir):
        self.num_dirs = 0
        self.num_removed = 0
        self.from_dir = from_dir
        self.to_dir = to_dir
        
        self.copy_list = []
        self.delete_list = []
        self.rmdir_list = []
        cur_dir = ''
        self.check_dir(cur_dir)
        for dr in self.rmdir_list:
            self.rmdirs(dr)
        for file in self.delete_list:
            os.remove(file)
        for frm,to in tqdm.tqdm(self.copy_list,desc="Copying files: "):
            copy(frm,to)
            
        
        
    def check_dir(self,cur_dir):
        from_dir = os.path.join(self.from_dir,cur_dir)
        from_file_list,from_dir_list = self.list_dir(from_dir)
        to_dir = os.path.join(self.to_dir,cur_dir)
        to_file_list,to_dir_list = self.list_dir(to_dir)
        
        files_both,files_from,files_to = self.compare_lists(from_file_list, to_file_list)
        dirs_both,dirs_from,dirs_to = self.compare_lists(from_dir_list, to_dir_list)
        
        for file in files_to:
            self.delete_list.append(os.path.join(self.to_dir,cur_dir,file))
        
        for file in files_both:
            if not self.compare_files(cur_dir, file):
                self.delete_list.append(os.path.join(self.to_dir,cur_dir,file))
                self.copy_list.append((os.path.join(self.from_dir,cur_dir,file),
                                       os.path.join(self.to_dir,cur_dir,file)))
                
        for file in files_from:
            self.copy_list.append((os.path.join(self.from_dir,cur_dir,file),
                                   os.path.join(self.to_dir,cur_dir,file)))
         
        dirs_to = [os.path.join(self.to_dir,cur_dir,dr) for dr in dirs_to]
        self.rmdir_list.extend(dirs_to)
        
        for dr in dirs_from:
            os.makedirs(os.path.join(self.to_dir,cur_dir,dr))
            self.check_dir(os.path.join(cur_dir,dr))
            
        for dr in dirs_both:
            self.check_dir(os.path.join(cur_dir,dr))
        
    def compare_files(self,cur_dir,file):
        frm_file = os.path.join(self.from_dir,cur_dir,file)
        frm_size = os.path.getsize(frm_file)
        to_file = os.path.join(self.to_dir,cur_dir,file)
        to_size = os.path.getsize(to_file)
        return frm_size == to_size
    
    def compare_lists(self,frm,to):
        in_both = [item for item in frm if item in to]
        in_from_only = [item for item in frm if item not in to]
        in_to_only = [item for item in to if item not in frm]
        
        return in_both,in_from_only,in_to_only
        
        
    def list_dir(self,abs_dir):
        lst = os.listdir(abs_dir)
        files = [item for item in lst if os.path.isfile(os.path.join(abs_dir,item))]
        dirs = [item for item in lst if os.path.isdir(os.path.join(abs_dir,item))]
        return files,dirs
        
        
             
    def rmdirs(self,cur_dir):  
        #Display progress
        self.display_txt = '{} checked, {} removed'.format(self.num_dirs,self.num_removed)
        
        #List the items in the directory print
        dir_list = os.listdir(cur_dir)
        #Store the files and subdirectories in separate lists
        new_files = [file for file in dir_list if os.path.isfile(os.path.join(cur_dir,file))]
        for file in new_files:
            os.remove(os.path.join(cur_dir,file))
        new_dirs = [os.path.join(cur_dir,item) for item in dir_list if os.path.isdir(os.path.join(cur_dir,item))]
        #For each subdirectory, increment the counter and call the rmdirs function
        for new_dir in new_dirs:
            self.num_dirs += 1
            self.rmdirs(new_dir)
        
        # #After checking all subdirectories, re-list the directory and 
        # #list any remaining directories
        # dir_list = os.listdir(cur_dir)
        # non_empty_dirs = [item for item in dir_list if os.path.isdir(os.path.join(cur_dir,item))]
        # #If there are no files files and no remaining subdirectories, remove
        # #the directory and increment the counter
        # if (len(new_files)+len(non_empty_dirs)) == 0:
        os.rmdir(cur_dir)
        self.num_removed += 1
            
