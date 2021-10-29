# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageSequence
import os
import copy as cp

try:
    import settings
except:
    import temp_settings as settings

from shutil import copy2, move

class App:
    def __init__(self, parent):
        self.parent = parent
        self.parent.lift()
        self.parent.focus_force()
        self.canvas = tk.Canvas(parent, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.MAX_ZOOM = 10
        self.MIN_ZOOM = -10
        
        # Initialize the scaling/zoom table
        self.mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.mux[n] = round(self.mux[n-1] * 1.1, 5)
            
        print(self.mux)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.mux[n] = round(self.mux[n+1] * 0.9, 5)
            
        print(self.mux)
        
        
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        print('width:{}, height:{}'.format(width,height))
        
        
        self.source_dir = settings.source_dir
        
        
        self.get_img_list()
        
        self.cur_img = 0
        self.loop_ctr = 0
        self.load_next = False
        self.load_prev = False
        self.redraw_image = False
        self.fit_to_canvas = False
        self.delay = 20
        self.default_canvas_width = 500
        self.default_canvas_height= 500
        self.zoomcycle = 0
        self.move_events = []
        self.show_menu = False
        
        
        
        self.set_keybindings()
        
        
        self.toggle_fs()
        
        self.init_image(self.img_list[self.cur_img])
        
    def get_img_list(self):
        
        img_formats = [
            'gif',
            'jpg',
            'jpeg',
            'tif']
        
        files = [file for file in os.listdir(self.source_dir) if os.path.isfile(os.path.join(self.source_dir,file))]
        files = [file for file in files if file.split('.')[-1].lower() in img_formats]
        self.img_list = [os.path.join(self.source_dir,file) for file in files]
        print('Found {} image files'.format(len(self.img_list)))
        
    
    def set_keybindings(self):
        self.parent.bind('<Escape>', self.toggle_fs)
        self.parent.bind('<Right>', self.load_next_img)
        self.parent.bind('<Left>', self.load_prev_img)
        self.parent.bind('<Down>', self.increase_delay)
        self.parent.bind('<Up>', self.decrease_delay)
        self.parent.bind('<Tab>', self.toggle_fit_to_canvas)
        self.parent.bind('<Configure>', self.resize_canvas)
        self.parent.bind("<MouseWheel>",self.zoomer)
        self.parent.bind("<Control-z>",self.undo)
        self.parent.bind("<Control-q>",self.quit_app)
        self.parent.bind("<Control-r>",self.reload_img)
        self.parent.bind('<Alt-m>',self.toggle_menu)
        self.parent.bind('<KeyRelease>',self.keyup)
        
        
    def keyup(self,event):
        key = event.char
        if key in settings.move_dict.keys():
            self.move_file(settings.move_dict[key])
        
    def quit_app(self,dummy=None):
        self.parent.destroy()
        
    def toggle_menu(self,dummy=None):
        if self.show_menu:
            self.show_menu = False
            self.reload_img()
        else:
            self.show_menu = True
        
    def move_file(self,dest_dir):
        if not os.path.isdir(dest_dir):
            os.makedirs(dest_dir)
        file = self.img_list[self.cur_img]
        orig_fn = os.path.split(file)[1]
        fn_parts = orig_fn.split('.')
        if len(fn_parts) != 2:
            print('WARNING: UNEXPECTED NUMBER OF FILENAME PARTS\n  file not moved')
            return
        dest_fn = cp.deepcopy(orig_fn)
        dest_files = [file for file in os.listdir(dest_dir) if os.path.isfile(os.path.join(dest_dir,file))]
        
        ctr = 0
        while dest_fn in dest_files:
            ctr += 1
            dest_fn = '{}({}).{}'.format(fn_parts[0],ctr,fn_parts[1])
        
        dest_file = os.path.join(dest_dir,dest_fn)
        
        self.move_events.append((file,dest_file,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
        
        print(file)
        print(dest_file)
        
        move(file,dest_file)
        
        self.img_list.remove(file)
        if self.cur_img >= len(self.img_list):
            self.cur_img = 0
        
        self.redraw_image = True
        
        
    def undo(self,dummy=None):
        file,dest_file,self.cur_img,self.img_list = self.move_events.pop()
        print('file:{}'.format(file))
        print('dest_file:{}'.format(dest_file))
        print('cur img: {}'.format(self.cur_img))
        print('items: {}'.format(self.img_list))
        move(dest_file,file)
        self.redraw_image = True
        
    def zoomer(self,event):
        # (x,y) = self.to_raw((event.x,event.y))

        if (event.delta > 0 and self.zoomcycle < self.MAX_ZOOM):
            self.zoomcycle += 1
            print(f'zoomcycle: {self.zoomcycle}, scale: {self.mux[self.zoomcycle]}')
        elif (event.delta < 0 and self.zoomcycle > self.MIN_ZOOM):
            self.zoomcycle -= 1
            print(f'zoomcycle: {self.zoomcycle}, scale: {self.mux[self.zoomcycle]}')
        else:
            print('Max/Min zoom reached!')
            return

        
    def toggle_fs(self,dummy=None):
        self.redraw_image = True
        print('toggling full screen')
        state = False if self.parent.attributes('-fullscreen') else True
        self.parent.attributes('-fullscreen', state)
        if not state:
            self.parent.geometry(f'{self.default_canvas_width}x{self.default_canvas_height}+0+0')
            
    def resize_canvas(self,event):
        self.redraw_image = True
        
    def toggle_fit_to_canvas(self,dummy=None):
        if self.fit_to_canvas:
            self.fit_to_canvas = False
        else:
            self.fit_to_canvas = True
        self.redraw_image = True
            
    def increase_delay(self,dummy=None):
        self.delay += 5
        
    def decrease_delay(self,dummy=None):
        self.delay -= 5
        if self.delay <= 0:
            self.delay = 5
        
        
    def load_next_img(self,dummy=None):
        self.load_next = True
        
    def load_prev_img(self,dummy=None):
        self.load_prev = True
        
        
    def next_img(self,dummy=None):
        self.cur_img = (self.cur_img+1) % len(self.img_list)
        self.init_image(self.img_list[self.cur_img])
        
    def prev_img(self,dummy=None):
        self.cur_img -= 1
        if self.cur_img < 0:
            self.cur_img = len(self.img_list)-1
        self.init_image(self.img_list[self.cur_img])
        
    def reload_img(self,dummy=None):
        self.init_image(self.img_list[self.cur_img])
        
    def resize_img(self,frames,width,height):
        ratio = min(self.canvas_width/width,self.canvas_height/height)
        new_width = int(width*ratio)
        new_height = int(height*ratio)
        
        for frame in frames:
            thumbnail = frame.copy()
            thumbnail = thumbnail.resize((new_width,new_height),Image.LANCZOS)
            yield thumbnail
    
    def init_image(self,img_file):
        
        self.parent.update()
        self.canvas_width = self.canvas.winfo_width()
        self.canvas_height = self.canvas.winfo_height()
        
        if self.canvas_width == 1:
            self.canvas_width = 500
        if self.canvas_height == 1:
            self.canvas_height = 500
            
        num_frames = len([img for img in ImageSequence.Iterator(Image.open(img_file))])
            
        img_frames = ImageSequence.Iterator(Image.open(img_file))
        
        raw_frame = [img for img in img_frames][0]
        (width, height) = raw_frame.size

        img_frames = ImageSequence.Iterator(Image.open(img_file))
        
        if self.fit_to_canvas or (width>self.canvas_width) or (height>self.canvas_height):
            img_frames = self.resize_img(img_frames,width,height)
        
        
        self.sequence = [ImageTk.PhotoImage(img) for img in img_frames]
        
        
        
        self.canvas.delete('all')
        self.image = self.canvas.create_image(int(self.canvas_width/2),int(self.canvas_height/2), image=self.sequence[0],tag='img')
        self.animate(0)
        
        
        
    def animate(self, counter):
        
        if self.show_menu:
            self.canvas.delete('all')
            menu_txt = ''
            for key in settings.move_dict.keys():
                menu_txt = menu_txt+'{} ==> {}\n'.format(key,os.path.split(settings.move_dict[key])[1])
            text_item = self.canvas.create_text(
                int(self.canvas_width/2),
                int(self.canvas_height/2),
                fill='lightblue',
                font='times 10 bold',
                text=menu_txt,tag='menu_txt')
            self.canvas.tag_raise(text_item)
            return
             
        
        if len(self.img_list)>0:
            self.canvas.itemconfig(self.image, image=self.sequence[counter])
            counter_text = '{}/{}'.format(self.cur_img+1,len(self.img_list))
            text_item = self.canvas.create_text(20,15,fill='lightblue',font='times 10 bold',text=counter_text,tag='ctr_txt')
            bbox = self.canvas.bbox(text_item)
            rect_item = self.canvas.create_rectangle(bbox,fill='black',tag='ctr_txt')
            self.canvas.tag_raise(text_item,rect_item)
            
            
            if self.load_next:
                self.load_next = False
                self.next_img()
            elif self.load_prev:
                self.load_prev = False
                self.prev_img()
                
            elif self.redraw_image:
                self.redraw_image = False
                self.reload_img()
                
            else:
                self.parent.after(self.delay, lambda: self.animate((counter+1) % len(self.sequence)))
        else:
            error_text = 'No images remain in list'
            self.canvas.delete('all')
            text_item = self.canvas.create_text(int(self.canvas_width/2),int(self.canvas_height/2),fill='lightblue',font='times 10 bold',text=error_text,tag='ctr_txt')
            self.reload_img()
            

root = tk.Tk()
root.attributes('-fullscreen', True)
app = App(root)
root.mainloop()
