'''
Created on Sep 23, 2017

@author: chris
'''

from PyQt5.Qt import *
from guiUtil.guidata import guiData
from guiUtil.gUBase import gUWidgetBase
from guiUtil.fileSelectListWidget import fileSelectList
import numpy as np
import os
import subprocess as subp
from threading import Thread
import traceback

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
        
        idd= { "startDir": [os.environ[ 'HOME' ]] }
        
        guiDataObj= guiData( persistentDir= persistentDir, \
                               persistentFile= persistentFile, \
                               prefGroup= prefGroup, \
                               initDefaultDict= idd )
        
        self.guiData= guiDataObj
    
    def _createOtherWidgetMembers( self ):
        self.pbr= QPushButton( "->" )
        self.pbr.clicked.connect( self._push2Right )
        self.pbl= QPushButton( "<-" )
        self.pbl.clicked.connect( self._remFromRight )
        
        self.fb= QPushButton( "Select Exe(s)")
        self.fb.setMaximumWidth( 90 )
        self.fb.clicked.connect( self._fileSelect )
        
        self.fcb= QCheckBox( "Directory" )
        
        self.exeb= QPushButton( "Execute" )
        self.exeb.clicked.connect( self._executeScripts )
    
    def _executeScripts( self, threads= False ):
        rlb= self.fsl2
        
        selectedTextList= [ rlb.item( itemIdx ).text() \
                      for itemIdx in range( rlb.count() ) 
                      if rlb.item( itemIdx ).isSelected() ]
        
        passList= [ "-f", self.tmFile ]
        if self.namedPipe is not None:
            passList += [ "-p", self.namedPipe ]
        
        if self.xDataVar is not None:
            passList += [ "--xDataVar", self.xData ]
        
        sysCommands= []
        threadCommands= []
        for aScript in selectedTextList:
            threadCommands.append( " ".join( passList ) )
            sysCommands.append( aScript + " ".join( passList ) )
        
        for aScript, threadComm, sysComm,  in zip( *[ selectedTextList, threadCommands, sysComm ] ):
            if threads and aScript.endswith( ".py" ):
                try:
                    t= Thread( target = scriptMain,
                        args= ( sysComm ) )
                    t.daemon= True
                    t.start()
                except:
                    traceback.print_exc()
            else:
                try:
                    proc= subp.Popen( sysComm )
                except:
                    traceback.print_exc()
    
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
        
        startDir= self.guiData.startDir[0]
        if not os.path.isdir( startDir ):
            startDir= os.environ[ "HOME" ]
            
        if self.fcb.isChecked():
            selDir= qfd.getExistingDirectory( caption= "select exe(s)", directory= startDir )
            fileNames= []
            for root, dirs, files in os.walk( selDir ):
                for aFile in files:
                    tFile= os.path.join( root, aFile )
                    if tFile.endswith( ".py" ):
                        fileNames.append( tFile )
        else:
            fileNames= qfd.getOpenFileNames( caption= "select exe(s)", directory= startDir )
        
        if isinstance( fileNames, tuple ):
            fileTypeSelectedAllowed= fileNames[1]
            fileNames= fileNames[0]
        
        """ for now require that it ends in .py"""
        fileNames= [ aFile for aFile in fileNames if aFile.endswith( ".py" ) ]
        
        if len( fileNames ) == 0:
            return
        
        modeDir= _getModeDir( fileNames )
        if len( modeDir ) > 0:
            self.guiData.startDir= [ modeDir ]
            self.guiData.save( "startDir" )
        
        if len( fileNames ) == 0:
            return
        
        self.fsl1._addListItems( fileNames )
       
    def _setupLayout( self ):
        mainLayout= QGridLayout()
        
        l1= QHBoxLayout()
        l1.addWidget( self.fb )
        l1.addWidget( self.fcb )
        l1.addWidget( self.exeb )
#         layout.addWidget( l2, 0, 0 )
        
        l2= QGridLayout()
        l2.addWidget( self.pbr, 0, 0 )
        l2.addWidget( self.pbl, 0, 1 )
        
        l2.addWidget( self.fsl1, 1, 0 )
        l2.addWidget( self.fsl2, 1, 1 )
        
        l2.addWidget( self.fsl1.clearButton, 2, 0 )
        l2.addWidget( self.fsl2.clearButton, 2, 1 )
    
        mainLayout.addLayout( l1, 0, 0 )
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
    