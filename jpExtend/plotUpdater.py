#!/usr/local/bin/anaconda3/bin/python
import argparse as ap
import functools as ft
import importlib
import inspect
import matplotlib
from matplotlib import pyplot as plt
import multiprocessing
from multiprocessing import queues
import numpy as np
import os
import re
import sys
import traceback
import warnings

from guiUtil.gUBase import gUWidgetBase
from bokeh.core.tests.test_query import plot
import jpExtend

debugPrints= False

class updateListElement( object ):
    
    def __init__( self, ax= None, \
                  xAlign= None, \
                  updateMethod= None, \
                  name= None ):
        
        self._ax= ax
        self._xAlign= xAlign
        self._updateMethod= updateMethod
        self._updateObj= None
        self._name= None
        self.register( ax= ax, \
                       xAlign= xAlign, \
                       updateMethod= updateMethod,\
                       name= name )

            
    def _getAx( self ):
        return self._ax
    
    def _setAx( self, inAx ):
        assert isinstance( inAx, plt.Axes )
        self._ax= inAx
    
    def _get_name( self ):
        return self._name
    
    def _set_name( self, inName ):
        assert isinstance( inName, str )
        self._name= inName
    
    def _get_xAlign( self ):
        return self._xAlign
    
    def _set_xAlign( self, inData ):
        assert isinstance( inData, np.ndarray ) and len( inData.shape ) == 1
        
        self._xAlign= inData
    
    def _get_updateMethod( self ):
        return self._updateMethod
    
    def _set_updateMethod( self, val ):
        assert inspect.ismethod( val ) or isinstance( val, ft.partial ), "must be instance method or functools.partial"
        self._updateMethod= val
    
    def register( self, \
                  ax= None, \
                  xAlign= None, \
                  updateMethod= None,\
                  name= None ):
        """
        register an axis for being updated.
        """
        if ax is not None and xAlign is not None:
            self.ax= ax
            self.xAlign= xAlign
            
        elif ax is None and updateMethod is not None:
            self.ax= ax
            self.updateMethod= updateMethod
        
        elif ax is None:
            self.ax= ax
    
    def update( self, frame, putInBack= False ):
        """
        default axis update
        """
        if debugPrints:
            print("SinglePlotUpdate")
            print("plt.isinteractive: " + str(plt.isinteractive()))
            
        if self.updateMethod is not None:
            self.updateMethod.__call__( frame )
        else:
            assert self.ax is not None, "must have defined update axis"
            assert self.xAlign is not None, ""
            
        
        """
        This is the default update method for timeseries based plots.
        """
        ylim= self.ax.get_ylim()
        if self._updateObj is None:
            self._updateObj= self.ax.plot( [ self.xAlign[0] , self.xAlign[0] ], \
                                           ylim, \
                                           color= jpExtend.frameLineColor, \
                                           )[0]
        
        if putInBack:
            self._updateObj.set_zorder(0)
        
        if frame < 0 or frame >= len( self.xAlign ):
            self._updateObj.set_visible( True )
        else:
            self._updateObj.set_xdata( [self.xAlign[frame], self.xAlign[frame]] )
            self._updateObj.set_ydata( ylim )
            self._updateObj.set_visible( True )
        
        if debugPrints:
            print("updating canvas")
        
        ax= self.ax    
        ax.get_figure().canvas.draw()

        if debugPrints:
            print( "past show ")
    
    updateMethod= property( _get_updateMethod, _set_updateMethod )
    ax= property( _getAx, _setAx )
    xAlign= property( _get_xAlign, _set_xAlign )
    name= property( _get_name, _set_name )

class plotUpdater( object ):
    """
    class which contains list of update objects for different axes
    """
    def __init__( self, *args, \
                  multproc= False, \
                  multiprocQueue= None, \
                  **kwargs ):
        
#         assert not plt.isinteractive(), "multiproc mode cannot use plt.ion()"
        
        self._updateList= []
        
        assert isinstance( multproc, bool )
        self.multproc= multproc
        
        if multiprocQueue is not None:
            assert isinstance( multiprocQueue, queues.Queue )
            self.multiprocQueue= multiprocQueue
    
    def __len__( self ):
        return len( self._updateList )
    
    def updatePlots( self, frame, putInBack= False, startIndex= 0 ):
        """
        update everything I have a record of
        """
        popIdxs= []
        for idx, anUpdate in enumerate( self._updateList ):
            if idx >= startIndex:
                
                if debugPrints:
                    print( "updating " + str(len(self._updateList)) + " plots" )
                    
                try:
                    if anUpdate.ax is None or \
                        not plt.fignum_exists( anUpdate.ax.figure.number ):
                        
                        popIdxs.append(idx)
                        
                    else:
                        if debugPrints:
                            print("update " + str( idx+1 ) + "of " + str( len(self._updateList) ) )
                        anUpdate.update( frame, putInBack= putInBack )
                        
                except:
                    popIdxs.append( idx )
                    nameStr= ""
                    if hasattr( anUpdate, "name" ):
                        nameStr= str( getattr( anUpdate, "name" ) )
                    warnings.warn( "update failed: " + nameStr )
        
        if len( popIdxs ) > 0:
            popIdxs.reverse()
            [ self._updateList.pop( idx ) for idx in popIdxs ]
    
    def executePlots( self, fileList, mainMethodsList,  tmObj, frame= None, xDataVar= None, **kwargs ):
        """
        execute all selected files
        """
        if debugPrints:
            print("in Execute Plots")
            
        preLenOfUpdates= len( self._updateList )
        
