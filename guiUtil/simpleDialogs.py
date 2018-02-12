
import os
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit
from PyQt5.QtWidgets import QFileDialog, QMainWindow, QMessageBox
from PyQt5.QtGui import QIcon
import sys

from guiUtil.guidata import guiData
from guiUtil.gUBase import gUWidgetBase 
import guiUtil
 
class App( QWidget , gUWidgetBase ):
 
    def __init__( self, parent, caseStr= "open", fileFilter= "All Files (*)", \
                  window_title= None, msg= None, **kwargs ):
        
        QWidget.__init__( self, parent )
        gUWidgetBase.__init__( self, **kwargs )
        
        self.fileFilter= fileFilter
        self.msgbox_selection= None
        self.saveFile= None
        self.selected_files= None
        
        self._setCaseStr( caseStr )
        if self.case == "MSGBOX":
            assert msg is not None, "must set message if case is message box"
            
        self._window_title= window_title
        
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        
        
        idd= { "directory": [ guiUtil.gUBase.home() ] }
        self._initGuiData( idd= idd, **kwargs )
            
        self._initUI( msg= msg, **kwargs )
    
    def _setCaseStr( self, caseStr ):
        allowedCases= [ "multi_open", "open", "save", "msgbox" ]
        self.case= None
        for aCase in allowedCases:
            if caseStr.upper() == aCase.upper():
                self.case= aCase.upper()
        assert self.case is not None, "Case not allowed: " + caseStr

    def _initUI( self, msg= None, **kwargs ):
        
        self.setGeometry( self.left, self.top, self.width, self.height )
 

        if self.case == "OPEN":
            if self._window_title is None:
                self._window_title= "Open"
            
            self._openFileNameDialog()
            
        elif self.case == "MULTI_OPEN":
            if self._window_title is None:
                self._window_title= "Multi Open"
            
            self._openFileNamesDialog()
            
        elif self.case == "SAVE":
            if self._window_title is None:
                self._window_title= "Save"
            
            self._saveFileDialog()
        
        elif self.case == "MSGBOX":
            self._msgBox( msg= msg )
 
    def _openFileNameDialog( self ):    
        options= QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName( self,"QFileDialog.getOpenFileName()", \
                                                   self.guiData.directory[0], \
                                                   self.fileFilter, \
                                                   options=options)
        
        if len( fileName ) > 0:
            self._saveSelectedDirectory( os.path.dirname( fileName ) )
            self.selected_files= fileName
        else:
            self.selected_files= None
    
    def _openFileNamesDialog( self ):    
        options= QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, self._window_title, \
                                                self.guiData.directory[0], \
                                                self.fileFilter, \
                                                options=options)
        
        if len( files ) > 0:
            self._saveSelectedDirectory( os.path.dirname( files[0] ) )
            self.selected_files= files
        else:
            self.selected_files= None

    def _saveSelectedDirectory( self, dirName ):
        if os.path.isdir( dirName ):
            self.guiData.directory= [ dirName ]
            self.guiData.save( "directory" )

    def _msgBox( self, msg ):
    
        reply = QMessageBox.question(self, 'Message', 
                         msg, QMessageBox.Yes, QMessageBox.No)
    
        if reply == QMessageBox.Yes:
            self.msgbox_selection= True
        else:
            self.msgbox_selection= False
    
    def _saveFileDialog( self ):    
        options= QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        
        fileName, _ = QFileDialog.getSaveFileName(self, self._window_title, \
                                                  self.guiData.directory[0], \
                                                  self.fileFilter, \
                                                  options=options)
        
        if len( fileName ) > 0:
            self._saveSelectedDirectory( os.path.dirname( fileName ) )
            self.saveFile= fileName
        else:
            self.saveFile= None
  
if __name__ == '__main__':
    app = QApplication(sys.argv)
    qmw= QMainWindow()
    ex = App( qmw, app= app, caseStr= "save" )
    sys.exit(app.exec_())