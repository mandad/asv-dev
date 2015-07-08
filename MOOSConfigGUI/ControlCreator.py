from PyQt4 import QtGui
import xml.etree.ElementTree as ET
import pdb
import copy

class ControlCreator(object):
    """Creates Controls from XML configuration file"""
    def __init__(self, filename):
        super(ControlCreator, self).__init__()
        self.filename = filename
        self.app_groups = list()
        self.read_file()

    def read_file(self):
        try:
            self.xml_file = ET.parse(self.filename)
        except Exception, e:
            print 'Problem reading xml file.' + e

    def create_controls(self):
        self.main_vbox = QtGui.QVBoxLayout()

        self.root = self.xml_file.getroot()
        # Loop through the apps
        for moosapp in self.root:
            self.app_groups.append(QtGui.QGroupBox(moosapp.attrib['name']))
            # self.app_groups[-1].addLayout()
            config_list = list();
            print moosapp.attrib['name']

            # Loop through the configuration options, creating controls
            # pdb.set_trace()
            this_grid = QtGui.QGridLayout()
            for i, config in enumerate(moosapp):
                this_grid.addWidget(QtGui.QLabel(config.attrib['name']), i, 0)
                this_grid.addWidget(QtGui.QLineEdit(), i, 1)
            self.app_groups[-1].setLayout(this_grid)
                # config_list.
            self.main_vbox.addWidget(self.app_groups[-1])       