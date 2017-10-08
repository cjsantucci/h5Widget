#!/home/chris/anaconda3/bin/python
'''
Created on Jun 11, 2017

@author: chris
'''
import non_block_stream_reader as nbsread
from PyQt5.Qt import *

class spQthread( QThread ):
    '''
    system process thread for Q objects. Reads standard IO
    and sends signal "lines_read" when lines have been read
    '''
    lines_read= pyqtSignal()
    finished= pyqtSignal()

    def __init__( self, processCommand, \
                  pyqtSlotReadIn= None, \
                  pyqtSlotFinishedIn= None ):
        
        QThread.__init__( self )
        self.processCommand= processCommand
        self.nbsr= None
        if pyqtSlotReadIn is not None:
            self.lines_read.connect( pyqtSlotReadIn )
    
        if pyqtSlotReadIn is not None:
            self.finished.connect( pyqtSlotFinishedIn )
    
    def alive( self ):
        if self.nbsr is not None and \
            self.nbsr._terr.isAlive() and \
            self.nbsr._tstd.isAlive():
        
            return True
        
        return False
    
    def kill( self ):
        self.nbsr.kill()
    
    def run( self ):
        """
        enable push button here
        """
        self.nbsr= nbsread.NonBlockingStreamReader( self.processCommand, \
                                                    pyqtsigRead= self.lines_read, \
                                                    pyqtsigFinished= self.finished, \
                                                    usecolor= False )