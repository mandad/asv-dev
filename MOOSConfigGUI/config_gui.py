import sys
from PyQt4.QtGui import *
import pdb
# Create an PyQT4 application object.
a = QApplication(sys.argv)       
 
# The QWidget widget is the base class of all user interface objects in PyQt4.
w = QMainWindow()
 
# Set window size. 
w.resize(900, 768)
 
# Set window title  
w.setWindowTitle("MOOS Mission Configuration") 

# Create main menu
mainMenu = w.menuWidget()
pdb.set_trace()
fileMenu = mainMenu.addMenu('&File')
 
# Add exit button
exitButton = QAction(QIcon('exit24.png'), 'Exit', w)
#exitButton.setShortcut('Ctrl+Q')
exitButton.setStatusTip('Exit application')
exitButton.triggered.connect(w.close)
fileMenu.addAction(exitButton)
 
# Show window
w.show() 
 
sys.exit(a.exec_())