#!/home/chris/anaconda3/bin/python
'''
Created on Feb 13, 2017

@author: chris
'''
from PyQt5.Qt import *

import os
import sys

sys.path.append("/home/chris/workspace/py3")

from guiUtil.scroller import scroller
from guiUtil import guidata as gdat
from guiUtil.gUBase import gUWidgetBase, dictOverride

# from matplotlib.offsetbox import kwargs

class scroll_control( QWidget, gUWidgetBase ):
    """
    adds another layer of control to scroller
    """
    scroller= None
    guiData= None

    def __init__( self, parent= None, **kwargs ):
        '''
        Constructor
        '''
        
        QListWidget.__init__( self, parent, **kwargs )
        gUWidgetBase.__init__( self, parent, **kwargs )
        
        idd= { "onStartup": False,
              "processCommand": ["/home/chris/h5Sim.py"], 
              "closeOnFinish": False
            }
        
        dictOverride( kwargs, idd, popOrig= True ) # override the defaults or saved values
        
        guiData= gdat.guiData( persistentDir= os.environ[ "HOME" ]+ "/.scroll_control", \
                               persistentFile= 'jpePref.h5', \
                               prefGroup= "/scroll_control", \
                               initDefaultDict= idd )
        
        self.guiData= guiData
        """
        Do these
        # add load method to guidata?
        # the process command will be sent in, so how do we not double it here
        """ 
        guiData.resetStoredDefaults()
        self.scroller= scroller( pyqtSigFinished= self._procFinished, **kwargs, **self.guiData.defDict )
        self.qmw.setMinimumHeight( 500 )
        
        self._setupCB()
        self._setupPB()
        
        if not self.kwargCheck( "qmw", kwargs, None ):
            self.qmw.show()
    
    def _killClicked( self ):
        self._procFinished()
        self.scroller.kill()
    
    @pyqtSlot()
    def _procFinished( self ):
        self.qpbExe.setEnabled( True )
        self.kpb.setEnabled( False )
    
    def _clearWindow( self ):
        self.scroller.statusEdit.setText( "" )
        self.scroller.app.processEvents()
    
    def _execute( self ):
        self._clearWindow()
        self.kpb.setEnabled( True )
        self.qpbExe.setEnabled( False )
        self.scroller.app.processEvents()
        self.scroller.execute()
    
    def _setupCB( self ):
        self.qcb= QCheckBox( "EXE on Startup", self.qmw )
        self.qcb.setGeometry( QRect( 0, 0, 200, 50 ) )
        if self.onStartup:
            self.qcb.setChecked( True )

    def _setupPB( self ):
        self.qpbExe= QPushButton( "Execute", self.qmw )
        self.qpbExe.setGeometry( QRect( 798/2, 420, 798/2, 50 ) )
        self.qpbExe.clicked.connect( self._execute )

        self.kpb= QPushButton( "Kill Process", self.qmw )
        self.kpb.setGeometry( QRect( 798/2, 0, 798/2, 50 ) )
        self.kpb.clicked.connect( self._killClicked )
        
        self.cwb= QPushButton( "Clear Window", self.qmw )
        self.cwb.setGeometry( QRect( 798/4, 0, 798/4, 50 ) )
        self.cwb.clicked.connect( self._clearWindow )
        
        if self.guiData.onStartup:
            self.qpbExe.setEnabled( False )
        else:
            self.kpb.setEnabled( False )
            
        
        
if __name__ == "__main__":
    app= QApplication([])
    qmw= QMainWindow()
#     qmw.setCentralWidget()
    inputdict= {
                "processRect": QRect( 0, 50, 798, 50 ), \
                "statusRect": QRect( 0, 101, 798, 320 ), \
                "app": app, \
                "qmw": qmw, \
                 }
    scObj= scroll_control( **inputdict )
#     qmw.setCentralWidget( scObj )
    
    qmw.show()
    app.processEvents()
#     scObj.scroller.qmw.show()
#     scObj.scroller.app.processEvents()
#     qmw.setCentralWidget(scObj)
    print("yay")
    sys.exit( app.exec_() )    
    print("duh")