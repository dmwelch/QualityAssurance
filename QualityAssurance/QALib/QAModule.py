import ConfigParser as cParser
import os, keyring

import slicer, ctk, qt
from pg8000 import DBAPI as sql # Move to QADatabase._getDatabaseType()

import Resources
from QALib import *

Resources.derived_images.printButton("THIS IS A TEST")


class QAModule(object):
    """
    Class to contain parameters from module file and matching database file
    """

    def __init__(self, logger, section):
        """

        Arguments:
        - `section`:
        """
        self.logger = logger
        self.logger.debug("Instantiate QAModule class")
        self.parser = cParser.SafeConfigParser()
        self.parser.read(self._getFullPath("qualityassurance.cfg.EXAMPLE")) # HACK
        self._section = section
        self._name = self._getModuleName()
        self._module = self._getModuleFile()
        self._database = self._getDatabaseFile()
        self.logic = self._getModuleLogic()
        self.parents = None

    def _getDatabaseFile(self):
        return self.parser.get(self._section, "Database")

    def _getModuleFile(self):
        return self.parser.get(self._section, "Module")

    def _getModuleName(self):
        return self.parser.get(self._section, "Name")

    def _getModuleLogic(self):
        return self.parser.get(self._section, "Logic")

    def _getFullPath(self, filename):
        module = "QualityAssurance".lower()
        qaModuleDir = os.path.dirname(eval("slicer.modules.%s.path" % module))
        return os.path.join(qaModuleDir, filename)

    def _getParents(self):
        """

        """
        # Read and construct the GUI from the config file
        self.parser.read(self._getFullPath(self._module))
        # Create the new container
        self.logger.debug("Creating new widget...")
        self.parents = []
        for section in self.parser.sections():
            if self.parser.has_option(section, "root") and self.parser.getboolean(section, "root"):
                print "Appending to parents:", section
                self.parents.append(self.parseWidget(section))
        print "Parents:", self.parents

    def _getGUI(self):
        if self.parents is None:
            self._getParents()
        assert (not self.parents is None) and (len(self.parents) > 0), "Parents did not get set correctly!"
        for parent in self.parents:
            print "Parent.name:", parent.name
            if parent.name == self.parser.get(self._section, "Module").split(".")[0]:  # ctkCollapsibleButton
                print "Parent found:", parent.name
                return parent

    def parseWidget(self, section, parent=None):
        # Construct the widget
        widget = self._getWidgetClass(section)
        layout = self._getWidgetLayout(section, widget)
        # Add the widget to the parent layout
        if not parent is None:
            parent.addWidget(widget)
            self.logger.debug("Adding widget to parent: %s ----> %s" % (widget, parent))
        if layout is None:
            # If widget is a leaf, return the parent layout
            assert not self.parser.has_option(section, "children"), \
                "ConfigurationError: widget %s has children but no layout" % section
            assert not parent is None or self.parser.has_option(section, "root"), \
                "ConfigurationError: no parent and no layout for widget %s" % section
            if parent is None:
                return widget  # Case: root
            return parent
        else:
            # Run recursively...
            children = parseList(self.parser.get(section, "children"))
            self.logger.debug("The children: %s" % children)
            for child in children:
                self.logger.debug("Current child: %s" % child)
                self.parseWidget(child, parent=layout)
            if parent is None:
               return widget
            return parent
        raise Exception("No case covered!")

    def _getWidgetClass(self, section):
        """ Create the widget """
        widgetClass = self.parser.get(section, "widget")
        if widgetClass[0:3] == 'ctk':
            exec("widget = ctk.%s()" % widgetClass)
        elif widgetClass[0] == 'Q':
            exec("widget = qt.%s()" % widgetClass)
        else:
            raise Exception
        # Set the additional parameters
        items = self.parser.items(section)
        for item, value in items:
            if not item in ["widget", "layout", "children", "root"]:
                try:
                    exec("widget.%s = '%s'" % (item, value))
                except Exception, e:
                    try:  # signal to slot
                        eval("widget.connect('%s()', Resources.%s.%s)" % (item, self.logic.strip(".py"), value))
                    except Exception, e:
                        print "widget.connect('%s()', Resources.%s.%s)" % (item, self.logic.strip(".py"), value)
                        raise e  # For DEBUGGING
                    ### print "widget.%s = '%s'" % (item, value)
                    ### raise e  # For DEBUGGING
                    self.logger.error("-*" * 30)
                    self.logger.error("%s in %s raised exception!!!\n" % (section, item))
        self.logger.debug("Generated widget: %s" % widget)
        return widget

    def _getWidgetLayout(self, section, widget):
        """ Construct the layout, if necessary """
        if not self.parser.has_option(section, "layout"):
            self.logger.debug("No layout section: %s" % widget)
            return None
        # This is a parent widget
        layout = self.parser.get(section, "layout")
        layout = layout.strip()
        if layout.lower().startswith('v'):
            self.logger.debug("Layout value: 'Vertical'")
            widgetLayout = qt.QVBoxLayout(widget)
        elif layout.lower().startswith('h'):
            self.logger.debug("Layout value: 'Horizontal'")
            widgetLayout = qt.QHBoxLayout(widget)
        elif layout.lower().startswith('f'):
            self.logger.debug("Layout value: 'Form'")
            widgetLayout = qt.QFormLayout(widget)
        else:
            raise Exception("Layout value is unrecognized:", layout)
        self.logger.debug("widget layout: %s" % widgetLayout)
        return widgetLayout


class QADatabase(object):
    def __init__(self, logger, filename):
        """
        """
        self.logger = logger
        self.logger.debug("Instantiate QADatabase class")
        self.parser = cParser.SafeConfigParser()
        self.parser.read(filename)
        self._type = self._getDatabaseType()
        self._connection = None

    def _getDatabaseType(self):
        sections = self.parser.sections()
        if "Postgres" in sections:
            # TODO: import into global namespace depending on self._type
            # import pg8000 as sql
            return "Postgres"
        elif "MySQL" in sections:
            pass
        elif "SQLite" in sections:
            pass
        elif "Excel" in sections:
            pass
        raise NotImplementedError("Unsupported database format!")

    def _connectToDatabase(self):
        if self._type == "Postgres":
            return self._connectToPostgres()
        else:
            raise NotImplementedError("Unsupported database format!")

    def _connectToPostgres(self):
        host = self.parser.get(self._type, "Host")
        port = self.parser.get(self._type, "Port")
        database = self.parser.get(self._type, "Database")
        user = self.parser.get(self._type, "User")
        password = keyring.get_password(database, user) #TODO: Add support for no password and setting password
        paramstyle = self.parser.get(self._type, "paramstyle")
        self._connection = sql.connect(host=host, port=port, database=database,
                                       user=user, password=password)

    def _open(self):
        if self._connection is None:
            self._connectToDatabase()
        return self._connection.cursor()

    def _close(self, cursor):
        cursor.close()
        self.connection.close()
        self.connection = None

    def runGenericQuery(self, query, inputs):
        cursor = self._open()
        cursor.execute(query, inputs)
        result = None
        try:
            result = cursor.fetchall()
        finally:
            self._close(cursor)
        return result

    def _getQuery(self, section):
        if self.parser.has_option(section, "query"):
            return self.parser.get(section, "query")
        raise Exception("No query option found for %s" % section)

    def _getInputs(self, section):
        if self.parser.has_option(section, "inputs"):
            inputList = parseList(self.parser.get(section, "inputs"))
            inputDict = dict(zip(inputList, [None] * len(inputList))) # Create empty dictionary w/ correct keys
            return inputDict
        raise Exception("No inputs option found for %s" % section)
