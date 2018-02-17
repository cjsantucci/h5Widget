'''
Created on Feb 16, 2018

@author: chris
'''
import functools as ft
import inspect
from matplotlib import pyplot as plt
import numpy as np

from guiUtil.gUBase import gUWidgetBase
from bokeh.core.tests.test_query import plot
import jpExtend

class updateListElement( object ):
    
    def __init__( self, ax= None, xAlign= None, updateMethod= None ):
        self._ax= ax
        self._xAlign= xAlign
        self._updateMethod= updateMethod
        self._updateObj= None
        self.register( ax= ax, \
                       xAlign= xAlign, \
                       updateMethod= updateMethod )

            
    def _getAx( self ):
        return self._ax
    
    def _setAx( self, inAx ):
        assert isinstance( inAx, plt.Axes )
        self._ax= inAx

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
                  updateMethod= None ):
        
        if ax is not None and xAlign is not None:
            self.ax= ax
            self.xAlign= xAlign
            
        elif ax is None and updateMethod is not None:
            self.ax= ax
            self.updateMethod= updateMethod
        
        elif ax is None:
            self.ax= ax
    
    def update( self, frame, putInBack= False ):
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
    
    updateMethod= property( _get_updateMethod, _set_updateMethod )
    ax= property( _getAx, _setAx )
    xAlign= property( _get_xAlign, _set_xAlign )

class plotUpdater( object ):
    
    def __init__( self, *args, **kwargs ):
        self._updateList= []
    
    def __len__( self ):
        return len( self._updateList )
    
    def updatePlots( self, frame, putInBack= False, startIndex= 0 ):
        
        popIdxs= []
        for idx, anUpdate in enumerate( self._updateList ):
            if idx >= startIndex:
                if anUpdate.ax is None or \
                    not plt.fignum_exists( anUpdate.ax.figure.number ):
                    
                    popIdxs.append(idx)
                    
                else:
                    anUpdate.update( frame, putInBack= putInBack )
        
        if len( popIdxs ) > 0:
            popIdxs.reverse()
            [ self._updateList.pop( idx ) for idx, _ in enumerate( self._updateList ) ]
        
    def append( self, inUpdate ):
        assert isinstance( inUpdate, updateListElement )
        self._updateList.append( inUpdate )
        
    def register( self, **kwargs ):
        self.append( updateListElement( **kwargs ) )
        
def plotDeco( inFunc ):
    func2run= inFunc
    
    def extraFUNCTIONality( *args, jpEObj= None, **kwargs ):
        extraFUNCTIONality.jpEObj= jpEObj
        if jpEObj is None:
            extraFUNCTIONality.register= register
        else:
            extraFUNCTIONality.register= jpEObj.register
        
        func2run( *args, **kwargs )
        
    return extraFUNCTIONality    
  
def register( *args, **kwargs ):
    pass      

if __name__ == '__main__':
    pass