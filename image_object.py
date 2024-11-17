from PIL import Image, ImageTk, ImageSequence, ImageOps, ImageFile, ImageEnhance
ImageFile.LOAD_TRUNCATED_IMAGES = True
import os
import copy as cp

class IMAGE:
    def __init__(self, image_fn, img_window_width, img_window_height, fit_to_canvas):
        self.image_fn = image_fn
        
        self.img_window_width = img_window_width
        self.img_window_height = img_window_height

        self.rotation = 0

        self.fit_to_canvas = fit_to_canvas

        #Set the max/min steps in the zoom cycle
        self.MAX_ZOOM = 15
        self.MIN_ZOOM = -15
        
        # Initialize the scaling/zoom table
        self.mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.mux[n] = round(self.mux[n-1] * 1.1, 5)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.mux[n] = round(self.mux[n+1] * 0.9, 5)

        # Initialize the brightness table
        self.brightness_mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.brightness_mux[n] = round(self.brightness_mux[n-1] * 1.1, 5)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.brightness_mux[n] = round(self.brightness_mux[n+1] * 0.9, 5)
            
        # Initialize the contrast table
        self.contrast_mux = {0 : 1.0}
        for n in range(1,self.MAX_ZOOM+1,1):
            self.contrast_mux[n] = round(self.contrast_mux[n-1] * 1.1, 5)

        for n in range(-1, self.MIN_ZOOM-1, -1):
            self.contrast_mux[n] = round(self.contrast_mux[n+1] * 0.9, 5)

        self.reset_zoomcycle()
        self.open_image()
        
    def update_zoom(self,event,x,y):
        #Increment or decrement the zoom step based on the mouse wheel
        #movement
        updated = True
        if (event.delta > 0 and self.zoomcycle < self.MAX_ZOOM):
            self.zoomcycle += 1
        elif (event.delta < 0 and self.zoomcycle > self.MIN_ZOOM):
            self.zoomcycle -= 1
        else:
            print('Max/Min zoom reached!')
            updated = False

        print('Zoom updated: {}'.format(updated))
        self.update_bbox_zoom(x,y)
        self.gen_sequence()
        return updated
        
    def reset_zoomcycle(self,bright_contrast_reset=True):
        #Set the gif frame rate to default
        self.delay = 20
        #Set the zoomcycle position to default
        self.zoomcycle = 0
        if bright_contrast_reset:
            self.brightcycle = 0
            self.contrastcycle = 0
        #Reset the variables tracking movement of the bounding box to zero
        self.bbox_dx = 0
        self.bbox_dy = 0
        #Set the anchor to the upper left of the image and reset the bounding
        #box flag to false
        self.bbox_anchor = [0,0]
        self.bbox = False

    def init_bbox(self):
        #indicate that bbox exists
        self.bbox = True
        #Set the crop box coordinates
        self.crop_bbox = [0,0,self.img_width,self.img_height]
        #Set the initial bbox anchor at the upper left of the image
        self.bbox_anchor = [0,0]
        #Set the bounding box width and height to the image dimensions
        self.bbox_width = self.new_img_width
        self.bbox_height = self.new_img_height
        
        #Find the width of the crop box
        self.crop_width = self.crop_bbox[2] - self.crop_bbox[0]
        self.crop_height = self.crop_bbox[3] - self.crop_bbox[1]
     
    def update_bbox_pan(self,dx,dy):
        #Update the viewable area after mouse drag
        
        #Update the bbox anchor based on how far the mouse was dragged
        self.bbox_anchor[0] -= dx
        self.bbox_anchor[1] -= dy
        
        #Prevent the anchor from being set past the left side of the image
        if self.bbox_anchor[0] < 0:
            self.bbox_anchor[0] = 0
            
        #Prevent the anchor from being set past the top of the image
        if self.bbox_anchor[1] < 0:
            self.bbox_anchor[1] = 0
            
        #Prevent the anchor from being set past the right side of the image
        if self.bbox_anchor[0] + self.bbox_width > self.new_img_width:
            self.bbox_anchor[0] = self.new_img_width - self.bbox_width
            
        #Prevent the anchor from being set past the bottom of the image
        if self.bbox_anchor[1] + self.bbox_height > self.new_img_height:
            self.bbox_anchor[1] = self.new_img_height - self.bbox_height
            
        #Update the crop box
        self.update_crop_box()
        self.gen_sequence()

    def update_bbox_zoom(self,x,y):
        #Store the distance between the left edge and top of the canvas before
        #the zoom.  Needed to find the position of the mouse relative to the
        #image prior to zoom.
        prev_img_edge = [(self.img_window_width-self.bbox_width)/2,(self.img_window_height-self.bbox_height)/2]
        #Store the previous width and height of the zoomed image in a list for iterating
        prev_img_wh = [self.new_img_width,self.new_img_height]
        #Update the width & height of the image & store in a list for iterating
        self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
        self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
        cur_img_wh = [self.new_img_width,self.new_img_height]
        
        #Update the absolute zoom ratio (the starting zoom if image zoomed/shrunk
        #to fit the canvas times the zoomcycle zoom)
        self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
        
        #Update the bounding box width and height (the width and height of the
        #image display area in units of canvas pixels) and stor in a list for 
        #iterating
        self.bbox_width = min(self.new_img_width,self.img_window_width)
        self.bbox_height = min(self.new_img_height,self.img_window_height)
        cur_bbox_wh = [self.bbox_width,self.bbox_height]
        
        #Store the position of the mouse in a list for iterating
        cur_mouse_xy = [x,y]
        
        #Iterate over width and height
        for i in range(2):
            #Determine the location of the mouse relative to the image before
            #the zoom occurred
            prev_mouse_pix = (cur_mouse_xy[i]-prev_img_edge[i]+self.bbox_anchor[i])
            #Move the center of the bounding box to the mouse location
            new_center = prev_mouse_pix*cur_img_wh[i]/prev_img_wh[i]
            #Update the location of the bounding box anchor relative to the
            #mouse location
            self.bbox_anchor[i] = new_center-cur_bbox_wh[i]/2
        
        #Check that the bounding box does not extend past the edges of the zoomed
        #image
        if self.bbox_anchor[0] < 0:
            self.bbox_anchor[0] = 0
        if self.bbox_anchor[1] < 0:
            self.bbox_anchor[1] = 0
        if self.bbox_anchor[0] + self.bbox_width > self.new_img_width:
            self.bbox_anchor[0] = self.new_img_width - self.bbox_width
        if self.bbox_anchor[1] + self.bbox_height > self.new_img_height:
            self.bbox_anchor[1] = self.new_img_height - self.bbox_height
        
        #Update the crop box
        self.update_crop_box()
    
    def update_crop_box(self):
            
        #Update the location of the crop box anchor.  This converts the bbox_anchor
        #from zoomed_image_coordinates to original_image_coordinates based
        #on the original/zoomed width and height ratios
        crop_bbox_anchor = [
            self.bbox_anchor[0]*(self.img_width/self.new_img_width),
            self.bbox_anchor[1]*self.img_height/self.new_img_height]
        
        #Calculate the height and width of the crop box
        self.crop_height = self.bbox_height/self.abs_ratio
        self.crop_width = self.bbox_width/self.abs_ratio
        
        #Set the crop box coordinates
        self.crop_bbox[0:2] = crop_bbox_anchor
        self.crop_bbox[2] = crop_bbox_anchor[0]+self.crop_width
        self.crop_bbox[3] = crop_bbox_anchor[1]+self.crop_height
        
        #Convert the crop box coordinates to integers
        self.crop_bbox = [int(round(item)) for item in self.crop_bbox]

    def open_image(self):
        if isinstance(self.image_fn,type(None)):
            self.sequence = None
        else:
            if os.path.isfile(self.image_fn):
                self.has_open_image=True
                #Set the rotation to default of zero
                self.rotation = 0
                #Open the image file
                self.open_image = Image.open(self.image_fn)
                #Find the width/height of the raw image file
                (self.img_width, self.img_height) = self.open_image.size
                
                #Set the flag to indicate that an image is already loaded (to avoid
                #unnecessary disk accesses)
                self.new_image = False
                #init a placeholder for self.sequence
                self.sequence = 'generate sequence'
                self.img_missing = False
            else:
                self.sequence = False
                self.img_missing = True

            self.gen_sequence()

    def gen_sequence(self):
        if not (isinstance(self.sequence,type(None)) or self.img_missing):
            #Extract the raw frames in the image
            img_frames_raw = ImageSequence.Iterator(self.open_image)
            
            #Rotate/crop/resize the image as necessary
            img_frames = self.resize_img(img_frames_raw)
            
            #Build the sequence of frames in the image and return the sequence
            self.sequence = [ImageTk.PhotoImage(img) for img in img_frames]
            self.img_missing = False
        
    def close(self,dummy=None):
        self.open_image.close()
        
    def resize_img(self,frames):
        
        #If a bounding box does not exist
        if not self.bbox:
            #Calculate the zoom ratio required to fit the image to the canvas
            self.ratio = min(self.img_window_width/self.img_width,self.img_window_height/self.img_height)
            #If the zoom required to fit is more than 200%, set to 200%
            if self.ratio>2:
                self.ratio=2 
                
            #If the image should be fit to the canvas or if the image is larger
            #than the canvas, calculate new image width/height values.  Otherwise
            #use the actual image width/height
            if self.fit_to_canvas or self.ratio < 1:
                self.new_img_width = int(self.img_width*self.ratio*self.mux[self.zoomcycle])
                self.new_img_height = int(self.img_height*self.ratio*self.mux[self.zoomcycle])
            else:
                self.new_img_width = self.img_width
                self.new_img_height = self.img_height
                self.ratio = 1
            #Calculate the absolute zoom ratio and initialize the bounding box
            self.abs_ratio = self.ratio*self.mux[self.zoomcycle]
            self.init_bbox()
        
        for frame in frames:
            #Make a copy of the frame
            thumbnail = frame.copy()
            
            if self.rotation != 0:
                #Rotate the image
                thumbnail = thumbnail.rotate(self.rotation, expand=1, center=None, translate=None)
                # thumbnail.save('rotate_{}.jpg'.format(self.rotation))
            
            if (self.crop_width<self.img_width) or (self.crop_height<self.img_height):
                #Crop the image to the coordinates of the crop box
                thumbnail = thumbnail.crop(self.crop_bbox)
                
            if self.brightcycle != 0:
                enhancer = ImageEnhance.Brightness(thumbnail)
                thumbnail = enhancer.enhance(self.brightness_mux[self.brightcycle])
                
            if self.contrastcycle != 0:
                enhancer = ImageEnhance.Contrast(thumbnail)
                thumbnail = enhancer.enhance(self.contrast_mux[self.contrastcycle])
            
            #Resize the cropped image to the bounding box width and height
            thumbnail = thumbnail.resize((self.bbox_width,self.bbox_height),Image.LANCZOS)
            # thumbnail.save('thumbnail.jpg')
            #Return the rotated, cropped, resized image
            yield thumbnail
        
    def rotate(self,rotation):
        #update the rotation
        #+90 ==> clockwise
        #-90 ==> counter clockwise
        self.rotation += rotation
        #Store the sign of the rotation direction for use after the mod
        if self.rotation == 0:
            sign = 1
        else:
            sign = self.rotation/abs(self.rotation)
        #Restrict the rotation to -360:360
        self.rotation %= sign*360
        #convert to integer
        self.rotation = int(self.rotation)
        
        #Swap the height and the width dimensions of the image
        temp = cp.deepcopy(self.img_height)
        self.img_height = cp.deepcopy(self.img_width)
        self.img_width = temp
        #reset the zoom and bounding box
        self.reset_zoomcycle(False)
        #Display the image
        self.gen_sequence()

    def adjust_contrast(self,adjustment):
        #Decrement the contrast step
        if (self.contrastcycle > self.MIN_ZOOM) and (self.contrastcycle < self.MAX_ZOOM):
            self.contrastcycle += adjustment
            #Regenerate the sequence
            self.gen_sequence()
        else:
            if self.contrastcycle == self.MIN_ZOOM:
                print('Min contrast!')
            else:
                print('Max contrast!')
                
    def adjust_brightness(self,adjustment):
        #Decrement the contrast step
        if (self.brightcycle > self.MIN_ZOOM) and (self.brightcycle < self.MAX_ZOOM):
            self.brightcycle += adjustment
            #Regenerate the sequence
            self.gen_sequence()
        else:
            if self.brightcycle == self.MIN_ZOOM:
                print('Min brightness!')
            else:
                print('Max brightness!')
        
    def brightness_up(self,dummy=None):
        #Increment the brightness step
        if self.brightcycle < self.MAX_ZOOM:
            self.brightcycle += 1
        else:
            print('Max brightness!')
            return
        
        #Display the image
        self.init_image()
