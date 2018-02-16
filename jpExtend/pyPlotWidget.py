'''
Created on Sep 23, 2017

@author: chris
'''

import functools as ft
import importlib
import numpy as np
import os
from PyQt5.Qt import *
import re
import subprocess as subp
from threading import Thread
import traceback

import guiUtil
from guiUtil.fileSelect import fileSelectRemember
from guiUtil.guidata import guiData
from guiUtil.gUBase import gUWidgetBase
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil import simpleDialogs

class mySlider( QSlider, gUWidgetBase ):
    '''
    classdocs
    '''
    def __init__( self, parent, \
                  topWidget, \
                  numFrames= 0, \
                  **kwargs ):

        QSlider.__init__( self, parent )
        
        gUWidgetBase.__init__( self, **kwargs )
        self.topWidget= topWidget
        self.setMinimum( 0 )
        self.setMaximum( numFrames-1 )
        self.setOrientation( Qt.Horizontal  )
        self.valueChanged.connect( self.valuechanged )
    
    def valuechanged( self ):
        self.topWidget.updateAll( self.value() )
        
        
class App( QWidget, gUWidgetBase ):
    '''
    classdocs
    '''
    def __init__( self, parent, \
                  topWidget, \
                  leftRect= None, leftClearButtonLoc= None, \
                  leftPrefGroup= None, \
                  rightRect= None, rightClearButtonLoc= None, \
                  rightPrefGroup= None, \
                  boxPrefGroup= None, \
                  makeSlider= False, \
                  **kwargs ):

        QWidget.__init__( self, parent, **kwargs )
        gUWidgetBase.__init__( self, **kwargs )

        self._slider= None
        self.topWidget= topWidget

        idd= { "startDir": [ guiUtil.gUBase.home() ], \
          "startDir2": [ guiUtil.gUBase.home() ], \
          "pyPlotStartDir": [ guiUtil.gUBase.home() ], \
          "xDataVar": "MCLOCK", \
          "diraddRE": ".py$", \
        }

        self._initGuiData( idd= idd, prefGroup= boxPrefGroup, **kwargs )

        self.fsl1    = fileSelectList( self, listRect= leftRect, \
                          clearButtonLoc= leftClearButtonLoc, \
                          prefGroup= leftPrefGroup, \
                          **kwargs )
          
        self.fsl2    = fileSelectList( self, listRect= rightRect, \
                          clearButtonLoc= rightClearButtonLoc, \
                          prefGroup= rightPrefGroup, \
                          **kwargs )
        
        self._createOtherWidgetMembers()
        
        self._setupLayout( makeSlider )
        
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
        appObj= simpleDialogs.App( self, caseStr= "save", persistentDir= self.guiData.persistentDir, \
             persistentFile= self.guiData.persistentFile, \
             prefGroup= "/callWidget/saveList", window_title= "jpeExtend save",\
             fileFilter= "Text Files (*.txt)"  )
        
        if appObj.saveFile is None:
            return
        
        selectedTextList= [ self.fsl2.item( itemIdx ).text() for itemIdx in range( self.fsl2.count() ) ] 
        with open( appObj.saveFile, 'w' ) as f:
            [ f.write( aLine + "\n" ) for aLine in selectedTextList ]
    
    def _loadList( self ):
        appObj= simpleDialogs.App( self, \
                     caseStr= "MULTI_OPEN", \
                     persistentDir= self.guiData.persistentDir, \
                     persistentFile= self.guiData.persistentFile, \
                     prefGroup= "/pyPlotWidget/loadList", \
                     window_title= "jpeExtend load list", \
                     fileFilter= "Text Files (*.txt)" )
        
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
        rlb= self.fsl2
        selectedTextList= [ rlb.item( itemIdx ).text() \
                              for itemIdx in range( rlb.count() ) 
                              if rlb.item( itemIdx ).isSelected() ]
        
        if len( selectedTextList ) == 0:
            return
        
        for aFile in selectedTextList:
            dotFile= ".".join( aFile.split( "." )[:-1] )
            modName= os.path.basename( dotFile )
            modPath= os.path.dirname( dotFile )
            dotFile= re.sub( os.path.sep, ".", modPath ).lstrip(".") 
            dyn_mod= importlib.import_module( modName, dotFile )
            mainMethod= getattr( dyn_mod, "main" )
            dyn_mod.main([], block= False, show= True)
        
        
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
        
        self.fsl1._addListItems( selectedTextList )
        
        self.fsl2._clearButtonPushed()
    
    def _fileSelect( self ):
        grabDirectory= self.fcb.isChecked()
        if self.fcb.isChecked():
            startDirField= "startDir2"
        else:
            startDirField= "startDir"
        
        if self.diradd_le.text().strip() == "":
            regex= "*.py"
        else:
            regex= self.diradd_le.text().strip()
            
        fileNames= fileSelectRemember( self.guiData, startDirField, grabDirectory, \
                                       regex= regex, multipleFiles= True, \
                                       caption= "select exe(s)" )
        
        if fileNames is not None:
            self.fsl1._addListItems( fileNames )
       
    def _setupLayout( self, makeSlider ):
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
        
        row= 0
        if makeSlider:
            sliderLayout= QHBoxLayout()
            self._slider= mySlider( self, self.topWidget, \
                                    numFrames= self.topWidget.tmObj.numFrames )
            sliderLayout.addWidget( self._slider )
            mainLayout.addLayout( sliderLayout, row, 0 )
            row += 1
        
        mainLayout.addLayout( topRow, row, 0 )
        row += 1
        mainLayout.addLayout( l2, row, 0 )
        self.setLayout( mainLayout )
          
    def resetGuiDefaults( self ):
        self.guiData.resetStoredDefaults()
        self.fsl1.resetGuiDefaults()
        self.fsl2.resetGuiDefaults()
        