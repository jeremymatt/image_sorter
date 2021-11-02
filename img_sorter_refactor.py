# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""

import tkinter as tk
from PIL import Image, ImageTk, ImageSequence, ImageOps
import os
import copy as cp
import random

import time

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
        self.parent_canvas = tk.Canvas(parent, bg='black', highlightthickness=0)
        self.parent_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.screen_width = self.parent.winfo_screenwidth()
        self.screen_height = self.parent.winfo_screenheight()
        
        
        self.MAX_ZOOM = 15
        self.MIN_ZOOM = -15
        
        # Initialize the scaling/zoom table
        self.mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.mux[n] = round(self.mux[n-1] * 1.1, 5)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.mux[n] = round(self.mux[n+1] * 0.9, 5)
        
        
        self.source_dir = settings.source_dir
        
        
        self.get_img_list()
        
        self.previous_images = []
        
        self.img_window_list = []
        self.cur_img = 0
        self.loop_ctr = 0
        self.load_next = False
        self.load_prev = False
        self.rand_order = settings.random_display_order
        self.redraw_image = False
        self.fit_to_canvas = True
        self.new_image = True
        self.delay = 20
        self.default_canvas_width = 500
        self.default_canvas_height= 500
        self.default_window_width = 500
        self.default_window_height= 500
        self.img_window = None
        self.zoomcycle = 0
        self.bbox_dx = 0
        self.bbox_dy = 0
        self.bbox_anchor = [0,0]
        self.move_events = []
        self.show_menu = False
        self.no_files = False
        self.full_screen = settings.start_fullscreen
        if self.full_screen:
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        else:
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        self.img_window_wh_ratio = self.img_window_width/self.img_window_height
        
        self.reset_zoomcycle()
        self.img_window = self.parent
        self.set_keybindings(self.parent)
        
        self.init_first_image()
        # self.show_nofiles_window()
        
    def reset_zoomcycle(self):
        self.zoomcycle = 0
        self.bbox_dx = 0
        self.bbox_dy = 0
        self.bbox = None
        
    def get_img_list(self):
        
        dirs_to_process = [self.source_dir]
        self.img_list = []
        while len(dirs_to_process)>0:
            cur_dir = dirs_to_process.pop()
            new_files = [file for file in os.listdir(cur_dir) if os.path.isfile(os.path.join(cur_dir,file))]
            new_files = [file for file in new_files if file.split('.')[-1].lower() in settings.img_formats]
            new_files = [os.path.join(cur_dir,file) for file in new_files]
            self.img_list.extend(new_files)
            
            if settings.include_sub_dirs:
                new_dirs = [item for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
                dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
            
            
            
        # if len(self.img_list) == 0:
        #     self.show_nofiles_window()
        
    def show_menu_window(self,dummy=None):
        self.menu_window = tk.Toplevel(self.parent)
        # self.menu_window.attributes('-fullscreen', True)
        # self.menu_window.configure(background='black')
        canvas = tk.Canvas(self.menu_window,height=500,width=500)
        canvas.pack()
        menu_txt = self.gen_menutext()
        text_item = canvas.create_text(
            int(100),
            int(100),
            fill='black',
            font='times 10 bold',
            text=menu_txt,tag='menu_txt')
        bbox = canvas.bbox(text_item)
        dim = (bbox[2]-bbox[0]+50,bbox[3]-bbox[1]+50)
        self.menu_window.geometry(f'{dim[0]}x{dim[1]}+0+0')
        canvas.move(text_item,int(dim[0]/4),int(dim[1]/3))
        canvas.update()
        canvas.tag_raise(text_item)
        
    def show_nofiles_window(self,dummy=None):
        self.nofiles_window = tk.Toplevel(self.parent)
        self.nofiles_window.focus_force()
        
        
        self.nofiles_window.bind("<Control-q>",self.quit_app)
        self.nofiles_window.bind("<Escape>",self.quit_app)
        self.nofiles_window.bind("<Control-z>",self.undo)
        
        # self.window.attributes('-fullscreen', True)
        # self.window.configure(background='black')
        canvas = tk.Canvas(self.nofiles_window,height=50,width=100)
        canvas.pack()
        error_text = 'No images remain in list'
        text_item = canvas.create_text(
            int(self.img_window_width/2),
            int(self.img_window_height/2),
            fill='lightblue',
            font='times 10 bold',
            text=error_text,
            tag='error_txt')
        canvas.tag_raise(text_item)
        # text_item = canvas.create_text(
        #     int(100),
        #     int(100),
        #     fill='black',
        #     font='times 10 bold',
        #     text=error_text,tag='error_txt')
        bbox = canvas.bbox(text_item)
        dim = (bbox[2]-bbox[0]+50,bbox[3]-bbox[1]+50)
        self.nofiles_window.geometry(f'{dim[0]}x{dim[1]}+0+0')
        canvas.move(text_item,int(dim[0]/4),int(dim[1]/3))
        canvas.update()
        canvas.tag_raise(text_item)
        
        
    def set_keybindings(self,window):
        window.bind('<F11>', self.toggle_fs)
        window.bind('<Right>', self.load_next_img)
        window.bind('<Left>', self.load_prev_img)
        window.bind('-', self.increase_delay)
        window.bind('=', self.decrease_delay)
        window.bind('<Down>', self.rotate_cw)
        window.bind('<Up>', self.rotate_ccw)
        window.bind('<Tab>', self.toggle_fit_to_canvas)
        window.bind('<Configure>', self.resize_canvas)
        window.bind("<MouseWheel>",self.zoomer)
        window.bind("<Control-z>",self.undo)
        window.bind("<Control-q>",self.quit_app)
        window.bind("<F12>",self.toggle_rand_order)
        window.bind("<Escape>",self.quit_app)
        window.bind("<Control-r>",self.reload_img)
        window.bind('<Alt-m>',self.toggle_menu)
        window.bind('<KeyRelease>',self.keyup)
        
        
    # def tr(rotation):
        
    #     sign = rotation/abs(rotation)
    #     rotation %= 360
    #     rotation *= sign
    #     rotation  = int(rotation)
    #     print(rotation)
        
    def rotate_cw(self,dummy=None):
        self.rotation += 90
        if self.rotation == 0:
            sign = 1
        else:
            sign = self.rotation/abs(self.rotation)
        self.rotation %= sign*360
        self.rotation = int(self.rotation)
        
        temp = cp.deepcopy(self.img_height)
        self.img_height = cp.deepcopy(self.img_width)
        self.img_width = temp
        self.bbox = None
        self.zoomcycle = 0
        self.init_image()
        
    def rotate_ccw(self,dummy=None):
        self.rotation -= 90
        if self.rotation == 0:
            sign = 1
        else:
            sign = self.rotation/abs(self.rotation)
        self.rotation %= sign*360
        self.rotation = int(self.rotation)
        
        temp = cp.deepcopy(self.img_height)
        self.img_height = cp.deepcopy(self.img_width)
        self.img_width = temp
        self.bbox = None
        self.zoomcycle = 0
        self.init_image()
        
        
        
    def toggle_rand_order(self,dummy=None):
        if self.rand_order:
            self.rand_order = False
            self.previous_images = []
        else:
            self.rand_order = True
        
    
    def motion(self,event):
        self.mouse_x,self.mouse_y = event.x,event.y
        # print("motion: {}, {}".format(self.mouse_x,self.mouse_y))
        
    def move_from(self,event):
        self.start_x = event.x
        self.start_y = event.y
        
    def move_to(self,event):
        end_x = event.x
        end_y = event.y
        
        self.bbox_dx = end_x-self.start_x
        self.bbox_dy = end_y-self.start_y
        self.update_bbox_pan()
        self.init_image()
        
    def get_img_path(self):
        if len(self.img_list) == 0:
            return None
        else:
            return self.img_list[self.cur_img]
        
    def keyup(self,event):
        key = event.char
        if key in settings.move_dict.keys():
            self.move_file(settings.move_dict[key])
        
    def quit_app(self,dummy=None):
        self.parent.destroy()
        
    def toggle_menu(self,dummy=None):
        if self.show_menu:
            self.show_menu = False
            self.menu_window.destroy()
        else:
            self.show_menu = True
            self.show_menu_window()
        
    def move_file(self,dest_dir):
        self.new_image = True
        self.open_image.close()
        self.reset_zoomcycle()
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
        
        
        move(file,dest_file)
        
        self.img_list.remove(file)
        if self.cur_img >= len(self.img_list):
            self.cur_img = 0
            
        
        self.init_image()
        
        
    def undo(self,dummy=None):
        file,dest_file,self.cur_img,self.img_list = self.move_events.pop()
        move(dest_file,file)
        self.reset_zoomcycle()
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def zoomer(self,event):
        # (x,y) = self.to_raw((event.x,event.y))

        if (event.delta > 0 and self.zoomcycle < self.MAX_ZOOM):
            self.zoomcycle += 1
            # print(f'zoomcycle: {self.zoomcycle}, scale: {self.mux[self.zoomcycle]}')
        elif (event.delta < 0 and self.zoomcycle > self.MIN_ZOOM):
            self.zoomcycle -= 1
            # print(f'zoomcycle: {self.zoomcycle}, scale: {self.mux[self.zoomcycle]}')
        else:
            print('Max/Min zoom reached!')
            return
        
        self.update_bbox_zoom()
        self.init_image()

        
    def toggle_fs(self,dummy=None):
        if self.full_screen:
            self.full_screen = False
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        else:
            self.full_screen = True
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        self.img_window_wh_ratio = self.img_window_width/self.img_window_height
        self.reset_zoomcycle()
        
        self.init_image()
        
            
    def resize_canvas(self,event):
        self.default_canvas_height = 500
        self.default_canvas_width = 500
        self.init_image()
        
    def toggle_fit_to_canvas(self,dummy=None):
        if self.fit_to_canvas:
            self.fit_to_canvas = False
        else:
            self.fit_to_canvas = True
        self.reset_zoomcycle()
        self.init_image()
            
    def increase_delay(self,dummy=None):
        self.delay += 5
        
    def decrease_delay(self,dummy=None):
        self.delay -= 5
        if self.delay <= 0:
            self.delay = 5
        
        
    def load_next_img(self,dummy=None):
        self.reset_zoomcycle()
        if self.rand_order:
            step = random.randint(0,len(self.img_list)-2)
            self.previous_images.append(self.cur_img)
        else:
            step = 1
        self.cur_img = (self.cur_img+step) % len(self.img_list)
        # print(self.previous_images)
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def load_prev_img(self,dummy=None):
        self.reset_zoomcycle()
        if len(self.previous_images)>0:
            cur_img = self.previous_images.pop()
            if cur_img == self.cur_img:
                self.cur_img = self.previous_images.pop()
            else:
                self.cur_img = cur_img
        else:
            self.cur_img -= 1
            if self.cur_img < 0:
                self.cur_img = len(self.img_list)-1
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def reload_img(self,dummy=None):
        self.reset_zoomcycle()
        self.init_image()
        
    def init_bbox(self):
        self.bbox = [0,0,self.new_img_width,self.new_img_height]
        self.crop_bbox = [0,0,self.img_width,self.img_height]
        self.bbox_ratio_x = self.abs_ratio
        self.bbox_ratio_y = self.abs_ratio
        self.bbox_anchor = [0,0]
        
        self.bbox_width = self.bbox[2]-self.bbox[0]
        self.bbox_height = self.bbox[3]-self.bbox[1]
        
        
        self.crop_width = self.crop_bbox[2] - self.crop_bbox[0]
        self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
        
        
    def update_bbox_pan(self):
        
        
        self.bbox_anchor[0] -= self.bbox_dx
        self.bbox_anchor[1] -= self.bbox_dy
        self.bbox_dx = 0
        self.bbox_dy = 0
        
        if self.bbox_anchor[0] < 0:
            self.bbox_anchor[0] = 0
            
        if self.bbox_anchor[1] < 0:
            self.bbox_anchor[1] = 0
            
        if self.bbox_anchor[0] + self.bbox_width > self.new_img_width:
            self.bbox_anchor[0] = self.new_img_width - self.bbox_width
            
        if self.bbox_anchor[1] + self.bbox_height > self.new_img_height:
            self.bbox_anchor[1] = self.new_img_height - self.bbox_height
            
        
        crop_bbox_anchor = [
            self.bbox_anchor[0]*(self.img_width/self.new_img_width),
            self.bbox_anchor[1]*self.img_height/self.new_img_height]
        
        
        
        self.crop_bbox[0:2] = crop_bbox_anchor
        self.crop_bbox[2] = crop_bbox_anchor[0]+self.crop_width
        self.crop_bbox[3] = crop_bbox_anchor[1]+self.crop_height
        
        
        self.crop_bbox = [int(round(item)) for item in self.crop_bbox]
        
        
        
        
    def update_bbox_zoom(self):
        print('bbox dim:{}x{}'.format(self.bbox_width,self.bbox_height))
        print('old bbox: {}'.format(self.bbox))
        print('old crop box: {} ({}x{})'.format(self.crop_bbox,self.crop_width,self.crop_height))
        self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
        self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
        self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
        
        self.bbox_width = min(self.new_img_width,self.img_window_width)
        self.bbox_height = min(self.new_img_height,self.img_window_height)
        
        bb_wh_ratio = self.bbox_width/self.bbox_height
        
        self.bbox_ratio_x = self.bbox_width/self.new_img_width
        self.bbox_ratio_y = self.bbox_height/self.new_img_height
        
        
        mouse_x_fraction = self.mouse_x/self.img_window_width
        mouse_y_fraction = self.mouse_y/self.img_window_height
        
        self.bbox[0] = int(self.mouse_x-self.bbox_width*mouse_x_fraction)
        self.bbox[2] = int(self.mouse_x+self.bbox_width*(1-mouse_x_fraction))
        self.bbox[1] = int(self.mouse_y-self.bbox_height*mouse_y_fraction)
        self.bbox[3] = int(self.mouse_y+self.bbox_height*(1-mouse_y_fraction))
        
        
        
        
        self.bbox_ratio_x = (self.img_window_width/self.bbox_width)*self.mux[self.zoomcycle]
        self.bbox_ratio_y = (self.img_window_height/self.bbox_height)*self.mux[self.zoomcycle]
        
        
        if (self.bbox_width == self.new_img_width) and (self.bbox_height == self.new_img_height):
            self.crop_bbox[0] = 0
            self.crop_bbox[2] = self.img_width
            
            self.crop_bbox[1] = 0
            self.crop_bbox[3] = self.img_height
            
            
        if (self.bbox_width == self.new_img_width) and (self.bbox_height < self.new_img_height):
            self.crop_bbox[0] = 0
            self.crop_bbox[2] = self.img_width
            
            self.crop_height = self.bbox_height/self.abs_ratio
            print('intended crop height: {}'.format(self.crop_height))
            
            self.crop_bbox[1] = self.bbox[1]/self.abs_ratio
            self.crop_bbox[3] = self.bbox[3]/self.abs_ratio
            self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
            print('actual crop height: {}'.format(self.crop_height))
            
            
        if (self.bbox_width < self.new_img_width) and (self.bbox_height == self.new_img_height):
            self.crop_bbox[1] = 0
            self.crop_bbox[3] = self.img_height
            
            self.crop_width = self.bbox_width/self.abs_ratio
            print('intended crop width: {}'.format(self.crop_width))
            
            self.crop_bbox[0] = self.bbox[0]/self.abs_ratio
            self.crop_bbox[2] = self.bbox[2]/self.abs_ratio
            self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
            print('actual crop width: {}'.format(self.crop_width))
            
        if (self.bbox_width < self.new_img_width) and (self.bbox_height < self.new_img_height):
            self.crop_bbox[0] = self.bbox[0]/self.abs_ratio
            self.crop_bbox[2] = self.bbox[2]/self.abs_ratio
            
            self.crop_height = self.bbox_height/self.abs_ratio
            print('intended crop height: {}'.format(self.crop_height))
            
            self.crop_bbox[1] = self.bbox[1]/self.abs_ratio
            self.crop_bbox[3] = self.bbox[3]/self.abs_ratio
            self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
            print('actual crop height: {}'.format(self.crop_height))
            
        self.crop_bbox = [int(round(item)) for item in self.crop_bbox]
            
                        
        self.crop_width = self.crop_bbox[2] - self.crop_bbox[0]
        self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
        
        cb_wh_ratio = self.crop_width/self.crop_height
        
        print('img w/h ratios: \n   img: {}\n   crp: {}\n   bbx: {}\n   win: {}'.format(self.img_wh_ratio,cb_wh_ratio,bb_wh_ratio,self.img_window_wh_ratio))
        
        print('new bbox: {} ({}x{})'.format(self.bbox,self.bbox_width,self.bbox_height))
        print('new crop box: {} ({}x{})'.format(self.crop_bbox,self.crop_width,self.crop_height))
        
        # self.img_window_wh_ratio
        
        
            
            
        
    def resize_img(self,frames):
        
        if self.bbox == None:
            self.ratio = min(self.img_window_width/self.img_width,self.img_window_height/self.img_height)
            if self.ratio>2:
                self.ratio=2 
                
            if self.fit_to_canvas or self.ratio < 1:
                self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
                self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
            else:
                self.new_img_width = self.img_width
                self.new_img_height = self.img_height
                self.ratio = 1
            self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
            self.init_bbox()
        
        
            
        for frame in frames:
            thumbnail = frame.copy()
            
            if self.rotation != 0:
                thumbnail = thumbnail.rotate(self.rotation, expand=1, center=None, translate=None)
                # thumbnail.save('rotate_{}.jpg'.format(self.rotation))
            
            if (self.crop_width<self.img_width) or (self.crop_height<self.img_height):
                thumbnail = thumbnail.crop(self.crop_bbox)
                
            thumbnail = thumbnail.resize((self.bbox_width,self.bbox_height),Image.LANCZOS)
            # thumbnail.save('thumbnail.jpg')
            yield thumbnail
            
            
    def gen_sequence(self,img_file):
        
        if self.new_image:
            self.rotation = 0
            (self.img_width, self.img_height) = Image.open(img_file).size
            self.img_wh_ratio = self.img_width/self.img_height
            self.open_image = Image.open(img_file)
            self.new_image = False
        img_frames_raw = ImageSequence.Iterator(self.open_image)
        
        img_frames = self.resize_img(img_frames_raw)
        
        
        sequence = [ImageTk.PhotoImage(img) for img in img_frames]
        
        return sequence
        
    
    def init_first_image(self):
        img_file = self.get_img_path()
        
        if img_file == None: 
            sequence = None   
        else:
            sequence = self.gen_sequence(img_file)
        
        self.open_img_window(sequence)
        
    def init_image(self):
        img_file = self.get_img_path()
        
        
        if img_file == None: 
            sequence = None   
        else:
            sequence = self.gen_sequence(img_file)
        
        self.img_window.destroy()
        self.open_img_window(sequence)
            
    def open_img_window(self,sequence):
        self.img_window = tk.Toplevel(self.parent)
        
        # self.set_keybindings(self.img_window)
        self.img_window.bind("<MouseWheel>",self.zoomer)
        self.img_window.bind('<Motion>',self.motion)
        self.img_window.bind("<Control-q>",self.quit_app)
        self.img_window.bind("<Escape>",self.quit_app)
        
        self.img_window.bind('<ButtonPress-1>', self.move_from)
        self.img_window.bind('<ButtonRelease-1>',     self.move_to)
        
        if self.full_screen:
            self.img_window.attributes('-fullscreen', True)
        else:
            self.img_window.geometry(f'{self.img_window_width}x{self.img_window_height}+100+100')
            
        self.img_window.configure(background='black')
        self.canvas = tk.Canvas(self.img_window,height=self.img_window_height,width=self.img_window_width, bg='black', highlightthickness=0)
        self.canvas.pack()
        
        
        if sequence == None:
            error_text = 'No images remain in list'
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
            self.image = self.canvas.create_image(int(self.img_window_width/2),int(self.img_window_height/2), image=sequence[0],tag='img')
            self.animate(0,sequence)
        
        
    def gen_menutext(self):
        
            menu_txt = ''
            
            menu_txt += 'Esc ==> Quit\n'
            menu_txt += 'Alt+M ==> Toggle this menu\n'
            menu_txt += 'Ctrl+Z ==> Undo move\n'
            menu_txt += 'L/R arrows ==> prev/next image\n'
            menu_txt += 'U/D arrows ==> +/- GIF animation speed\n'
            menu_txt += 'F11 ==> toggle full screen\n'
            menu_txt += 'F12 ==> toggle random display order\n'
            menu_txt += 'TAB ==> toggle fit to canvas\n'
            menu_txt += 'Ctrl+R ==> reload image\n'
            
            menu_txt += '\nPress key to move to subdirectory in {}\n'.format(settings.dest_root)
            for key in settings.move_dict.keys():
                menu_txt += '   {} ==> {}\n'.format(key,os.path.split(settings.move_dict[key])[1])
            
            return menu_txt
        
    def animate(self, counter,sequence):
        
        self.canvas.itemconfig(self.image, image=sequence[counter])
        try:
            self.canvas.delete('ctr_txt')
        except:
            print('no text to delete')
        fn = os.path.split(self.img_list[self.cur_img])[1]
        item = self.cur_img+1
        num_items = len(self.img_list)
        zoom_perc = '{}%'.format(int(self.abs_ratio*100))
        if self.rand_order:
            r_flag = '\nR'
            height = 13
        else:
            r_flag = ''
            height = 5
        counter_text = '{}({}/{} ({}){}'.format(fn,item,num_items,zoom_perc,r_flag)
        text_item = self.canvas.create_text(5,height,fill='lightblue',anchor='w',font='times 10 bold',text=counter_text,tag='ctr_txt')
        bbox = self.canvas.bbox(text_item)
        rect_item = self.canvas.create_rectangle(bbox,fill='black',tag='ctr_txt')
        self.canvas.tag_raise(text_item,rect_item)
        
        self.img_window.after(self.delay, lambda: self.animate((counter+1) % len(sequence),sequence))
            
            

root = tk.Tk()
# root.attributes('-fullscreen', True)
app = App(root)
root.mainloop()
