#!/usr/local/bin/anaconda3/bin/python
from PyQt5.Qt import *

import jpExtend
import matplotlib
matplotlib.use( jpExtend.matploblib_backend )
import matplotlib.pyplot as plt
plt.ion()
import argparse as ap
import functools as ft
import getpass as gp
import os
from queue import Queue, Empty
import signal
import sys
import time
from threading import Lock
import traceback
import warnings

import guiUtil
from guiUtil.fileSelect import fileSelectRemember
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil.gUBase import gUWidgetBase
from guiUtil.guidata import guiData
from jpExtend.h5Widget import App as h5App
from jpExtend.pyPlotWidget import App as pyPlotApp

class dummyTM2Remove( ):
    """
    This is the placeholder for the tm object to prototype the gui etc
    """
    def __init__( self, tmFile, numFrames= 25  ):
        self.numFrames= numFrames
        self.filename= tmFile

class myQmw( QMainWindow ):
    """
    qmain window class to override close functionality
    """
    def __init__( self, mainProgram= None ):
        QMainWindow.__init__( self )
        self.mainProgram= mainProgram
        
    def closeEvent(self, *args, **kwargs):
        self.mainProgram.closeEvent( *args, **kwargs )

class tabMaster( QObject, gUWidgetBase ):
    """
    Main constructor of all of the tabs
    """
    _fifoUpdateSignal= pyqtSignal()

    def __init__( self, *args, tmFile= None, commandLineArgs= None, **kwargs ):

        QObject.__init__( self )
        gUWidgetBase.__init__( self, **kwargs )
        
        self._fifoQ= Queue()
        self._tmObj= None
        self.currentMenu= None
        
        self._verbose= commandLineArgs.verbose

        """the gui data object holds the defaults for 
        gui objects
        """                
        idd= { \
          "fileOpenTm": [ guiUtil.gUBase.home() ], \
        }
        self._initGuiData( idd= idd, prefGroup= "/tabMaster", **kwargs )
        
        if tmFile is not None and os.path.exists( tmFile ):            
            self.guiData.fileOpenTm= os.path.dirname( tmFile )
        
        """
        if there is a fifo file from a controlling
        program open, read and kick off daemon thread
        to continuiously get the information
        """
        
        self._fifoFile= commandLineArgs.fifoFile
        self._fifoLock= None
        self._fifoReadThread= None
        makeSlider= True
        if self._fifoFile is not None:
            self._fifoUpdateSignal.connect( self.fifoThreadUpdate )
            self._fifoLock= Lock()
            self._kickOffReadThread()
        
        width= 900
        height= 250
                
        tabs    = QTabWidget()
        self.qmw.mainProgram= self
        self.tabs= tabs
        tabs.currentChanged.connect( self._onChange )
        self.qmw.setCentralWidget( tabs )
        
        tab1= None
        tab2= None
        tab3= None
        tab4= None
        
        if makeH5Tab():
            tab1    = h5App( tabs, self, **kwargs )
            self.h5WidgetTab= tab1
            tabs.addTab( tab1, "h5Diaglog" )
        
        if makePlotTab():
            tab2    = pyPlotApp( \
                                 tabs, \
                                 self, \
                                 leftRect= QRect( 5, 50, 230, 300 ), leftClearButtonLoc= ( 10, 370 ), \
                                 leftPrefGroup= "plt_tab/L1", \
                                 rightRect= QRect( 250, 50, 200, 300 ), rightClearButtonLoc= ( 250, 370 ), \
                                 rightPrefGroup= "plt_tab/L2", \
                                 boxPrefGroup= "plt_tab/other", \
                                 makeSlider= makeSlider, \
                                 **kwargs )
            self.plotterWidgetTab= tab2
            self.enableCritical( False )
            tabs.addTab( tab2, "plt_exe" )

