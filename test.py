# -*- coding: utf-8 -*-
"""
Created on Sat Oct 30 13:53:41 2021

@author: jmatt
"""

import settings
import os
fn = os.path.join(settings.source_dir,'.files')
with open(fn,'r') as file:
    lines = file.readlines()
    
img_list = [line.strip() for line in lines]

with open(fn,'w') as file:
    file.write('update')


def add1(Y):
    Y += 1
    
X = np.zeros(5)
print('X before addition: {}'.format(X))

add1(X)

print('X after addition: {}'.format(X))





'''
import tkinter as tk #fixed typo in here
w=tk.Tk()
a=tk.Canvas(w,width=20, height=30, bg="red")
a.place(x=20, y=30)
a.pack(side=tk.LEFT)
b=tk.Canvas(w,width=20, height=30, bg="blue")
b.place(x=25, y=35)
b.pack(side=tk.LEFT)
c=tk.Canvas(w,width=20, height=30, bg="green")
c.place(x=30, y=0)
tk.Misc.lower(c)
w.mainloop()
'''


'''
if dup or processing dup
    if not (both,existing, or new)
        init counter
        Show the compare window
    else
        if BOTH
            update destination filename
            if updated fn is dup
                increment counter
                Show compare window
            else
                move the file
                store previous state
                update current state
        elif EXISTING
            move current source file to temp trash directory
            store prev. state
            update current state
        elif NEW
            move dup dest file to temp trash directory
            move current source file to dest directory
            store prev. state
            update current state
else
    move file
    store prev. state
    update current state
    
    
    
    
    