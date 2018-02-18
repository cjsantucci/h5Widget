'''
Created on Sep 23, 2017

@author: chris
'''

import functools as ft
import importlib
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
from PyQt5.Qt import *
import re
import subprocess as subp
import threading
from threading import Thread
import traceback
import warnings

import guiUtil
from guiUtil.fileSelect import fileSelectRemember
from guiUtil.guidata import guiData
from guiUtil.gUBase import gUWidgetBase
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil import simpleDialogs
import jpExtend
from jpExtend.plotUpdater import plotUpdater

class myFrameEdit( QLineEdit, gUWidgetBase ):
    """
    frame edit text box
    """
    def __init__( self, parent, \
              topWidget, \
              numFrames= 0, \
              **kwargs ):
        
        QLineEdit.__init__( self, parent )
        gUWidgetBase.__init__( self, **kwargs )
        self.topWidget= topWidget
        self.numFrames= numFrames
        
        self.textChanged.connect( self._frameTextChanged )
        
    def _frameTextChanged( self, *args, **kwargs ):
        """
        method when frame gets changed in text box
        """
        try:
            slider= self.parent()._slider
            
            val= int( self.text().strip() )
            if val < 0:
                val= 0
            if val >= self.numFrames:
                val= self.numFrames-1
            
            sliderVal= int( slider.value() )
            
            if val != sliderVal:
                """ slider does the update """
                slider.setValue( val )
                
        except:
            pass    

class mySlider( QSlider, gUWidgetBase ):
    '''
    slider to control/parrot external caller frame
    '''
    def __init__( self, parent, \
                  topWidget, \
                  numFrames= 0, \
                  **kwargs ):

        QSlider.__init__( self, parent )
        
        gUWidgetBase.__init__( self, **kwargs )
        self.topWidget= topWidget
        self.setMinimum( 0 )
        if numFrames == 0:
            self.setMaximum( numFrames )
        else:
            self.setMaximum( numFrames-1 )
        self.setOrientation( Qt.Horizontal  )
        self.valueChanged.connect( self.valuechanged )
        
    def valuechanged( self ):
        val= int( self.value() )
        textVal= int( self.parent()._frameLineEdit.text().strip() )
        
        if val != textVal:
            self.parent()._frameLineEdit.setText( str(self.value()) )
            
        self.topWidget._updateAll( self.value() )

class plotUpdaterPyplot( gUWidgetBase, plotUpdater ):
    
    def __init__( self, topWidget, **kwargs ):       
#         gUWidgetBase.__init__( self, **kwargs )
        plotUpdater.__init__( self, **kwargs )
        self.topWidget= topWidget

class App( QWidget, gUWidgetBase ):
    """
    main plotter widget
    """
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

        self._pyPlotUpdater= plotUpdaterPyplot( topWidget, **kwargs )
        self._multiProcRunningList= []
        self._allMultiProcRunningList= []
        self._popenList= []
        
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
    
    def _updateAll( self, frame ):
        self._pyPlotUpdater.updatePlots( frame )
        self._updateMultiProc( frame )
    
    def _updateMultiProc( self, frame ):
        """
        right now this is dormant due to both backends being whack.
        """
        if len( self._multiProcRunningList ) == 0:
            return
        
        propPopIdxs= []
        idx= 0
        for anElement in self._multiProcRunningList:
            mProc= anElement[0]
            q= anElement[1]
            idx += 1
            if mProc.is_alive():
                try:
#                     if not q.empty():
#                         q.clear()
                    q.put( frame )
                except:
                    traceback.print_exc()
                    try:
                        propPopIdxs.append( idx )
                    except:
                        pass
            else:
                try:
                    propPopIdxs.append( idx )
                except:
                    pass
                
        propPopIdxs.reverse() 
        
        if len( propPopIdxs ) > 0:
            for idx in propPopIdxs:
                self._multiProcRunningList.pop( idx )
    
    
    def _disconnectOldPlots( self ):
        """
        so the old plots will not update
        """
        self._pyPlotUpdater.disconnect()
        self._multiProcRunningList= []
    
    def closeEvent( self, *args, **kwargs ):
        """
        do all these things when close is clicked on the main window
        """
        for aProc in self._popenList:
            try:
                aProc.terminate()
            except:
                pass
        
        if len( self._allMultiProcRunningList ) == 0:
            return 
        
        for anElement in self._allMultiProcRunningList:
            mProc= anElement[0]
            try:
                mProc.terminate()
            except:
                pass
       
    def _save_LE_Data( self, leObjStr, saveStr ):
        """
        save the data in the list boxes to persistent data
        """
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
        
        self.distb= QPushButton( "Distribute" )
        self.distb.clicked.connect( ft.partial( self._executeScripts, multiprocess= True ) )
        self.distb.setEnabled( False )
        
        self.popenb= QPushButton( "POpen" )
        self.popenb.clicked.connect( ft.partial( self._executeScripts, popen= True ) )
        
        self.saveListb= QPushButton( "Save List" )
        self.saveListb.clicked.connect( self._saveList )
        self.loadListb= QPushButton( "Load List" )
        self.loadListb.clicked.connect( self._loadList )
    
    def _saveList( self, **kwargs ):
        """
        save list of .py files in the right text box as a text file
        """
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
        """
        load a list of .py files saved in a text file into text box
        """
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
    
    def _doPOpen( self, fileList ):
