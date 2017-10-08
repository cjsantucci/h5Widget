#!/home/chris/anaconda3/bin/python
'''
Created on Feb 12, 2017

@author: chris
'''

import functools
import traceback

import os

from PyQt5.Qt import *

from queue import Empty
import subprocess as subp
import signal
import sys
import time

sys.path.append("/home/chris/workspace/py3")

from guiUtil.systemProcQthread import spQthread
from guiUtil.gUBase import gUWidgetBase

class scroller( QWidget, gUWidgetBase ):
    '''
    lowest level of number of widgets for running system process in window
    '''
    _pyqtSigFinished= pyqtSignal()
    spqObj= None
    statusRect= None
    processRect= None
    pyqtSigFinished= None,
    _layout= None
    _processCommand= None

    def __init__( self, parent= None, **kwargs ):
        
        QListWidget.__init__( self, parent, **kwargs )
        gUWidgetBase.__init__( self, parent, **kwargs )
        
        assert self.statusRect is not None and self.processRect is not None and self.processCommand is not None, \
        "editRect, processRect and processCommand must be passed"
        
        appPassed= True
        if not self.kwargCheck( "app", kwargs ):
            appPassed= False
            app= QApplication([])        
        
        if not self.kwargCheck( "qmw", kwargs ):
            self.qmwPassed= False
            self.qmw= QMainWindow()
        else:
            self.qmwPassed= True
        
        if self.kwargCheck( "pyqtSigFinished", kwargs ):
            self._pyqtSigFinished.connect( self.pyqtSigFinished )     
        
        self._layout= QGridLayout()
        
        #self.qmw.setObjectName( "Window for: " + " ".join( self.processCommand ) )

        self.processScrollArea= self._setupEdit( self.processRect )
        self.processEdit.setText( " ".join( self.processCommand ) )
        self.statusScrollArea= self._setupEdit( self.statusRect )
        
        self._setupMainWindow()
            
        if self.onStartup:
            self.execute( onStartup= self.onStartup )
        
        if not appPassed:
            sys.exit( app.exec_() )
    
    def _setupEdit( self, rect ):
        edit = QTextEdit()
        edit.setGeometry( rect )
        
        scrollArea = QScrollArea( self.qmw )
        scrollArea.setWidget( edit ) 
        scrollArea.setGeometry( QRect( rect.left(), rect.top(),\
                                   rect.width()+2, rect.height()+2 )       
                               )
        return scrollArea
    
    def _setupMainWindow( self ):
#         pass
        centerPoint= self.centerOfScreenForCurrentMouse() 
        
        #process Rect
        pR= self.processScrollArea.geometry()
        # status Rect
        sR= self.statusScrollArea.geometry()
        
        wMaxX= max( [ pR.left()+ pR.width(), sR.left()+ sR.width() ] )
        wMaxY= max( [ pR.top()+ pR.height(), sR.top()+ sR.height() ] )
        
        self.qmw.setGeometry( \
                            QRect( centerPoint.x()-wMaxX/2, \
                            centerPoint.y()-wMaxY/2,\
                            wMaxX,\
                            wMaxY ) )
        self._layout.addWidget( self.statusScrollArea, 0, 0 )
        self._layout.addWidget( self.processScrollArea, 0, 1 )
        
        if not self.qmwPassed:
            self.qmw.show()
        
    def execute( self, onStartup= False ):
        if self.onStartup:
            QTimer.singleShot( 500, functools.partial( self.sysCommand, self.processCommand ) )
        else:
            self.sysCommand( self.processCommand )
            
    def sysCommand( self, processCommand ):
        try:
            self.spqObj= spQthread( processCommand, \
                                    pyqtSlotReadIn= self._updateLinesRead, \
                                    pyqtSlotFinishedIn= self._procFinished )
            self.spqObj.run()   
            self.runningProcess= True
        except:
            traceback.print_exc()
            self._pyqtSigFinished.emit()
    
    @pyqtSlot()
    def _procFinished( self ):
        self.runningProcess= False
        if self.closeOnFinish:
            self.qmw.close()
        else:
            if self._pyqtSigFinished is not None:
                self._pyqtSigFinished.emit()
            
    @pyqtSlot()
    def _updateLinesRead( self ):
        try:
            blackText = "<span style=\"color:#000000;\" >"
            line= self.spqObj.nbsr._qout.get_nowait()
            blackText= blackText + line + "</span>"
            self.statusEdit.append( blackText )
        except Empty:
            pass
        
        try:
            redText = "<span style=\"color:#ff0000;\" >"
            line= self.spqObj.nbsr._qerr.get_nowait()
            redText= redText + line + "</span>" 
            self.statusEdit.append( redText )
            self.closeOnFinish= False
        except Empty:
            pass
        #             
        self._updateScroller()
            
    def _updateScroller( self ):
        c =  self.processEdit.textCursor();
        c.movePosition( QTextCursor.End );
        self.processEdit.setTextCursor( c );
        
        c =  self.statusEdit.textCursor();
        c.movePosition( QTextCursor.End );
        self.statusEdit.setTextCursor( c );
        
        self.app.processEvents()
        
    def kill( self ):
        if self.runningProcess:
            self.spqObj.kill()
    
    def getStatusEdit( self ):
        return self.statusScrollArea.widget()
    
    def getProcessEdit( self ):
        return self.processScrollArea.widget()
    
    def setProcessEdit( self, inWidget ):
        self.processScrollArea.setWidget( inWidget )
    
    def setStatusEdit( self, inWidget ):
        self.statusScrollArea.setWidget( inWidget )
    
    def getProcCommand( self ):
        return self._processCommand
    
    def setProcCommand( self, inProcCommand ):
        assert type( inProcCommand ) == type( list() ), "input must be list"
        for anElement in inProcCommand:
            assert type( anElement ) == type( str() ), \
            str( anElement ) + " is type: " + str(type(anElement)) + ", but must be string"
        
        self._processCommand= inProcCommand  
    
    processCommand= property( getProcCommand, setProcCommand ) 
    statusEdit= property( getStatusEdit, setStatusEdit )
    processEdit= property( getProcessEdit, setProcessEdit ) 
    
if __name__ == "__main__": 
    scroller( processRect= QRect( 0, 50, 798, 80 ), \
             statusRect= QRect( 0, 131, 798, 320 ), \
             processCommand=["/home/chris/h5Sim.py"], onStartup= True)

    
    
    