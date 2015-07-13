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
        self.app_list = list()
        self.read_file()

    def read_file(self):
        try:
            self.xml_file = ET.parse(self.filename)
        except Exception, e:
            print 'Problem reading xml file.' + e
        self.root = self.xml_file.getroot()

    def create_main_entry(self):
        #Create the scrolling box
        central = QtGui.QWidget();
        self.main_scroll = QtGui.QScrollArea();
        vbox = QtGui.QVBoxLayout(central)
        self.main_scroll.setWidget(central);
        self.main_scroll.setWidgetResizable(True);


    def get_apps(self):
        if len(self.app_list) == 0:
            for moosapp in self.root:
                self.app_list.append(moosapp.attrib['name'])
        return self.app_list

    def create_controls(self):
        # Loop through the apps
        for moosapp in self.root:
            # if moosapp.attrib['name'])
            self.app_groups.append(QtGui.QGroupBox(moosapp.attrib['name']))
            self.app_groups[-1].setCheckable(True)
            self.app_groups[-1].setChecked(True)
            config_list = list();
            print moosapp.attrib['name']

            # Loop through the configuration options, creating controls
            # pdb.set_trace()
            this_grid = QtGui.QGridLayout()
            for i, config in enumerate(moosapp):
                this_label = QtGui.QLabel(config.attrib['name'])
                # Display if required and has default value
                if config.attrib['required'] == 'true':
                    this_label.setStyleSheet("QLabel {color : red; }")
                else:
                    this_label.setStyleSheet("QLabel {color : black; }")
                this_grid.addWidget(this_label, i, 0)
                if config.attrib.has_key('default'):
                    default_val = config.attrib['default']
                else:
                    default_val = ''
                this_grid.addWidget(QtGui.QLineEdit(default_val), i, 1)
            self.app_groups[-1].setLayout(this_grid)
                # config_list.
            vbox.addWidget(self.app_groups[-1])