#         self._openFileSelect( tmFile= "/home/chris/Music/0001.tm" 

        tab3    = QWidget()
        tab4    = QWidget()
        
        tabs.setCurrentIndex(1)
        
        self._allowMenuChangesNow= True
        self._onChange()
        
        if makeH5Tab():
            centerPoint= tab1.centerOfScreenForCurrentMouse()    
            self.qmw.setGeometry( QRect( centerPoint.x()-width/2, centerPoint.y()-height/2, width, height ) )
        
        elif makePlotTab():
            centerPoint= tab2.centerOfScreenForCurrentMouse()
            self.qmw.setGeometry( QRect( centerPoint.x()-width/2, centerPoint.y()-height/2, width, height ) )
        
            
        
        self.qmw.show()
        self.app.processEvents()
        sys.exit( self.app.exec_() )
    
    def enableMenus( self, inVal= True ):
        self.currentMenu.setEnabled( inVal )
    
    def enableCritical( self, inVal= True ):
        self.plotterWidgetTab.setEnabled( inVal )
        
    def _onChange( self ):
        
        if hasattr( self, "_allowMenuChangesNow" ) and self._allowMenuChangesNow:
            menuBar= QMenuBar()
            currentTabIndex= self.tabs.currentIndex()
            currentTab= self.tabs.currentWidget()
            
            if currentTabIndex == 0:
                menu= menuBar.addMenu("h5Widget")
                
                resetMenu= QMenu( "Reset Gui Defaults", menu )
                resetMenu.addAction( "Reset", currentTab.resetGuiDefaults )
                menu.addMenu( resetMenu )
                
            elif currentTabIndex == 1:
                menu= menuBar.addMenu("plt_exe")
                
                fileMenu= QMenu( "File" , menu )
                openMenu= QMenu( "Open", menu )
                openMenu.addAction( "Open TM/H5 File", \
                                    self._openFileSelect )
                menu.addMenu( fileMenu )
                fileMenu.addMenu( openMenu )
                
                resetMenu= QMenu( "Reset Gui Defaults", menu )
                resetMenu.addAction( "Reset", currentTab.resetGuiDefaults )
                menu.addMenu( resetMenu )
            
            self.currentMenu= menuBar
            
            self.qmw.setMenuBar( menuBar )
    
    def closeEvent( self, event ):
        plt.close("all")
        self.plotterWidgetTab.closeEvent()
        if self._fifoReadThread is not None:
            self._fifoReadThread.stop= True
        event.accept()
    
    def _openFileSelect( self, tmFile= None, startup= False ):
        
        if tmFile is None:
            prefVar= "fileOpenTm"
            fileList= fileSelectRemember( self.guiData, \
                                          prefVar, grabDirectory= False, \
                                          regex= ".*", multipleFiles= False, \
                                          caption= "Select TM/H5 file", \
                                          fileListFilter= "TM/H5 files (*.tm *.tm.gz *.h5)" ) 
            if fileList is None:
                if startup:
                    """
                    this is the path it gets to in startup
                    """
                    return
                else:
                    return
            else:
                tmFile= fileList[0]
        
        else: 
            """Got passed in"""
            if tmFile.endswith(".tm") or tmFile.endswith(".tm.gz"):
                if tmFile.endswith(".tm.gz"):
                    endNum= -2
                else:
                    endNum= -1
                    
                h5File= "".join( tmFile.split(".")[0:endNum] ) + ".h5"
                if os.path.isfile( h5File ):
                    tmFile= h5File
        
        if not startup and (self.tmObj is not None) and (self.tmObj.filename == tmFile):
            return
        
        elif self.tmObj is None: # this will happen the first time you select a file
            if not os.path.isfile( tmFile ):
                QMessageBox.warning( self.tabs, "Message" , "could not open tm: " + tmFile )
                return
            try:
                if self._fifoLock is not None:
                    self._fifoLock.acquire()
                
                self.tmObj= dummyTM2Remove( tmFile )
                self._changedTm()
                
                if self._fifoLock is not None:
                    self._fifoLock.release()
            except:
                traceback.print_exc()
                QMessageBox.critical( self.tabs, "Message" , "failed to process new TM" )
                time.sleep(5)
                sys.exit()
                
        else:
            if not os.path.isfile( tmFile ):
                QMessageBox.warning( self.tabs, "Message" , "could not open tm: " + tmFile )
                return
            
            try:                
                if self._fifoLock is not None:
                    self._fifoLock.acquire()

                
                self.tmObj= dummyTM2Remove( tmFile )
                self._changedTm()
                self._disconnectOldPlots()

                if self._fifoLock is not None:
                    self._fifoLock.release()

            except:
                traceback.print_exc()
                QMessageBox.critical( self.tabs, "Message" , "failed to process new TM" )
                time.sleep(5)
                sys.exit()
        
    def _changedTm( self ):
        """function performs whenever tm changes so everything gets the information"""
        try:
            self.plotterWidgetTab._changedTm()
            self.enableCritical( True )
        except:
            QMessageBox.critical( self, "Message" , "failed to communicate tm obj to children" )
            time.sleep(5)
            sys.exit()
            traceback.print_exc()
    
    def _updateAll( self, frame ):
        """
        update all plots
        """
        self.plotterWidgetTab._updateAll( frame )
    
    def _disconnectOldPlots( self ):
        """
        when tmFile is changed abandon updating of 
        old plots
        """
        self.plotterWidgetTab._disconnectOldPlots()
             
    @pyqtSlot()
    def fifoThreadUpdate( self ):
        """
        when the frame comes in from the controlling program
        here is where we update
        """
        self._fifoLock.acquire()
        
        if self._fifoQ.empty():
            warnings.warn( "Don't think this should occur...")
            self._fifoLock.release()
            return
        
        frame= self._fifoQ.get(0)
        self.plotterWidgetTab._slider.setValue( frame )
        
        if len( self.plotterWidgetTab._pyPlotUpdater ) == 0:
            self._fifoLock.release()
            return
        
        self.h5WidgetTab.setEnabled( False )
        self.plotterWidgetTab.setEnabled( False )
        self.plotterWidgetTab._slider.setEnabled( False )
        
        self._updateAll( frame )
    
        self.h5WidgetTab.setEnabled( True )
        self.plotterWidgetTab.setEnabled( True )
        self.plotterWidgetTab._slider.setEnabled( True )
        self.plotterWidgetTab._slider.setEnabled( True )
        
        self._fifoLock.release()
    
    def _kickOffReadThread( self ):

        thread= guiUtil.gUBase.myThread( target = self._readThreadMethod,
                args= ( self._fifoFile, self._fifoQ, self._fifoLock, self._fifoUpdateSignal ) )
        
        thread.daemon = True                            # Daemonize thread
        thread.start() 
        self._fifoReadThread= thread
    
    def _readThreadMethod( self, fifoFile, fifoQ, fifoLock, updateBroadCast ):
