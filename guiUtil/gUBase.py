'''
Created on Jul 23, 2017

@author: chris
'''
import os
from PyQt5.Qt import *

from guiUtil.guidata import guiData

class gUWidgetBase( object ):

    def __init__( self, guiDataOverride= None, **kwargs ):
        
        self.qmw= None
        self.onStartup= False
        self.closeOnFinish= False
        self.app= None
        self.prefDir= None
        '''
        Constructor
        '''
        
#         super( gUWidgetBase, self ).__init__()
        
        if guiDataOverride is not None:
            assert isinstance( guiDataOverride, dict ), "kwargs not correct type"
        
        self._assignKW( kwargs )
    
    def _assignKW( self, kwargs ):
        for aKey in kwargs:
            if hasattr( self, aKey ):
                setattr( self, aKey, kwargs[ aKey ] )
            elif not aKey[0] == "_" and len( aKey.lstrip("_") ) == len( aKey )- 1:
                if hasattr( self, "_" + aKey ):
                    setattr( self, aKey, kwargs[ aKey ] )

    def kwargCheck( self, inKey, kw, inCheck= None ):
        if inKey in kw.keys():
            if inCheck is None:
                return True
            elif kw[ inKey ] == inCheck:
                return True
        
        return False
        
    def _initGuiData( self, idd= None, persistentDir= None, persistentFile= None, prefGroup= None, **kwargs ):
        assert idd is not None, "must define initial data dict"    
        
        guiDataObj= guiData( persistentDir= persistentDir, \
                               persistentFile= persistentFile, \
                               prefGroup= prefGroup, \
                               initDefaultDict= idd )
        
        self.guiData= guiDataObj
    
    def getQApp( self ):
        return QCoreApplication.instance()  
    
    def setQApp( self, inApp ):
        pass
        
    def centerOfScreenForCurrentMouse( self ):
        frameGm = self.frameGeometry()
        screen = QApplication.desktop().screenNumber( QApplication.desktop().cursor().pos() )
        centerPoint = QApplication.desktop().screenGeometry( screen ).center()
        return centerPoint
    
    app= property( getQApp, setQApp )

def home():
    if os.name == "nt":
        assert False, "DEFINE HOME FOR WINDOWS"
    else:
        return os.environ["HOME"]
 
def dictOverride( d1, d2, popOrig= False ):
    popKeys= []
    for aKey in d1:
        if aKey in d2:
            d2[ aKey ]= d1[ aKey ]
            popKeys.append( aKey )
    
    if popOrig:
        for aKey in popKeys:
            d1.pop( aKey )
    