from PyQt5.Qt import *

import getpass as gp
import os
import argparse as ap
import sys
import jpExtend
from jpExtend.qdlgex import h5dialog
from jpExtend.callWidget import boxWidget
from guiUtil.fileSelectListWidget import fileSelectList
from guiUtil.gUBase import gUWidgetBase

class tabMaster( gUWidgetBase ):
    """
    Main constructor of all of the tabs
    """

    def __init__( self, app= None, qmw= None, *args, **kwargs ):
        
        gUWidgetBase.__init__( self, **kwargs )
        
        width= 900
        height= 250
        

#         menu.addAction( QAction('50%', menu) )
#         app.addWidget( QMenu( "File" ) )
        tabs    = QTabWidget()
        self.qmw.setCentralWidget( tabs )

        
        tab1    = h5dialog( **kwargs )
        tabs.addTab( tab1, "h5Diaglog" )
        
        tab2    = boxWidget( \
                             leftRect= QRect( 5, 50, 230, 300 ), leftClearButtonLoc= ( 10, 370 ), \
                             leftPrefGroup= "plt_tab/L1", \
                             rightRect= QRect( 250, 50, 200, 300 ), rightClearButtonLoc= ( 250, 370 ), \
                             rightPrefGroup= "plt_tab/L2", \
                             boxPrefGroup= "plt_tab/other", \
                             **kwargs )
        tabs.addTab( tab2, "plt_exe" )
#         p= tab1.palette()
#         tab1.setAutoFillBackground( True );
#         p.setColor( tab1.backgroundRole(), Qt.gray )    
#         tab1.setPalette( p )

        tab3    = QWidget()
        tab4    = QWidget()
        
        tabs.addTab( tab3, "Tab 2" )
        tabs.addTab( tab4, "Tab 3" ) 
        tabs.resize(500, 150)
        
        tabs.setCurrentIndex(1)
        
        #         qmw.
        menu= qmw.menuBar()
        bm= QMenu( "Reset Defaults" )
        menu.addMenu( bm  )
        
        bl= bm.addMenu( "h5Pref" )
        bl.addAction( "Reset to Defaults", tab1.resetGuiDefaults )
        
        bl2= bm.addMenu( "plot pref" )
        bl2.addAction( "Reset to Defaults", tab2.resetGuiDefaults )
        
        centerPoint= tab1.centerOfScreenForCurrentMouse()
        qmw.setGeometry( QRect( centerPoint.x()-width/2, centerPoint.y()-height/2, width, height ) )
        
        qmw.show()
        app.processEvents()
        sys.exit(app.exec_())

def init( persistenDir ):
    user= gp.getuser()
    homedir = os.environ[ 'HOME' ]
    pDir= os.path.join( homedir, persistenDir )
    
    if not os.path.isdir( pDir ):
        os.makedirs( pDir )
    
    return pDir
# end init 

def main( argv ):

    app     = QApplication( argv )
#         app.setStyle(QStyleFactory.create("Plastique"))
    qmw     = QMainWindow()
    qmw.setWindowTitle( "Python h5 Plotter" )
    
    pDir= init( ".jpExtend" )
    tabMaster( argv[1:], persistentDir= pDir, parent=qmw, app= app, qmw= qmw, persistentFile= "jpePref.h5" )

if __name__ == "__main__": 
    main( sys.argv )