import sys
from PyQt4 import QtGui
from PyQt4.QtCore import Qt
import ControlCreator

class AddAppDialog(QtGui.QDialog):
    def __init__(self, app_list):
        super(AddAppDialog, self).__init__()
        self.app_list = app_list
        self.initUI()

    def initUI(self):
        # central = QtGui.QWidget();
        # self.main_scroll = QtGui.QScrollArea();
        # vbox = QtGui.QVBoxLayout(central)
        # self.main_scroll.setWidget(central);
        # self.main_scroll.setWidgetResizable(True);

        vbox = QtGui.QVBoxLayout()

        # Create the list
        self.disp_list = QtGui.QListView()
        self.disp_list.selectionMode = QtGui.QAbstractItemView.ExtendedSelection
        self.disp_list.setAutoScroll(True)
        model = QtGui.QStandardItemModel(self.disp_list)
        for app in self.app_list:
            print app
            item = QtGui.QStandardItem(app)
            model.appendRow(item)

        self.disp_list.setModel(model)
        vbox.addWidget(self.disp_list)

        # addAppButton = QtGui.QPushButton('Add Apps')
        # # addAppButton.clicked.connect(self.onClickAddApp)
        # cancelButton = 
        self.buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel,
            Qt.Horizontal, self)
        vbox.addWidget(self.buttons)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)        
        # vbox.addWidget(addAppButton)

        self.setLayout(vbox)
        self.setGeometry(300, 300, 300, 400)
        self.setWindowTitle('Available MOOS Apps')

    def onClickAddApp(self):
        self.close()

    def getSelectedItems(self):
        # It gives indices not items
        print self.disp_list.selectedIndexes()
        app_names = [str(self.disp_list.model().item(index.row()).text()) for index in 
            self.disp_list.selectedIndexes()]

        # print "Selected Rows:"
        # for index in self.disp_list.selectedIndexes():
        #     print index.row()
        #     print self.disp_list.model().item(index.row()).text()
        # for index in self.disp_list.selectedIndexes:
        #     app_names.append(self.disp_list.model.item(0).text())
        return app_names

    @staticmethod
    def getNewApps(app_list, parent = None):
        dialog = AddAppDialog(app_list)
        result = dialog.exec_()

        return (dialog.getSelectedItems(), result == QtGui.QDialog.Accepted)
