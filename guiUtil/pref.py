'''
Created on Jan 21, 2017

@author: chris
'''

import getpass
import h5py
import numpy as np
import os
import platform
import re
import sys
import traceback
from PyQt5.Qt import *

class pref( object ):
    '''
    preference class similar to matlab preferences for python
    '''
    if platform.system() == "Linux":
        DEFAULT_FILE= "/home/" + getpass.getuser() + "/.pypref.h5"
    else:
        DEFAULT_FILE= "C:\\pypref.h5"
        
    DEF_GROUPSTR= "default"
    DEF_COMPRESSION= "gzip"
    
    def __init__( self, file= DEFAULT_FILE, compression= DEF_COMPRESSION ):
        """
        -- file is the name of the h5 file name
        -- compression--uses gzip compression
        """
        self.file= file
        self.compression= compression
        
        try:
            pass
            #with h5py.File( self.file, 'w', compression= self.compression ) as f:
        except Exception as e:
            traceback.print_exc()
            self._typicalErrorDLG( str(e) )
            sys.exit()
    
    def _typicalErrorDLG( self, exc= None ):
        """
        not sure if this is necessary yet
        """
        qapp= QApplication( sys.argv )
        qm= QMessageBox()
        if exc is None:
            exc= ""
        qm = QMessageBox(QMessageBox.Critical, "Pref error.", "Preferences Critical Issue: " + exc )
#             qm.setStandardButtons(QMessageBox.Ok);
        qm.setIcon( QMessageBox.Critical )
        qm.show()
        qapp.exec_()
    
    def _saveHelper( self, f, procStr, data ):
        """
        for recursive call for lists
        """
        tData= type( data )
        if procStr in f:
            del f[procStr]
        
        # string or list of strings
        singleNpArray= isinstance( data, np.ndarray ) and len( data.shape ) == 0
            
        if isinstance( data, str ) or ( isinstance( data, list ) and _entireListIsStrings( data, type( str() ) ) ):  
                
            if isinstance( data, list ):
                maxLenS= [1]
                asciiList = [ _stringListEncoderHelper( n, maxLenS ) for n in data ]
                f.create_dataset( procStr, (len(asciiList),1), \
                                  dtype= "S" + str( maxLenS[0] ), data= asciiList, \
                                  compression= self.compression )
            else:
                if data == "":
                    assert False, "Unable to save \"\" within file"
                f.create_dataset( procStr, dtype= "S" + str(len(data)), \
                                  data= np.string_( data ) )

        elif _numeric_type( data ) or \
            tData == type( np.array(np.nan) ) or \
            singleNpArray:
            if _numeric_type( data ) or singleNpArray:
                comp= None 
            else:
                comp= self.compression
                
            f.create_dataset( procStr, data= data, compression= comp )
                
    # end _saveHelper    
    
    def load( self, group= DEF_GROUPSTR, name= None, default= None, returnDict= True ):
        """
        read data from the h5 file
        """
        if not isinstance( name, list ): # name is not list
            name= [ name ]
            assert not isinstance( default, list ), "if name is list default must be"
            default= [ default ]
        else: # name is list
            if default is None:
                default= [ None for i in np.arange( len( name ) ) ]
            else:
                assert len( default ) == len( name ), "length mismatch on name and default"
        
        procStrList= [ _joinGroupAndName( group, aName ) for aName in name ]
        self._saveDefaultsIfNotInFile( group, procStrList, default )
        
        try:        
            with h5py.File( self.file, 'r' ) as f:
                tmpList= []
                if len( procStrList ) == 1:
                    tmpList= self._loadHelper( f, procStrList[0], default )
                else:
                    tmpList= [ self._loadHelper( f, aProcStr, default ) for aProcStr in procStrList ]
    
                if returnDict == True:
                    if len( procStrList ) == 1:
                        return { procStrList[0]: tmpList }
                    else:
                        return { procStrList[jj]: tmpList[jj] for jj in np.arange( len(procStrList) ) }
                else:
                    return tmpList
        except:
            traceback.print_exc()
            sys.exit()
    # end load

    def _loadHelper( self, f, procStr, default ):     
            
        dset= f[ procStr ]
        if re.search("S", str( dset.dtype ) ):
            if len( dset.shape ) > 0:
                return [ str(np.array(dset[idx]).astype( np.unicode )[0]) 
                        for idx in np.arange( dset.shape[0] ) ]
            else:
                return str( np.array(dset).astype( np.unicode ) )
            
        elif dset.dtype == "int64" or dset.dtype == "float64" or dset.dtype == "bool":
            return np.array( dset )
    
    # end _loadHelper

    def _saveDefaultsIfNotInFile( self, group, procStrList, defaultList ):
        anyNone= [ True for jj in defaultList if jj is not None ]
        
        procStrList2Save= []
        dataList= []
        if len( anyNone ) > 0:
            try:
                with h5py.File( self.file, 'a' ) as f:
                    
                    [ _saveDefaultHelper( procStrList2Save, dataList, procStrList[i], defaultList[i] )
                     for i in np.arange( len(procStrList) ) 
                     if ( defaultList[i] is not None ) and ( procStrList[i] not in f ) ]
                    
                    f.close()
            except:
                traceback.print_exc()
                sys.exit()
                
        assert len(procStrList2Save) == len( dataList ), "lists unequal lengths--something is wrong"
        if len( procStrList2Save ) > 0:
            self.save( group= "", name= procStrList2Save, data= dataList )
    
    #end _saveDefaultsIfNotInFile    
        
    def save( self, group= DEF_GROUPSTR, name= None, data= None ):
        """
        save data method
        -- group saves data in that h5 group
        -- name is the name of the hdf5 dataset
        -- data is the data getting saved
        """
        assert data is not None, "data must be populated"
        with h5py.File( self.file, 'a' ) as f:
            try:
                procStrList, data= _dataConfigurationHelper( group, name, data )
                [ self._saveHelper( f, procStr, data[idx] ) for idx, procStr in enumerate( procStrList ) ]
                
                f.flush()
            except:
                traceback.print_exc()
                sys.exit()
    # end save

    def delete( self, group= DEF_GROUPSTR, name= None ):
        "delete data from the preference file"
        if not os.path.exists( self.file ):
            return
        
        if name is None:
            name= ""
            group= _procGroupStr( group )
            
            try:
                with h5py.File( self.file, 'a', compression= self.compression ) as f:
                    if group in f:
                        del f[ group ]
            except:
                traceback.print_exc()
                sys.exit()
        else:
            procStrList, _ = _dataConfigurationHelper( group, name, None )
            try:
                with h5py.File( self.file, 'a', compression= self.compression ) as f:
                    for aProcStr in procStrList:
                        if aProcStr in f:
                            del f[ aProcStr ]
            except:
                traceback.print_exc()
                sys.exit()

