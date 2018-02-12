'''
Created on Sep 23, 2017

@author: chris
'''

import functools as ft
import numpy as np
import os
from PyQt5.Qt import *
import re
import subprocess as subp
from threading import Thread
import traceback

import guiUtil
from guiUtil.guidata import guiData
from guiUtil.gUBase import gUWidgetBase
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil.simpleDialogs import App

class boxWidget( QWidget, gUWidgetBase ):
    '''
    classdocs
    '''
    def __init__( self, parent, \
                  leftRect= None, leftClearButtonLoc= None, \
                  leftPrefGroup= None, \
                  rightRect= None, rightClearButtonLoc= None, \
                  rightPrefGroup= None, \
                  boxPrefGroup= None, \
                  **kwargs ):

        QWidget.__init__( self, parent, **kwargs )
        gUWidgetBase.__init__( self, **kwargs )

        self._initGuiData( prefGroup= boxPrefGroup, **kwargs )

        self.fsl1    = fileSelectList( self, listRect= leftRect, \
                          clearButtonLoc= leftClearButtonLoc, \
                          prefGroup= leftPrefGroup, \
                          **kwargs )
          
        self.fsl2    = fileSelectList( self, listRect= rightRect, \
                          clearButtonLoc= rightClearButtonLoc, \
                          prefGroup= rightPrefGroup, \
                          **kwargs )
        
        self._createOtherWidgetMembers()
        
        self._setupLayout()
    
    def _initGuiData( self, persistentDir= None, persistentFile= None, prefGroup= None, **kwargs ):
        
        idd= { "startDir": [ guiUtil.gUBase.home() ], \
              "startDir2": [ guiUtil.gUBase.home() ], \
               "xDataVar": "MCLOCK", \
               "diraddRE": ".py$", \
                }
        
        guiDataObj= guiData( persistentDir= persistentDir, \
                               persistentFile= persistentFile, \
                               prefGroup= prefGroup, \
                               initDefaultDict= idd )
        
        self.guiData= guiDataObj
        
    def _save_LE_Data( self, leObjStr, saveStr ):
        leObj= getattr( self, leObjStr )
        
        leObj.setText( leObj.text().strip() )
        setattr( self.guiData, saveStr, leObj.text().strip() )
        if getattr( self.guiData, saveStr ) != "":
            self.guiData.save( saveStr )
    
    def _createOtherWidgetMembers( self ):
        self.pbr= QPushButton( "->" )
        self.pbr.clicked.connect( self._push2Right )
        self.pbl= QPushButton( "<-" )
        self.pbl.clicked.connect( self._remFromRight )
        
        self.fb= QPushButton( "Select Exe(s)")
        self.fb.setMaximumWidth( 90 )
        self.fb.clicked.connect( self._fileSelect )
        self.fcb= QCheckBox( "Directory" )
        self.diradd_le= QLineEdit( self.guiData.diraddRE )
        self.diradd_le.setPlaceholderText( "dir only--file regex--.py$ is default" )
        self.diradd_le.textChanged.connect( ft.partial( self._save_LE_Data, "diradd_le", "diraddRE" ) )
        
        self.xdat_le= QLineEdit( self.guiData.xDataVar )
        self.xdat_le.setPlaceholderText( "T, MCLOCK, _TIME ..." )
        self.xdat_le.textChanged.connect( ft.partial( self._save_LE_Data, "xdat_le", "xDataVar" ) )
        
        self.exeb= QPushButton( "Execute" )
        self.exeb.clicked.connect( self._executeScripts )
        self.saveListb= QPushButton( "Save List" )
        self.saveListb.clicked.connect( self._saveList )
        self.loadListb= QPushButton( "Load List" )
        self.loadListb.clicked.connect( self._loadList )
    
    def _saveList( self, **kwargs ):
        appObj= App( self, caseStr= "save", persistentDir= self.guiData.persistentDir, \
             persistentFile= self.guiData.persistentFile, \
             prefGroup= "/callWidget/saveList", window_title= "jpeExtend save",\
             fileFilter= "Text Files (*.txt)"  )
        
        if appObj.saveFile is None:
            return
        
        selectedTextList= [ self.fsl2.item( itemIdx ).text() for itemIdx in range( self.fsl2.count() ) ] 
        with open( appObj.saveFile, 'w' ) as f:
            [ f.write( aLine + "\n" ) for aLine in selectedTextList ]
    
    def _loadList( self ):
        appObj= App( self, caseStr= "MULTI_OPEN", persistentDir= self.guiData.persistentDir, \
             persistentFile= self.guiData.persistentFile, \
             prefGroup= "/callWidget/multiOpenList", window_title= "jpeExtend load list",\
             fileFilter= "Text Files (*.txt)"  )
        
        if appObj.selected_files is None:
            return
        
        filesList= appObj.selected_files
        
        readFiles= []
        for aFile in filesList:
            with open( aFile, "r" ) as f:
                lines= [ aLine.strip()  for aLine in f  if len(aLine.strip()) > 0 ]
                
            readFiles += [ aLine for aLine in lines if aLine not in readFiles ]
         
        self.fsl1._addListItems( readFiles )
        self.fsl2._addListItems( readFiles )
    
    def _executeScripts( self, threads= False ):
        pass
        
    def _push2Right( self ):
        llb= self.fsl1
        selectedTextList= [ llb.item( itemIdx ).text() \
                              for itemIdx in range( llb.count() ) 
                              if llb.item( itemIdx ).isSelected() ]
        
        self.fsl2._addListItems( selectedTextList )
        
    def _remFromRight( self ):
        rlb= self.fsl2
        selectedTextList= [ rlb.item( itemIdx ).text() \
                              for itemIdx in range( rlb.count() ) 
                              if rlb.item( itemIdx ).isSelected() ]
        
        if len( selectedTextList ) == 0:
            return
        
        self.fsl2._clearButtonPushed()
    
    def _fileSelect( self ):
        qfd= QFileDialog()
        qfd.setFileMode( QFileDialog.ExistingFiles )
