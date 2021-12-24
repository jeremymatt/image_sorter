# -*- coding: utf-8 -*-
"""
Created on Fri Dec  3 17:20:55 2021

@author: jmatt
"""

import getpass

pwd = getpass.getpass('Enter password')

guess = None
while guess != 'e':
    if guess == None:
        guess = getpass.getpass('Enter guess (e for exit): ')
    else:
        if guess == pwd:
            guess = getpass.getpass('\r{} is Correct!!! Try again? (e for exit): '.format(guess))
        else:
            guess = getpass.getpass('\r{} is WRONG!!!!! Try again? (e for exit): '.format(guess))