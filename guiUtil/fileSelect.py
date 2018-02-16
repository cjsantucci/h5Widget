'''
Created on Feb 4, 2017

@author: chris
'''

import guiUtil
import guiUtil.guidata as gdat
import os
from PyQt5.Qt import *
import re
import numpy as np

class pb_combo_selector( object ):
    '''
    create a group of buttons to aid in selecting files
    Keeps a history around
    '''

    def __init__( self, selectDir= False, historyLength= 10, \
                  persistentDir= None, persistentFile= None, prefGroup= None, \
                  caption= "", buttonstr= "", guiDataObj= None, \
                  defaultFileList= None, groupSubCat= None, \
                  allowBlankSelection= False ):
        '''
        Constructor
        '''
        
        self.historyLength= historyLength
        self.caption= caption
        self.selectDir= selectDir
        self.allowBlankSelection= allowBlankSelection

        self.guiData= self._createGuiData( guiDataObj, groupSubCat, defaultFileList, \
                                           prefGroup, persistentDir, persistentFile )
        
        self._initStartDir()
                
        self._setupComboBox()
        self._setupPushButton( buttonstr )
    
    def _setupPushButton( self, buttonstr ):
#         self.ComboBox.setEditable( True )
        self.PushButton= QPushButton( buttonstr )
        self.PushButton.clicked.connect( self._buttonPushed )
    
    def _setupComboBox( self ):
        self.ComboBox= QComboBox()
        p= self.ComboBox.palette()
        self.ComboBox.setAutoFillBackground( True );
        p.setColor( self.ComboBox.backgroundRole(), Qt.black )    
        self.ComboBox.setPalette( p )
        
        self.guiData.fileList= [ anElement for anElement in self.guiData.fileList if not anElement.replace(" ","") == "" ]
        self.guiData.fileList.append( "" )
        self.ComboBox.addItems( self.guiData.fileList )
        
        # leave this last so that it will not grab the item data and save un-necessarily on init
        self.ComboBox.currentIndexChanged.connect( self._selectionchange )
    
    def _createGuiData( self, guiDataObj, groupSubCat, defaultFileList, \
                        prefGroup, persistentDir, persistentFile ):
        
        if defaultFileList is None:
            defaultFileList= [""]
            
        
        if guiDataObj is not None:
            guiData= gdat.guiData( guiDataObj= guiDataObj, groupSubCat= groupSubCat, \
                                   initDefaultDict= { "fileList": defaultFileList } )
        else:
            guiData= gdat.guiData( persistentDir= persistentDir, \
                                   persistentFile= persistentFile, \
                                   prefGroup= prefGroup, \
                                   groupSubCat= groupSubCat, \
                                   initDefaultDict= { "fileList": defaultFileList }  )

        if not isinstance( guiData.fileList, list ):
            guiData.fileList= [ guiData.fileList ]
        
        return guiData
    
    def getComboItems( self ):
        return [ self.ComboBox.itemText(i) 
                for i in range( self.ComboBox.count() ) ]
    
    def _initStartDir( self ):
        """
        start directory for file selection dialog
        """
        self.startDir= ""
        if not self.selectDir and len( self.guiData.fileList ) > 0:
            if os.path.isdir( os.path.dirname( self.guiData.fileList[0] ) ):
                self.startDir= os.path.dirname( self.guiData.fileList[0] )
                              
        elif  len( self.guiData.fileList ) > 0:
            if os.path.isdir( self.guiData.fileList[0] ):
                self.startDir= self.guiData.fileList[ 0 ]
    
    def _selectionchange( self ):
        """
        needed to resave the most recent order based on click
        """
        
        # needed for weird state changes
        if self.ComboBox.count() == 0:
            return 
        
        fileList= [ self.ComboBox.itemText( i ) for i in range( self.ComboBox.count() ) ]        
        
        tmp= fileList[ 0 ]
        fileList[ 0 ]= self.ComboBox.currentText()
        
        if fileList[ 0 ].strip() == "" and not self.allowBlankSelection:
            self.ComboBox.setCurrentIndex(0)
            return        
        
        fileList[ self.ComboBox.currentIndex() ]= tmp
        
        if fileList[-1] != "":
            fileList.append( "" )
        
        self.guiData.fileList= fileList
        self.guiData.save( "fileList" )
    
    def _buttonPushed( self ):
        """
        saves the list if a new file was selected.
        """
        
        qfd= QFileDialog()
        
        passDir= ""
        if len( self.guiData.fileList ) > 0 and self.guiData.fileList[0] != "":
            if not self.selectDir:
                passDir= os.path.dirname( self.guiData.fileList[0] )
            else:
                passDir= self.guiData.fileList[ 0 ]
            
        if self.selectDir:
            fileName= qfd.getExistingDirectory( caption= self.caption, directory= self.startDir )
        else:
            fileName= qfd.getOpenFileName( caption= self.caption, directory= self.startDir )
        
        if isinstance( fileName, tuple ):
            fileTypeSelectedAllowed= fileName[1]
            fileName= fileName[0]
        
        """if the selection is blank and blanks are not allowed than exit"""
        if fileName.strip() == "" and not self.allowBlankSelection:
            return
        
        """if the old selection is in the list remove as we will re-add""" 
        while fileName in self.guiData.fileList:
            self.guiData.fileList.remove( fileName )
        
        """remove blanks"""
        tList= []
        for anElement in self.guiData.fileList:
            if not anElement.strip() == "":
                tList.append( anElement )
        self.guiData.fileList= tList
        
        """insert the selection into the front of the list"""
        self.guiData.fileList.insert( 0, fileName )
        
        """limit the total selections to the history length"""
        self.guiData.fileList= self.guiData.fileList[ :self.historyLength-1 ]
        
        """put a blank at the end if they are allowed"""
        if self.allowBlankSelection and self.guiData.fileList[0].strip() != "":
            self.guiData.fileList.append( "" )
            
        self.guiData.save( "fileList" )
        
        self.ComboBox.clear()
        self.ComboBox.addItems( self.guiData.fileList )
