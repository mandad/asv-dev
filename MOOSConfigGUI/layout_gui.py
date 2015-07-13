import sys
from PyQt4 import QtGui
import ControlCreator
import AddAppDialog
import pdb


class MOOSConfigGUI(QtGui.QWidget):
    
    def __init__(self):
        super(MOOSConfigGUI, self).__init__()
        self.controls = ControlCreator.ControlCreator('moos_config.xml')
        
        self.initUI()
        
    def initUI(self):
        self.controls.create_main_entry()

        addButton = QtGui.QPushButton('Add Config Section')
        saveButton = QtGui.QPushButton("Save .moos")
        cancelButton = QtGui.QPushButton("Close")

        # Event Handlers
        addButton.clicked.connect(self.onClickAddButton)

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(saveButton)
        hbox.addWidget(cancelButton)

        vbox = QtGui.QVBoxLayout()

        # #--------------------
        
        # title = QtGui.QLabel('Title')
        # author = QtGui.QLabel('Author')
        # review = QtGui.QLabel('Review')

        # titleEdit = QtGui.QLineEdit()
        # authorEdit = QtGui.QLineEdit()
        # reviewEdit = QtGui.QTextEdit()

        # grid = QtGui.QGridLayout()
        # grid.setSpacing(10)

        # grid.addWidget(title, 1, 0)
        # grid.addWidget(titleEdit, 1, 1)

        # grid.addWidget(author, 2, 0)
        # grid.addWidget(authorEdit, 2, 1)

        # grid.addWidget(review, 3, 0)
        # grid.addWidget(reviewEdit, 3, 1, 5, 1)

        # # QGridLayout.addWidget (self, QWidget, int row, int column, int rowSpan, 
        # #   int columnSpan, Qt.Alignment alignment = 0)
        
        # # self.setLayout(grid)
        # vbox.addLayout(grid)

        vbox.addWidget(addButton)
        vbox.addWidget(self.controls.main_scroll)
        # vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox) 
        # self.setLayout(self.controls.main_vbox)
        
        self.setGeometry(150, 150, 900, 768)
        self.setWindowTitle('MOOS Mission Configuration')    
        self.show()

    def onClickAddButton(self):
        # add_gui = AddAppDialog.AddAppDialog(self.controls.get_apps())
        # add_gui.exec_()
        selected_apps, ok = AddAppDialog.AddAppDialog.getNewApps(self.controls.get_apps())
        print 'GUI Shown'
        print selected_apps
        
def main():
    app = QtGui.QApplication(sys.argv)
    ex = MOOSConfigGUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()