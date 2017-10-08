'''
Created on Jan 25, 2017

@author: chris
'''

import h5py
from guiUtil import pref as p
import inspect
import numpy as np
import os
from random import randint
import traceback
import unittest


class test_pypref(unittest.TestCase):


    def setUp( self ):
        self.selfPath= os.path.dirname( inspect.stack()[0][1] )
        self.unitTestDir= os.path.join( self.selfPath, "testDir" )
        self.testFile= os.path.join( self.unitTestDir, "test.h5" )
        if os.path.exists( self.unitTestDir ):
            self.tearDown()  
        os.mkdir( self.unitTestDir )

    def tearDown( self ):
        try:
            if os.path.exists( self.unitTestDir ):
                os.system( "rm -rf " + self.unitTestDir )
        except Exception as e:
            traceback.print_exc()

    def testSaveNums( self ):
        pObj= p.pref( file= self.testFile )
        pObj.save( name= "num1", data= 1 );
        pObj.save( name= "num1", data= 1 );
        pObj.save( name= "num2", data= 2.0 );
        pObj.save( name= "num2", data= 2.0 );
        self.assertTrue( type( pObj.load( name= "num1", returnDict= False ) ) == np.ndarray )
        self.assertTrue( pObj.load( name= "num1", returnDict= False ).dtype == "int64" )
        self.assertTrue( pObj.load( name= "num1", returnDict= False ) == 1 )
        self.assertTrue( type( pObj.load( name= "num2", returnDict= False ) ) == np.ndarray )
        self.assertTrue( pObj.load( name= "num2", returnDict= False ).dtype == "float64" )
        self.assertTrue( pObj.load( name= "num2", returnDict= False ) == 2 )

        pObj.save( group= "yummy", name= "num2", data= 2.0 );
        self.assertTrue( pObj.load( group= "", name= "yummy/num2", returnDict= False ) == 2 )
        self.assertTrue( type( pObj.load( group= "", name= "yummy/num2", returnDict= False ) ) == np.ndarray )
        self.assertTrue( pObj.load( group= "", name= "yummy/num2", returnDict= False ).dtype == "float64" )
        
        self.assertTrue( type( pObj.load( group= "yummy", name= "num2", returnDict= False ) ) == np.ndarray )
        self.assertTrue( pObj.load( group= "yummy", name= "num2", returnDict= False ).dtype == "float64" )

    def testSaveString( self ):
        pObj= p.pref( file= self.testFile )
        pObj.save( name= "str1", data= "blahblahblah" )
        myStr= pObj.load( name= "str1", returnDict= False )
        self.assertTrue( myStr == "blahblahblah" )
        
    def testSaveNaN( self ):
        pObj= p.pref( file= self.testFile )
        pObj.save( name= "blah", data= np.NAN )
        data= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( np.isnan( data ) )
        
    def testSaveListOfString( self ):
        pObj= p.pref( file= self.testFile )
        pObj.save( name= "blah", data= "asdfasdfasdf" )
        data= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( data == "asdfasdfasdf" )
        pObj.save( name= "blah", data= ["aaasdfasdfasdfasdf","b","c","d","easdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdf"])
        data= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( data == ["aaasdfasdfasdfasdf","b","c","d","easdfasdfasdfasdfasdfasdfasdfasdfasdfasdfasdf"] )
        pObj.save( name= "blah", data= ["a","b","c","d","e"] )
        data= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( data == ["a","b","c","d","e"] )
        
    def testMatrix( self ):
        pObj= p.pref( file= self.testFile )
        
        x= np.array( [(1,2),(3,4)] )
        pObj.save( name= "blah", data= x )
        xRead= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( np.all( xRead == x ) )
        
        y= np.array( [ (1, 2, 3), \
                      (4, 5, 6), \
                      (5, 6, 7) \
                      ] )
        pObj.save( name= "blah", data= y )
        yRead= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( np.all( y == yRead ) )    
