# -*- coding: utf-8 -*-
"""
Created on Fri Feb 25 16:24:46 2022

@author: jmatt
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""


# from argparse import ArgumentParser


# import tkinter as tk
# from PIL import Image, ImageTk, ImageSequence, ImageOps, ImageFile, ImageEnhance
# ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
import hashlib
import time
import pickle as pkl


try:
    import settings
except:
    import temp_settings as settings


import imghdr

# Monkeypatch bug in imagehdr
#https://stackoverflow.com/questions/36870661/imghdr-python-cant-detec-type-of-some-images-image-extension
from imghdr import tests

def test_jpeg1(h, f):
    """JPEG data in JFIF format"""
    if b'JFIF' in h[:23]:
        return 'jpeg'


JPEG_MARK = b'\xff\xd8\xff\xdb\x00C\x00\x08\x06\x06' \
            b'\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f'

def test_jpeg2(h, f):
    """JPEG with small header"""
    if len(h) >= 32 and 67 == h[5] and h[:32] == JPEG_MARK:
        return 'jpeg'


def test_jpeg3(h, f):
    """JPEG data in JFIF or Exif format"""
    if h[6:10] in (b'JFIF', b'Exif') or h[:2] == b'\xff\xd8':
        return 'jpeg'

tests.append(test_jpeg1)
tests.append(test_jpeg2)
tests.append(test_jpeg3)


class App:
    def __init__(self, source_dir):
        
        
        self.source_dir = source_dir
        
        
    def generate_settings(self):
        
        
        # #Load saved hashes if available.  Otherwise init empty variables
        # #as flags and to avoid errors when saving state for undo
        # if os.path.isfile(os.path.join(self.source_dir,'.pickled_hashes')):
        #     with open(os.path.join(self.source_dir,'.pickled_hashes'), 'rb') as file:
        #         self.hash_dict = pkl.load(file)
        #         self.dup_hashes = pkl.load(file)
        #     self.hash_ctr = 0
        # else:
        #     self.hash_dict = None
        #     self.dup_hashes = None
        #     self.hash_ctr = None
           
        self.get_img_list()
        
        
    def get_img_list(self):
        
        file_list_fn = os.path.join(self.source_dir,'.img_files_list')
        print("GETTING IMAGE LIST")
        #If an image list file exists, load from file, else inspect directories
        #for image files
        #Record the start time
        if os.path.isfile(file_list_fn):
            print('reading file list')
            self.read_file_list()
            #Indicate that the existing file list was read from file
            self.img_list_updated = False
        else:
            #Indicate that the existing file list was updated from the directory
            self.img_list_updated = True
        
            
            dirs_to_process = [self.source_dir]
            self.img_list = []
            ctr = 0
            while len(dirs_to_process)>0:
                
                # print('point1')
                #Pop directory from list to process
                cur_dir = dirs_to_process.pop()
                        
                # print('point2')
                #Display progress
                ctr +=1
                txt = '\r{} dirs checked ({} dirs remaining).  Found {} images'.format(ctr,len(dirs_to_process),len(self.img_list))
                print(txt,end='')
                
                # print('point3')
                #list of all files in the directory
                new_files = [file for file in os.listdir(cur_dir) if os.path.isfile(os.path.join(cur_dir,file))]
                
                # print('point4')
                #Add absolute path to the file names
                new_files = [os.path.join(cur_dir,file) for file in new_files]
                
                #Check if file extension is a common video type for speed
                new_files = [file for file in new_files if file.split('.')[-1] not in settings.video_extensions]
                
                # print('point5')
                #Check if file is an image file
                new_files = [file for file in new_files if imghdr.what(file) != None]
                # print('point6')
                #Add new images to the image list
                self.img_list.extend(new_files)
                
                
                # print('point7')
                #Recursively include subdirectories
                if settings.include_sub_dirs:
                    #Add subdirectories in the current directory to the directories to check
                    new_dirs = [item for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
                    dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
            
            print('\nCOMPLETED\nSearching for images in:\n     {}\n     Found {} images'.format(self.source_dir,len(self.img_list)))
            
            self.img_list.sort()
            
            
            
    def read_file_list(self):
        #Load the image list from file
        file_list_fn = os.path.join(self.source_dir,'.img_files_list')
                
        with open(file_list_fn,'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        self.img_list = [line.strip() for line in lines]
            
    def write_file_list(self):
        #Write the image list to file
        file_list_fn = os.path.join(self.source_dir,'.img_files_list')
        
        with open(file_list_fn,'w', encoding='utf-8') as file:
            for fn in self.img_list:
                file.write('{}\n'.format(fn))
                
                
    def reload_img_list(self,dummy=None):
        #Force check of source directory for image files
        file_list_fn = os.path.join(self.source_dir,'.img_files_list')
        
        #If a file list exists, remove it
        if os.path.isfile(file_list_fn):
            print('removing old list')
            os.remove(file_list_fn)
                  
        self.get_img_list()
                    
    def calc_time_remaining(self,start_time,ctr,num_items):
        #Check how much time has elapsed
        delta_time = time.time()-start_time
        if (delta_time>0) & (ctr > 0):
            #Calculate the remaining time & convert to a string
            items_per_sec = ctr/delta_time
            remaining_sec = (num_items-ctr)/items_per_sec
            
            hrs,minutes,seconds = self.sec_to_hr_min_sec(remaining_sec)
            
            time_remaining = '{}hr {}min {}sec'.format(hrs,str(minutes).zfill(2),str(seconds).zfill(2))
        else:
            #Placeholder for the first iteration
            time_remaining = '---'
        
        return time_remaining
    
    def sec_to_hr_min_sec(self,remaining_sec):
        seconds = int(round(remaining_sec % 60))
        minutes = int(remaining_sec/60)
        hrs = int(minutes/60)
        minutes %= 60
        
        return hrs,minutes,seconds
        
               
    def check_file_hashes(self,dummy=None):
        #Init the hash dict and list of dup hashes
        self.hash_dict = {}
        self.dup_hashes = set()
        #Record the start time
        start_time = time.time()
        missing_files = []
        num_items = len(self.img_list)
        print('Checking file hashes for images in: {}'.format(self.source_dir))
        for ctr,file in enumerate(self.img_list):
            time_remaining = self.calc_time_remaining(start_time,ctr,num_items)
            #Build the text display string and show the text window to update
            #the user
            txt = '\rChecked {}/{} ({} remaining)'.format(ctr,len(self.img_list),time_remaining)
            print(txt,end='')
            #Calculate the hash of the current file
            if os.path.isfile(file):
                hsh = hashlib.md5(open(file,'rb').read()).hexdigest()
            else:
                missing_files.append(file)
            if hsh in self.hash_dict.keys():
                #Add the current hash the duplicate hashes set and add the file
                #path to the hash dict
                self.dup_hashes.add(hsh)
                self.hash_dict[hsh].append(file)
            else:
                #Add the current file to the hash dict
                self.hash_dict[hsh] = [file]
                
        for key in self.hash_dict.keys():
            self.hash_dict[key].sort()
            
        for file in missing_files:
            self.img_list.remove(file)
            
        
        #Convert the duplicate hash set to a list and update the text window
        self.dup_hashes = list(self.dup_hashes)
        self.dup_hashes.sort()
        txt = 'Checked {} images, found {} duplicate hashes'.format(len(self.img_list),len(self.dup_hashes))
        print('\n{}'.format(txt))
        
        
    def save_hashes(self):
                
        #If a hash dict has been generated, save it to disk
        if self.hash_dict != None:
            with open(os.path.join(self.source_dir,'.pickled_hashes'), 'wb') as file:
                pkl.dump(self.hash_dict,file)
                pkl.dump(self.dup_hashes,file)
        else:
            print('ERROR: no hash dict')
        
          
    # def remove_all_missing_files(self):
    #     #Record the start time
    #     start_time = time.time()
    #     missing_files = []
    #     num_items = len(self.img_list)
    #     self.close_open_image()
    #     for ctr,file in enumerate(self.img_list):
    #         time_remaining = self.calc_time_remaining(start_time,ctr,num_items)
    #         #Build the text display string and show the text window to update
    #         #the user
    #         txt = 'Checked {}/{} ({} remaining)'.format(ctr,len(self.img_list),time_remaining)
    #         self.show_text_window('Checking file list for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
    #         #Check if the file is missing or not
    #         if not os.path.isfile(file):
    #             missing_files.append(file)
    #             self.img_list_updated = True
           
    #     #Remove the missing files
    #     for file in missing_files:
    #         self.img_list.remove(file)
            
    #     #Update the image index
    #     self.cur_img = min(len(self.img_list)-1,self.cur_img)
        
    #     txt = 'Checked {} entries, found {} missing files ({} remaining)'.format(num_items,len(missing_files),len(self.img_list))
    #     self.show_text_window('COMPLETED:\nChecking for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
    #     #Get the number of items in the current folder & the position in the folder
        
        
        
#sample call: 
    # python main.py -huc8 Winooski_River -huc12_list WIN_0502 -n 2 -reach_type SGA

def main():
    """Highest-level function. Called by user.
    
    sample calls:

    Parameters:
        None

    Returns:
        None
    """

    # ### Initialize argument parser
    # parser = ArgumentParser()

    # ### Add arguments to parser
    # parser.add_argument('-s_dir', dest='source_dir', default="None")
    # parser.add_argument('-d_dir', dest='dest_root', default="None")
    # args = parser.parse_args()
    
    # #Pull the source and destination directories from the argument parser
    # source_dir = args.source_dir
    # dest_root = args.dest_root
    
    # run_program = True
    
    
    source_dir = settings.to_check_dir
    
    
    app = App(source_dir)
    
    gen_img_list = False
    if gen_img_list:
        app.reload_img_list()
        app.write_file_list()
        
    calc_hashes = True
    if calc_hashes:
        app.read_file_list()
        app.check_file_hashes()
        app.save_hashes()



if __name__ == '__main__':
    main()