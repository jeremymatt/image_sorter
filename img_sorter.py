# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""


from argparse import ArgumentParser


import tkinter as tk
from PIL import Image, ImageTk, ImageSequence, ImageOps
import os
import copy as cp
import random
import inspect


try:
    import settings
except:
    import temp_settings as settings

from shutil import move

import imghdr

class App:
    def __init__(self, parent,source_dir,dest_root):
        #Init the parent canvas
        self.parent = parent
        self.parent.lift()
        self.parent.focus_force()
        self.parent_canvas = tk.Canvas(parent, bg='black', highlightthickness=0)
        self.parent_canvas.pack(fill=tk.BOTH, expand=True)
        
        #Record width & height of the screen
        self.screen_width = self.parent.winfo_screenwidth()
        self.screen_height = self.parent.winfo_screenheight()
        
        #Set the max/min steps in the zoom cycle
        self.MAX_ZOOM = 15
        self.MIN_ZOOM = -15
        
        # Initialize the scaling/zoom table
        self.mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.mux[n] = round(self.mux[n-1] * 1.1, 5)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.mux[n] = round(self.mux[n+1] * 0.9, 5)
        
        if source_dir == "None":
            #Use the default source directory from the settings file
            self.source_dir = settings.source_dir
        else:
            #Use the user-supplied source directory
            self.source_dir = source_dir
        
        #Set the temp trash directory and make if it doesn't exist
        self.trash_dest = os.path.join(settings.dest_root,'.temp_trash')
        if not os.path.isdir(self.trash_dest):
            os.makedirs(self.trash_dest)
        
        if dest_root == "None":
            #Use destination root specified in the settings file
            self.dest_root = settings.dest_root
        else:
            #Use user-supplied destination direectory
            self.dest_root = dest_root
            
        #Extract the keystroke dictionary from settings and prepend the destination
        #root to each path
        self.move_dict = settings.move_dict
        for key in self.move_dict.keys():
            self.move_dict[key] = os.path.join(self.dest_root,self.move_dict[key])
        
        #Flag to indicate that image display hasn't started yet
        self.displaying_images = False
        #Show the settings window so user knows where files are being viewed
        #from and moved to
        self.show_settings_window()
        
    def generate_settings(self):
        #Get the list of images in the source directory
        self.get_img_list()
        
        #Init the history list of previously viewed images for random view order
        self.previous_images = []
        #Set the index into the image list
        self.cur_img = 0
        #Load the display order from the settings file
        self.rand_order = settings.random_display_order
        #Load zoom/shrink to canvas setting
        self.fit_to_canvas = settings.fit_to_canvas
        #Set new image flag (indicate that image frames need to be reloaded)
        self.new_image = True
        #Default delay for the gif frame rate
        self.delay = 20
        #Set the default non-full screen width height
        self.default_window_width = 500
        self.default_window_height= 500
        #flag to indicate that there is no open image window
        self.img_window = None
        #flag to indicate that a compare window is open
        self.has_compare_window = False
        #Init a list of file move events for undo purposes
        self.move_events = []
        #Flag to show the menu window
        self.show_menu = False
        #Set flags to control duplicate file handling
        self.keep_both = False
        self.keep_new = False
        self.keep_existing = False
        self.processing_duplicates = False
        #Load the full screen setting from the settings files
        self.full_screen = settings.start_fullscreen
        #Init the window dimensions 
        if self.full_screen:
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        else:
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        
        #Reset zoom and bounding box settings
        self.reset_zoomcycle()
        
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
            #Initialize the first image of the run
            self.init_first_image()
        
        
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
        
    def reset_zoomcycle(self):
        #Set the gif frame rate to default
        self.delay = 20
        #Set the zoomcycle position to default
        self.zoomcycle = 0
        #Reset the variables tracking movement of the bounding box to zero
        self.bbox_dx = 0
        self.bbox_dy = 0
        #Set the anchor to the upper left of the image and reset the bounding
        #box flag to false
        self.bbox_anchor = [0,0]
        self.bbox = False
        
    def get_img_list(self):
        
        file_list_fn = os.path.join(self.source_dir,'.files')
        
        #If an image list file exists, load from file, else inspect directories
        #for image files
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
            while len(dirs_to_process)>0:
                print('{} files, {} dirs to process'.format(len(self.img_list),len(dirs_to_process)))
                #Pop directory from list to process
                cur_dir = dirs_to_process.pop()
                #list of all files in the directory
                new_files = [file for file in os.listdir(cur_dir) if os.path.isfile(os.path.join(cur_dir,file))]
                #Add absolute path to the file names
                new_files = [os.path.join(cur_dir,file) for file in new_files]
                #Check if file is an image file
                new_files = [file for file in new_files if imghdr.what(file) != None]
                #Add new images to the image list
                self.img_list.extend(new_files)
                
                #Recursively include subdirectories
                if settings.include_sub_dirs:
                    #Add subdirectories in the current directory to the directories to check
                    new_dirs = [item for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
                    dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
    
    def remove_empty_dirs(self,dummy = None):
        #Init the number of dirs and removed dirs counters
        self.num_dirs = 1
        self.num_removed = 0
        #Call recursive rmdirs function on source dirs
        self.rmdirs(self.source_dir)
        print("\r", end="")
        print('\nDone removing empty directories')
                    
    def rmdirs(self,cur_dir):  
        #Print the state
        if self.num_dirs > 1:
            print("\r", end="")
        print('{} dirs checked, {} dirs removed'.format(self.num_dirs,self.num_removed), end="")
        #List the items in the directory
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
        file_list_fn = os.path.join(self.source_dir,'.files')
                
        with open(file_list_fn,'r', encoding='utf-8') as file:
            lines = file.readlines()
            
        self.img_list = [line.strip() for line in lines]
            
    def write_file_list(self):
        #Write the image list to file
        file_list_fn = os.path.join(self.source_dir,'.files')
        
        with open(file_list_fn,'w', encoding='utf-8') as file:
            for fn in self.img_list:
                file.write('{}\n'.format(fn))
                
                
    def reload_img_list(self,dummy=None):
        #Force check of source directory for image files
        file_list_fn = os.path.join(self.source_dir,'.files')
        
        #If a file list exists, remove it
        if os.path.isfile(file_list_fn):
            print('removing old list')
            os.remove(file_list_fn)
            
        #Set the image index to zero, get the image list from the source dir
        #and load image 0
        self.cur_img = 0        
        self.get_img_list()        
        self.reload_img()
        
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
        window.bind('<F11>', self.toggle_fs)               #toggle full screen
        window.bind('<F1>', self.reload_img_list)          #Check source for images
        window.bind('<F2>', self.remove_empty_dirs)        #remove empty directories
        window.bind('<Right>', self.load_next_img)         #Load the next image
        window.bind('<Left>', self.load_prev_img)          #Load the previous
        window.bind('-', self.increase_delay)              #Slow GIF animation
        window.bind('=', self.decrease_delay)              #Speed GIF animation
        window.bind('<Down>', self.rotate_cw)              #Rotate the image clockwise
        window.bind('<Up>', self.rotate_ccw)               #Rotate the image counterclockwise
        window.bind('<Tab>', self.toggle_fit_to_canvas)    #zoom/shrink to canvas
        window.bind("<MouseWheel>",self.zoomer)            #mouse wheel to increase/decrease zoom
        window.bind("<Control-z>",self.undo)               #Undo file move
        window.bind("<Control-q>",self.quit_app)           #Quit app
        window.bind("<Escape>",self.quit_app)              #Quit app
        window.bind("<F12>",self.toggle_rand_order)        #Display images in random order
        window.bind("<Control-r>",self.reload_img)         #Reset zoom, animation speed etc. to defaults
        window.bind('<Alt-m>',self.toggle_menu)            #Display controls menu
        window.bind('<KeyRelease>',self.keyup)             #Monitor key presses (check for file moves)
        window.bind('1',self.set_keep_new_flag)            #dup processing: keep source_dir file
        window.bind('2',self.set_keep_existing_flag)       #dup processing: keep dest_dir file
        window.bind('3',self.set_keep_both_flag)           #dup processing: keep both files
        window.bind('<End>',self.close_img_compare_window) #Stop comparing dups & cancel move
        
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
        
        
    def rotate_cw(self,dummy=None):
        #Increment the rotation by 90 degrees
        self.rotation += 90
        #Store the sign of the rotation direction for use after the mod
        if self.rotation == 0:
            sign = 1
        else:
            sign = self.rotation/abs(self.rotation)
        #Restrict the rotation to -360:360
        self.rotation %= sign*360
        #convert to integer
        self.rotation = int(self.rotation)
        
        #Swap the height and the width dimensions of the image
        temp = cp.deepcopy(self.img_height)
        self.img_height = cp.deepcopy(self.img_width)
        self.img_width = temp
        #reset the zoom and bounding box
        self.reset_zoomcycle()
        #Display the image
        self.init_image()
        
    def rotate_ccw(self,dummy=None):
        #Decrement the rotation by 90 degrees
        self.rotation -= 90
        #Store the sign of the rotation direction for use after the mod
        if self.rotation == 0:
            sign = 1
        else:
            sign = self.rotation/abs(self.rotation)
        #Restrict the rotation to -360:360
        self.rotation %= sign*360
        #convert to integer
        self.rotation = int(self.rotation)
        
        #Swap the height and the width dimensions of the image
        temp = cp.deepcopy(self.img_height)
        self.img_height = cp.deepcopy(self.img_width)
        self.img_width = temp
        #reset the zoom and bounding box
        self.reset_zoomcycle()
        #Display the image
        self.init_image()
        
        
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
        
    def move_from(self,event):
        #Store starting point of image pan
        self.start_x = event.x
        self.start_y = event.y
        
    def move_to(self,event):
        #Store end point of image pan
        end_x = event.x
        end_y = event.y
        
        #Calculate how far the bounding box moved
        self.bbox_dx = end_x-self.start_x
        self.bbox_dy = end_y-self.start_y
        #Update the bounding box after pan and display image
        self.update_bbox_pan()
        self.init_image()
        
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
        if (key in self.move_dict.keys()) and not self.processing_duplicates:
            #Reload the image to reset zoom
            self.reload_img()
            #Store the destination directory based on the key pressed
            self.dest_dir = self.move_dict[key]
            #If the destination directory doesn't exist, create it
            if not os.path.isdir(self.dest_dir):
                os.makedirs(self.dest_dir)
            #Move the file
            self.move_file()
        
    def quit_app(self,dummy=None):
        if self.displaying_images:
            #Close the image window
            self.img_window.destroy()
            #Close the compare window if one exists
            self.close_img_compare_window()
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
                menu_txt += 'Alt+M ==> Toggle this menu\n'
                menu_txt += 'Ctrl+Z ==> Undo move\n'
                menu_txt += 'L/R arrows ==> prev/next image\n'
                menu_txt += 'U/D arrows ==> +/- GIF animation speed\n'
                menu_txt += 'F1  ==> reload img list from directory\n'
                menu_txt += 'F2  ==> Recursively remove empty dirs from source\n'
                menu_txt += 'F11 ==> toggle full screen\n'
                menu_txt += 'F12 ==> toggle random display order\n'
                menu_txt += 'TAB ==> toggle fit to canvas\n'
                menu_txt += 'Ctrl+R ==> reload image\n'
                #Build list of destination folders and corresponding keys
                menu_txt += '\nPress key to move to subdirectory in {}\n'.format(settings.dest_root)
                for key in self.move_dict.keys():
                    menu_txt += '   {} ==> {}\n'.format(key,os.path.split(settings.move_dict[key])[1])
            
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
        #Split off the filename
        orig_fn = os.path.split(self.img_list[self.cur_img])[1]
        #Split the filename into name and extension
        fn_parts = orig_fn.split('.')
        #Cancel if more or less than 1 period in filename
        if len(fn_parts) != 2:
            print('WARNING: UNEXPECTED NUMBER OF FILENAME PARTS\n  file not moved')
            return
        
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
                        self.open_image.close()
                        #Generate the absolute path to the destination
                        dest_file = os.path.join(self.dest_dir,self.dest_fn)
                        #Store the move in the move history
                        moved_files = [(file,dest_file)]
                        self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
                        
                        #Move the file to the destination and update the image
                        #list
                        move(file,dest_file)
                        self.update_img_list(file)
                        
                #User has elected to keep the file in the destination directory        
                elif self.keep_existing:
                    #Close the compare window
                    self.close_img_compare_window()
                    #Close the PIL image file
                    self.open_image.close()
                    
                    #Move the file in the source directory to the temporary
                    #trash direcetory
                    trash_dest_fn = os.path.join(self.trash_dest,orig_fn)
                    #Move the file
                    move(file,trash_dest_fn)
                    #Store the move in the move history & update the image
                    #list
                    moved_files = [(file,trash_dest_fn)]
                    self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
                    self.update_img_list(file)
                
                #User has elected to keep the file in the source directory
                elif self.keep_new:
                    #Close the compare window
                    self.close_img_compare_window()
                    #Close the PIL image file
                    self.open_image.close()
                    
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
                    
                    self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
                    self.update_img_list(file)
        else:
            #Move the file in the source directory to the destination
            #directory, store the move history, & update the image
            #list
            dest_file = os.path.join(self.dest_dir,self.dest_fn)
            moved_files = [(file,dest_file)]
            self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
            
            move(file,dest_file)
            self.update_img_list(file)
            
            
    def update_img_list(self,file):
        #Remove the moved file from the image list
        self.img_list.remove(file)
        if self.rand_order:
            self.cur_img = random.randint(0,len(self.img_list)-1)
        #If the last image was removed, set the image index to the start
        if self.cur_img >= len(self.img_list):
            self.cur_img = 0
         
        #Set the new image flag
        self.new_image = True
        #Close the PIL open image file, reset the zoom cycle and initialize
        #the next image
        self.open_image.close()
        self.reset_zoomcycle()
        self.init_image()
        
        
    def undo(self,dummy=None):
        #Pop the move source/dest directories, the old image index and the old
        #image list from the move events list
        moved_files,self.cur_img,self.img_list = self.move_events.pop()
        #Undo the move(s)
        while len(moved_files)>0:
            moved_from,moved_to = moved_files.pop()
            move(moved_to,moved_from)
        #Close the PIL open image file, reset the zoom cycle and initialize
        #the next image
        self.reset_zoomcycle()
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def zoomer(self,event):
        #Increment or decrement the zoom step based on the mouse wheel
        #movement
        if (event.delta > 0 and self.zoomcycle < self.MAX_ZOOM):
            self.zoomcycle += 1
        elif (event.delta < 0 and self.zoomcycle > self.MIN_ZOOM):
            self.zoomcycle -= 1
        else:
            print('Max/Min zoom reached!')
            return
        
        #Update the bounding box
        self.update_bbox_zoom()
        #Display the zoomed image
        self.init_image()

        
    def toggle_fs(self,dummy=None):
        #Toggle full screen mode
        if self.full_screen:
            self.full_screen = False
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        else:
            self.full_screen = True
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        self.reset_zoomcycle()
        
        self.init_image()
        
    def toggle_fit_to_canvas(self,dummy=None):
        #Toggle zoom/shrink to fit canvas
        if self.fit_to_canvas:
            self.fit_to_canvas = False
        else:
            self.fit_to_canvas = True
        self.reset_zoomcycle()
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
        #Reset zoom
        self.reset_zoomcycle()
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
        self.new_image = True
        #Close the PIL image file and init the new image
        self.open_image.close()
        self.init_image()
        
    def load_prev_img(self,dummy=None):
        #Move to the next image
        #If there is a duplicate compare window open, close it and reset the 
        #compare flags
        self.close_img_compare_window()
        #Reset zoom
        self.reset_zoomcycle()
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
        #Set the new image flag, close the PIL image file, and init the new 
        #image
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def reload_img(self,dummy=None):
        #Reset the image display parameters and re-display the current image
        self.delay = 20
        self.reset_zoomcycle()
        self.init_image()
        
    def init_bbox(self):
        #indicate that bbox exists
        self.bbox = True
        #Set the crop box coordinates
        self.crop_bbox = [0,0,self.img_width,self.img_height]
        #Set the initial bbox anchor at the upper left of the image
        self.bbox_anchor = [0,0]
        #Set the bounding box width and height to the image dimensions
        self.bbox_width = self.new_img_width
        self.bbox_height = self.new_img_height
        
        #Find the width of the crop box
        self.crop_width = self.crop_bbox[2] - self.crop_bbox[0]
        self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
        
        
    def update_bbox_pan(self):
        #Update the viewable area after mouse drag
        
        #Update the bbox anchor based on how far the mouse was dragged
        self.bbox_anchor[0] -= self.bbox_dx
        self.bbox_anchor[1] -= self.bbox_dy
        #Reset the mouse drag distances
        self.bbox_dx = 0
        self.bbox_dy = 0
        
        #Prevent the anchor from being set past the left side of the image
        if self.bbox_anchor[0] < 0:
            self.bbox_anchor[0] = 0
            
        #Prevent the anchor from being set past the top of the image
        if self.bbox_anchor[1] < 0:
            self.bbox_anchor[1] = 0
            
        #Prevent the anchor from being set past the right side of the image
        if self.bbox_anchor[0] + self.bbox_width > self.new_img_width:
            self.bbox_anchor[0] = self.new_img_width - self.bbox_width
            
        #Prevent the anchor from being set past the bottom of the image
        if self.bbox_anchor[1] + self.bbox_height > self.new_img_height:
            self.bbox_anchor[1] = self.new_img_height - self.bbox_height
            
        #Update the crop box
        self.update_crop_box()
        
        
    def update_bbox_zoom(self):
        #Store the distance between the left edge and top of the canvas before
        #the zoom.  Needed to find the position of the mouse relative to the
        #image prior to zoom.
        prev_img_edge = [(self.img_window_width-self.bbox_width)/2,(self.img_window_height-self.bbox_height)/2]
        #Store the previous width and height of the zoomed image in a list for iterating
        prev_img_wh = [self.new_img_width,self.new_img_height]
        #Update the width & height of the image & store in a list for iterating
        self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
        self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
        cur_img_wh = [self.new_img_width,self.new_img_height]
        
        #Update the absolute zoom ratio (the starting zoom if image zoomed/shrunk
        #to fit the canvas times the zoomcycle zoom)
        self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
        
        #Update the bounding box width and height (the width and height of the
        #image display area in units of canvas pixels) and stor in a list for 
        #iterating
        self.bbox_width = min(self.new_img_width,self.img_window_width)
        self.bbox_height = min(self.new_img_height,self.img_window_height)
        cur_bbox_wh = [self.bbox_width,self.bbox_height]
        
        #Store the position of the mouse in a list for iterating
        cur_mouse_xy = [self.mouse_x,self.mouse_y]
        
        #Iterate over width and height
        for i in range(2):
            #Determine the location of the mouse relative to the image before
            #the zoom occurred
            prev_mouse_pix = (cur_mouse_xy[i]-prev_img_edge[i]+self.bbox_anchor[i])
            #Move the center of the bounding box to the mouse location
            new_center = prev_mouse_pix*cur_img_wh[i]/prev_img_wh[i]
            #Update the location of the bounding box anchor relative to the
            #mouse location
            self.bbox_anchor[i] = new_center-cur_bbox_wh[i]/2
        
        #Check that the bounding box does not extend past the edges of the zoomed
        #image
        if self.bbox_anchor[0] < 0:
            self.bbox_anchor[0] = 0
        if self.bbox_anchor[1] < 0:
            self.bbox_anchor[1] = 0
        if self.bbox_anchor[0] + self.bbox_width > self.new_img_width:
            self.bbox_anchor[0] = self.new_img_width - self.bbox_width
        if self.bbox_anchor[1] + self.bbox_height > self.new_img_height:
            self.bbox_anchor[1] = self.new_img_height - self.bbox_height
        
        #Update the crop box
        self.update_crop_box()
    
    def update_crop_box(self):
            
        #Update the location of the crop box anchor.  This converts the bbox_anchor
        #from zoomed_image_coordinates to original_image_coordinates based
        #on the original/zoomed width and height ratios
        crop_bbox_anchor = [
            self.bbox_anchor[0]*(self.img_width/self.new_img_width),
            self.bbox_anchor[1]*self.img_height/self.new_img_height]
        
        #Calculate the height and width of the crop box
        self.crop_height = self.bbox_height/self.abs_ratio
        self.crop_width = self.bbox_width/self.abs_ratio
        
        #Set the crop box coordinates
        self.crop_bbox[0:2] = crop_bbox_anchor
        self.crop_bbox[2] = crop_bbox_anchor[0]+self.crop_width
        self.crop_bbox[3] = crop_bbox_anchor[1]+self.crop_height
        
        #Convert the crop box coordinates to integers
        self.crop_bbox = [int(round(item)) for item in self.crop_bbox]
            
        
    def resize_img(self,frames):
        
        #If a bounding box does not exist
        if not self.bbox:
            #Calculate the zoom ratio required to fit the image to the canvas
            self.ratio = min(self.img_window_width/self.img_width,self.img_window_height/self.img_height)
            #If the zoom required to fit is more than 200%, set to 200%
            if self.ratio>2:
                self.ratio=2 
                
            #If the image should be fit to the canvas or if the image is larger
            #than the canvas, calculate new image width/height values.  Otherwise
            #use the actual image width/height
            if self.fit_to_canvas or self.ratio < 1:
                self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
                self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
            else:
                self.new_img_width = self.img_width
                self.new_img_height = self.img_height
                self.ratio = 1
            #Calculate the absolute zoom ratio and initialize the bounding box
            self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
            self.init_bbox()
        
        for frame in frames:
            #Make a copy of the frame
            thumbnail = frame.copy()
            
            if self.rotation != 0:
                #Rotate the image
                thumbnail = thumbnail.rotate(self.rotation, expand=1, center=None, translate=None)
                # thumbnail.save('rotate_{}.jpg'.format(self.rotation))
            
            if (self.crop_width<self.img_width) or (self.crop_height<self.img_height):
                #Crop the image to the coordinates of the crop box
                thumbnail = thumbnail.crop(self.crop_bbox)
            
            #Resize the cropped image to the bounding box width and height
            thumbnail = thumbnail.resize((self.bbox_width,self.bbox_height),Image.LANCZOS)
            # thumbnail.save('thumbnail.jpg')
            #Return the rotated, cropped, resized image
            yield thumbnail
            
            
    def gen_sequence(self,img_file):
        
        if self.new_image:
            #Set the rotation to default of zero
            self.rotation = 0
            #Find the width/height of the raw image file
            (self.img_width, self.img_height) = Image.open(img_file).size
            
            #Open the image file
            self.open_image = Image.open(img_file)
            #Set the flag to indicate that an image is already loaded (to avoid
            #unnecessary disk accesses)
            self.new_image = False
            #Indicate that a new bounding box is needed
            self.bbox = False
        #Extract the raw frames in the image
        img_frames_raw = ImageSequence.Iterator(self.open_image)
        
        #Rotate/crop/resize the image as necessary
        img_frames = self.resize_img(img_frames_raw)
        
        #Build the sequence of frames in the image and return the sequence
        sequence = [ImageTk.PhotoImage(img) for img in img_frames]
        
        return sequence
    
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
        txt = '{}({}x{}'.format(new_file,new_width,new_height)
        text_item = new_canvas.create_text(5,5,fill='lightblue',anchor='w',font='times 10 bold',text=txt,tag='new_txt')
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
        txt = '{}({}x{}'.format(existing_file,existing_width,existing_height)
        text_item = existing_canvas.create_text(5,5,fill='lightblue',anchor='w',font='times 10 bold',text=txt,tag='ex_txt')
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
        
        
    
    def init_first_image(self):
        #Initialize the window for the first image of the session.  Required
        #because loading the image with a call to the destroy function (even 
        #located behind conditional statements) results in errors.  Not entirely
        #sure why
        
        #Get the path to the current image
        img_file = self.get_img_path()
        
        #If there's no image file, flag the sequence as "None".  Otherwise open
        #the file and generate the sequence
        if img_file == None: 
            sequence = None   
        else:
            sequence = self.gen_sequence(img_file)
        #Open an image window and load the image sequence
        self.open_img_window(sequence)
        
    def init_image(self):
        
        #Get the path to the current image
        img_file = self.get_img_path()
        
        #If there's no image file, flag the sequence as "None".  Otherwise open
        #the file and generate the sequence
        if img_file == None: 
            sequence = None   
        else:
            sequence = self.gen_sequence(img_file)
        #Close the existing image window
        self.img_window.destroy()
        #Open an image window and load the image sequence
        self.open_img_window(sequence)
            
            
            
    def open_img_window(self,sequence):
        #Open a new window and lift it to the front
        self.img_window = tk.Toplevel(self.parent)
        
        self.parent.focus_force()
        self.img_window.lift()
        
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
        if sequence == None:
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
        else:
            #Create an image on the canvas and load first frame in the image sequence
            self.image = self.canvas.create_image(int(self.img_window_width/2),int(self.img_window_height/2), image=sequence[0],tag='img')
            inputs = (self.canvas,self.img_window,self.image)
            self.animate(0,sequence,inputs)
            
        
    def animate(self, counter,sequence,inputs):
        #Unpack the inputs
        canvas,img_window,image = inputs
        #Reset the image frame to the one designated by the frame counter
        canvas.itemconfig(image, image=sequence[counter])
        
        #Try to delete existing text from the frame
        try:
            canvas.delete('ctr_txt')
        except:
            print('no text to delete')
        
        #Extract the image file name from the absolute path
        parts = os.path.split(self.img_list[self.cur_img])
        fn = parts[1]
        #Extract the name of the containing folder from the absolute path
        folder = os.path.split(parts[0])[1]
        #The number of the item in the image list (convert to one-indexing)
        item = self.cur_img+1
        #The number of items in the image list
        num_items = len(self.img_list)
        #Convert the absolute zoom percentage to a string
        zoom_perc = '{}%'.format(int(self.abs_ratio*100))
        #If displaying in random order, display a flag and set the height of
        #the text
        if self.rand_order:
            r_flag = '\nR'
            height = 13
        else:
            r_flag = ''
            height = 5
        #Build the info text string including the folder, file name, item numbers, 
        #the zoom cycle and percentage, and the random flag
        counter_text = '{}/{}({}/{} ({}:{}){}'.format(folder,fn,item,num_items,self.zoomcycle,zoom_perc,r_flag)
        #Add the info text over a black rectangle to the canvas
        text_item = canvas.create_text(5,height,fill='lightblue',anchor='w',font='times 10 bold',text=counter_text,tag='ctr_txt')
        bbox = canvas.bbox(text_item)
        rect_item = canvas.create_rectangle(bbox,fill='black',tag='ctr_txt')
        canvas.tag_raise(text_item,rect_item)
        
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

    ### Initialize argument parser
    parser = ArgumentParser()

    ### Add arguments to parser
    parser.add_argument('-s_dir', dest='source_dir', default="None")
    parser.add_argument('-d_dir', dest='dest_root', default="None")
    args = parser.parse_args()
    
    #Pull the source and destination directories from the argument parser
    source_dir = args.source_dir
    dest_root = args.dest_root

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