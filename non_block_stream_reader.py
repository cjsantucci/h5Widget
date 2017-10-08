#!/home/chris/anaconda3/bin/python
'''*
'''
from colorama import Fore, Back
import os
from queue import Queue, Empty
import re
import signal
from threading import Thread
import subprocess as subp
import traceback

class NonBlockingStreamReader:

    def __init__( self, comm, pyqtsigRead= None, pyqtsigFinished= None, usecolor= False ):
        '''
        comm is the command list you want
        pyqtsig is the pyqt signal which will emit when a line is read from stderr or stdout
        use colors will populate the stderr queue with red
        '''
        assert type( comm ) == type( list() ), "comm argument must be list"
        shebang= obtainSheBang( comm )
        if shebang is not None:
            # call the command with the same shebang
            # but start the process with -u to make unbuffered
            comm.insert( 0, "-u" )
            comm.insert( 0, shebang )
            self._comm= comm
        else:
            self._comm= comm
        
        self._usecolor= usecolor
        self._qout = Queue()
        self._qerr = Queue()
        self._sigRead= pyqtsigRead
        self._sigFinished= pyqtsigFinished
        self.proc= None
        
        self._startThreads()
    
    def kill( self ):
        if self.proc is not None and \
            self.proc.poll() is None:
            try:
                os.kill( self.proc.pid, signal.SIGKILL )
            except:
                traceback.print_exc()
    
    def _startThreads( self ):
        """
        one thread for stdout and one for stderr
        """
        proc= subp.Popen( self._comm, stdout=subp.PIPE, stderr=subp.PIPE, universal_newlines= True )    
        self.proc= proc
        
        self._tstd= Thread( target = _populateQueue,
                args= ( proc, proc.stdout, self._sigRead, \
                        self._qout, False ) )
        self._tstd.daemon= True
        
        self._terr= Thread( target = _populateQueue,
                args= ( proc, proc.stderr, self._sigRead, \
                        self._qerr, self._usecolor ) )
        self._terr.daemon= True
        
        self._tstd.start() #start collecting lines from the stream
        self._terr.start()
        
        if self._sigFinished is not None:
            self._tfin= Thread( target = _monitorFinished,
                args= ( self._tstd, self._terr, self._sigFinished ) )
            self._tfin.daemon= True
            
            self._tfin.start()
            
    # end def _startThreads

    def readline( self, stdout= True, timeout = None ):
        """
        provide readline method for those who do not sent signal to emit
        """ 
        try:
            if stdout:
                return self._qstdout.get( block = timeout is not None,
                        timeout= timeout )
            else: # std error
                return self._qstderr.get( block = timeout is not None,
                        timeout= timeout )
                
        except Empty:
            return None
    
    # end def readline
    
def _monitorFinished( tstd, terr, pyqtSigIn ):
    
    while True:
        if tstd.isAlive() or terr.isAlive():
            continue
        pyqtSigIn.emit()
        return

def _populateQueue( proc, stream, sigRead, inQ, usecolor ):
    '''
    Collect lines from 'stream' and put them in 'queue'.
    '''
    while proc.poll() is None:
        try:
            line= stream.readline().rstrip()
            if usecolor:
                inQ.put( Fore.RED + line.rstrip() + Back.RED + "\n" )
            else:
                inQ.put( line )
            if sigRead is not None:
                sigRead.emit()
        except:
            traceback.print_exc()
    
    line= stream.readlines()
    lastStr= "".join( line )
    if lastStr != "":
        inQ.put( lastStr )
        if sigRead is not None:
            sigRead.emit()

# end def _populateQueue

def obtainSheBang( comm ):
    """
        grab the shebang so it can be called with -u added 
    """
    try:
        assert type( comm ) == type( list() ), "comm argument must be list"
        assert os.path.isfile( comm[0].split()[0] ), "must pass in file"
        
        if comm[0].split()[0].endswith( ".py" ): # only override python scripts with -u option
            with open( comm[0], 'r' ) as f:
                for aLine in f:
                    if re.search( "[\s]*#\!.*", aLine ):
                        if re.search( "\-u", aLine ):
                            return None
                        else:
                            return aLine[2:].rstrip()
    except:
        pass
                
    return None

# end obtainSheBang