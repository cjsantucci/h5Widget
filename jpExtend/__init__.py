
import argparse

import jpExtend
import os, sys, tempfile

frameLineColor= [0.8, 0.8, 0.8]
# matploblib_backend= "TkAgg"
matploblib_backend= "Qt5Agg"

def getTempFileName( name= "jpExtendFifo" ):
    tmpdir = tempfile.mkdtemp()
    filename = os.path.join( tmpdir, name )
    
    return tmpdir, filename

def fakeJP( fifoName= None ):
    if fifoName is not None:
        tmpdir, fifoName= getTempFileName( name= "fakeJP" )
    jpExtend.fakeFifo.write2Fifo( fifoName )

def commonArgParser( argv ):
    parser= argparse.ArgumentParser( description= "General Argument Parser For JP Python extension" )
    parser.add_argument( [ "-f", "--fifo" ], type=str, help="fifo file for inter-process comm." )
    sys.exit()