#         print("pipe: " + fifoFile)
        try:
            with open( fifoFile, "r" ) as f:
                while True and not self._fifoReadThread.stop:
#                     print("read")
                    lines= f.read().split("\n")
                    lines.reverse()
                    tokenList= [ aTok.strip().split()[0] for aLine in lines for aTok in aLine ]
#                     print( "lines: " + str(lines))
                    
                    mostRecentData= None
                    for aTok in tokenList:
                        try:
                            mostRecentData= int(aTok)
                        except:
                            pass
                    
#                     print("mostRecent on read: " + str(mostRecentData))
                    if mostRecentData is None:
                        continue
                    
#                     print("lock")
                    fifoLock.acquire()
                    fifoQ.put( mostRecentData )
                    fifoLock.release()
                    
#                     print("emit")
#                     print(type(updateBroadCast))
                    updateBroadCast.emit()

#                     print("read Value: " + str(mostRecentData))
#                     print("read2")
                    
        except Exception as e:
            print("read side exception")
            print("Exception e: " + e)
    
    def getTmObj( self ):
        return self._tmObj
    
    def setTmObj( self, inObj ):
        # assert
        self._tmObj= inObj
    
    tmObj= property( getTmObj, setTmObj )

def makePlotTab():
    return True

def makeH5Tab():
    return True
#     return os.name != "nt"

def init( persistenDir ):
    user= gp.getuser()
    homedir = guiUtil.gUBase.home()
    pDir= os.path.join( homedir, persistenDir )
    
    if not os.path.isdir( pDir ):
        os.makedirs( pDir )
    
    return pDir
# end init 

def parseArgs( argv ):
    parserObj= ap.ArgumentParser()
    parserObj.add_argument("--fifoFile", default= None, type= str, help= "name of FIFO to communicate TO parent.")
    parserObj.add_argument("--tmFile", default= None, type= str, help= "tm or h5 file.")
    parserObj.add_argument("--verbose", default= 0, type= int, help= "increase command line output text" )
    args= parserObj.parse_args( argv )
    
    return args
    
def main( argv ):
    
    clArgs= parseArgs( argv[1:] )
    qapp     = QApplication( argv )
#         app.setStyle(QStyleFactory.create("Plastique"))
    qmw     = myQmw()
    qmw.setWindowTitle( "Python h5 Plotter" )
    
    pDir= init( ".jpExtend" )
    tabMaster( persistentDir= pDir, \
               persistentFile= "jpePref.h5", \
               app= qapp, qmw= qmw, \
               tmFile= clArgs.tmFile, \
               commandLineArgs= clArgs )
    
if __name__ == "__main__": 
    main( sys.argv )