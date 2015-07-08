from PyQt4 import QtGui
import xml.etree.ElementTree as ET

class ControlCreator(object):
    """Creates Controls from XML configuration file"""
    def __init__(self, filename):
        super(ControlCreator, self).__init__()
        self.filename = filename
        self.read_file();

    def read_file(self):
        try:
            self.xml_file = ET.parse(self.filename);
        except Exception, e:
            print 'Problem reading xml file.' + e

    def create_controls(self):
        self.root = self.xml_file.getroot();
        
        

        