#         if not self.tmObj.filename.endswith( ".h5" ):
#             QMessageBox.critical( self.tabs, "Message" , "could not do tm system call only supports h5 currently: " + self.tmObj.filename )
#             return 
        
        for aFile in fileList:
            try:
                proc= subp.Popen( [ aFile, self.topWidget.tmObj.filename ], \
                                  stdout= subp.PIPE, stderr= subp.PIPE )
#                 stdout, stderr= proc.communicate()
#                 print(stdout)
                self._popenList.append( proc )
            except:
                traceback.print_exc()
                pass
                
    
    def _executeScripts( self, popen= False, multiprocess= False ):
        rlb= self.fsl2
        selectedTextList= [ rlb.item( itemIdx ).text() \
                              for itemIdx in range( rlb.count() ) 
                              if rlb.item( itemIdx ).isSelected() ]
        
        if len( selectedTextList ) == 0:
            return
        
        if popen:
            self._doPOpen( selectedTextList )
            return
        
        fileList, mainMethods= jpExtend.plotUpdater.getMains( selectedTextList )
        
        self.setEnabled( False )
        self.topWidget.enableMenus( False )
        
        xDataVar= self.xdat_le.text().strip()
        passArgs= ( fileList, mainMethods, self.topWidget.tmObj, self._slider.value() )
        if not multiprocess:
            self._pyPlotUpdater.executePlots( \
                                              *passArgs, \
                                              xDataVar= xDataVar, \
                                            )
        else:
            """
            this is really not working currently because of the backend issues
            """
            try:
                q= multiprocessing.Queue()
                mDict= { "multproc": True, "multiprocQueue": q }
                mProc= multiprocessing.Process( target= jpExtend.plotUpdater.multiprocessRunner, \
                                             args= passArgs, \
                                             kwargs= mDict, \
                                           )
                mProc.start()
                self._multiProcRunningList.append( ( mProc, q ) )
                self._allMultiProcRunningList.append( ( mProc, q ) )
                
            except:
                traceback.print_exc()
                try:
                    mProc.Terminate()
                except:
                    print("unable to terminate plot process")
                
        
        self.setEnabled( True )
        self.topWidget.enableMenus()
    
#         print("done execute")
    
    def _push2Right( self ):
        """
        push from left list box to right list box
        """
        llb= self.fsl1
        selectedTextList= [ llb.item( itemIdx ).text() \
                              for itemIdx in range( llb.count() ) 
                              if llb.item( itemIdx ).isSelected() ]
        
        self.fsl2._addListItems( selectedTextList )
        
    def _remFromRight( self ):
        """
        take away from right list box
        """
        rlb= self.fsl2
        selectedTextList= [ rlb.item( itemIdx ).text() \
                              for itemIdx in range( rlb.count() ) 
                              if rlb.item( itemIdx ).isSelected() ]
        
        if len( selectedTextList ) == 0:
            return
        
        self.fsl1._addListItems( selectedTextList )
        
        self.fsl2._clearButtonPushed()
    
    def _fileSelect( self ):
        """
        select .py files
        """
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
    
    def _changedTm( self ):
        """
        reset everything when tm has been changed
        """
        self._slider.setMaximum( self.getNumFrames() )
        self._slider.setValue( 0 )
        self._frameLineEdit.numFrames= self.getNumFrames()
        self._frameLineEdit.setText( str(0) )
      
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
        
        twoButtonLayout= QVBoxLayout()
        twoButtonLayout.addWidget( self.exeb )
        twoButtonLayout.addWidget( self.distb )
        twoButtonLayout.addWidget( self.popenb )
        topRow.addLayout( twoButtonLayout )
        
        twoButtonLayout= QVBoxLayout()
        twoButtonLayout.addWidget( self.saveListb )
        twoButtonLayout.addWidget( self.loadListb )
        topRow.addLayout( twoButtonLayout )

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
                                    numFrames= self.getNumFrames() )
            sliderLayout.addWidget( self._slider )
            
            self._frameLineEdit= myFrameEdit( self, self.topWidget, \
                                             numFrames= self.getNumFrames() )
            self._frameLineEdit.setText( str(0) )
            self._frameLineEdit.setMaximumHeight(30)
            self._frameLineEdit.setMaximumWidth(50)
            sliderLayout.addWidget( self._frameLineEdit )
            
            mainLayout.addLayout( sliderLayout, row, 0 )
            row += 1
        
        mainLayout.addLayout( topRow, row, 0 )
        row += 1
        mainLayout.addLayout( l2, row, 0 )
        self.setLayout( mainLayout )
    
    def getNumFrames( self ):
        if self.topWidget.tmObj is not None:
            return self.topWidget.tmObj.numFrames
        else:
            return 0
      
    def resetGuiDefaults( self ):
        self.guiData.resetStoredDefaults()
        self.fsl1.resetGuiDefaults()
        self.fsl2.resetGuiDefaults()
        