#         np.array()
    
    def testBigStringList( self ):
        pObj= p.pref( file= self.testFile )
        saveStr= [ _randomString( 16 ) for i in np.arange( 500 ) ]
        pObj.save( name= "blah", data= saveStr )
        pObj.save( name= "blah", data= saveStr )
        readStr= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( saveStr == readStr )

    def test_saveAndloadListOfMatrices( self ):
        pObj= p.pref( file= self.testFile )
        x= np.array( [(1,2),(3,4)] )
        y= np.array( [ (1, 2, 3), \
                      (4, 5, 6), \
                      (5, 6, 7) \
                      ] )
        pObj.save( name= [ "blue", "blah" ], data= [ x, y ] )
        xRead= pObj.load( name= "blue", returnDict= False )
        yRead= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( np.all(x==xRead) and np.all(y==yRead) )
        
        listRead= pObj.load( name= [ "blue", "blah" ], returnDict= False )
        
        self.assertTrue( np.all(x==listRead[0]) and \
                         np.all(y==listRead[1]) )
    
    def test_saveBool( self ):
        pObj= p.pref( file= self.testFile )
        pObj.save( name= "blah", data= True )
        readBool= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( readBool == True )
    
    def test_default( self ):
        pObj= p.pref( file= self.testFile )
        data= pObj.load( name= "blah", default= True, returnDict= False )
        self.assertTrue( data==True )
        
        # this means it is has been saved
        data= pObj.load( name= "blah", returnDict= False )
        self.assertTrue( data==True )
        
        x= np.array( [(1,2),(3,4)] )
        dataList= [ True, "yay", x ]
        data= pObj.load( name= [ "blah", "blue", "blend" ],\
                        default= dataList, returnDict= False )
        
        boolList= [ np.all( dataList[i] == data[i] ) 
                   if type( dataList[i] ) == type( np.array([]) )
                   else dataList[i] == data[i] 
                   for i in np.arange( len(dataList) ) ]
        
        self.assertTrue( np.all( boolList ) )
        
        # This will ensure they were saved
        data= pObj.load( name= [ "blah", "blue", "blend" ], returnDict= False )
        boolList= [ np.all( dataList[i] == data[i] ) 
                   if type( dataList[i] ) == type( np.array([]) )
                   else dataList[i] == data[i] 
                   for i in np.arange( len(dataList) ) ]
        
        self.assertTrue( np.all( boolList ) )
    
    def test_returnDictionary( self ):
        pObj= p.pref( file= self.testFile )
        dataList= [ True, False, 1 ]
        nameList= [ "blah", "blue", "blend" ]
        _= pObj.load( group= "", name= nameList, \
                         default= dataList )
        dataDict= pObj.load( group= "", name= nameList, \
                         default= dataList )
                
        for aKey, anElement in zip( nameList, dataList ):
                self.assertTrue( dataDict[ aKey ] == anElement )
                
        pObj.save( group= "", name= "blah", \
                 data= ["asdf","basdf"] )
        
        dataDict= pObj.load( group= "", name= "blah" )
        self.assertTrue( dataDict[ "blah" ] == ["asdf","basdf"] ) 

                
    def test_delete( self ):
        pObj= p.pref( file= self.testFile )
        dataList= [ True, False, 1 ]
        nameList= [ "blah", "blue", "blend" ]
        _= pObj.load( group= "", name= nameList, \
                         default= dataList )
        
        _= pObj.load( name= nameList, \
                         default= dataList )
        
        pObj.delete( group= "", name= nameList )
        with h5py.File( pObj.file, 'r', compression= pObj.compression ) as f:
            for aName in nameList:
                self.assertTrue( aName not in f )   
            self.assertTrue( pObj.DEF_GROUPSTR in f )
            fullNameList= [ p._joinGroupAndName( pObj.DEF_GROUPSTR, aName ) 
                           for aName in nameList ]
            for aName in fullNameList:
                self.assertTrue( aName in f )
            
        pObj.delete( name= nameList )
        with h5py.File( pObj.file, 'r', compression= pObj.compression ) as f:
            for aName in fullNameList:
                    self.assertTrue( aName not in f )
    
    def test_saveListOfStringsWithStringName( self ):
        pass
#         pObj= p.pref( file= self.testFile )
#         pObj.save( name= "blah" , data= ['asdf','dfgh'] )
#         data= pObj.load( name= "blah" )
#         pObj.save( name= [ "blah" ], data= [['asdf','dfgh']] )
#         data= pObj.load( name= "blah" )
#         pObj.save( name= "blah" , data= ['asdf','dfgh'] )
#         data= pObj.load( name= "blah" )
#         print()
    
def _randomString( lenStr ):
    tList= [ chr( randint(95, 109) ) for i in np.arange( lenStr ) ]
    return "".join( tList )
    
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
    
#     tpObj= test_pypref()
#     tpObj.setUp()
#     tpObj.testMatrix()
#     tpObj.tearDown()
    print()