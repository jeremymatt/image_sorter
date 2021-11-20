# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 19:53:29 2021

@author: jmatt
"""
import os

cd = os.getcwd()
dest_root = os.path.join(cd,'sorted_pictures') #root directory to save moved images

source_dir = os.path.join(cd,'images') #Directory to open images from

start_fullscreen = True
fit_to_canvas = True #zoom/shrink to canvas
#show images from sub-directories of the source directory
include_sub_dirs = True 
#Display images in random order
random_display_order = False

move_dict = {
    '.':'trash',
    's':'sunsets',
    'f':'fish',
    'F':r'fish\cooked'
    }

for key in move_dict.keys():
    move_dict[key] = os.path.join(dest_root,move_dict[key])