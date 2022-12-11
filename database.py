# -*- coding: utf-8 -*-
"""
Created on Sat Nov 12 13:52:38 2022

@author: jerem
"""

import sqlite3 as sql
import settings


conn = sql.connect(settings.file_database)

c = conn.cursor()

c.execute("""CREATE TABLE hashes (
    hash 
    )
          """)