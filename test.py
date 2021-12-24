# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""


import tkinter as tk

class App:
    def __init__(self, parent):
        self.parent = parent
        
        self.show_input_window()
        
        
    def show_input_window(self,dummy=None):
        #Init the menu window 
        self.input_window = tk.Toplevel(self.parent)
        self.input_window.title('Get input')
        self.input_window.geometry('400x200+200+200')
        self.input_window.bind('<Return>',self.button_fcn)      #Close text window if one is open
        
        
        self.input_txt = tk.Text(self.input_window,height=7,width=100)
        
        self.input_txt.pack()
        
        button = tk.Button(self.input_window,text='Go to',command = self.button_fcn)
        button.pack()
        self.input_window.focus_force()
        self.input_txt.focus_force()
        self.input_txt.focus()
        
        
    def button_fcn(self,dummy=None):
        inpt = self.input_txt.get('1.0', "end-1c")
        
        print(inpt)
        self.input_window.destroy()
        self.show_input_window()
       
    
#Init a tkinter application
root = tk.Tk()
#Initialize the application object and start the run
app = App(root)
root.mainloop()
