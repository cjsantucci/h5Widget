'''
Created on Feb 16, 2018

@author: chris
'''
import functools as ft
import matplotlib.pyplot as plt
import numpy as np
import unittest

from jpExtend.plotUpdater import updateListElement as uLE

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass


    def testUpdateListElementClass( self ):
        
        f, ax= plt.subplots( 1, 1 )
        plt.plot([1,2],[1,2])
        
        uLE( ax= ax, xAlign= np.array([1,2]) )
        uLE( ax= ax, xAlign= np.array([1,2]), xRange=np.array([1,2,3]))
        uLE( ax= ax, xAlign= np.array([1,2]), xRange=np.array([1,2,3]))
        uleObj= uLE( ax= ax, updateMethod= dummyMethod )
        uleObj.update( 3 )
        uleObj= uLE( ax= ax, updateMethod= ft.partial( dummyMethod, fakeKeyword= 5 ) )
        uleObj.update( 4 )

def dummyMethod( frame, fakeKeyword= 0 ):
    print( "dummy: " + str(fakeKeyword) )
    print( frame )

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testUpdateListElementClass']
    unittest.main()