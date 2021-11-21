# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 19:53:29 2021

@author: jmatt
"""
import os

cd = os.getcwd()
#root directory to save moved images. Does not need to exist, the program will
#create it if necessary
dest_root = os.path.join(cd,'sorted_pictures')

source_dir = os.path.join(cd,'images') #Directory to open images from

start_fullscreen = True
fit_to_canvas = True #zoom/shrink to canvas
#show images from sub-directories of the source directory
include_sub_dirs = True 
#Display images in random order
random_display_order = False

#Defines the keystrokes used to move images.  For example, pressing period will
#move the image to <dest_root>\trash\<image_filename>
#If they don't exist, these directories will be created as-needed
move_dict = {
    '.':'trash',
    's':'sunsets',
    'f':'fish',
    'F':r'fish\salmon'
    }
