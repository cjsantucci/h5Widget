from guiUtil.guidata import guiData
import guiUtil.fileSelect as fsel
from guiUtil.scroll_control import scroll_control  
from PyQt5.Qt import *
import re
import sys
import functools as ft
from guiUtil.gUBase import gUWidgetBase

class procWindow( QMainWindow ):
    
    def __init__( self, parent= None ):
        QMainWindow.__init__( self, parent )
        allowClose= True
    
    def closeEvent( self, event ):
        # do stuff
        if self.allowClose:
            event.accept() # let the window close
        else:
            event.ignore()

class App( QWidget, gUWidgetBase ):
    """
    Gui interface to hdf5 converter.
    The utility to this could be argued to be limited
    Except that it required me to build all of the underlying tools
    like prefernce defaults, fileSelector stuff, etc.
    """
    def _initGuiData( self, persistentDir= None, persistentFile= None, **kwargs ):
        
        idd= { "cbAm4": False,
              "cbBeam": False, 
              "cbCpi": False,  
              "cbChannel": False,
              "cbOverwrite": False, 
              "cbPdi": True, 
              "rbYh5": True, 
              "cbSourceBeam": False,
              "cbToTempFile": True,
              "cbProcessStatusWindow": True,
              "cbByBeginLetter": True,
              "cbWriteChunks": True,
              "cbWriteAll": True,
              "h5ScriptDefault": "/home/chris/h5Sim.py"
            }
        guiDataObj= guiData( persistentDir= persistentDir, \
                               persistentFile= persistentFile, \
                               prefGroup= "h5Tab/guiDefaults", \
                               initDefaultDict= idd )
        
        """
        these must be named EXACTLY as above with Str on the end
        to preserve gui functionality.
        """
        guiDataObj.__dict__.update( { "cbAm4Str": "-a",
                                  "cbBeamStr": "-b",
                                  "cbCpiStr": "-c",
                                  "cbChannelStr": "-ch",
                                  "cbOverwriteStr": "-o",
                                  "cbPdiStr": "-p",
                                  "cbSourceBeamStr": "-s",
                                  "cbToTempFileStr": "-t",
                                  "cbByBeginLetterStr": "-l",
                                  "cbWriteChunksStr": "-k",
                                  "cbWriteAllStr": "-w"
                                } )
        
        self.guiData= guiDataObj

        h5ExecuteString= property()

    def _getGuiDataStrsAndDefaults( self, typeStr ):
        defDict= self.guiData.defDict.copy()
        
        defaultKeys= [ aKey for aKey in defDict.keys()
                      if re.search( "^" + typeStr, aKey ) ]
        
        strKeys= [ aKey for aKey in self.guiData.__dict__ 
                  if re.search( "^" + typeStr, aKey ) and aKey.endswith( "Str" ) ]

        return sorted( defaultKeys ), sorted( strKeys )

    def __init__( self, parent, \
                  topWidget, \
                  **kwargs ):
        
        QWidget.__init__( self, parent )
        gUWidgetBase.__init__( self, **kwargs )
        
        self.topWidget= topWidget
        
        self._initGuiData( **kwargs )
        
        dlgwidth= 500
        dlgheight= 50
        
        centerPoint= self.centerOfScreenForCurrentMouse()
        self.setGeometry( QRect( centerPoint.x()-dlgwidth/2, centerPoint.y()-dlgheight/2, dlgwidth, dlgheight ) )
        
        self._setupRB()
        self._setupCB()
        self._setupPB()
        self._setupFileSelect()
        self._setupLayout()
        
        if self.rbYh5.isChecked():
            self.exeh5()
    
    def processH5Text( self ):
        cmd= [ self.fileSelecth5Script.getComboItems()[0] ]
        tmFiles= self.tmSelect.getComboItems()
        if len( cmd ) == 0 or len( tmFiles ) == 0:
            return
        
        aCBKeyList, aCBStrList= self._getGuiDataStrsAndDefaults( "cb" )
        for aCB, aCBStr in zip( aCBKeyList, aCBStrList ):
            if getattr( self, aCB ).isChecked():
                cmd.append( getattr( self.guiData, aCBStr ) )
        
        am4List= self.fileSelectAm4.getComboItems()
        if len( am4List ) > 0 and am4List[0] != "":
            cmd= cmd + [ "--am4Dict", am4List[0] ]

        cmd= cmd + [ "-f", tmFiles[ 0 ] ]        
        
        return cmd
        
     
    def _setupLayout( self ):
        layout= QGridLayout()
        self.setLayout( layout )
        
        self.layoutRow= 0
        layout.addWidget( self.rbGB, 0, 0 )
        
        layout.addWidget( self.h5CB, self.incrementLayoutRow(), 0 )
        
        fileSelectNames= [ "fileSelectAm4", "tmDictSelect", "tmSelect", "fileSelecth5Script" ]
        for aName in fileSelectNames:
            layout.addWidget( getattr( self, aName ).ComboBox, self.incrementLayoutRow(), 0 )
            layout.addWidget( getattr( self, aName ).PushButton, self.incrementLayoutRow(), 0 )
            layout.addWidget( QLabel(""), self.incrementLayoutRow(), 0 )
            if aName == "tmDictSelect":
                self.checkboxTmDir= QCheckBox( "TM directory select:" )
                layout.addWidget( self.checkboxTmDir, self.incrementLayoutRow(), 0 )
        
        self.checkboxTmDir.setChecked( False )
        self.checkboxTmDir.clicked.connect( self._setTmSelectDirOrFile )
        self.tmSelect.selectDir= False
        
        layout.addWidget( self.pbExecuteH5, self.incrementLayoutRow(), 0 )
  
    def _setTmSelectDirOrFile( self ):
        self.tmSelect.selectDir= self.checkboxTmDir.checkState()
  
    def _setupFileSelect( self ):
        self.fileSelectAm4= fsel.pb_combo_selector( 
                        guiDataObj= self.guiData, 
                        buttonstr= "AM4 Dictionary Select", 
                        caption= "Select Dictionary", 
                        groupSubCat= "fileSelAm4",
                        allowBlankSelection= True
                       )
        
        self.tmDictSelect= fsel.pb_combo_selector( 
                        guiDataObj= self.guiData, 
                        buttonstr= "TM Dictionary Select", 
                        caption= "Select Dictionary", 
                        groupSubCat= "fileSelDictTM",
                        allowBlankSelection= True
                       )
        
        self.tmSelect= fsel.pb_combo_selector( 
                        guiDataObj= self.guiData, 
                        buttonstr= "TM File Select", 
                        caption= "Select File", 
                        groupSubCat= "fileSelTM",
                        selectDir= True
                       )

        self.fileSelecth5Script= fsel.pb_combo_selector( \
                                guiDataObj= self.guiData, \
                                buttonstr= "Select h5 Script", \
                                caption= "Select h5Script", \
                                defaultFileList= [ self.guiData.h5ScriptDefault ] ,
                                groupSubCat= "fileSelh5Script"
                               )
  
    def resetGuiDefaults( self ):
        self.guiData.resetStoredDefaults()
        self.fileSelectAm4.guiData.resetStoredDefaults()
        self.fileSelecth5Script.guiData.resetStoredDefaults()
        self.tmSelect.guiData.resetStoredDefaults()
        self.tmDictSelect.guiData.resetStoredDefaults()
        
        """
        reset check box values
        """
        defaultKeysCB, _= self._getGuiDataStrsAndDefaults( "cb" )
        [ getattr( self, aKey ).setChecked( getattr( self.guiData, aKey ) ) 
         for aKey in defaultKeysCB ]
        
        """
        reset file selection lists
        """
        selectNames= [ "fileSelectAm4", "tmDictSelect", "tmSelect" ]
        for aName in selectNames:
            getattr( self, aName ).ComboBox.clear()
            getattr( self, aName ).ComboBox.addItems([])
        
        self.fileSelecth5Script.ComboBox.clear()
        self.fileSelecth5Script.ComboBox.addItems( [self.guiData.h5ScriptDefault] )
        
        self.rbYh5.setChecked( self.guiData.rbYh5 )
        self.rbYh5.setChecked( not self.guiData.rbYh5 )
        
    def incrementLayoutRow( self ):
        self.layoutRow += 1        
        return self.layoutRow
    
    def exeh5( self ):
        cmd= self.processH5Text()
        onStartup= False
        if self.cbProcessStatusWindow.isChecked():
            onStartup= True
        
        inputdict= {
            "processRect": QRect( 0, 50, 798, 50 ), \
            "statusRect": QRect( 0, 101, 798, 320 ), \
            "app": self.getQApp(), \
            "qmw": procWindow(), \
            "onStartup": onStartup, \
            "processCommand": cmd, \
             }
        
        try:
            self.scObj= scroll_control( persistentDir= self.guiData.persistentDir,\
                                        persistentFile= self.guiData.persistentFile, \
                                        prefGroup= "/process_scroll_control", \
                                        **inputdict )
            
            if onStartup:
                self.scObj.qcb.setEnabled( False )
                
            self.scObj.qmw.setWindowTitle("Window for h5 conversion process")
            self.scObj.scroller._pyqtSigFinished.connect( self.procFinished )
            self.scObj.qmw.show()
            self.pbExecuteH5.setEnabled( False )
            self.scObj.qmw.allowClose= False
        except:
            self.pbExecuteH5.setEnabled( True )
            self.scObj.qmw.allowClose= True
    
    @pyqtSlot()
    def procFinished( self ):
        self.pbExecuteH5.setEnabled( True )
        self.scObj.qmw.allowClose= True
