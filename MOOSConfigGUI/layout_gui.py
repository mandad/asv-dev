#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt4 import QtGui
import ControlCreator


class MOOSConfigGUI(QtGui.QWidget):
    
    def __init__(self):
        super(MOOSConfigGUI, self).__init__()
        self.controls = ControlCreator.ControlCreator('moos_config_test.xml')
        
        self.initUI()
        
    def initUI(self):
        self.controls.create_controls()

        saveButton = QtGui.QPushButton("Save .moos")
        cancelButton = QtGui.QPushButton("Close")

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(saveButton)
        hbox.addWidget(cancelButton)

        vbox = self.controls.main_vbox

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



        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox) 
        # self.setLayout(self.controls.main_vbox)
        
        self.setGeometry(150, 150, 900, 768)
        self.setWindowTitle('MOOS Mission Configuration')    
        self.show()
        
def main():
    app = QtGui.QApplication(sys.argv)
    ex = MOOSConfigGUI()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()