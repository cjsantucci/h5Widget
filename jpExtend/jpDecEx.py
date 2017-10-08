#!/home/chris/anaconda3/bin/python
'''
Created on Dec 10, 2016

@author: chris
'''
import inspect
import struct
import sys
import time
from matplotlib import pyplot as plt
import numpy as np
import warnings

class decoFigData( object ):
    
    def pop( self, idx ):
        self._axesList.pop( idx )
        self._xDataList.pop( idx )
        self._lineHList.pop( idx )
        self._figList.pop( idx )        
    
    def containsData( self ):
        return len( self._figList ) > 0
    
    def _addfigs( self, inFigs ):
        inFigs= convertToListIfNecessary( inFigs )
        assertListDataype( inFigs, "<class 'matplotlib.figure.Figure'>" )            
        self._figList= self._figList + inFigs
     
    def getfigs( self ):
        """get f"""
        return self._figList
    
    def addxdata( self, inData ):
        """add to the list of xdata into which the frame will index"""
        inData= convertToListIfNecessary( inData )
        assertListDataype( inData, "<class 'numpy.ndarray'>" )
        self._xDataList= self._xDataList+ inData
        
    def getxdata( self ):
        """return list of axes which will update with line"""
        return self._xDataList
    
    def addaxes( self, inAxes ):
        """add to list of axes which will update with frame line"""
        inAxes= convertToListIfNecessary( inAxes )
        assertListDataype( inAxes, "<class 'matplotlib.axes._subplots.AxesSubplot'>" )            
        self._axesList= self._axesList + inAxes
        self._addfigs( [ anAx.figure for anAx in inAxes ] )
        assert len( self._axesList ) == len( self._figList ), "list lengths do not match for figure and list"
    
    def getaxes( self ):
        """get axes"""
        return self._axesList
    
    def addAxAndData( self, ax, xdata ):
        """add ax data pairs/lists"""
        self.addaxes( ax )
        self.addxdata( xdata )
        
    def getlines( self ):
        return self._lineHList
    
    def addlines( self, inLines ):
        """add to list of lines which will update"""
        inLines= convertToListIfNecessary( inLines )
        assertListDataype( inLines, "<class 'matplotlib.lines.Line2D'>" )            
        self._lineHList= self._lineHList + inLines
#     figList= property( getfigs, addfigs )
    axesList= property( getaxes, addaxes )
    xDataList= property( getxdata, addxdata )
    lineHList= property( getlines, addlines )
    figList= property( getfigs )
    
    def __init__( self ):
        self._axesList= []
        self._xDataList= []
        self._lineHList= []
        self._figList= []
 

def decoratedJPFigure( inFunc ):
    """If you declare your function as being decorated by this it will give your plots the ability to update from Jataprobe
    
    Your file must have the following format:
    
    @decoratedJPFigure # must decorate your function
    def somePlottingFunction( filename=None or tmObj=None,  **kwargs or decoFigData= None ) 
        #if you specify tmObj, then one will be create for you.
        #if you specify a filename, then you must create one on your own.
        #if you specify either kwargs or decoFigData one of those objects will come through
            -- without this the decoration is pointless
        
        In the body of your function you would do some plotting
        Then all you need to do is one of the following:
        1. Set decoFigData.fig= matplotlib figure or
        2. set decoFigData.axes= list of matplotlibaxes
        
        Finally,
        You must set decoFigData.xData. This will be indexed into to plot the update vertical line
        
    # Here is how you must call your function from __main__, which must be specified.
    if __name__ == '__main__':
        somePlottingFunction( *sys.argv )
    
    """
    plt.ion()
    func2run= inFunc
    # runs at compile time.
    
    def extraFunctionalityFunc( pythonScriptName, filename, fifoInName, **kwargs ):
        # runs at runtime.
        plotPauseTime= 0.00000001
        
        # Look at the input arguments of the function to run to provide some flexible calling
        args, varargs, varkw, defaults= inspect.getargspec( func2run )
        
        # key word args
        hasKWArgs= not varkw is None
        
        DFD= decoFigData()
        argHash= {}
        argHash[ "DFD" ]= DFD
        argHash[ "jpFifoName" ]= fifoInName
        