#         os.system( fileList[0] )
    
    def _setupPB( self ):
        self.pbExecuteH5= QPushButton( "Process .h5 File" )
        self.pbExecuteH5.clicked.connect( self.exeh5 )
        
    def _cbSave( self, aKey ):
        setattr( self.guiData, aKey, getattr( self, aKey ).isChecked() )
        self.guiData.save( aKey )
  
    def _setupCB( self ):
        layout= QGridLayout()
        self.h5CB= QGroupBox( )
        self.h5CB.setTitle( "h5 file options" )
        self.h5CB.setLayout( layout )
        
        defaultKeys, _= self._getGuiDataStrsAndDefaults( "cb" )

        checkBoxList= []
        for aKey in defaultKeys:
            cbStrType= aKey.split( "cb" )[-1]
            cbStrType= cbStrType[0].lower() + cbStrType[1:]
            if hasattr( self.guiData, aKey + "Str" ):
                cbStr= cbStrType + ": " + getattr( self.guiData, aKey + "Str" )
            else:
                cbStr= cbStrType
            
            # e.g., self.cbPdi= QCheckBox( ... )
            setattr( self, aKey, QCheckBox( cbStr ) )
            checkBoxList.append( getattr( self, aKey ) )
            
            # e.g., self.cbPdi.setChecked= self.guiData.cbPdi   
            getattr( self, aKey ).setChecked( getattr( self.guiData, aKey ) )
            
            # self.guiData.save( ["cbPdi"] )
            getattr( self, aKey ).clicked.connect( ft.partial( self._cbSave, aKey ) )
            
            
        nCols= 4
        row= 0
        col= 0
        for aCB in checkBoxList:
            layout.addWidget( aCB, row, col )
            col += 1
            if col >= nCols:
                col= 0
                row += 1
        
        self.cbWriteAll.clicked.connect( self._checkWriteAll )
        
        self.cbWriteChunks.setEnabled( False )
        
        self._checkWriteAll()
            
    def _checkWriteAll( self ):
        if self.cbWriteAll.checkState():
            flag= False
        else:
            flag= True
            
        cbNames= [ 'cbPdi', 'cbCpi', 'cbBeam', 'cbSourceBeam', 'cbChannel' ]
        
        [ getattr( self, aName ).setChecked( flag ) 
         for aName in cbNames if hasattr( self, aName ) ]
        
        [ getattr( self, aName ).setEnabled( flag ) 
         for aName in cbNames if hasattr( self, aName ) ]
    
    def _setupRB( self ):
        layout= QGridLayout()
        
        self.rbYh5 = QRadioButton( "Yes" )
        self.rbYh5.setChecked( self.guiData.rbYh5 )
        self.rbYh5.clicked.connect( ft.partial( self.selYes, yesClicked= True ) ) 

        self.rbNh5 = QRadioButton( "No" )
        self.rbNh5.setChecked( not self.guiData.rbYh5 )
        self.rbNh5.clicked.connect( ft.partial( self.selYes, yesClicked= False ) ) 

        self.rbGB= QGroupBox( )
        self.rbGB.setTitle( "Auto-generate h5 files on open" )
        layout.addWidget( self.rbYh5, 0, 0 )
        layout.addWidget( self.rbNh5, 0, 1 )
        self.rbGB.setLayout( layout )
    
    def selYes( self, yesClicked= True ):
        self.guiData.rbYh5= yesClicked
        self.guiData.save( "rbYh5" )
    
    
            
def main(): 
    app = QApplication( sys.argv )
    ex = App( "~/.jpExtend" )
    ex.show()
    sys.exit( app.exec_() )
    
if __name__ == '__main__':
    main()