# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 19:53:29 2021

@author: jmatt
"""
import os

cd = os.getcwd()
dest_root = os.path.join(cd,'sorted_pictures')


source_dir = os.path.join(cd,'images')

move_dict = {
    '.':'trash',
    's':'sunsets',
    'f':'fish',
    'F':r'fish\cooked'
    }

for key in move_dict.keys():
    move_dict[key] = os.path.join(dest_root,move_dict[key])