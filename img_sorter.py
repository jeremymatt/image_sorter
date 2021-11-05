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


try:
    import settings
except:
    import temp_settings as settings

from shutil import move

import imghdr

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
        
        self.trash_dest = os.path.join(settings.dest_root,'.temp_trash')
        if not os.path.isdir(self.trash_dest):
            os.makedirs(self.trash_dest)
        
        self.get_img_list()
        
        self.previous_images = []
        
        self.cur_img = 0
        self.rand_order = settings.random_display_order
        self.fit_to_canvas = True
        self.new_image = True
        self.delay = 20
        self.default_window_width = 500
        self.default_window_height= 500
        self.img_window = None
        self.has_compare_window = False
        self.zoomcycle = 0
        self.bbox_dx = 0
        self.bbox_dy = 0
        self.bbox_anchor = [0,0]
        self.move_events = []
        self.show_menu = False
        self.keep_both = False
        self.keep_new = False
        self.keep_existing = False
        self.processing_duplicates = False
        self.full_screen = settings.start_fullscreen
        if self.full_screen:
            self.img_window_width = self.screen_width
            self.img_window_height = self.screen_height
        else:
            self.img_window_width = self.default_window_width
            self.img_window_height = self.default_window_height
        
        self.reset_zoomcycle()
        self.img_window = self.parent
        self.set_keybindings(self.parent)
        
        self.init_first_image()
        
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
            new_files = [os.path.join(cur_dir,file) for file in new_files]
            new_files = [file for file in new_files if imghdr.what(file) != None]
            self.img_list.extend(new_files)
            
            if settings.include_sub_dirs:
                new_dirs = [item for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
                dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
            
            
        
    def show_menu_window(self,dummy=None):
        self.menu_window = tk.Toplevel(self.parent)
        canvas = tk.Canvas(self.menu_window,height=1000,width=500)
        canvas.pack()
        menu_txt = self.gen_menutext()
        text_item = canvas.create_text(
            25,
            25,
            fill='black',
            font='times 10 bold',
            text=menu_txt,tag='menu_txt',
            anchor=tk.NW)
        bbox = canvas.bbox(text_item)
        dim = (bbox[2]-bbox[0]+100,bbox[3]-bbox[1]+100)
        self.menu_window.geometry(f'{dim[0]}x{dim[1]}+0+0')
        canvas.move(text_item,25,25)
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
        window.bind("<MouseWheel>",self.zoomer)
        window.bind("<Control-z>",self.undo)
        window.bind("<Control-q>",self.quit_app)
        window.bind("<F12>",self.toggle_rand_order)
        window.bind("<Escape>",self.quit_app)
        window.bind("<Control-r>",self.reload_img)
        window.bind('<Alt-m>',self.toggle_menu)
        window.bind('<KeyRelease>',self.keyup)
        window.bind('1',self.set_keep_new_flag)
        window.bind('2',self.set_keep_existing_flag)
        window.bind('3',self.set_keep_both_flag)
        window.bind('<End>',self.close_img_compare_window)
        
    def set_keep_new_flag(self,dummy=None):
        if self.processing_duplicates:
            self.keep_new = True
            self.move_file()
        
    def set_keep_existing_flag(self,dummy=None):
        if self.processing_duplicates:
            self.keep_existing = True
            self.move_file()
        
    def set_keep_both_flag(self,dummy=None):
        if self.processing_duplicates:
            self.keep_both = True
            self.move_file()
        
        
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
        if self.processing_duplicates:
            print('ERROR: processing duplicates')
        if (key in settings.move_dict.keys()) and not self.processing_duplicates:
            self.dest_dir = settings.move_dict[key]
            if not os.path.isdir(self.dest_dir):
                os.makedirs(self.dest_dir)
            self.move_file()
        
    def quit_app(self,dummy=None):
        if os.path.isdir(self.trash_dest):
            files = [os.path.join(self.trash_dest,file) for file in os.listdir(self.trash_dest)]
            for file in files:
                os.remove(file)
            os.rmdir(self.trash_dest)
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
                
                menu_txt = ''
                
                menu_txt += 'Esc ==> Quit\n'
                menu_txt += 'Alt+M ==> Toggle this menu\n'
                menu_txt += 'End ==> cancel move\n'
                menu_txt += '1 ==> keep new image and delete old image\n'
                menu_txt += '2 ==> keep old image and delete new image\n'
                menu_txt += '3 ==> rename new image and keep both\n'
            else:
                
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
            
    def show_img_compare_window(self,files=None):
        if self.has_compare_window:
            self.img_compare_window.destroy()
        self.has_compare_window = True
        if len(files)==2:
            new_file,existing_file = files
            self.open_compare_window(new_file,existing_file)
        else:
            print('Expected 2 files, got {}'.format(len(filest = ())))
        
    def close_img_compare_window(self,dummy=None):
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
        file = self.img_list[self.cur_img]
        orig_fn = os.path.split(self.img_list[self.cur_img])[1]
        fn_parts = orig_fn.split('.')
        if len(fn_parts) != 2:
            print('WARNING: UNEXPECTED NUMBER OF FILENAME PARTS\n  file not moved')
            return
        
        dest_files = [file for file in os.listdir(self.dest_dir) if os.path.isfile(os.path.join(self.dest_dir,file))]
        
        if not self.processing_duplicates:
            self.dest_fn = orig_fn
        
        if (self.dest_fn in dest_files) or self.processing_duplicates:
            self.processing_duplicates = True
            if not any([self.keep_both,self.keep_existing,self.keep_new]):
                self.move_ctr = 1
                self.show_img_compare_window((file,os.path.join(self.dest_dir,os.path.join(self.dest_dir,self.dest_fn))))
            else:
                if self.keep_both:
                    self.keep_both = False
                    self.dest_fn = '{}({}).{}'.format(fn_parts[0],self.move_ctr,fn_parts[1])
                    if self.dest_fn in dest_files:
                        self.move_ctr+=1
                        self.show_img_compare_window((file,os.path.join(self.dest_dir,os.path.join(self.dest_dir,self.dest_fn))))
                    else:
                        self.close_img_compare_window()
                        self.open_image.close()
                        dest_file = os.path.join(self.dest_dir,self.dest_fn)
                        moved_files = [(file,dest_file)]
                        self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
                        
                        move(file,dest_file)
                        self.update_img_list(file)
                        
                        
                elif self.keep_existing:
                    self.close_img_compare_window()
                    self.open_image.close()
                    
                    trash_dest_fn = os.path.join(self.trash_dest,orig_fn)
                    move(file,trash_dest_fn)
                    moved_files = [(file,trash_dest_fn)]
                    self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
                    self.update_img_list(file)
                    
                elif self.keep_new:
                    self.close_img_compare_window()
                    self.open_image.close()
                    
                    trash_dest_fn = os.path.join(self.trash_dest,self.dest_fn)
                    existing_file = os.path.join(self.dest_dir,self.dest_fn)
                    moved_files = [(existing_file,trash_dest_fn)]
                    move(existing_file,trash_dest_fn)
                    
                    dest_file = os.path.join(self.dest_dir,self.dest_fn)
                    moved_files.append((file,dest_file))
                    move(file,dest_file)
                    
                    self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
                    self.update_img_list(file)
        else:
            dest_file = os.path.join(self.dest_dir,self.dest_fn)
            moved_files = [(file,dest_file)]
            self.move_events.append((moved_files,cp.deepcopy(self.cur_img),cp.deepcopy(self.img_list)))
            
            move(file,dest_file)
            self.update_img_list(file)
            
            
    def update_img_list(self,file):
        
        self.img_list.remove(file)
        if self.cur_img >= len(self.img_list):
            self.cur_img = 0
            
        self.new_image = True
        self.open_image.close()
        self.reset_zoomcycle()
        self.init_image()
        
        
    def undo(self,dummy=None):
        moved_files,self.cur_img,self.img_list = self.move_events.pop()
        while len(moved_files)>0:
            moved_from,moved_to = moved_files.pop()
            move(moved_to,moved_from)
        self.reset_zoomcycle()
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def zoomer(self,event):
        if (event.delta > 0 and self.zoomcycle < self.MAX_ZOOM):
            self.zoomcycle += 1
        elif (event.delta < 0 and self.zoomcycle > self.MIN_ZOOM):
            self.zoomcycle -= 1
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
        self.reset_zoomcycle()
        
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
        self.close_img_compare_window()
        self.reset_zoomcycle()
        if self.rand_order:
            step = random.randint(0,len(self.img_list)-2)
            self.previous_images.append(self.cur_img)
        else:
            step = 1
        self.cur_img = (self.cur_img+step) % len(self.img_list)
        self.new_image = True
        self.open_image.close()
        self.init_image()
        
    def load_prev_img(self,dummy=None):
        self.close_img_compare_window()
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
        self.delay = 20
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
        prev_img_edge = [(self.img_window_width-self.bbox_width)/2,(self.img_window_height-self.bbox_height)/2]
        prev_img_wh = [self.new_img_width,self.new_img_height]
        self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
        self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
        cur_img_wh = [self.new_img_width,self.new_img_height]
        
        self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
        
        self.bbox_width = min(self.new_img_width,self.img_window_width)
        self.bbox_height = min(self.new_img_height,self.img_window_height)
        cur_bbox_wh = [self.bbox_width,self.bbox_height]
        
        cur_mouse_xy = [self.mouse_x,self.mouse_y]
        
        for i in range(2):
            prev_mouse_pix = (cur_mouse_xy[i]-prev_img_edge[i]+self.bbox_anchor[i])
            new_center = prev_mouse_pix*cur_img_wh[i]/prev_img_wh[i]
            self.bbox_anchor[i] = new_center-cur_bbox_wh[i]/2
        
        self.bbox_ratio_x = (self.img_window_width/self.bbox_width)*self.mux[self.zoomcycle]
        self.bbox_ratio_y = (self.img_window_height/self.bbox_height)*self.mux[self.zoomcycle]
        
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
        
        self.crop_height = self.bbox_height/self.abs_ratio
        self.crop_width = self.bbox_width/self.abs_ratio
        
        self.crop_bbox[0:2] = crop_bbox_anchor
        self.crop_bbox[2] = crop_bbox_anchor[0]+self.crop_width
        self.crop_bbox[3] = crop_bbox_anchor[1]+self.crop_height
        
        self.crop_bbox = [int(round(item)) for item in self.crop_bbox]
            
        
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
            self.bbox = None
        img_frames_raw = ImageSequence.Iterator(self.open_image)
        
        img_frames = self.resize_img(img_frames_raw)
        
        
        sequence = [ImageTk.PhotoImage(img) for img in img_frames]
        
        return sequence
    
    def gen_compare_sequence(self,iterator,w,h):
        
        
        ratio = min(self.default_window_width/w,self.default_window_height/h)
        if ratio>2:
            ratio=2 
                
        new_w = int(w*ratio)
        new_h = int(h*ratio)
        
        for frame in iterator:
            thumbnail = frame.copy()
                
            thumbnail = thumbnail.resize((new_w,new_h),Image.LANCZOS)
            yield thumbnail
        
    def open_compare_window(self,new_file,existing_file):
        
        
        self.new_file = Image.open(new_file)
        self.existing_file = Image.open(existing_file)
        self.iterator_new = ImageSequence.Iterator(self.new_file)
        self.iterator_existing = ImageSequence.Iterator(self.existing_file)
        
        new_width,new_height = Image.open(new_file).size
        existing_width,existing_height = Image.open(existing_file).size
        
        self.new_sequence = self.gen_compare_sequence(self.iterator_new,new_width,new_height)
        self.existing_sequence = self.gen_compare_sequence(self.iterator_existing,existing_width,existing_height)
            
        self.new_sequence = [ImageTk.PhotoImage(img) for img in self.new_sequence]
        
        self.existing_sequence = [ImageTk.PhotoImage(img) for img in self.existing_sequence]
        
        self.img_compare_window = tk.Toplevel(self.parent)
        
        self.img_compare_window.bind("<MouseWheel>",self.zoomer)
        self.img_compare_window.bind('<Motion>',self.motion)
        self.img_compare_window.bind("<Control-q>",self.quit_app)
        self.img_compare_window.bind("<Escape>",self.quit_app)
        self.img_compare_window.bind('1',self.set_keep_new_flag)
        self.img_compare_window.bind('2',self.set_keep_existing_flag)
        self.img_compare_window.bind('3',self.set_keep_both_flag)
        self.img_compare_window.bind('<End>',self.close_img_compare_window)
        
        compare_width = 2*self.default_window_width+5
        self.img_compare_window.geometry(f'{compare_width}x{self.default_window_height}+100+100')
            
        self.img_compare_window.configure(background='white')
        
        new_canvas = tk.Canvas(
            self.img_compare_window,
            height=self.default_window_height,
            width=self.default_window_width,
            bg='black',
            highlightthickness=0)
        new_canvas.place(x=0, y=0,anchor=tk.NW)
        
        
        
        existing_canvas = tk.Canvas(
            self.img_compare_window,
            height=self.default_window_height,
            width=self.default_window_width,
            bg='black',
            highlightthickness=0)
        existing_canvas.place(x=self.default_window_width+5, y=0,anchor=tk.NW)
        
        new_image = new_canvas.create_image(
            int(self.default_window_width/2),
            int(self.default_window_height/2), 
            image=self.new_sequence[0],
            tag='new_img')
        
        txt = '{}({}x{}'.format(new_file,new_width,new_height)
        text_item = new_canvas.create_text(5,5,fill='lightblue',anchor='w',font='times 10 bold',text=txt,tag='new_txt')
        bbox = new_canvas.bbox(text_item)
        rect_item = new_canvas.create_rectangle(bbox,fill='black',tag='new_txt')
        new_canvas.tag_raise(text_item,rect_item)
        
        text_item = new_canvas.create_text(int(self.default_window_width/2),self.default_window_height-25,fill='lightblue',anchor=tk.S,font='times 20 bold',text='1',tag='new_txt')
        bbox = new_canvas.bbox(text_item)
        rect_item = new_canvas.create_rectangle(bbox,fill='blue',tag='new_txt')
        new_canvas.tag_raise(text_item,rect_item)
        
        existing_image = existing_canvas.create_image(
            int(self.default_window_width/2),
            int(self.default_window_height/2), 
            image=self.existing_sequence[0],
            tag='new_img')
        
        txt = '{}({}x{}'.format(existing_file,existing_width,existing_height)
        text_item = existing_canvas.create_text(5,5,fill='lightblue',anchor='w',font='times 10 bold',text=txt,tag='ex_txt')
        bbox = existing_canvas.bbox(text_item)
        rect_item = existing_canvas.create_rectangle(bbox,fill='black',tag='ex_txt')
        existing_canvas.tag_raise(text_item,rect_item)
        
        text_item = existing_canvas.create_text(int(self.default_window_width/2),self.default_window_height-25,fill='lightblue',anchor=tk.S,font='times 20 bold',text='2',tag='ex_txt')
        bbox = existing_canvas.bbox(text_item)
        rect_item = existing_canvas.create_rectangle(bbox,fill='blue',tag='ex_txt')
        existing_canvas.tag_raise(text_item,rect_item)
        
        
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
        
        inputs = new_canvas,existing_canvas,both_canvas,new_image,existing_image
        self.animate_compare(0,0,inputs)
        
        
    
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
        self.img_window.lift()
        
        if self.has_compare_window:
            self.img_compare_window.lift()
        
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
            main_window = True
            inputs = (self.canvas,self.img_window,self.image,main_window)
            self.animate(0,sequence,inputs)
            
        
    def animate(self, counter,sequence,inputs):
        canvas,img_window,image,main_window = inputs
        
        canvas.itemconfig(image, image=sequence[counter])
        
        if main_window:
            try:
                canvas.delete('ctr_txt')
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
            counter_text = '{}({}/{} ({}:{}){}'.format(fn,item,num_items,self.zoomcycle,zoom_perc,r_flag)
            text_item = canvas.create_text(5,height,fill='lightblue',anchor='w',font='times 10 bold',text=counter_text,tag='ctr_txt')
            bbox = canvas.bbox(text_item)
            rect_item = canvas.create_rectangle(bbox,fill='black',tag='ctr_txt')
            canvas.tag_raise(text_item,rect_item)
        
        img_window.after(self.delay, lambda: self.animate((counter+1) % len(sequence),sequence,inputs))
        
        
        
    def animate_compare(self, new_counter,existing_counter,inputs):
        new_canvas,existing_canvas,both_canvas,new_img,existing_img = inputs
        
        new_canvas.itemconfig(new_img, image=self.new_sequence[new_counter])
        existing_canvas.itemconfig(existing_img, image=self.existing_sequence[existing_counter])
        tk.Misc.lower(new_canvas)
        tk.Misc.lower(existing_canvas)
        tk.Misc.lift(both_canvas)
        
        new_counter = (new_counter+1) % len(self.new_sequence)
        existing_counter = (existing_counter+1) % len(self.existing_sequence)
        self.img_compare_window.after(self.delay, lambda: self.animate_compare(new_counter,existing_counter,inputs))
            
            

root = tk.Tk()
root.attributes('-fullscreen', True)
app = App(root)
root.mainloop()