def _dataConfigurationHelper( group, name, data ):
    dataNotNone= data is not None # added since the method is reused by save and by delete
    assert isinstance( group, str ), "group must be string"
    if isinstance( name, list ):
        if dataNotNone: 
            assert isinstance( data, list ), "if name list, then data must be list"
    else:
        name= [ name ]
        if dataNotNone:
            data= [ data ]
    
    procStrList= [ _joinGroupAndName( group, aName ) for aName in name ]    
    
    return procStrList, data    
        
def _saveDefaultHelper( procStrList, dataList, aProcStr, aDefault ):
    procStrList.append( aProcStr )
    dataList.append( aDefault )

def _entireListIsStrings( inData, inType ):
    """
    check type of entire list to make sure strings before saving
    """
    assert isinstance( inData, list ), "Must be list type for function"
    assert np.all( [ isinstance( aData, str ) for aData in inData ] )
    return True
            
def _stringListEncoderHelper( n, maxLenS ):
    """
    helper method for string encoding for list iterator
    """
    maxLenS[0]= max( maxLenS[0], len( n ) )
    return n.encode( "ascii", "ignore" )

def _numeric_type( data ):
    return isinstance( data, int ) or \
           isinstance( data, float ) or \
           isinstance( data, bool )

def _joinGroupAndName( group, name ):
    """
    join group with name
    """
    assert isinstance( group, str ), "group must be string...list not yet supported"
    if group == "":
        return name.strip()
    else:
        return _procGroupStr( group.strip() ) + "/" + name.strip()
    
def _procGroupStr( groupStr ):
    """
    Ensure proper formatting of group string
    """
    groupStr= groupStr.strip()
    while groupStr.endswith("/"):
        groupStr= groupStr[:-1]
    
    return groupStr    
    
if __name__ == "__main__":
    prefObj= pref()        
    prefObj.set( "testGroup1", "dat", "asdfasdf" )
    a= prefObj.get( "testGroup1", "dat" )
    print( a )