#         if not self.multproc:
#             plt.ion()
        for aFile, aMain in zip( fileList, mainMethodsList ):
            try:
                if debugPrints:
                    print("main running for: " + aFile)
                    
                aMain( tmObj, \
                           block= False, \
                           show= True, \
                           jpEObj= self, \
                           xDataVar= xDataVar ) 
                
                if debugPrints:
                    print("main run for: " + aFile)
                
                if frame is not None:
                    self.updatePlots( \
                                     frame, \
                                     putInBack= True, \
                                     startIndex= preLenOfUpdates 
                                   )
                    
            except:
                traceback.print_exc()
                warnings.warn( "Plot didn't work: " + aFile )
        
        if not self.multproc:
            plt.show( block= False )
        if debugPrints:
            print("out of execute")
    
    
    def disconnect( self ):
        """
        stop updating plots
        """
        self._updateList= []
     
    def append( self, inUpdate ):
        """
        insert plots into list
        """
        assert isinstance( inUpdate, updateListElement )
        self._updateList.append( inUpdate )
        
    def register( self, **kwargs ):
        """
        insert plots into update list--default update
        """
        self.append( updateListElement( **kwargs ) )

    def mpUpdateLoop( self ):
        """
        multiprocessing loop which does not work because matplotlib backends
        """
        assert self.multproc, "only to be used when multiprocessing"
        
        q= self.multiprocQueue
#         plt.ion()
#         plt.draw()
#         plt.pause(.001)
        while True:
            try:
                print("here")
                try:
                    frame= q.get(timeout= 2)
                except:
                    continue
                
                self.updatePlots( frame )
                if len( self._updateList ) == 0:
                    sys.exit()
                print("here2")
            except:
                traceback.print_exc()
                sys.exit()
        

"""give me to multiprocess.Process"""
def multiprocessRunner( \
                        fileList, mainMethodsList, tmObj, frame, \
                        *args, \
                        **kwargs, \
                      ):
    
    """
    currently not working because of backend issues.
    """
    
    pObj= plotUpdater( **kwargs )
    pObj.executePlots( fileList, mainMethodsList, tmObj, frame, **kwargs )
                    
    if pObj.multproc:
        pass
#         pObj.mpUpdateLoop()
        
def plotDeco( inFunc ):
    func2run= inFunc
    
    def extraFUNCTIONality( *args, jpEObj= None, **kwargs ):
        if isinstance( args[0], str ):
            if args[0].endswith(".h5"):
                pass #load tm here
        
        extraFUNCTIONality.jpEObj= jpEObj
        if jpEObj is None:
            extraFUNCTIONality.register= register
            extraFUNCTIONality.append= append
        else:
            extraFUNCTIONality.register= jpEObj.register
            extraFUNCTIONality.append= jpEObj.append
        
        func2run( *args, **kwargs )
        
    return extraFUNCTIONality    
  
"""KEEP THIS DUMMY FUNCTION"""
def register( *args, **kwargs ):
    pass      

"""KEEP THIS DUMMY FUNCTION"""
def append( *args, **kwargs ):
    pass      

def getMains( inList ):
    outFiles= []
    outMains= []
    for aFile in inList:
        try:
            dotFile= ".".join( aFile.split( "." )[:-1] )
            modName= os.path.basename( dotFile )
            modPath= os.path.dirname( dotFile )
            dotFile= re.sub( os.path.sep, ".", modPath ).lstrip(".") 
#             print(dotFile)
#             print(modName)
            dyn_mod= importlib.import_module( modName, dotFile )
#             print(dyn_mod)
            mainMethod= getattr( dyn_mod, "main" )
            outFiles.append( aFile )
            outMains.append( mainMethod )
        except:
            print("Dynamic Module: " + dyn_mod)
            traceback.print_exc()
            warnings.warn( "Couldn't import main " + aFile )
    
    return outFiles, outMains

def main( argv, **kwargs ):
    args= parseArgs( argv )
    fileList= args.files.split(",")
    fileList = [ aFile.strip() for aFile in fileList ]
    fileList, mainMethodsList= getMains( fileList )
    if len( fileList ) == 0:
        return
    tmObj= args.tmFile #update here
    pObj= plotUpdater( **kwargs )
    pObj.executePlots( fileList, mainMethodsList, tmObj, xDataVar= args.xDataVar, **kwargs )
    plt.show()
    
def parseArgs( argv ):
    """
    support calls from popen
    """
    print(argv)
    parserObj= ap.ArgumentParser()
    parserObj.add_argument("--files", default= None, type= str, help= "name of FIFO to communicate TO parent.")
    parserObj.add_argument("--tmFile", default= None, type= str, help= "tm or h5 file.")
    parserObj.add_argument("--xDataVar", default= None, type= str, help= "tm or h5 file.")
    parserObj.add_argument("--verbose", default= 0, type= int, help= "increase command line output text" )
    args= parserObj.parse_args( argv[1:] )
    
    return args

if __name__ == '__main__':
    main( sys.argv )