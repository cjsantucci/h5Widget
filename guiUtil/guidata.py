'''z
Created on Feb 3, 2017

@author: chris
'''

from guiUtil.pref import pref
import os
import re
import warnings

class guiData( object ):
    """
    class with functionality for storing default data options
    the default dictionary will have a data fields which can be stored in persistent memory
    if the data has been overwritten and saved, the underlying preference object will load the most recently
    saved value, rather than the default value.
    
    called a recent on the defaults will overwrite the old defaults. 
    """
    def __init__( self, persistentDir= None, persistentFile= None, \
                  prefGroup= None, guiDataObj= None, \
                  initDefaultDict= None, groupSubCat= None ):
        """
        -Must define the directory, file and group.
        -if the guiDataObj is defined, then the copy constructor uses only these fields
        and NOT any of the data.
        - if initDefault dict is defined, it laods the values from disk/persistent memory
        """
        if guiDataObj is not None:
            assert groupSubCat is not None, "When using copy constructor must define groupSubCat" 
            # copy constructor, use the same file as the other guy
            persistentDir= guiDataObj.persistentDir
            persistentFile= guiDataObj.persistentFile
            prefGroup= guiDataObj.prefGroup + "/" + groupSubCat
        else:
            assert persistentFile is not None, "must define persistent file" 
            assert prefGroup is not None, "must define prefGroup"
            assert prefGroup != "", "must define prefGroup as non empty string"
            if groupSubCat is not None:
                prefGroup= prefGroup + "/" + groupSubCat
        
        self.prefGroup= prefGroup
        self.persistentDir= ""
        self.persistentFile= persistentFile
        if persistentDir is not None:
            self.persistentDir= persistentDir
            prefFile= os.path.join( persistentDir, persistentFile )
        else:
            prefFile= os.environ[ 'HOME' ]
    
        self._prefObj= pref( file= prefFile )
        
        self._loadedDefaults= list()
        self._defDict= dict()
        if initDefaultDict is not None:
            self.addAndStoreDefaults( initDefaultDict )
            
        
    def deletePrefFile( self ):
        os.system( "rm -f " + self.prefFile )
    
    def getPrefFile( self ):
        return self.prefObj.file
    
    def getDefaultDict( self ):
        return self._defDict.copy()
            
    def setDefaultDict( self, inDict ):
        """
        resets awareness of which defaults have already been saved to disk
        """
        self._defDict= inDict
        self._loadedDefaults= list()
    
    def addDefaults( self, inDict ):
        self._defDict.update( inDict )

    def addAndStoreDefaults( self, inDict ):
        self.addDefaults( inDict )
        self.storeUnloadedDefaultsOnly()
        
    def storeUnloadedDefaultsOnly( self ):
        """
        1. determine which defaults have not been loaded from pref file
        2. keep track of the loaded by adding to _loadedDefaults
        3. load them, BUT only overwrite in the self dictionary if 
           that field DNE in self already. Send warning if not
        """
        
        unStoredKeys= [ aKey 
                      for aKey in self._defDict.keys() 
                      if aKey not in self._loadedDefaults ]
        if len( unStoredKeys ) == 0:
            return
        
        # keep track of what has been loaded
        [ self._loadedDefaults.append( aKey ) for aKey in unStoredKeys ]
        
        # get the data  
        data= [ self._defDict[ aKey ] for aKey in unStoredKeys ] 
        
        # loading only unloaded
        tempDict= self._prefObj.load( group= self.prefGroup, \
                               name= unStoredKeys, default= data )
        
        # add if already not a field
        addDict= { aKey.split("/")[-1]: tempDict[aKey] 
                  if aKey not in self.__dict__ 
                  else warnings.warn( "\"" + aKey + "\" is already stored in the data, " + \
                                      "Will not updated this field with unstored default" )
                  for aKey in tempDict  }
        
        self.__dict__.update( addDict )
    
    def resetSelfWithDefaults( self ):
        """
        over-write any property with the defaults 
        """
        self.__dict__.update( self._defDict )
        
    def resetStoredDefaults( self ):
        """
        save the defaults to the file and update my dictionary with the defaults
        """
        keys= list( self._defDict.keys() )
        data= [ self._defDict[ aKey ] for aKey in keys ]
        
        self.prefObj.save( group= self.prefGroup, name= keys, data= data )
        self.resetSelfWithDefaults()
        
    def save( self, propList= None ):
        """
        save a list
        if no list provided save all properties without an underscore
        """
        if propList is None:
            # props which do not begin with underscore
            propList= [ aKey 
                       for aKey in self.__dict__.keys() 
                       if aKey.split("_")[0].strip() != "" ]
            
        elif type( propList ) == type( str() ):
            propList= [ propList ]
            
        data= [ getattr( self, aProp ) 
               if aProp in self.__dict__ 
               else warnings.warn( "\"" + aProp + "\" not able to be saved, not a property" )
               for aProp in propList ]
        
        self.prefObj.save( group= self.prefGroup, name= propList, data= data )
        
    def getPrefObj( self ):
        return self._prefObj
    
    prefFile= property( getPrefFile )
    defDict= property( getDefaultDict, setDefaultDict )   
    prefObj= property( getPrefObj )