#             self.ComboBox.
    
def fileSelectRemember( guiData, startDirField, \
                        grabDirectory= False, \
                        regex= "", \
                        multipleFiles= True, \
                        caption= "",\
                        fileListFilter= "All Files (*)" ):
    
    qfd= QFileDialog()
    if multipleFiles:
        qfd.setFileMode( QFileDialog.ExistingFiles )
#         QAbstractItemView::MultiSelection
        qfd.setNameFilters( [ fileListFilter ] )
    
    selDir= None 
    if grabDirectory:
        startDir= getattr( guiData, startDirField )[0]
        if not os.path.isdir( startDir ):
            startDir= guiUtil.gUBase.home()
        
        selDir= qfd.getExistingDirectory( caption= caption, directory= startDir )
        if os.path.isdir( selDir ):
            setattr( guiData, startDirField, [ os.path.dirname( selDir ) ] )
            guiData.save( startDirField )
            
        fileNames= []
        for root, dirs, files in os.walk( selDir ):
            for aFile in files:
                tFile= os.path.join( root, aFile )
                if regex.strip() != "" and re.match( regex, tFile ):
                    fileNames.append( tFile )
                elif tFile.endswith( ".py" ):
                    fileNames.append( tFile )
    else:
        startDir= getattr( guiData, startDirField )[0]

        if not os.path.isdir( startDir ):
            startDir= guiUtil.gUBase.home()
        fileNames= qfd.getOpenFileNames( caption= "select exe(s)", directory= startDir )
    
    if isinstance( fileNames, tuple ):
        fileTypeSelectedAllowed= fileNames[1]
        fileNames= fileNames[0]
    
    else:
        fileNames= [ aFile for aFile in fileNames 
                    if aFile.endswith( ".py" ) or
                    regex.strip() != "" and re.match( regex, aFile )
                   ]
    
    if len( fileNames ) == 0:
        return
    
    modeDir= _getModeDir( fileNames ) 
    if len( modeDir ) > 0: 
        setattr( guiData, startDirField , [ modeDir ] )
        guiData.save( startDirField ) 
    
    if selDir is not None: # selected files not directories
        modeDir= _getModeDir( fileNames )
        if len( modeDir ) > 0:
            setattr( guiData, startDirField, [ modeDir ] )
            guiData.save( startDirField )
    
    if len( fileNames ) == 0:
        return
    
    return fileNames
    
def _getModeDir( fileNames ):
    unqDirNames= []
    [ unqDirNames.append( os.path.dirname( aFile ) ) for aFile in fileNames if os.path.dirname( aFile ) not in unqDirNames ]
    
    countIdxList= [0]*len(unqDirNames)
    for aFile in fileNames:
        idx= unqDirNames.index( os.path.dirname( aFile ) )
        countIdxList[ idx ] += 1
    
    modeDir= unqDirNames[ np.where( countIdxList == np.max(countIdxList) )[0][0] ]
    
    return modeDir        
        