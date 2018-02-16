#!/usr/local/bin/anaconda3/bin/python
from PyQt5.Qt import *

import argparse as ap
import functools as ft
import getpass as gp
import os
from queue import Queue, Empty
import signal
import sys
from threading import Thread

import guiUtil
from guiUtil.fileSelect import fileSelectRemember
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil.gUBase import gUWidgetBase
from guiUtil.guidata import guiData
import jpExtend
from jpExtend.h5Widget import App as h5App
from jpExtend.pyPlotWidget import App as pyPlotApp

class dummyTM2Remove():
    
    def __init__( self, tmFile ):
        self.numFrames= 25
        self.filename= tmFile

class tabMaster( gUWidgetBase ):
    """
    Main constructor of all of the tabs
    """

    def __init__( self, *args, tmFile= None, commandLineArgs= None, **kwargs ):
        
        gUWidgetBase.__init__( self, **kwargs )
        
        self._fifoQ= Queue()
        self._tmObj= None
        
        self._verbose= commandLineArgs.verbose
        
        self._openFileSelect( tmFile= tmFile, startup= True )
            
        self._fifoFile= commandLineArgs.fifoFile
        if self._fifoFile is not None:
            self._kickOffReadThread()
            makeSlider= False
        else:
            makeSlider= True
        
        width= 900
        height= 250
        
        idd= { \
          "fileOpenTm": [ guiUtil.gUBase.home() ], \
        }

        self._initGuiData( idd= idd, prefGroup= "/tabMaster", **kwargs )

        
        tabs    = QTabWidget()
        self.tabs= tabs
        tabs.currentChanged.connect( self._onChange )
        self.qmw.setCentralWidget( tabs )
        
        tab1= None
        tab2= None
        tab3= None
        tab4= None
        
        if makeH5Tab():
            tab1    = h5App( tabs, self, **kwargs )
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
            tabs.addTab( tab2, "plt_exe" )

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
            
            self.qmw.setMenuBar( menuBar )
    
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
                    sys.exit()
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
        
        if not startup and self.tmObj.filename == tmFile:
            return
        elif self.tmObj is None:
            assert os.path.isfile( tmFile ), "File DNE: " + tmFile        
            self.tmObj= dummyTM2Remove( tmFile )
        else:
            assert os.path.isfile( tmFile ), "File DNE: " + tmFile        
            self.tmObj= dummyTM2Remove( tmFile )
            self._disconnectOldPlots()
    
    def updateAll( self, frame ):
        pass
    
    def _disconnectOldPlots( self ):
        pass
        
    def _kickOffReadThread( self ):
        self._inUpdate= pyqtSignal()
        self._updateFinished.connect( self.procFinished )
        
        thread= Thread( target = self._readThreadMethod,
                args= ( self._fifoQ, self._fifoFile ) )
        
        thread.daemon = True                            # Daemonize thread
        thread.start() 
        self._fifoReadThread= thread
    
    def _readThreadMethod( self, fifoFile, fifoQ, updateBroadCast, receiveSignal ):
        print("pipe: " + fifoFile)
        try:
            with open( fifoFile, "r" ) as f:
                while True:
                    print("read")
                    lines= f.read().split("\n")
                    lines.reverse()
                    print( "lines: " + str(lines))
                    for aLine in lines:
                        if len( aLine ) != 0:
                            mostRecentData= aLine
                            with fifoQ.mutex:
                                fifoQ.queue.clear()
                                fifoQ.put( mostRecentData )
                                self._inUpdate= True
                                updateBroadCast.emit()
                                
                            break
                    print("read Value: " + mostRecentData)
                    print("read2")
        except Exception as e:
            print("read side exception")
            print(e)
    
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
    args= parserObj.parse_args()
    
    return args
    
def main( argv ):
    argv.append( "--tmFile")
    argv.append( "/home/chris/0001.tm")
    
    clArgs= parseArgs( argv[1:] )
    qapp     = QApplication( argv )
#         app.setStyle(QStyleFactory.create("Plastique"))
    qmw     = QMainWindow()
    qmw.setWindowTitle( "Python h5 Plotter" )
    
    pDir= init( ".jpExtend" )
    tabMaster( persistentDir= pDir, \
               persistentFile= "jpePref.h5", \
               app= qapp, qmw= qmw, \
               tmFile= clArgs.tmFile, \
               commandLineArgs= clArgs )
    
if __name__ == "__main__": 
    main( sys.argv )