#         QAbstractItemView::MultiSelection
        
        selDir= None 
        if self.fcb.isChecked():
            startDir= self.guiData.startDir2[0]
            if not os.path.isdir( startDir ):
                startDir= guiUtil.gUBase.home()
                
            selDir= qfd.getExistingDirectory( caption= "select exe(s)", directory= startDir )
            if os.path.isdir( selDir ):
                self.guiData.startDir2= [ os.path.dirname( selDir ) ]
                self.guiData.save( "startDir2" )
                
            fileNames= []
            for root, dirs, files in os.walk( selDir ):
                for aFile in files:
                    tFile= os.path.join( root, aFile )
                    if self.diradd_le.text().strip() != "" and re.match( self.diradd_le.text().strip(), tFile ):
                        fileNames.append( tFile )
                    elif tFile.endswith( ".py" ):
                        fileNames.append( tFile )
        else:
            startDir= self.guiData.startDir[0]
            if not os.path.isdir( startDir ):
                startDir= guiUtil.gUBase.home()
            fileNames= qfd.getOpenFileNames( caption= "select exe(s)", directory= startDir )
        
        if isinstance( fileNames, tuple ):
            fileTypeSelectedAllowed= fileNames[1]
            fileNames= fileNames[0]
        
        """ for now require that it ends in .py"""
        fileNames= [ aFile for aFile in fileNames if aFile.endswith( ".py" ) ]
        
        if len( fileNames ) == 0:
            return
        
        if selDir is not None: # selected files not directories
            modeDir= _getModeDir( fileNames )
            if len( modeDir ) > 0:
                self.guiData.startDir= [ modeDir ]
                self.guiData.save( "startDir" )
        
        if len( fileNames ) == 0:
            return
        
        self.fsl1._addListItems( fileNames )
       
    def _setupLayout( self ):
        mainLayout= QGridLayout()
        
        topRow= QHBoxLayout()
        
        lgb2= QHBoxLayout()
        lgb2.addWidget( self.xdat_le )
        lgb2.addWidget( self.diradd_le )
        qgb2= QGroupBox( "File Select" )
        qgb2.setLayout( lgb2 )
        topRow.addWidget( qgb2 )
        
        lgb2.addWidget( self.fb )
        lgb2.addWidget( self.fcb )
        
        # XDATA
        
        lgb= QHBoxLayout()
        lgb.addWidget( self.xdat_le )
        qgb= QGroupBox( "xDataVar" )
        qgb.setLayout( lgb )
        topRow.addWidget( qgb )
        
        topRow.addWidget( self.exeb )
        topRow.addWidget( self.saveListb )
        topRow.addWidget( self.loadListb )
#         layout.addWidget( l2, 0, 0 )
        
        l2= QGridLayout()
        l2.addWidget( self.pbr, 0, 0 )
        l2.addWidget( self.pbl, 0, 1 )
        
        l2.addWidget( self.fsl1, 1, 0 )
        l2.addWidget( self.fsl2, 1, 1 )
        
        l2.addWidget( self.fsl1.clearButton, 2, 0 )
        l2.addWidget( self.fsl2.clearButton, 2, 1 )
    
        mainLayout.addLayout( topRow, 0, 0 )
        mainLayout.addLayout( l2, 1, 0 )
        self.setLayout( mainLayout )
          
    def resetGuiDefaults( self ):
        self.guiData.resetStoredDefaults()
        self.fsl1.resetGuiDefaults()
        self.fsl2.resetGuiDefaults()
        
def _getModeDir( fileNames ):
    unqDirNames= []
    [ unqDirNames.append( os.path.dirname( aFile ) ) for aFile in fileNames if os.path.dirname( aFile ) not in unqDirNames ]
    
    countIdxList= [0]*len(unqDirNames)
    for aFile in fileNames:
        idx= unqDirNames.index( os.path.dirname( aFile ) )
        countIdxList[ idx ] += 1
    
    modeDir= unqDirNames[ np.where( countIdxList == np.max(countIdxList) )[0][0] ]
    
    return modeDir
    