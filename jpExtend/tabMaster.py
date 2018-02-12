#!/usr/local/bin/anaconda3/bin/python
from PyQt5.Qt import *

import getpass as gp
import os
import argparse as ap
import sys
import jpExtend
from jpExtend.qdlgex import h5dialog
from jpExtend.callWidget import boxWidget
import guiUtil
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil.gUBase import gUWidgetBase

class tabMaster( gUWidgetBase ):
    """
    Main constructor of all of the tabs
    """

    def __init__( self, *args, **kwargs ):
        
        gUWidgetBase.__init__( self, **kwargs )
        
        width= 900
        height= 250

        tabs    = QTabWidget()
        self.tabs= tabs
        tabs.currentChanged.connect( self._onChange )
        self.qmw.setCentralWidget( tabs )
        
        tab1= None
        tab2= None
        tab3= None
        tab4= None
        
        if makeH5Tab():
            tab1    = h5dialog( tabs, **kwargs )
            tabs.addTab( tab1, "h5Diaglog" )
        
        if makePlotTab():
            tab2    = boxWidget( \
                                 tabs, \
                                 leftRect= QRect( 5, 50, 230, 300 ), leftClearButtonLoc= ( 10, 370 ), \
                                 leftPrefGroup= "plt_tab/L1", \
                                 rightRect= QRect( 250, 50, 200, 300 ), rightClearButtonLoc= ( 250, 370 ), \
                                 rightPrefGroup= "plt_tab/L2", \
                                 boxPrefGroup= "plt_tab/other", \
                                 **kwargs )
            tabs.addTab( tab2, "plt_exe" )

        tab3    = QWidget()
        tab4    = QWidget()
        
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
                menu= menuBar.addMenu("h5Dialog")
                menu.addAction( "Reset Gui Defaults", currentTab.resetGuiDefaults )
            elif currentTabIndex == 1:
                menu= menuBar.addMenu("plt_exe")
                menu.addAction( "Reset Gui Defaults", currentTab.resetGuiDefaults )
                
            self.qmw.setMenuBar( menuBar )

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
    parserObj.add_argument("--verbosity", default= 0, type= int, help= "increase command line output text" )
    args= parserObj.parse_args()
    
    print()

def readThread( fifoFile ):
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
                        break
                print("read Value: " + mostRecentData)
                print("read2")
    except Exception as e:
        print("read side exception")
        print(e)

def main( argv ):
    parseArgs( argv[1:] )
    qapp     = QApplication( argv )
#         app.setStyle(QStyleFactory.create("Plastique"))
    qmw     = QMainWindow()
    qmw.setWindowTitle( "Python h5 Plotter" )
    
    pDir= init( ".jpExtend" )
    tabMaster( persistentDir= pDir, \
               persistentFile= "jpePref.h5", \
               app= qapp, qmw= qmw )

if __name__ == "__main__": 
    main( sys.argv )