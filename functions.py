# -*- coding: utf-8 -*-
"""
Created on Sun Nov 21 21:32:49 2021

@author: jmatt
"""

import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

plt.rcParams.update({'font.size': 22})
# def interpolate(x,y,xval):
#     if xval in x:
#         yval = y[x==xval].mean()
#     else:
#         if 
   
    
xval=2
x = np.array([0,1,1.5,3,4,3.75,3.5,5,6,7,8,9])
y = np.array([0,1,2,3,4,2,1,1.25,2,4,6,7])
# plt.plot(x,y)


f2 = interp1d(x,y,kind='cubic')
f = interp1d(x,y,kind='linear')


xnew = np.linspace(0,9,50)
fig,ax = plt.subplots(1,1,figsize=(20,20))
plt.plot(x, y, 'o', xnew, f(xnew), '-', xnew, f2(xnew), '--')
plt.legend(['data', 'linear', 'cubic'], loc='best')
plt.show()
