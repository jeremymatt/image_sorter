# -*- coding: utf-8 -*-
"""
Created on Sat Jan  1 17:02:33 2022

@author: jmatt
"""

import backup_dir as BD

from_dir = r'P:\t'
to_dir = r'P:\t_bkup'
from_dir = 'J:\\'
to_dir = 'K:\\'

bdo = BD.backup_dirs(from_dir,to_dir)

# print('rmdirs:\n{}'.format(bdo.rmdir_list))
# print('del list:\n{}'.format(bdo.delete_list))
# print('cp lst:\n{}'.format(bdo.copy_list))