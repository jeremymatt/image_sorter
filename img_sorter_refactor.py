# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""


from argparse import ArgumentParser


import tkinter as tk
from PIL import Image, ImageTk, ImageSequence, ImageOps, ImageFile, ImageEnhance
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
import copy as cp
import random
import hashlib
import time
import pickle as pkl
import image_object as IO
import gc

try:
    import settings
except:
    import example_settings as settings

from shutil import move

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
    def __init__(self, parent,source_dir,dest_root):
        
        self.remove_ctr = 0
        
        
        #Init the parent canvas
        self.start_time = time.time()
        self.parent = parent
        self.parent.lift()
        self.parent.focus_force()
        self.parent_canvas = tk.Canvas(parent, bg='black', highlightthickness=0)
        self.parent_canvas.pack(fill=tk.BOTH, expand=True)
        
        #Record width & height of the screen
        self.screen_width = self.parent.winfo_screenwidth()
        self.screen_height = self.parent.winfo_screenheight()

        self.open_image_window = False
        
        # if source_dir == "None":
        #     #Use the default source directory from the settings file
        #     self.source_dir = settings.source_dir
        # else:
        #     #Use the user-supplied source directory
        #     self.source_dir = source_dir
        self.source_dir = source_dir
        
        #Set the temp trash directory and make if it doesn't exist
        self.trash_dest = os.path.join(source_dir,'.temp_trash')
        if not os.path.isdir(self.trash_dest):
            os.makedirs(self.trash_dest)
        
        # if dest_root == "None":
        #     #Use destination root specified in the settings file
        #     self.dest_root = settings.dest_root
        # else:
        #     #Use user-supplied destination direectory
        #     self.dest_root = dest_root
        self.dest_root = dest_root
            
        #Extract the keystroke dictionary from settings and prepend the destination
        #root to each path
        self.move_dict = settings.move_dict
        self.keep_mode_move_dict = settings.keep_mode_move_dict
        # for key in self.move_dict.keys():
        #     self.move_dict[key] = os.path.join(self.dest_root,self.move_dict[key])
        
        #Flag to indicate that image display hasn't started yet
        self.displaying_images = False
        #Show the settings window so user knows where files are being viewed
        #from and moved to
        self.show_settings_window()
        
    def generate_settings(self):
        #Init the history list of previously viewed images for random view order
        self.previous_images = []
        #Set the index into the image list
        self.cur_img = 0
        #Load the display order from the settings file
        self.rand_order = settings.random_display_order
        #Load zoom/shrink to canvas setting
        self.fit_to_canvas = settings.fit_to_canvas
        #Init a variable that will hold the current image
        self.current_image = None
        #Default delay for the gif frame rate
        self.delay = 20
        #Set the default non-full screen width height
        self.default_window_width = 500
        self.default_window_height= 500
        #flag to indicate that there is no open image window
        self.img_window = None
        self.canvas = None
        self.has_open_image=False
        #flag to indicate that a compare window is open
        self.has_compare_window = False
        #Init a list of file move events for undo purposes
        self.move_events = []
        #Flag to show the menu window
        self.show_menu = False
        self.open_text_window = False
        #Set flags to control duplicate file handling
        self.keep_both = False
        self.keep_new = False
        self.keep_existing = False
        self.processing_duplicates = False
        #Set flag to control sorting mode
        self.keep_mode = False
        #set flag for reviewing duplicate hash values
        self.reviewing_dup_hashes = False
        
        #Default image information setting
        self.img_info_display = 2
        
        #Flag for missing images
        self.img_missing = False
        
        #set mouse position to 0,0 if mouse hasn't moved
        self.mouse_x = 0
        self.mouse_y = 0
        #Variable to check if image is being dragged
        self.panning_image = False
        
        #Load saved hashes if available.  Otherwise init empty variables
        #as flags and to avoid errors when saving state for undo
        if os.path.isfile(os.path.join(self.source_dir,'.pickled_hashes')):
            with open(os.path.join(self.source_dir,'.pickled_hashes'), 'rb') as file:
                self.hash_dict = pkl.load(file)
                self.dup_hashes = pkl.load(file)
            self.hash_ctr = 0
        else:
            self.hash_dict = None
            self.dup_hashes = None
            self.hash_ctr = None
            
        #Counter for how many images where processed
        self.processed_images = 0
            
        #Init empty backup list/index variables to avoid error when saving state
        #for undo
        self.img_list_bkup = None
        self.cur_img_bkup = None
        #Load the full screen setting from the settings files
        self.full_screen = settings.start_fullscreen
        #Init the window dimensions 
        if self.full_screen:
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        else:
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        
        #Get the list of images in the source directory
        self.get_img_list()
        
    def continue_run(self,event):
        key = event.char
        if key in 'abcdefghijklmnopqrstuvwxyz1234567890':
            self.settings_window.destroy()
            self.parent.focus_force()
            # set the parent keybindings
            self.set_keybindings(self.parent)
            #Initialize the starting settings
            self.generate_settings()
            #Flag to indicate that the program has continued
            self.displaying_images = True
        
    def show_settings_window(self,dummy=None):
        #Init the menu window 
        self.settings_window = tk.Toplevel(self.parent)
        self.settings_window.bind("<Control-q>",self.quit_app)           #Quit app
        self.settings_window.bind("<Escape>",self.quit_app)              #Quit app
        self.settings_window.bind('<KeyRelease>',self.continue_run)      #Monitor key presses (check for file moves)
        #Add a canvas
        canvas = tk.Canvas(self.settings_window,height=1000,width=500)
        canvas.pack()
        #Get the text for the menu
        menu_txt = ''
        menu_txt += '    Read files from: {}\n'.format(self.source_dir)
        menu_txt += 'Move files files to: {}\n'.format(self.dest_root)
        menu_txt += '\nAny letter/number key ==> continue\nCtrl+Q ==> quit\nEsc ==> quit'
        #Create a text item of the menu text
        text_item = canvas.create_text(
            25,
            25,
            fill='black',
            font='times 10 bold',
            text=menu_txt,tag='menu_txt',
            anchor=tk.NW)
        #Make a bounding box around the text to determine required window size
        bbox = canvas.bbox(text_item)
        dim = (bbox[2]-bbox[0]+100,bbox[3]-bbox[1]+100)
        #Set the window geometry to the dimensions of the bounding box plus 
        #some padding and move the text item to the center of the window
        locn = [int(self.screen_width/2-dim[0]/2),int(self.screen_height/2-dim[1]/2)]
        self.settings_window.geometry(f'{dim[0]}x{dim[1]}+{locn[0]}+{locn[1]}')
        canvas.move(text_item,25,25)
        canvas.update()
        canvas.tag_raise(text_item)
        self.settings_window.focus_force()
        
    def close_txt_window(self,dummy=None):
        #If a text window is open, close it and reload the image to bring
        #it back to focus
        if self.open_text_window:
            self.open_text_window = False
            self.txt_window.destroy()
            self.reload_img()
        
    def show_input_window(self,dummy=None):
        #Init the menu window 
        self.input_window = tk.Toplevel(self.parent)
        self.input_window.title('Go to image # of {}'.format(len(self.img_list)))
        self.input_window.geometry('400x200+200+200')
        self.input_window.bind('<Return>',self.close_input_and_go)      #Close text window if one is open
        self.input_window.bind("<Control-q>",self.quit_app)           #Quit app
        self.input_window.bind("<Escape>",self.quit_app)              #Quit app
        
        self.input_txt = tk.Text(self.input_window,height=7,width=100)
        
        self.input_txt.pack()
        
        button = tk.Button(self.input_window,text='Go to',command = self.close_input_and_go)
        button.pack()
        button2 = tk.Button(self.input_window,text='Cancel',command = self.close_input)
        button2.pack()
        self.input_window.focus_force()
        self.input_txt.focus_force()
        self.input_txt.focus()
        
        
    def close_input(self,dummy=None):
        self.input_window.destroy()
        
    def close_input_and_go(self,dummy=None):
        inpt = self.input_txt.get('1.0', "end-1c")
        
        prev_img = self.cur_img
        
        if inpt[0] in ['-','+']:
            try:
                inpt = int(inpt)
            except:
                return
            self.cur_img += inpt
            self.cur_img %= len(self.img_list)
        else:
            try:
                inpt = int(inpt)
            except:
                return
            self.cur_img = min(inpt-1,len(self.img_list)-1)
            
            
        self.update_folder_position(self.cur_img-prev_img)
            
        self.load_new_image()           
          
        self.input_window.destroy()
        
        
    def show_text_window(self,txt,delete_dups=False):
        if not self.open_text_window:
            self.open_text_window = True
            #Init the menu window 
            self.txt_window = tk.Toplevel(self.parent)
            
            self.set_keybindings(self.txt_window)
            
            if delete_dups == 'hashes':
                self.txt_window.bind('<Alt-P>', self.delete_dup_hashes)    #Toggle reviewing lists of images with dup hashes
            elif delete_dups == 'empty_dir':
                self.txt_window.bind('<Alt-P>', self.empty_current_folder)    #Toggle reviewing lists of images with dup hashes
                
            #Add a canvas
            self.txt_canvas = tk.Canvas(self.txt_window,height=1000,width=500)
            self.txt_canvas.pack()
        else:
            self.txt_canvas.delete(self.text_item)
        #Create a text item of the menu text
        self.text_item = self.txt_canvas.create_text(
            25,
            25,
            fill='black',
            font='times 10 bold',
            text=txt,tag='menu_txt',
            anchor=tk.NW)
        #Make a bounding box around the text to determine required window size
        bbox = self.txt_canvas.bbox(self.text_item)
        dim = (bbox[2]-bbox[0]+100,bbox[3]-bbox[1]+100)
        #Set the window geometry to the dimensions of the bounding box plus 
        #some padding and move the text item to the center of the window
        locn = [int(self.screen_width/2-dim[0]/2),int(self.screen_height/2-dim[1]/2)]
        self.txt_window.geometry(f'{dim[0]}x{dim[1]}+{locn[0]}+{locn[1]}')
        self.txt_canvas.move(self.text_item,25,25)
        self.txt_canvas.update()
        # self.txt_canvas.tag_raise(self.text_item)
        self.txt_window.focus_force()
        
    def get_img_list(self):
        
        file_list_fn = os.path.join(self.source_dir,'.img_files_list')
        
        #If an image list file exists, load from file, else inspect directories
        #for image files
        if os.path.isfile(file_list_fn):
            print('reading file list')
            self.read_file_list()
            #Indicate that the existing file list was read from file
            self.img_list_updated = False
            print("{} files in image list".format(len(self.img_list)))
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
                txt = '{} dirs checked ({} dirs remaining).  Found {} images'.format(ctr,len(dirs_to_process),len(self.img_list))
                self.show_text_window('Searching for images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
                
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
            
            self.show_text_window('COMPLETED\nSearching for images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
            
            self.img_list.sort()
            
            
        #Init folder position variables
        self.get_folder_pos_and_size()


        
        if isinstance(self.current_image,type(None)):
            # self.init_first_image()
            self.current_image = IO.IMAGE(self.get_img_path(),self.img_window_width,self.img_window_height,self.fit_to_canvas)
            self.open_img_window(self.current_image.sequence)
        else:
            self.load_new_image()
            self.init_image()
    
    def remove_empty_dirs(self,dummy = None):
        #Init the number of dirs and removed dirs counters
        self.num_dirs = 1
        self.num_removed = 0
        #Call recursive rmdirs function on source dirs
        self.rmdirs(self.source_dir)
        self.show_text_window('COMPLETED\nRemoving empty directories from:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,self.display_txt))
       
    def rmdirs(self,cur_dir):  
        #Display progress
        self.display_txt = '{} checked, {} removed'.format(self.num_dirs,self.num_removed)
        self.show_text_window('Removing empty directories from:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,self.display_txt))
       
        #List the items in the directory print
        dir_list = os.listdir(cur_dir)
        #Store the files and subdirectories in separate lists
        new_files = [file for file in dir_list if os.path.isfile(os.path.join(cur_dir,file))]
        new_dirs = [os.path.join(cur_dir,item) for item in dir_list if os.path.isdir(os.path.join(cur_dir,item))]
        #For each subdirectory, increment the counter and call the rmdirs function
        for new_dir in new_dirs:
            self.num_dirs += 1
            self.rmdirs(new_dir)
        
        #After checking all subdirectories, re-list the directory and 
        #list any remaining directories
        dir_list = os.listdir(cur_dir)
        non_empty_dirs = [item for item in dir_list if os.path.isdir(os.path.join(cur_dir,item))]
        #If there are no files files and no remaining subdirectories, remove
        #the directory and increment the counter
        if (len(new_files)+len(non_empty_dirs)) == 0:
            os.rmdir(cur_dir)
            self.num_removed += 1
            
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
            
        #Set the image index to zero, get the image list from the source dir
        #and load image 0
        self.cur_img = 0        
        self.get_img_list()
        
    def show_menu_window(self,dummy=None):
        #Init the menu window 
        self.menu_window = tk.Toplevel(self.parent)
        #Add a canvas
        canvas = tk.Canvas(self.menu_window,height=1000,width=500)
        canvas.pack()
        #Get the text for the menu
        menu_txt = self.gen_menutext()
        #Create a text item of the menu text
        text_item = canvas.create_text(
            25,
            25,
            fill='black',
            font='times 10 bold',
            text=menu_txt,tag='menu_txt',
            anchor=tk.NW)
        #Make a bounding box around the text to determine required window size
        bbox = canvas.bbox(text_item)
        dim = (bbox[2]-bbox[0]+100,bbox[3]-bbox[1]+100)
        #Set the window geometry to the dimensions of the bounding box plus 
        #some padding and move the text item to the center of the window
        locn = [int(self.screen_width/2-dim[0]/2),int(self.screen_height/2-dim[1]/2)]
        self.menu_window.geometry(f'{dim[0]}x{dim[1]}+{locn[0]}+{locn[1]}')
        canvas.move(text_item,25,25)
        canvas.update()
        canvas.tag_raise(text_item)
        
    def set_keybindings(self,window):
        #Set keybindings for the program controls
        window.bind('<F1>', self.reload_img_list)          #Check source for images
        window.bind('<F2>', self.remove_empty_dirs)        #remove empty directories
        window.bind('<F3>', self.check_file_hashes)        #check source dir for duplicate hashes
        window.bind('<F4>', self.toggle_review_dup_hashes) #Toggle reviewing lists of images with dup hashes
        window.bind('<F5>', self.ask_delete_dup_hashes)    #Delete all duplicate hashes (ask user first)
        window.bind('<F6>', self.ask_empty_current_folder) #Delete all files in current directory (ask user first)
        window.bind('<F7>', self.remove_missing)           #Remove missing files until non-missing file is found
        window.bind('<F8>', self.remove_all_missing)       #Check image list for missing files
        window.bind('<F9>', self.toggle_info_text)         #Toggle info displayed on image
        window.bind('<F10>', self.show_input_window)       #Goto specific image number
        window.bind('<F11>', self.toggle_fs)               #toggle full screen
        window.bind("<F12>",self.toggle_rand_order)        #Display images in random order
        window.bind('<Next>', self.next_dup_hash)          #Next list of dup hashes
        window.bind('<Prior>', self.prev_dup_hash)         #Previous list of dup hashes
        window.bind('<Right>', self.load_next_img)         #Load the next image
        window.bind('<Left>', self.load_prev_img)          #Load the previous
        window.bind('-', self.increase_delay)              #Slow GIF animation
        window.bind('=', self.decrease_delay)              #Speed GIF animation
        window.bind('<Down>', self.rotate_ccw)             #Rotate the image clockwise
        window.bind('<Up>', self.rotate_cw)                #Rotate the image counterclockwise
        window.bind('<Control-Down>', self.contrast_dn)    #Decrease contrast
        window.bind('<Control-Up>', self.contrast_up)      #Increase contrast
        window.bind('<Alt-Down>', self.brightness_dn)      #Decrease brightness
        window.bind('<Alt-Up>', self.brightness_up)        #Increase brightness
        window.bind('<Tab>', self.toggle_fit_to_canvas)    #zoom/shrink to canvas
        window.bind("<MouseWheel>",self.zoomer)            #mouse wheel to increase/decrease zoom
        window.bind("<Control-z>",self.undo)               #Undo file move
        window.bind("<Control-r>",self.reload_img)         #Reset zoom, animation speed etc. to defaults
        window.bind("<Control-K>",self.toggle_keep_mode)   #Sort images relative to the original containing folder
        window.bind("<Control-q>",self.quit_app)           #Quit app
        window.bind("<Escape>",self.quit_app)              #Quit app
        window.bind('<Alt-m>',self.toggle_menu)            #Display controls menu
        window.bind('<KeyRelease>',self.keyup)             #Monitor key presses (check for file moves)
        window.bind('1',self.set_keep_new_flag)            #dup processing: keep source_dir file
        window.bind('2',self.set_keep_existing_flag)       #dup processing: keep dest_dir file
        window.bind('3',self.set_keep_both_flag)           #dup processing: keep both files
        window.bind('<End>',self.close_img_compare_window) #Stop comparing dups & cancel move
        window.bind('<Return>',self.close_txt_window)      #Close text window if one is open
        window.bind('<Motion>',self.motion)                #Track mouse motion
        window.bind('<ButtonPress-1>',self.move_from)      #Store location of start of pan  
        window.bind('<ButtonRelease-1>',self.move_to)      #Store location of end of pan 
        window.bind('<Shift-Right>',self.next_folder)      #Skip to the next folder
        window.bind('<Shift-Left>',self.prev_folder)       #Skip to the next folder
    
    def rotate_cw(self,dummy=None):
        self.current_image.rotate(90)
        self.init_image()

    def rotate_ccw(self,dummy=None):
        self.current_image.rotate(-90)
        self.init_image()
    
    def contrast_dn(self,dummy=None):
        #Update contrast and show image
        self.current_image.adjust_contrast(-1)
        self.init_image()
        
    def contrast_up(self,dummy=None):
        #Update contrast and show image
        self.current_image.adjust_contrast(1)
        self.init_image()
    
    def brightness_dn(self,dummy=None):
        #Update brightness and show image
        self.current_image.adjust_brightness(-1)
        self.init_image()
        
    def brightness_up(self,dummy=None):
        #Update brightness and show image
        self.current_image.adjust_brightness(+1)
        self.init_image()
    
    def toggle_keep_mode(self,dummy=None):
        self.keep_mode = bool(self.keep_mode*-1+1)
        
    def toggle_info_text(self,dummy=None):
        self.img_info_display = (self.img_info_display+1)%4

    def next_folder(self,dummy=None):
        self.get_folder_pos_and_size()
        
        #Update the index
        self.cur_img += self.num_files_in_folder-self.folder_position
        #Check for valid image index
        if self.cur_img >= len(self.img_list):
            self.cur_img = 0
        
        self.get_folder_pos_and_size()
        
        #Set flag so revised image list will be exported on exit & load the next image
        self.img_list_updated = True
        self.close_txt_window()
        self.load_new_image()

    def prev_folder(self,dummy=None):
        self.get_folder_pos_and_size()
        
        #Update the index
        self.cur_img -= (self.folder_position+1)
        #Check for valid image index
        if self.cur_img < 0:
            self.cur_img = len(self.img_list)-1
        
        self.get_folder_pos_and_size()
        
        #Set flag so revised image list will be exported on exit & load the next image
        self.img_list_updated = True
        self.close_txt_window()
        self.load_new_image()
        
    def ask_delete_dup_hashes(self,dummy=None):
        self.show_text_window('WARNING:\nAbout to delete images with duplicate hashes\n\nCANNOT BE UNDONE\n\nEnter: Cancel\nAlt+Shift+p: Continue',delete_dups='hashes')
        
    def delete_dup_hashes(self,dummy=None):
        if self.reviewing_dup_hashes:
            self.toggle_review_dup_hashes()
        
        move_ctr = 0
        start_time = time.time()
        num_items = len(self.dup_hashes)
        self.close_image(self.current_image)
        for ctr,key in enumerate(self.dup_hashes):
            #Calculate the time remaining to completion & update display
            time_remaining = self.calc_time_remaining(start_time,ctr,num_items)
            txt = 'Processed {}/{} ({} remaining)'.format(ctr,num_items,time_remaining)
            self.show_text_window('Moving duplicate image hashes to temp trash\n ***TEMP TRASH WILL BE EMPTIED ON EXIT***\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
            
            #Extract the list of duplicate images for the current hash
            dup_list = self.hash_dict[key]
            for file in dup_list[1:]:
                #check that file exists
                if os.path.isfile(file):
                    #Update the move counter
                    move_ctr += 1
                    #Generate a new filename
                    fn = os.path.split(file)[1]
                    trash_files = os.listdir(self.trash_dest)
                    i=1
                    while fn in trash_files:
                        #If filename exists in destination, keep incrementing
                        #the counter and generating a new filename until an open
                        #filename is found
                        name = fn.split('.')[:-1]
                        name = '.'.join(name)
                        ext = fn.split('.')[-1]
                        fn = '{}({}).{}'.format(name,i,ext)
                        i += 1
                        
                    #Move the file to the temp trash directory
                    dest_file = os.path.join(self.trash_dest,fn)
                    move(file,dest_file)
                #Remove the image from the image list
                self.img_list.remove(file)
        
        #Set the hash dict to none and move the hash pickle
        self.hash_dict = None
        self.dup_hashes = None
        move(os.path.join(self.source_dir,'.pickled_hashes'),os.path.join(self.trash_dest,'.pickled_hashes'))
        txt = '{} images moved'.format(move_ctr)
        self.show_text_window('COMPLETD:\nMoving duplicate image hashes to temp trash\n ***WILL BE EMPTIED ON EXIT***\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
        self.reload_img()
                
    def ask_empty_current_folder(self,dummy=None):
        #Find the diretory of the current file & how many files are in it
        file = self.img_list[self.cur_img]
        cur_dir = os.path.split(file)[0]
        files = os.listdir(cur_dir)
        files = [file for file in files if os.path.isfile(os.path.join(cur_dir,file))]
        #Warn user that delete is permanent
        self.show_text_window('WARNING:\nAbout to delete all {} images in\n\n     {}\n\nCANNOT BE UNDONE\n\nEnter: Cancel\nAlt+Shift+p: Continue'.format(len(files),cur_dir),delete_dups='empty_dir')
                
    def empty_current_folder(self,dummy=None):
        self.move_events = []
        files = self.get_folder_pos_and_size()
        
        
        for file in files:
            # #If the file is in the image list, remove it
            # if file in self.img_list:
            os.remove(file)
            self.processed_images += 1
            self.img_list.remove(file)
        
        #Update the index
        self.cur_img -= self.folder_position
        #Check for valid image index
        if self.cur_img >= len(self.img_list):
            self.cur_img = 0
            
        files = self.get_folder_pos_and_size()
        
        #Set flag so revised image list will be exported on exit & load the next image
        self.img_list_updated = True
        self.close_txt_window()
        self.load_new_image()
        
    def get_folder_pos_and_size(self,dummy=None):
        #Find the directory of the current image & all the images in that dir
        file = self.img_list[self.cur_img]
        cur_dir = os.path.split(file)[0]
        if os.path.isdir(cur_dir):
            files = os.listdir(cur_dir)
        else:
            self.folder_position = -100000
            self.num_files_in_folder = 0
            return []
        
        files = [os.path.join(cur_dir,file) for file in files if os.path.isfile(os.path.join(cur_dir,file))]
        #keep only files remove list that are in the image list
        files = [file for file in files if file in self.img_list]
        files.sort()
        #Find the position of the currently viewed image within the current folder
        #for indexing purposes
        self.folder_position = files.index(file)
        self.num_files_in_folder = len(files)
        
        return files
        
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
        self.close_image(self.current_image)
        for ctr,file in enumerate(self.img_list):
            time_remaining = self.calc_time_remaining(start_time,ctr,num_items)
            #Build the text display string and show the text window to update
            #the user
            txt = 'Checked {}/{} ({} remaining)'.format(ctr,len(self.img_list),time_remaining)
            self.show_text_window('Checking file hashes for images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
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
            
        self.cur_img = min(len(self.img_list)-1,self.cur_img)
        
        #Convert the duplicate hash set to a list and update the text window
        self.dup_hashes = list(self.dup_hashes)
        self.dup_hashes.sort()
        txt = 'Checked {} images, found {} duplicate hashes'.format(len(self.img_list),len(self.dup_hashes))
        self.show_text_window('COMPLETED:\nChecking file hashes for images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
        self.reload_img()
        
    def remove_missing(self,dummy=None):
        missing_files = []
        num_items = len(self.img_list)
        self.close_image(self.current_image)
        ctr = 0
        file = self.img_list[self.cur_img]
        #Check files until a non-missing file is found
        while not os.path.isfile(file):
            self.img_list_updated = True
            #Add the file to the list of the missing
            missing_files.append(file)
            ctr +=1
            file = self.img_list[self.cur_img+ctr]
            #Build the text display string and show the text window to update
            #the user
            txt = 'Checked {}/{})'.format(ctr,len(self.img_list))
            self.show_text_window('Checking file list for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
            #Calculate the hash of the current file
            
        #Remove the missing ifles
        for file in missing_files:
            self.img_list.remove(file)
            
        #Update the image index
        self.cur_img = min(len(self.img_list)-1,self.cur_img)
        
        txt = 'Found {} missing files ({} remaining)'.format(ctr,len(self.img_list))
        self.show_text_window('COMPLETED:\nChecking for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
        #Get the number of items in the current folder & the position in the folder
        self.get_folder_pos_and_size()
        self.reload_img()
                 
    def remove_all_missing(self,dummy=None):
        
        dest_file = None
        if self.reviewing_dup_hashes:
            self.remove_all_missing_hashes()
            self.next_dup_hash("no-increment")
        else:
            self.remove_all_missing_files()
            
    def remove_all_missing_hashes(self): #Record the start time
        start_time = time.time()
        missing_files = []
        num_items = len(self.dup_hashes)
        self.close_image(self.current_image)
                
        hashes_removed = 0
        hsh_list = cp.deepcopy(self.dup_hashes)
        for ctr,hsh in enumerate(hsh_list):
            time_remaining = self.calc_time_remaining(start_time,ctr,num_items)
            #Build the text display string and show the text window to update
            #the user
            txt = 'Checked dup hashes of {}/{} ({} remaining)'.format(ctr,len(hsh_list),time_remaining)
            self.show_text_window('Checking file list for missing images in:\n     {}\n\n{}\n\n'.format(self.source_dir,txt))
            self.img_list = cp.deepcopy(self.hash_dict[hsh])
            self.img_list = self.hash_dict[hsh]
            for file in self.img_list:
                if not os.path.isfile(file):
                    self.img_list_updated = True
                    self.img_list.remove(file)                
                    
                    #remove the current image from the backed-up global image list 
                    self.img_list_bkup.remove(file)
                    #Confirm that the current image value doesn't exceed the max
                    #index
                    self.cur_img_bkup %= len(self.img_list_bkup)
                    missing_files.append(file)
        
            
            if len(self.img_list) <= 1:
                #Remove the current hash from the list of duplicate hashes
                #and go to the next duplicate hash
                self.dup_hashes.remove(hsh)
                hashes_removed += 1
        
        self.remove_ctr +=1
            
        txt = 'Checked {} duplicate hashes, found {} that are no longer dups ({} duplicate hashes remaining)'.format(num_items,hashes_removed,len(self.dup_hashes))
        self.show_text_window('COMPLETED:\nChecking for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
        
    def remove_all_missing_files(self):
        #Record the start time
        start_time = time.time()
        missing_files = []
        num_items = len(self.img_list)
        self.close_image(self.current_image)
        for ctr,file in enumerate(self.img_list):
            time_remaining = self.calc_time_remaining(start_time,ctr,num_items)
            #Build the text display string and show the text window to update
            #the user
            txt = 'Checked {}/{} ({} remaining)'.format(ctr,len(self.img_list),time_remaining)
            self.show_text_window('Checking file list for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
            #Check if the file is missing or not
            if not os.path.isfile(file):
                missing_files.append(file)
                self.img_list_updated = True
           
        #Remove the missing files
        for file in missing_files:
            self.img_list.remove(file)
            
        #Update the image index
        self.cur_img = min(len(self.img_list)-1,self.cur_img)
        
        txt = 'Checked {} entries, found {} missing files ({} remaining)'.format(num_items,len(missing_files),len(self.img_list))
        self.show_text_window('COMPLETED:\nChecking for missing images in:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,txt))
        #Get the number of items in the current folder & the position in the folder
        self.get_folder_pos_and_size()
        self.reload_img()
        
    def toggle_review_dup_hashes(self,dummy=None):
        if self.reviewing_dup_hashes:
            #Toggle the reviewing duplicate hash flag
            self.reviewing_dup_hashes = False
            #Restore the global image list and index from memory and load the image
            self.img_list = self.img_list_bkup
            self.cur_img = self.cur_img_bkup
            self.load_new_image()
        else:
            #If a hash dict has been generated
            if self.hash_dict != None:
                #Toggle the reviewing duplicate hash flag
                self.reviewing_dup_hashes = True
                #Back up the global image list and index
                self.img_list_bkup = self.img_list
                self.cur_img_bkup = self.cur_img
                #Set the index to the first duplicate hash
                self.hash_ctr = 0
                #Load the list of duplicate images and index to the first one
                self.img_list = self.hash_dict[self.dup_hashes[self.hash_ctr]]
                self.cur_img = 0
                #Load the image
                self.load_new_image()
                
    def next_dup_hash(self,increment=True):
        if self.reviewing_dup_hashes:
            if len(self.dup_hashes) == 0:
                #No duplicate hashes remain, stop reviewing hashes
                self.toggle_review_dup_hashes()
            else:
                if increment == "no-increment":
                    #The current hash has been removed, ensure the hash index
                    #isn't greater than the max dup hash index but don't 
                    #increment
                    self.hash_ctr = (self.hash_ctr)%len(self.dup_hashes)
                else:
                    #Increment the hash counter & check it's not greater than
                    #the max index
                    self.hash_ctr = (self.hash_ctr+1)%len(self.dup_hashes)
                #Load the new duplicate hash image list, index to the first
                #image, and load it
                self.img_list = self.hash_dict[self.dup_hashes[self.hash_ctr]]
                self.cur_img = 0
                self.load_new_image()
            
    def prev_dup_hash(self,dummy=None):
        if self.reviewing_dup_hashes:
            #Decrement the hash counter & make sure it's valid
            self.hash_ctr -= 1
            if self.hash_ctr<0:
                self.hash_ctr = len(self.dup_hashes)-1
            #Load the new duplicate hash image list, index to the first
            #image, and load it
            self.img_list = self.hash_dict[self.dup_hashes[self.hash_ctr]]
            self.cur_img = 0
            self.load_new_image()
            
    def set_keep_new_flag(self,dummy=None):
        #Set flag to indicate that the user wants to keep the file from the 
        #source directory
        if self.processing_duplicates:
            self.keep_new = True
            self.move_file()
        
    def set_keep_existing_flag(self,dummy=None):
        #Set flag to indicate that the user wants to keep the file from the 
        #target directory
        if self.processing_duplicates:
            self.keep_existing = True
            self.move_file()
        
    def set_keep_both_flag(self,dummy=None):
        #Set flag to indicate that the user wants to keep both duplicate files
        if self.processing_duplicates:
            self.keep_both = True
            self.move_file()
        
    def toggle_rand_order(self,dummy=None):
        #display the images in the image list sequentially or in random order
        if self.rand_order:
            self.rand_order = False
            #Clear the previously-viewed image history
            self.previous_images = []
        else:
            self.rand_order = True
        
    def motion(self,event):
        #Track motion of the mouse
        self.mouse_x,self.mouse_y = event.x,event.y
        if self.panning_image:
            dx = event.x-self.start_x
            self.start_x = event.x
            dy = event.y-self.start_y
            self.start_y = event.y
            self.current_image.update_bbox_pan(dx,dy)
            self.init_image()
        
    def move_from(self,event):
        #Store starting point of image pan
        self.start_x = event.x
        self.start_y = event.y
        self.panning_image = True
        
    def move_to(self,event):
        self.panning_image = False
        
    def get_img_path(self):
        #If there are no images in the list, return None, otherwise return the
        #absolute path of the current image
        if len(self.img_list) == 0:
            return None
        else:
            return self.img_list[self.cur_img]
        
    def keyup(self,event):
        #Function to track key releases for moving files
        #Store the key that was released
        key = event.char
        
        valid_move = False
        
        if self.keep_mode:
            if key in self.keep_mode_move_dict.keys():
                valid_move = True
                img_root = os.path.split(self.img_list[self.cur_img])[0]
                self.dest_dir = os.path.join(img_root,self.keep_mode_move_dict[key])
                
        elif (key in self.move_dict.keys()) and not self.processing_duplicates:
            valid_move = True
            #Reload the image to reset zoom
            self.reload_img()
            #Store the destination directory based on the key pressed
            # self.dest_dir = self.move_dict[key]
            self.dest_dir = os.path.join(self.dest_root,self.move_dict[key])
            
        if valid_move:
            #If the destination directory doesn't exist, create it
            if not os.path.isdir(self.dest_dir):
                os.makedirs(self.dest_dir)
            #Move the file
            self.move_file()
        
    def quit_app(self,dummy=None):
        
        #Calculate working statistics and print to console
        end_time = time.time()
        elapsed_seconds = end_time-self.start_time
        hrs,minutes,seconds = self.sec_to_hr_min_sec(elapsed_seconds)
        time_remaining = self.calc_time_remaining(self.start_time,self.processed_images,len(self.img_list))
        
        print('\n\nProcessed {} images; {} remaining.'.format(self.processed_images,len(self.img_list)))
        print('          Working time: {}hr {}min {}sec'.format(hrs,str(minutes).zfill(2),str(seconds).zfill(2)))
        print('   Est. time remaining: {}\n\n'.format(time_remaining))
        
        if self.displaying_images:
            #Close the image window
            self.img_window.destroy()
            #Close the compare window if one exists
            self.close_img_compare_window()
            
        #If reviewing dup hashes, toggle that off to avoid overwriting the saved
        #image list
        if self.reviewing_dup_hashes:
            self.toggle_review_dup_hashes()
        #Write the file list to file if the image list has been updated
        #from the directory or if files have been moved
        if (len(self.move_events)>0) or self.img_list_updated:
            self.write_file_list()
        #If the temp trash directory exists, empty it and remove the temp 
        #directory
        if os.path.isdir(self.trash_dest):
            files = [os.path.join(self.trash_dest,file) for file in os.listdir(self.trash_dest)]
            for file in files:
                os.remove(file)
            os.rmdir(self.trash_dest)
                
        #If a hash dict has been generated, save it to disk
        if self.hash_dict != None:
            with open(os.path.join(self.source_dir,'.pickled_hashes'), 'wb') as file:
                pkl.dump(self.hash_dict,file)
                pkl.dump(self.dup_hashes,file)
                
        #Destroy the application
        self.parent.destroy()
        
    def toggle_menu(self,dummy=None):
        if self.show_menu:
            self.show_menu = False
            self.menu_window.destroy()
        else:
            self.show_menu = True
            self.show_menu_window()
            
    def gen_menutext(self):
            if self.processing_duplicates:
                #Menu controls when processing dup image files
                menu_txt = ''
                menu_txt += 'Esc ==> Quit\n'
                menu_txt += 'Alt+M ==> Toggle this menu\n'
                menu_txt += 'End ==> cancel move\n'
                menu_txt += '1 ==> keep new image and delete old image\n'
                menu_txt += '2 ==> keep old image and delete new image\n'
                menu_txt += '3 ==> rename new image and keep both\n'
            else:
                #Menu during typical operation
                #program control settings
                menu_txt = ''
                menu_txt += 'Esc ==> Quit\n'
                menu_txt += 'L/R arrows ==> prev/next image (shift: prev/next folder)\n'
                menu_txt += '=/- arrows ==> +/- GIF animation speed\n'
                menu_txt += 'U/D arrows ==> rotate image\n'
                menu_txt += 'Ctrl/Alt U/D arrows ==> increase/decrease brightness/contrast\n'
                menu_txt += 'Page U/D ==> prev/next set of duplicate hashes\n'
                menu_txt += 'TAB ==> toggle fit to canvas\n'
                menu_txt += 'Mouse Wheel ==> increase/decrease zoom\n'
                menu_txt += 'Ctrl+Shift+k ==> toggle relative store mode\n'
                menu_txt += 'Alt+m ==> Toggle this menu\n'
                menu_txt += 'Ctrl+q ==> quit\n'
                menu_txt += 'Ctrl+r ==> reload image\n'
                menu_txt += 'Ctrl+z ==> undo file move\n'
                menu_txt += 'F1  ==> reload img list from directory\n'
                menu_txt += 'F2  ==> Recursively remove empty dirs from source\n'
                menu_txt += 'F3  ==> Check for duplicate image hashes\n'
                menu_txt += 'F4  ==> Review duplicate image hashes\n'
                menu_txt += 'F5  ==> Delete all images with hashes\n'
                menu_txt += 'F6  ==> Delete all imgs in current directory\n'
                menu_txt += 'F7  ==> Check image list for missing images until non-missing is found\n'
                menu_txt += 'F8  ==> Check image list for missing images\n'
                menu_txt += 'F9  ==> Toggle image info displayed\n'
                menu_txt += 'F10 ==> Goto specific image number\n'
                menu_txt += 'F11 ==> toggle full screen\n'
                menu_txt += 'F12 ==> toggle random display order\n'
                #Build list of destination folders and corresponding keys
                
                if self.keep_mode:
                    move_dict = self.keep_mode_move_dict
                    menu_txt += '\nPress key to move to subdirectory image\'s original directory\n'.format(settings.dest_root)
                else:
                    move_dict = self.move_dict
                    #Build list of destination folders and corresponding keys
                    menu_txt += '\nPress key to move to subdirectory in {}\n'.format(settings.dest_root)
                
                for key in move_dict.keys():
                    # menu_txt += '   {} ==> {}\n'.format(key,os.path.split(settings.move_dict[key])[1])
                    menu_txt += '   {} ==> {}\n'.format(key,move_dict[key])
            
            return menu_txt
            
    def show_img_compare_window(self,files=None):
        #Open a window to compare duplicate images
        #If there's an existing compare window, close it
        if self.has_compare_window:
            self.img_compare_window.destroy()
        #Flag to indicate that compare window exists
        self.has_compare_window = True
        #If there are exactly two files, compare them
        if len(files)==2:
            new_file,existing_file = files
            self.open_compare_window(new_file,existing_file)
        else:
            print('Expected 2 files, got {}'.format(len(filest = ())))
        
    def close_img_compare_window(self,dummy=None):
        #User has selected a duplicate resolution, stop comparing images and
        #reset flags to prep for next duplicate
        if self.has_compare_window:
            self.new_file.close()
            self.existing_file.close()
            self.img_compare_window.destroy()
        self.has_compare_window = False
        self.processing_duplicates = False
        self.keep_both = False
        self.keep_existing = False
        self.keep_new = False
        
    def move_file(self):
        #Store the current file in local variable
        file = self.img_list[self.cur_img]
        
        if self.img_missing:
            self.img_list.remove(file)
            self.cur_img %= len(self.img_list)
            self.init_image()
            return
        
        #Split off the filename
        orig_fn = os.path.split(self.img_list[self.cur_img])[1]
        #Split the filename into name and extension
        fn_parts = orig_fn.split('.')
        
        #List the files in the destination directory to check for dups
        dest_files = [file for file in os.listdir(self.dest_dir) if os.path.isfile(os.path.join(self.dest_dir,file))]
        
        #If not working on processing a duplicate, set the destination filename
        #to the original filename and store in self
        if not self.processing_duplicates:
            self.dest_fn = orig_fn
        
        #Check of destination file name exists in destination directory 
        #or if working on processing a duplicate
        if (self.dest_fn in dest_files) or self.processing_duplicates:
            #Set the processing duplicates flag
            self.processing_duplicates = True
            #If the user has NOT made a decision on which duplicate to keep
            if not any([self.keep_both,self.keep_existing,self.keep_new]):
                #Initialize the filename counter
                self.move_ctr = 1
                #Open a compare window and display both images
                self.show_img_compare_window((file,os.path.join(self.dest_dir,os.path.join(self.dest_dir,self.dest_fn))))
            else:
                #User has elected to keep both files
                if self.keep_both:
                    #Reset the flag to keep both
                    self.keep_both = False
                    #Generate an alternate filename from the original filename
                    #and extension and the filename counter
                    self.dest_fn = '{}({}).{}'.format(fn_parts[0],self.move_ctr,fn_parts[1])
                    if self.dest_fn in dest_files:
                        #If the new file name exists, increment the move counter
                        #and display the new duplicate pair
                        self.move_ctr+=1
                        self.show_img_compare_window((file,os.path.join(self.dest_dir,os.path.join(self.dest_dir,self.dest_fn))))
                    else:
                        #If the new file name does not exist in the dest. dir
                        #close the compare window
                        self.close_img_compare_window()
                        #Close the PIL image file
                        self.close_image(self.current_image)
                        #Generate the absolute path to the destination
                        dest_file = os.path.join(self.dest_dir,self.dest_fn)
                        #Store the move in the move history
                        moved_files = [(file,dest_file)]
                        #Move the file to the destination and update the image
                        #list
                        move(file,dest_file)
                        self.update_img_list(moved_files,file,dest_file)
                        
                #User has elected to keep the file in the destination directory        
                elif self.keep_existing:
                    #Close the compare window
                    self.close_img_compare_window()
                    #Close the PIL image file
                    self.close_image(self.current_image)
                    
                    #Move the file in the source directory to the temporary
                    #trash direcetory
                    trash_dest_fn = os.path.join(self.trash_dest,orig_fn)
                    #Move the file
                    move(file,trash_dest_fn)
                    #Store the move in the move history & update the image
                    #list
                    moved_files = [(file,trash_dest_fn)]
                    
                    self.update_img_list(moved_files,file,trash_dest_fn)
                
                #User has elected to keep the file in the source directory
                elif self.keep_new:
                    #Close the compare window
                    self.close_img_compare_window()
                    #Close the PIL image file
                    self.close_image(self.current_image)
                    
                    #Move the file in the destination directory to the temporary
                    #trash direcetory
                    trash_dest_fn = os.path.join(self.trash_dest,self.dest_fn)
                    existing_file = os.path.join(self.dest_dir,self.dest_fn)
                    #Store the move in the move history & update the image
                    #list
                    moved_files = [(existing_file,trash_dest_fn)]
                    move(existing_file,trash_dest_fn)
                    
                    #Move the file in the source directory to the destination
                    #directory, store the move history, & update the image
                    #list
                    dest_file = os.path.join(self.dest_dir,self.dest_fn)
                    moved_files.append((file,dest_file))
                    move(file,dest_file)
                    
                    self.update_img_list(moved_files,file,dest_file)
        else:
            #Move the file in the source directory to the destination
            #directory, store the move history, & update the image
            #list
            #Close the PIL image file
            self.close_image(self.current_image)
            dest_file = os.path.join(self.dest_dir,self.dest_fn)
            moved_files = [(file,dest_file)]
                      
            move(file,dest_file)
            self.update_img_list(moved_files,file,dest_file)
            
    def update_img_list(self,moved_files,file,dest_file):
        self.processed_images += 1
        if settings.max_allowed_undo != 0:
            
            if self.reviewing_dup_hashes:
                hash_dict_change = (self.dup_hashes[self.hash_ctr],file)
            else:
                hash_dict_change = None
            
            #Save the current state
            self.move_events.append((
                moved_files,
                cp.deepcopy(self.cur_img),
                cp.deepcopy(self.img_list),
                cp.deepcopy(self.cur_img_bkup),
                cp.deepcopy(self.img_list_bkup),
                hash_dict_change,
                cp.deepcopy(self.hash_ctr),
                cp.deepcopy(self.reviewing_dup_hashes)))
            
            #Trim old move events to prevent excessive memory usage
            if settings.max_allowed_undo != 'all':
                num_to_keep = min(settings.max_allowed_undo,len(self.move_events))
                self.move_events = self.move_events[len(self.move_events)-num_to_keep:]
            
        #Remove the moved file from the image list
        self.img_list.remove(file)
        if self.dest_root == self.source_dir:
            self.img_list.append(dest_file)
            self.img_list.sort()
        if self.rand_order:
            self.cur_img = random.randint(0,len(self.img_list)-1)
        #If the last image was removed, set the image index to the new last image
        if self.cur_img >= len(self.img_list):
            self.cur_img = len(self.img_list)-1
         
        if self.reviewing_dup_hashes:
            self.update_dup_hashes(file,dest_file)
        else:
            files = self.get_folder_pos_and_size()
            self.load_new_image()
            
    def update_dup_hashes(self,file,dest_file,removing_missing = False):
        #remove the current image from the backed-up global image list 
        self.img_list_bkup.remove(file)
        #Confirm that the current image value doesn't exceed the max
        #index
        self.cur_img_bkup %= len(self.img_list_bkup)
        if self.dest_root == self.source_dir:
            #If source&dest are the same, add the moved file path
            #to the backed up global image list
            self.img_list_bkup.append(dest_file)
            self.img_list_bkup.sort()
        if len(self.img_list) == 0:
            #Remove the current hash from the list of duplicate hashes
            #and go to the next duplicate hash
            self.dup_hashes.remove(self.dup_hashes[self.hash_ctr])
            self.next_dup_hash("no-increment")
        
    def undo(self,dummy=None):
        #Pop the previous state
        moved_files,self.cur_img,self.img_list,self.cur_img_bkup,self.img_list_bkup,hash_dict_change,self.hash_ctr,self.reviewing_dup_hashes = self.move_events.pop()
        
        if hash_dict_change != None:
            #If there were changes to the hash dict, restore dict to previous state
            key,file = hash_dict_change
            self.hash_dict[key].append(file)
            self.hash_dict[key].sort()
            if key not in self.dup_hashes:
                self.dup_hashes.append(key)
                self.dup_hashes.sort()
        
        #Undo the move(s)
        while len(moved_files)>0:
            moved_from,moved_to = moved_files.pop()
            move(moved_to,moved_from)
        
        self.processed_images -= 1
        self.load_new_image()
        
    def zoomer(self,event):
        if self.current_image.update_zoom(event,self.mouse_x,self.mouse_y):
            #Display the zoomed image
            self.init_image()
        
    def toggle_fs(self,dummy=None):
        #Toggle full screen mode
        if self.full_screen:
            #Set fullscreen to false and set window dimensions to default
            self.full_screen = False
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        else:
            #Set fullscreen to True and set window dimensions to screen dims
            self.full_screen = True
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        
        self.current_image.img_window_width = self.img_window_width
        self.current_image.img_window_height = self.img_window_height
        self.current_image.reset_zoomcycle()
        self.current_image.gen_sequence()
        self.init_image()
        
    def toggle_fit_to_canvas(self,dummy=None):
        #Toggle zoom/shrink to fit canvas
        if self.fit_to_canvas:
            self.fit_to_canvas = False
            self.current_image.fit_to_canvas = False
        else:
            self.fit_to_canvas = True
            self.current_image.fit_to_canvas = True
        self.current_image.reset_zoomcycle()
        self.current_image.gen_sequence()
        self.init_image()
            
    def increase_delay(self,dummy=None):
        #Increase the delay between gif frames (slow the animation)
        self.delay += 5
        
    def decrease_delay(self,dummy=None):
        #Decrease the delay between gif frames (speed up the animation)
        self.delay -= 5
        if self.delay <= 0:
            self.delay = 5
        
    def load_next_img(self,dummy=None):
        #Move to the next image
        #If there is a duplicate compare window open, close it and reset the 
        #compare flags
        self.close_img_compare_window()
        #If the display is in random order, generate a random step size and add
        #the current image to the view history list
        if self.rand_order:
            step = random.randint(0,len(self.img_list)-2)
            self.previous_images.append(self.cur_img)
        else:
            step = 1
        #Increment the current image index and mod by the number of items
        #in the image list
        self.cur_img = (self.cur_img+step) % len(self.img_list)
        
        #Update the img number relative to the number of images in the directory
        self.update_folder_position(1)
        
        self.load_new_image()
        
    def update_folder_position(self,increment):
        #Increment the position
        self.folder_position += increment
        #If the new position doesn't make sense, recheck the actual position and size
        if (self.folder_position >= self.num_files_in_folder) or (self.folder_position<0):
            self.get_folder_pos_and_size()
        
    def load_prev_img(self,dummy=None):
        #Move to the next image
        #If there is a duplicate compare window open, close it and reset the 
        #compare flags
        self.close_img_compare_window()
        #If there are images in the image history list
        if len(self.previous_images)>0:
            #Pop the previous image from the history list
            cur_img = self.previous_images.pop()
            #If the image from the history is the same as the current image
            #pop another image from the history list
            if cur_img == self.cur_img:
                self.cur_img = self.previous_images.pop()
            else:
                self.cur_img = cur_img
        else:
            #Decrement the current image index.  If the resulting index is less 
            #than zero, set the index to the last image.
            self.cur_img -= 1
            if self.cur_img < 0:
                self.cur_img = len(self.img_list)-1
                
        self.update_folder_position(-1)
        self.load_new_image()

    def load_new_image(self):
        #Close the PIL open image file, reset the zoom cycle and initialize
        #the next image
        if not isinstance(self.current_image,type(None)):
            self.close_image(self.current_image)
        self.current_image = IO.IMAGE(self.get_img_path(),self.img_window_width,self.img_window_height,self.fit_to_canvas)
        self.init_image()
        
    def close_image(self, image_obj):
        #If an image file was successfully loaded, close it
        if image_obj.has_open_image:
            self.img_window.destroy()
            image_obj.close()
        del image_obj
        gc.collect()
        
    def reload_img(self,dummy=None):
        #Reset the image display parameters and re-display the current image
        self.delay = 20
        self.current_image.reset_zoomcycle()
        self.load_new_image()
        self.init_image()
    
    def gen_compare_sequence(self,iterator,w,h):
        #Generates a sequence to compare two duplicate files
        
        #Determine the zoom ratio to fit the image to the compare window 
        #canvas sizes
        ratio = min(self.default_window_width/w,self.default_window_height/h)
        if ratio>2:
            ratio=2 
                
        #Calculate the new width/height and resize each frame
        new_w = int(w*ratio)
        new_h = int(h*ratio)
        for frame in iterator:
            thumbnail = frame.copy()
            thumbnail = thumbnail.resize((new_w,new_h),Image.LANCZOS)
            yield thumbnail
        
    def open_compare_window(self,new_file,existing_file):
        
        #Open a PIL image for the duplicate files in the source and destination
        #directories
        self.new_file = Image.open(new_file)
        self.existing_file = Image.open(existing_file)
        #Init iterator for the duplicate files in the source and destination
        #directories
        self.iterator_new = ImageSequence.Iterator(self.new_file)
        self.iterator_existing = ImageSequence.Iterator(self.existing_file)
        
        #Get the dimensions of the dup files in the source and destination
        #directories
        new_width,new_height = Image.open(new_file).size
        existing_width,existing_height = Image.open(existing_file).size
        
        #Generate sequence for the dup files
        self.new_sequence = self.gen_compare_sequence(self.iterator_new,new_width,new_height)
        self.existing_sequence = self.gen_compare_sequence(self.iterator_existing,existing_width,existing_height)
        #Convert the sequences to lists of frames
        self.new_sequence = [ImageTk.PhotoImage(img) for img in self.new_sequence]
        self.existing_sequence = [ImageTk.PhotoImage(img) for img in self.existing_sequence]
        
        #Open the compare window
        self.img_compare_window = tk.Toplevel(self.parent)
        
        #Bind basic keystrokes
        self.img_compare_window.bind("<MouseWheel>",self.zoomer)
        self.img_compare_window.bind('<Motion>',self.motion)
        self.img_compare_window.bind("<Control-q>",self.quit_app)
        self.img_compare_window.bind("<Escape>",self.quit_app)
        self.img_compare_window.bind('1',self.set_keep_new_flag)
        self.img_compare_window.bind('2',self.set_keep_existing_flag)
        self.img_compare_window.bind('3',self.set_keep_both_flag)
        self.img_compare_window.bind('<End>',self.close_img_compare_window)
        
        #Set the dimensions and location of the compare window
        compare_width = 2*self.default_window_width+5
        self.img_compare_window.geometry(f'{compare_width}x{self.default_window_height}+100+100')
        #set the background of the compare window to white
        self.img_compare_window.configure(background='white')
        
        #Init canvas for the file in the source directory and place the canvas
        #on the left side of the window
        new_canvas = tk.Canvas(
            self.img_compare_window,
            height=self.default_window_height,
            width=self.default_window_width,
            bg='black',
            highlightthickness=0)
        new_canvas.place(x=0, y=0,anchor=tk.NW)
        
        #Init canvas for the file in the destination directory and place the canvas
        #on the right side of the window
        existing_canvas = tk.Canvas(
            self.img_compare_window,
            height=self.default_window_height,
            width=self.default_window_width,
            bg='black',
            highlightthickness=0)
        existing_canvas.place(x=self.default_window_width+5, y=0,anchor=tk.NW)
        
        #Add an image object to the canvas for the source directory file
        new_image = new_canvas.create_image(
            int(self.default_window_width/2),
            int(self.default_window_height/2), 
            image=self.new_sequence[0],
            tag='new_img')
        #Print the name and dimensions of the source directory file
        txt = '{}\n({}x{})'.format(new_file,new_width,new_height)
        text_item = new_canvas.create_text(5,0,fill='lightblue',anchor='nw',font='times 10 bold',text=txt,tag='new_txt')
        bbox = new_canvas.bbox(text_item)
        rect_item = new_canvas.create_rectangle(bbox,fill='black',tag='new_txt')
        new_canvas.tag_raise(text_item,rect_item)
        #Label the source directory image with "1" (they keystroke to keep this file)
        text_item = new_canvas.create_text(int(self.default_window_width/2),self.default_window_height-25,fill='lightblue',anchor=tk.S,font='times 20 bold',text='1',tag='new_txt')
        bbox = new_canvas.bbox(text_item)
        rect_item = new_canvas.create_rectangle(bbox,fill='blue',tag='new_txt')
        new_canvas.tag_raise(text_item,rect_item)
        
        #Add an image object to the canvas for the destination directory file
        existing_image = existing_canvas.create_image(
            int(self.default_window_width/2),
            int(self.default_window_height/2), 
            image=self.existing_sequence[0],
            tag='new_img')
        #Print the name and dimensions of the destination directory file
        txt = '{}\n({}x{})'.format(existing_file,existing_width,existing_height)
        text_item = existing_canvas.create_text(5,0,fill='lightblue',anchor='nw',font='times 10 bold',text=txt,tag='ex_txt')
        bbox = existing_canvas.bbox(text_item)
        rect_item = existing_canvas.create_rectangle(bbox,fill='black',tag='ex_txt')
        existing_canvas.tag_raise(text_item,rect_item)
        #Label the source directory image with "2" (they keystroke to keep this file)
        text_item = existing_canvas.create_text(int(self.default_window_width/2),self.default_window_height-25,fill='lightblue',anchor=tk.S,font='times 20 bold',text='2',tag='ex_txt')
        bbox = existing_canvas.bbox(text_item)
        rect_item = existing_canvas.create_rectangle(bbox,fill='blue',tag='ex_txt')
        existing_canvas.tag_raise(text_item,rect_item)
        
        #Add a small canvas between the two images and place "3" on it (the 
        #keystroke to keep both the source and destination files)
        height = 30
        width=150
        both_canvas = tk.Canvas(
            self.img_compare_window,
            height=height,
            width=width,
            bg='blue',
            highlightthickness=0)
        both_canvas.pack(side=tk.BOTTOM)
        text_item = both_canvas.create_text(int(width/2),0,fill='lightblue',anchor=tk.N,font='times 20 bold',text='keep both: 3',tag='ex_txt')
        both_canvas.place(x=self.default_window_width+2, y=self.default_window_height-5,anchor=tk.S)
        
        #Build the inputs tuple and animate the compare window
        inputs = new_canvas,existing_canvas,both_canvas,new_image,existing_image
        self.animate_compare(0,0,inputs)
                
    def init_image(self):
        # self.img_window.destroy()
        # self.open_image_window = False
        #Open an image window and load the image sequence
        self.open_img_window(self.current_image.sequence)
            
    def open_img_window(self,sequence):
        #Open a new window and lift it to the front
        window_bkup = self.img_window
        canvas_bkup = self.canvas
        self.img_window = tk.Toplevel(self.parent)
        self.img_window.lower()
        self.parent.focus_force()
        try:
            window_bkup.lift()
        except:
            donothing=True
        
        #If there is a compare window, lift that to the top
        if self.has_compare_window:
            self.img_compare_window.lift()
        
        #Bind controls
        self.set_keybindings(self.img_window)
        
        #Set the window geometry
        if self.full_screen:
            self.img_window.attributes('-fullscreen', True)
        else:
            self.img_window.geometry(f'{self.img_window_width}x{self.img_window_height}+100+100')
            
        #Set the background to black and add a black canvas
        self.img_window.configure(background='black')
        self.canvas = tk.Canvas(self.img_window,height=self.img_window_height,width=self.img_window_width, bg='black', highlightthickness=0)
        self.canvas.pack()

                
        #If there are no images, inform the user
        if isinstance(sequence, type(None)):
            self.img_window.lift()
            self.parent.focus_force()
            try:
                window_bkup.destroy()
            except:
                donothing=True
            error_text = 'No images in the \ncurrently loaded list of images\n\nPress F1 to re-check \nthe source directory'
            text_item = self.canvas.create_text(
                int(self.img_window_width/2),
                int(self.img_window_height/2),
                fill='lightblue',
                font='times 20 bold',
                text=error_text,
                tag='error_txt')
            self.canvas.tag_raise(text_item)
            self.canvas.update()
            self.canvas.tag_raise(text_item)
        #If the current file doesn't exist, inform the user
        elif sequence == False:
            self.img_window.lift()
            self.parent.focus_force()
            try:
                window_bkup.destroy()
            except:
                donothing=True
            error_text = 'Image does not exist\n   {}\n\n   Press F1 to re-check the source directory\n   Press F7 remove missing until non-missing img is found\n   Press F8 to check image list for missing files\n   Press any move key to remove image from list'.format(self.img_list[self.cur_img])
            text_item = self.canvas.create_text(
                int(self.img_window_width/2),
                int(self.img_window_height/2),
                fill='lightblue',
                font='times 20 bold',
                text=error_text,
                tag='error_txt')
            self.canvas.tag_raise(text_item)
            self.canvas.update()
            self.canvas.tag_raise(text_item)
        else:
            #Create an image on the canvas and load first frame in the image sequence
            self.image = self.canvas.create_image(int(self.img_window_width/2),int(self.img_window_height/2), image=sequence[0],tag='img')
            inputs = (self.canvas,self.img_window,self.image)
            self.canvas.tag_raise(self.image)

        
            self.parent.focus_force()
            self.img_window.lift()
            try:
                window_bkup.destroy()
            except:
                donothing=True

            self.animate(0,sequence,inputs)
            
    def animate(self, counter,sequence,inputs):
        if self.open_text_window:
            self.txt_window.lift()
            self.txt_window.focus_force()
        #Unpack the inputs
        canvas,img_window,image = inputs
        #Reset the image frame to the one designated by the frame counter
        canvas.itemconfig(image, image=sequence[counter])
        
        #Try to delete existing text from the frame
        try:
            canvas.delete('ctr_txt1')
        except:
            donothing=1
        
        if self.img_info_display > 0:
            #Extract the image file name from the absolute path
            parts = os.path.split(self.img_list[self.cur_img])
            self.fn = parts[1]
            #Extract the name of the containing folder from the absolute path
            if self.img_info_display in [1,2]:
                self.folder = os.path.split(parts[0])[1]
            else:
                self.folder = parts[0]
            #The number of the item in the image list (convert to one-indexing)
            item = self.cur_img+1
            #The number of items in the image list
            num_items = len(self.img_list)
            #Convert the absolute zoom percentage to a string
            zoom_perc = '{}%'.format(int(self.current_image.abs_ratio*100))
            #If displaying in random order, display a flag and set the height of
            #the text
            if self.rand_order:
                r_flag = '\nR'
            else:
                r_flag = ''
                
            #If there are items in the undo queue, display the number of items
            if len(self.move_events)>0:
                u_flag = '\n#undos:{}'.format(len(self.move_events))
            else:
                u_flag = ''
                
            #Hash review text
            if self.reviewing_dup_hashes:
                hash_txt = "\n[hash dup:{}/{}]".format(self.hash_ctr+1,len(self.dup_hashes))
            else:
                hash_txt = ''
                
            #Keep mode flag
            if self.keep_mode:
                km_txt = "\nKeep Mode"
            else:
                km_txt = ''
                
            #brightness/contrast MUX cycle
            if (self.current_image.brightcycle != 0) | (self.current_image.contrastcycle != 0):
                brco_txt = "\nBr/Co: {}/{}".format(self.current_image.brightcycle,self.current_image.contrastcycle)
            else:
                brco_txt = ''
                
            
            
            counter_text1 = '{}/{}'.format(
                self.folder,
                self.fn)
            
            counter_text2 = 'Zoom:{}({})\nOverall Pos: {}\{} \nFolder Pos: {}\{}{}{}{}{}{}'.format(
                self.current_image.zoomcycle,
                zoom_perc,
                item,
                num_items,
                self.folder_position+1,
                self.num_files_in_folder,
                hash_txt,
                brco_txt,
                u_flag,
                r_flag,
                km_txt)
            
            
            #Add the info text over a black rectangle to the canvas
            text_item1 = canvas.create_text(5,5,fill='lightblue',anchor='nw',font='times 10 bold',text=counter_text1,tag='ctr_txt1')
            bbox = canvas.bbox(text_item1)
            rect_item1 = canvas.create_rectangle(bbox,fill='black',tag='ctr_txt1')
            
                
            canvas.tag_raise(text_item1,rect_item1)
            
            
            if settings.show_statistics & (self.img_info_display in [2,3]):
                text_item2 = canvas.create_text(5,20,fill='lightblue',anchor='nw',font='times 10 bold',text=counter_text2,tag='ctr_txt1')
                bbox = canvas.bbox(text_item2)
                rect_item2 = canvas.create_rectangle(bbox,fill='black',tag='ctr_txt1')
                canvas.tag_raise(text_item2,rect_item2)
        
        
        #After the delay specified by the GIF animation frame rate parameter
        #increment the counter, mod it by the number of frames in the animation
        #and call the animate function again.
        img_window.after(self.delay, lambda: self.animate((counter+1) % len(sequence),sequence,inputs))
        
    def animate_compare(self, new_counter,existing_counter,inputs):
        #Unpack the inputs
        new_canvas,existing_canvas,both_canvas,new_img,existing_img = inputs
        
        #Update the canvas for the source-directory file with the new frame
        new_canvas.itemconfig(new_img, image=self.new_sequence[new_counter])
        #Update the canvas for the destination-directory file with the new frame
        existing_canvas.itemconfig(existing_img, image=self.existing_sequence[existing_counter])
        #Arrange the canvases with the "3" for "keep both" on top
        tk.Misc.lower(new_canvas)
        tk.Misc.lower(existing_canvas)
        tk.Misc.lift(both_canvas)
        
        #Increment the counters and mod by the number of frames in each sequence
        new_counter = (new_counter+1) % len(self.new_sequence)
        existing_counter = (existing_counter+1) % len(self.existing_sequence)
        #After the GIF animation delay, call the compare window animation function
        #again
        self.img_compare_window.after(self.delay, lambda: self.animate_compare(new_counter,existing_counter,inputs))
      
def main():
    """Highest-level function. Called by user.
    
    sample calls:

    Parameters:
        None

    Returns:
        None
    """

    ### Initialize argument parser
    parser = ArgumentParser()

    ### Add arguments to parser
    parser.add_argument('-s_dir', dest='source_dir', default="None")
    parser.add_argument('-d_dir', dest='dest_root', default="None")
    args = parser.parse_args()
    
    #Pull the source and destination directories from the argument parser
    source_dir = args.source_dir
    dest_root = args.dest_root
    
    run_program = True
    
    
    if source_dir == "None":
        #Use the default source directory from the settings file
        source_dir = settings.source_dir
    
    if dest_root == "None":
        #Use destination root specified in the settings file
        dest_root = settings.dest_root
            
    
    if not os.path.isdir(source_dir):
        print('ERROR: Invalid Source Directory, quitting\n    {}'.format(source_dir))
        run_program = False
    elif not os.path.isdir(dest_root):
        print('Warning: Destination directory does not exist, will attempt to create on first move\n    {}'.format(dest_root))
        answer = ''
        while answer.lower() not in ['y','n']:
            answer = input('    Continue? (y/n)')
        if answer == 'n':
            run_program = False

    if run_program:
        #Init a tkinter application
        root = tk.Tk()
        #Make the root window full screen (reduces blinking when switching between windows
        #but makes it harder to view console outputs)
        root.attributes('-fullscreen', True)
        #Initialize the application object and start the run
        app = App(root,source_dir,dest_root)
        root.mainloop()

if __name__ == '__main__':
    main()