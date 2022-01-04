# -*- coding: utf-8 -*-
"""
Created on Sat Jan  1 17:02:33 2022

@author: jmatt
"""

import backup_dir as BD
from argparse import ArgumentParser
import os



# from_dir = r'P:\t'
# to_dir = r'P:\t_bkup'



def main():
    """Highest-level function. Called by user.
    
    sample calls:

    Parameters:
        None

    Returns:
        None
    """

    ### Initialize argument parser
    parser = ArgumentParser()

    ### Add arguments to parser
    parser.add_argument('-f_dir', dest='from_dir', default="None")
    parser.add_argument('-t_dir', dest='to_dir', default="None")
    args = parser.parse_args()
    
    #Pull the source and destination directories from the argument parser
    from_dir = args.from_dir
    to_dir = args.to_dir
    
    print('\nIN PYTHON')
    print('From dir: {}'.format(from_dir))
    print('To dir: {}'.format(to_dir))
    
    
    if to_dir == 'CD':
        with open(os.path.join(from_dir,'.bkup_settings'),'r') as f:
            lines = f.readlines()
            
        to_dir = lines[0].strip()
        
    elif (from_dir == "None") or (to_dir == "None"):
        from_dir = 'P:\\'
        to_dir = 'Q:\\'
        print('Using default directories')
        
    print('Backing up: \n    {}\nto\n    {}'.format(from_dir,to_dir))
    
    bdo = BD.backup_dirs(from_dir,to_dir)
    bdo.backup()
    




if __name__ == '__main__':
    main()
