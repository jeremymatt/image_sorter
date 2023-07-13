# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 19:53:29 2021

@author: jmatt

NOTE: Rename this file to "settings.py" to use
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
max_allowed_undo = 'all' #integer >=0 or "all"
max_allowed_undo = 100 #integer >=0 or "all"
show_statistics = True

video_extensions = [
    'mp4',
    'avi',
    'wmv',
    'mov',
    'flv',
    'mpg',
    'mpeg',
    'mpe',
    'mpv',
    'ogg',
    'm4p',
    'm4v',
    'qt',
    'swf']

#Defines the keystrokes used to move images.  For example, pressing period will
#move the image to <dest_root>\trash\<image_filename>
#If they don't exist, these directories will be created as-needed
move_dict = {
    '.':'trash',
    's':'sunsets',
    'f':'fish',
    'F':r'fish\salmon'
    }


#Save to path relative to the image's original directory
keep_mode_move_dict = {
    'k':r'keep',
    'p':r'keep\private',
    }