#         varkw["DFD"]= DFD
        if "h5Obj" in args:
            pass
        elif "tmbinObj" in args:
            pass
        elif "filename" in args:
            func2run( filename=filename, **argHash )
        elif "filename" in args:
            func2run( filename= filename )
                
        if len( DFD.getxdata() ) == 0:
            return
        
        assert len( DFD.xDataList ) == len( DFD.axesList ), "xData and axes list are not the same length"
        
        axes2Update= DFD.getaxes()
        
        ylimsList= [ anAx.get_ylim() for anAx in axes2Update ]
        xlimsList= [ anAx.get_xlim() for anAx in axes2Update ]
        xData= DFD.xDataList
        for axIdx, anAx in enumerate( axes2Update ):
            DFD.addlines( anAx.plot( [ xlimsList[axIdx][0], xlimsList[axIdx][0] ], [ ylimsList[axIdx][0], ylimsList[axIdx][1] ], c="grey", ls= "--" ) )
                      
        
        frameNumLast= None
        with open(fifoInName, 'r+b', 0) as fifoIn:
            while True:
                if not DFD.containsData( ):
                    return
                plt.pause( plotPauseTime )
                fifoBytes= fifoIn.read(4)
#                 time.sleep(1)
                if len( fifoBytes ) > 0:
                    frameNum = struct.unpack( 'I', fifoBytes )[0]
                    if frameNumLast is None or frameNum != frameNumLast:
                        frameNumLast= frameNum
                        updateAxes( DFD, frameNum, plotPauseTime )
                
#                 try:         
                fifoIn.seek(0)
#                 except:
#                     print("yay")
        
    return extraFunctionalityFunc 

def updateAxes( DFD, frameNum, plotPauseTime ):
    lines= DFD.lineHList
    [ updateAx( DFD, dfdIdx, frameNum, plotPauseTime ) for dfdIdx, _ in enumerate( lines ) ]
    
def updateAx( DFD, dfdIdx, frameNum, pltPauseTime ):
    lines= DFD.lineHList
    figures= DFD.figList
    xDataList= DFD.xDataList
    
    if not ( dfdIdx >= 0 and dfdIdx < len( lines ) ):
        warnings.warn( "index out of bounds")
        
    if plt.fignum_exists( figures[ dfdIdx ].number ):
        lines[dfdIdx].set_xdata( [ xDataList[ dfdIdx ][frameNum], xDataList[ dfdIdx ][frameNum] ] )
    else:
        DFD.pop( dfdIdx )
    
    if not DFD.containsData():    
        plt.draw()
        plt.pause( pltPauseTime )
#     cursor = SnaptoCursor(DFD.fig.get_axes()[0], np.arange(25), np.arange(25)+25)
#     plt.connect('motion_notify_event', cursor.mouse_move)
def assertListDataype( testVarList, inStr ):
    assert type( testVarList ) == type( list() ), "function \"assertMPLType\" must take in a list"
    for anElement in testVarList:
        assert str( type(anElement) ) == inStr, "invalid type in setter, should be type " + inStr + " but is type: " + str( type )  

def convertToListIfNecessary( inList ):
    if type( inList ) == type( list() ):
        return inList
    else:
        return [ inList ]     
    
@decoratedJPFigure
def one( filename= None, **kwargs ):
    lineHandleList= []
    plt.figure()
    ax= plt.subplot(2,1,1)
    
#     plt.show(block=False)
    x=np.arange(25)
    y=np.arange(25)+25
    x= np.arange(25)
    y= np.arange(25)+25
    lines= plt.plot( x, y )
    lines= plt.scatter(x, y)
    ax2= plt.subplot(2,1,2)
    lines2= plt.scatter(x, y)
    mpl.datacursor( [lines,lines2], draggable= True, display= 'multiple' )
    if "DFD" in kwargs.keys():
        kwargs["DFD"].addxdata([x, x])
        kwargs["DFD"].addaxes([ax, ax2])
    plt.grid()
    plt.hold(True)
    ax.set_title( " test plot " )
    ax.set_xlabel( "X" )
    ax.set_ylabel( "Y" )
    plt.draw()
    plt.pause(0.000001)
    plt.show(block= False)
#     time.sleep(2)
#     decoFigData.fig.canvas.draw()
#     time.sleep(2)
    print()
    
@decoratedJPFigure
def two( filename, **kwargs ):
    print("two")

@decoratedJPFigure    
def three( tmObj, **kwargs ):
    print("three")
    
def four():
    print("four")
#     print(count)


if __name__ == '__main__':
    one( *sys.argv )