# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 20:09:45 2021

@author: jmatt
"""


from argparse import ArgumentParser


import os


try:
    import settings
except:
    import temp_settings as settings


import imghdr

class App:
    def __init__(self,source_dir):
        
        self.source_dir = source_dir
        

        
    def get_img_list(self):
        
        
        
        dirs_to_process = [self.source_dir]
        self.img_list = []
        ctr = 0
        prev_text_len = 0
        while len(dirs_to_process)>0:
            
            # print('point1')
            #Pop directory from list to process
            cur_dir = dirs_to_process.pop()
                    
            # print('point2')
            #Display progress
            ctr +=1
            txt = '{} dirs checked ({} dirs remaining).  Found {} images'.format(ctr,len(dirs_to_process),len(self.img_list))
            padding = ' '*(prev_text_len - len(txt))
            prev_text_len = len(txt)
            
            print('\r{}{}'.format(txt,padding),end="")
            
            
            # print('point3')
            #list of all files in the directory
            new_files = [file for file in os.listdir(cur_dir) if os.path.isfile(os.path.join(cur_dir,file))]
            
            # print('point4')
            #Add absolute path to the file names
            new_files = [os.path.join(cur_dir,file) for file in new_files]
            
            # print('point5')
            #Check if file is an image file
            new_files = [file for file in new_files if imghdr.what(file) != None]
            # print('point6')
            #Add new images to the image list
            self.img_list.extend(new_files)
            
            
            # print('point7')
            #Recursively include subdirectories
            if settings.include_sub_dirs:
                #Add subdirectories in the current directory to the directories to check
                new_dirs = [item for item in os.listdir(cur_dir) if os.path.isdir(os.path.join(cur_dir,item))]
                dirs_to_process.extend([os.path.join(cur_dir,item) for item in new_dirs])
        
        
        self.img_list.sort()
            
       
    
    def remove_empty_dirs(self,dummy = None):
        #Init the number of dirs and removed dirs counters
        self.num_dirs = 1
        self.num_removed = 0
        #Call recursive rmdirs function on source dirs
        self.rmdirs(self.source_dir)
        self.show_text_window('COMPLETED\nRemoving empty directories from:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,self.display_txt))
       
                    
    def rmdirs(self,cur_dir):  
        #Display progress
        self.display_txt = '{} checked, {} removed'.format(self.num_dirs,self.num_removed)
        self.show_text_window('Removing empty directories from:\n     {}\n\n{}\n\nEnter to close'.format(self.source_dir,self.display_txt))
       
        #List the items in the directory print
        dir_list = os.listdir(cur_dir)
        #Store the files and subdirectories in separate lists
        new_files = [file for file in dir_list if os.path.isfile(os.path.join(cur_dir,file))]
        new_dirs = [os.path.join(cur_dir,item) for item in dir_list if os.path.isdir(os.path.join(cur_dir,item))]
        #For each subdirectory, increment the counter and call the rmdirs function
        for new_dir in new_dirs:
            self.num_dirs += 1
            self.rmdirs(new_dir)
        
        #After checking all subdirectories, re-list the directory and 
        #list any remaining directories
        dir_list = os.listdir(cur_dir)
        non_empty_dirs = [item for item in dir_list if os.path.isdir(os.path.join(cur_dir,item))]
        #If there are no files files and no remaining subdirectories, remove
        #the directory and increment the counter
        if (len(new_files)+len(non_empty_dirs)) == 0:
            os.rmdir(cur_dir)
            self.num_removed += 1
            
          
            
    def write_file_list(self):
        #Write the image list to file
        file_list_fn = os.path.join(self.source_dir,'.img_files_list')
        
        with open(file_list_fn,'w', encoding='utf-8') as file:
            for fn in self.img_list:
                file.write('{}\n'.format(fn))
                
  
app = App(r"P:\img\test2")
app.get_img_list()

# def main():
#     """Highest-level function. Called by user.
    
#     sample calls:

#     Parameters:
#         None

#     Returns:
#         None
#     """

#     ### Initialize argument parser
#     parser = ArgumentParser()

#     ### Add arguments to parser
#     parser.add_argument('-s_dir', dest='source_dir', default=r"P:\img")
#     parser.add_argument('-d_dir', dest='dest_root', default="None")
#     args = parser.parse_args()
    
#     #Pull the source and destination directories from the argument parser
#     source_dir = args.source_dir

#     app = App(source_dir)
#     app



# if __name__ == '__main__':
#     main()