# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""


import pickle as pkl
import copy as cp

from PIL import Image, ImageTk, ImageSequence, ImageOps, ImageFile, ImageEnhance

import imghdr
# Monkeypatch bug in imagehdr
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


img_file = r'p:\img\test6\General\Cutest_Real_Girls\0A1eLLT.jpg'

t = imghdr.what(img_file)
open_image = Image.open(img_file)






# # with open(r'P:\files_base.pkl', 'rb') as file:
# with open(r'P:\files_00.pkl', 'rb') as file:
#     missing_files_old = pkl.load(file)
#     found_files_old = pkl.load(file)
#     removed_hashes_old = pkl.load(file)
#     kept_hashes_old = pkl.load(file)
    

# with open(r'P:\files_01.pkl', 'rb') as file:
#     missing_files_new = pkl.load(file)
#     found_files_new = pkl.load(file)
#     removed_hashes_new = pkl.load(file)
#     kept_hashes_new = pkl.load(file)
    
    
    
# print('{} missing files'.format(len(missing_files_old)))
# print('{} found files'.format(len(found_files_old)))
# print('{} removed hashes'.format(len(removed_hashes_old)))
# print('{} kept hashes'.format(len(kept_hashes_old)))
# print('{} total hashes'.format(len(removed_hashes_old)+len(kept_hashes_old)))


    
# print('{} missing files'.format(len(missing_files_new)))
# print('{} found files'.format(len(found_files_new)))
# print('{} removed hashes'.format(len(removed_hashes_new)))
# print('{} kept hashes'.format(len(kept_hashes_new)))
# print('{} total hashes'.format(len(removed_hashes_new)+len(kept_hashes_new)))


# fn = 'Robin Redhead'

# all_old = cp.deepcopy(missing_files_old)
# all_old.extend(found_files_old)

# all_new = cp.deepcopy(missing_files_new)
# all_new.extend(found_files_new)

# files = [file for file in missing_files_old if file in all_new]

# new_files = [file for file in all_new if file not in all_old]
# ex_files = [file for file in all_new if file in all_old]
    
    # pkl.dump(missing_files,file)
    # pkl.dump(found_files,file)

# import tkinter as tk

# class App:
#     def __init__(self, parent):
#         self.parent = parent
        
#         self.show_input_window()
        
        
#     def show_input_window(self,dummy=None):
#         #Init the menu window 
#         self.input_window = tk.Toplevel(self.parent)
#         self.input_window.title('Get input')
#         self.input_window.geometry('400x200+200+200')
#         self.input_window.bind('<Return>',self.button_fcn)      #Close text window if one is open
        
        
#         self.input_txt = tk.Text(self.input_window,height=7,width=100)
        
#         self.input_txt.pack()
        
#         button = tk.Button(self.input_window,text='Go to',command = self.button_fcn)
#         button.pack()
#         self.input_window.focus_force()
#         self.input_txt.focus_force()
#         self.input_txt.focus()
        
        
#     def button_fcn(self,dummy=None):
#         inpt = self.input_txt.get('1.0', "end-1c")
        
#         print(inpt)
#         self.input_window.destroy()
#         self.show_input_window()
       
    
# #Init a tkinter application
# root = tk.Tk()
# #Initialize the application object and start the run
# app = App(root)
# root.mainloop()
