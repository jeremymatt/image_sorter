# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 21:32:49 2021

@author: jmatt
"""

import os
import hashlib
import tqdm

from shutil import copy

import datetime as DT

def sec_to_timestring(seconds):
    
    mins = int(seconds//60)
            
    secs = int(round(seconds%60,0))
    hrs = int(mins//60)
    mins = mins%60
    string = '{}:{}:{}'.format(str(hrs).zfill(2),str(mins).zfill(2),str(secs).zfill(2))
    return string

class backup_dirs:
    def __init__(self,from_dir,to_dir):
        print('\nSearching Directories')
        self.num_dirs = 0
        self.num_removed = 0
        self.from_dir = from_dir
        self.to_dir = to_dir
        
        self.previous_length = 0
        
        self.longspace = '                                                                                                                                                                                                                                     '
        
        self.start_time = DT.datetime.now()
        
        self.ignore_dirs = [
            '$RECYCLE.BIN',
            'System Volume Information']
        
        self.ignore_files = [
            '.is_backup',
            '.bkup_settings']
        
    
    def backup(self):
        
        from_files = os.listdir(self.from_dir)
        if '.is_backup' in from_files:
            print('ERROR: from directory is a backup\n   Delete the ".is_backup" file if this is incorrect')
        else:
            
            self.copy_list = []
            self.delete_list = []
            self.rmdir_list = []
            cur_dir = ''
            self.check_dir(cur_dir)
            self.process_changes()
            self.print_bkup_state()
        
        
    def process_changes(self):
        print('\n')
        self.previous_length = 0
        for dr in tqdm.tqdm(self.rmdir_list,desc='Removing directories: '):
            self.rmdirs(dr)
        for file in tqdm.tqdm(self.delete_list,desc='Removing files: '):
            # os.remove(file)
            self.rmfile(file)
            
        start_time = DT.datetime.now()
        print('\n')
        for ind,val in enumerate(self.copy_list):
            frm,to = val
            delta_t = DT.datetime.now()-start_time
            seconds = delta_t.seconds
            breakhere=1
            if seconds>0:
                it_per_sec = ind/seconds
                sec_remaining = (len(self.copy_list)-ind)/it_per_sec
                sec_remaining = sec_to_timestring(sec_remaining)
                it_per_sec = round(it_per_sec,2)
            else:
                sec_remaining = 'n/a'
                it_per_sec = 'n/a '
            
            perc = "{}%".format(int(round(100*ind/len(self.copy_list))))
            print_str = 'Copying Files: {} | {}/{} [{}/{} {}it/s] - file: {}'.format(
                perc,
                ind,
                len(self.copy_list),
                sec_remaining,
                sec_to_timestring(seconds),
                it_per_sec,
                frm)
            
            
            pad_len = max(len(print_str),self.previous_length)-len(print_str)
            self.previous_length = len(print_str)
            # print('t{}b'.format(' '*25))
            print('\r{}{}'.format(print_str,' '*pad_len),end="")
            copy(frm,to)
            
            
    def print_bkup_state(self):
            
        completed = DT.datetime.now()
        completed = str(completed).split('.')[0]
        completed = completed.split(' ')
        
        fn = 'backup_{}_{}.txt'.format(completed[0],completed[1])
        
        fn = fn.replace(':','-')
        
        if not os.path.isdir(os.path.join(self.from_dir,'backup_logs')):
            os.makedirs(os.path.join(self.from_dir,'backup_logs'))
            
        old_logs = os.listdir(os.path.join(self.from_dir,'backup_logs'))
        old_logs.sort()
        
        for f in old_logs[:-2]:
            os.remove(os.path.join(self.from_dir,'backup_logs',f))
        
        with open(os.path.join(self.from_dir,'backup_logs',fn),'w', encoding="utf-8") as f:
            f.write('Removed directories:\n')
            for dr in self.rmdir_list:
                f.write('   {}\n'.format(dr))
            f.write('\n\nDeleted files:\n')
            for file in self.delete_list:
                f.write('del:   {}\n'.format(file))
            f.write('\n\nCopied files:\n')
            for file in self.copy_list:
                f.write('copy:   {}\n'.format(file))
                
                
        if not os.path.isdir(os.path.join(self.to_dir,'backup_logs')):
            os.makedirs(os.path.join(self.to_dir,'backup_logs'))
            
        copy(os.path.join(self.from_dir,'backup_logs',fn),
             os.path.join(self.to_dir,'backup_logs',fn))
        
        with open(os.path.join(self.to_dir,'.is_backup'), 'w') as f:
            f.write('is a backup')
            
        
        
    def check_dir(self,cur_dir):
        
        self.num_dirs += 1
        
        from_dir = os.path.join(self.from_dir,cur_dir)
        from_file_list,from_dir_list = self.list_dir(from_dir)
        to_dir = os.path.join(self.to_dir,cur_dir)
        to_file_list,to_dir_list = self.list_dir(to_dir)
        
        delta_t = str(DT.datetime.now()-self.start_time).split('.')[0]
        print_str = '{}: | Elapsed Time: {} | {}'.format(str(self.num_dirs).zfill(5),delta_t,from_dir)
        pad_len = max(len(print_str),self.previous_length)-len(print_str)
        self.previous_length = len(print_str)
        # print('t{}b'.format(' '*25))
        print('\r{}{}'.format(print_str,' '*pad_len),end="")
        
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
        in_both = [item for item in frm if (item in to)]
        in_from_only = [item for item in frm if (item not in to)]
        in_to_only = [item for item in to if (item not in frm)]
        
        return in_both,in_from_only,in_to_only
        
        
    def list_dir(self,abs_dir):
        lst = os.listdir(abs_dir)
        files = [item for item in lst if os.path.isfile(os.path.join(abs_dir,item)) and (item not in self.ignore_files)]
        dirs = [item for item in lst if os.path.isdir(os.path.join(abs_dir,item)) and (item not in self.ignore_dirs)]
        return files,dirs
        
    
    def rmfile(self,file):
            
        try:
            os.remove(file)
        except:
            os.chmod(file,0o777)
            os.remove(file)
             
    def rmdirs(self,cur_dir):  
        #Display progress
        self.display_txt = '{} checked, {} removed'.format(self.num_dirs,self.num_removed)
        
        #List the items in the directory print
        dir_list = os.listdir(cur_dir)
        #Store the files and subdirectories in separate lists
        new_files = [file for file in dir_list if os.path.isfile(os.path.join(cur_dir,file))]
        for file in new_files:
            self.rmfile(os.path.join(cur_dir,file))
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
            
