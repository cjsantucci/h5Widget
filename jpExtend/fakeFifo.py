'''
Created on Oct 8, 2017

@author: chris
'''
import os
import sys
import tempfile
import traceback
from time import sleep
from jpExtend import getTempFileName
from threading import Thread

def readFromFifo( fifoName ):
    sleep(1)
    fif= os.open( fifoName, os.O_RDONLY )
    print("inread")
    try:
        while True:
    #             print("1")
    # #             select.select(fif,[],fif)
    #             print("3")
            dat= os.read( fif, 4 )
            sleep(0.6)
            fif= os.open( fifoName, os.O_RDONLY )
    #             print("2")
            print("read: " + str(int.from_bytes(dat, sys.byteorder)) )
    except:
        print("couldn't read")

print("readDone")

def write2Fifo( fifoName ):
    try:
        fif= os.open( fifoName, os.O_WRONLY )
        count= 0
        while True:
            print( "write:" + str(count) )
            os.write( fif, count.to_bytes( 4, sys.byteorder) )
#                 sys.byteorder
            count= count % 10
            sleep( 0.3 )
            count+=1
#             if count == 3:
#                 os.close(fif)
#                 return
#             if count ==9:
#                 return
        
        
    except OSError:
        traceback.print_exc()
        print ( "Failed to create FIFO: " + fifoName )
    else:
        fif.close()
        os.remove(fifoName)
        os.rmdir(os.path.dirname(fifoName))

def main():
    filename= getTempFileName()    
    print( filename )
    try:
        os.mkfifo( filename )
    except:
        print("ruh roh")
    writeThread= Thread( target = write2Fifo, \
                args= ( filename, ) )
    writeThread.daemon= True
    
    readThread= Thread( target = readFromFifo, \
                args= ( filename, ) )
    readThread.daemon= True
    
    writeThread.start()
    sleep(0.4)
    readThread.start()
    
    writeThread.join()
    readThread.join()
    
if __name__ == '__main__':
    main()