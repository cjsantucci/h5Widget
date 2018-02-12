'''
Created on Sep 9, 2017

@author: chris
'''

from guiUtil import fileSelect as fs
from guiUtil.guidata import guiData
from guiUtil.gUBase import gUWidgetBase
import numpy as np
from PyQt5.Qt import *

import sys

class fileSelectList( QListWidget, gUWidgetBase ):
    '''
    classdocs
    '''

    def __init__( self, parent= None, listRect= None, \
                  clearButtonLoc= None, dupListItems= False, **kwargs ):
        
        QListWidget.__init__( self, parent, **kwargs )
        gUWidgetBase.__init__( self, **kwargs )
        
        self.dupListItems= dupListItems
        
        """Multiple selections allowed"""
        self.setSelectionMode( QAbstractItemView.ExtendedSelection )
        
        if listRect is None:
            listRect= QRect( 50, 50, 300, 500 )
        self._setupLayout( listRect , clearButtonLoc= clearButtonLoc )
        
        idd= { "fileList": [""] }
        self._initGuiData( idd= idd, **kwargs )
        
        self._rememberOldList()

    def resetGuiDefaults( self ):
        self.guiData.resetStoredDefaults()
        self._storeListItemStrings()
        self._clearButtonPushed( selectedOverride= True )
        self._rememberOldList()

    def _rememberOldList( self ):
        if self.guiData.fileList == self.guiData.getDefaultDict()["fileList"]:
            return
        
        self._addListItems( self.guiData.fileList )

    def _addListItems( self, inStrList ):
        assert isinstance( inStrList, list ), "input must be list"
        for aStr in inStrList:
            assert isinstance( aStr, str ), "Input must be string"
        
        currentItemListText= [ self.item( itemIdx ).text() for itemIdx in range( self.count() ) ]
        
        for aStr in inStrList:
            if ( not self.dupListItems and aStr not in currentItemListText ) or \
                self.dupListItems:
                item = QListWidgetItem( self )
                item.setText( aStr.strip() )
        
        self._storeListItemStrings()
        
    def _storeListItemStrings( self ):
        itemTextList= [ self.item( itemIdx ).text() for itemIdx in range( self.count() ) ]
        if len( itemTextList ) == 0:
            itemTextList= self.guiData.getDefaultDict()["fileList"].copy()
            
        self.guiData.fileList= itemTextList
        self.guiData.save( "fileList" )

    def _setupLayout( self, listRect, clearButtonLoc= None ):
        
        self.setGeometry( QRect( listRect.left(), listRect.top(),\
                                   listRect.width()+2, listRect.height()+2 ) )
        
        self.clearButton= QPushButton( "Clear", self.parent() )
        self.clearButton.move( *clearButtonLoc )
        self.clearButton.clicked.connect( self._clearButtonPushed )

    def _clearButtonPushed( self, selectedOverride= False ):
        itemListIdxs= list( range( self.count() ) )
        itemListIdxs.reverse()
        
        sel= [ self.item( anItemNumber ).isSelected() for anItemNumber in itemListIdxs ]
        anySelected= np.any( sel )
        
        for anItemNumber in itemListIdxs:
            tItem= self.item( anItemNumber )
            if anySelected and tItem.isSelected() or selectedOverride:
                self.takeItem( anItemNumber )
            elif not anySelected:
                self.takeItem( anItemNumber )
        
        self._storeListItemStrings()

if __name__ == "__main__":
    
    app= QApplication([])
    qmw= QMainWindow()
    qmw.setMinimumSize(400, 600)
    fileSelectList( parent= qmw, listRect= QRect( 50, 50, 300, 500 ), \
                    clearButtonLoc= (175, 380)  )
     
    qmw.show()
    sys.exit( app.exec_() )