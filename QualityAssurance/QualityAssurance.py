import os
import unittest
from __main__ import vtk, qt, ctk, slicer
from QALib import *

#
# QualityAssurance
#

class QualityAssurance:
    def __init__(self, parent):
        parent.title = "Quality Assurance" # TODO make this more human readable by adding spaces
        parent.categories = ["Quality Assurance"]
        parent.dependencies = ["Volumes"]
        parent.contributors = ["Dave Welch (UIowa), Hans Johnson (UIowa), Steve Pieper (Isomics)"]
        parent.helpText = """
        Configurable scripted Slicer module for quality assurance that loads INI-like files that define the module GUI and the output database
        """
        parent.acknowledgementText = """
        This file was originally developed by Dave Welch and Hans Johnson, SINAPSE, University of Iowa and was partially funded by NIH grant 3P41RR013218-12S1.    Thanks to Steve Pieper, Isomics, Inc. for guidance and encouragement.
"""
        self.parent = parent

        # Add this test to the SelfTest module's list for discovery when the module
        # is created.    Since this module may be discovered before SelfTests itself,
        # create the list if it doesn't already exist.
        try:
            slicer.selfTests
        except AttributeError:
            slicer.selfTests = {}
        slicer.selfTests['QualityAssurance'] = self.runTest

    def runTest(self):
        tester = QualityAssuranceTest()
        tester.runTest()

#
# qQualityAssuranceWidget
#

class QualityAssuranceWidget:
    def __init__(self, parent = None):
        self.util = QAUtil()
        self.util.CONFIG_FILE = os.path.join(os.path.dirname(slicer.modules.qualityassurance.path), "qualityassurance.cfg.EXAMPLE") # HACK
        self.logger = self.util.getLogger()
        for name in self.util.findModules():
            exec "self.{module} = QAModule(self.logger, '{module}')".format(module=name) in globals(), locals()

        if parent is None:
            self.parent = slicer.qMRMLWidget()
            self.parent.setLayout(qt.QVBoxLayout())
            self.parent.setMRMLScene(slicer.mrmlScene)
        else:
            self.parent = parent
        self.layout = self.parent.layout()
        if parent is None:
            self.setup()
            self.createModuleButtons()
            self.parent.show()

    def setup(self):
        self.logger.debug("Initial setup")
        sm = ctk.ctkCollapsibleButton()
        sm.text = "Avaliable Configurations"
        self.layout.addWidget(sm)
        ml = qt.QVBoxLayout(sm)

        # Setup module selection buttons
        self.moduleButtonMapper = qt.QSignalMapper()
        self.moduleButtonMapper.connect('mapped(const QString&)', self.setupModuleGUI)
        self.createModuleButtons(ml)

        self.moduleWidget = ctk.ctkCollapsibleButton()
        self.moduleWidget.name = "module_gui"
        self.moduleWidget.text = "QA GUI"
        self.layout.addWidget(self.moduleWidget)
        # Instantiate and connect widgets ...

        #
        # Reload and Test area
        #
        reloadCollapsibleButton = ctk.ctkCollapsibleButton()
        reloadCollapsibleButton.text = "Reload && Test"
        self.layout.addWidget(reloadCollapsibleButton)
        reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

        # reload button
        # (use this during development, but remove it when delivering
        # your module to users)
        self.reloadButton = qt.QPushButton("Reload")
        self.reloadButton.toolTip = "Reload this module."
        self.reloadButton.name = "QualityAssurance Reload"
        reloadFormLayout.addWidget(self.reloadButton)
        self.reloadButton.connect('clicked()', self.onReload)

        # reload and test button
        # (use this during development, but remove it when delivering
        # your module to users)
        self.reloadAndTestButton = qt.QPushButton("Reload and Test")
        self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
        reloadFormLayout.addWidget(self.reloadAndTestButton)
        self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

        #
        # Volume Scrolling Area
        #
        scrollingCollapsibleButton = ctk.ctkCollapsibleButton()
        scrollingCollapsibleButton.text = "Volume Scrolling"
        self.layout.addWidget(scrollingCollapsibleButton)
        # Layout within the scrolling collapsible button
        scrollingFormLayout = qt.QFormLayout(scrollingCollapsibleButton)

        # volume selection scroller
        self.slider = ctk.ctkSliderWidget()
        self.slider.decimals = 0
        self.slider.enabled = False
        scrollingFormLayout.addRow("Volume", self.slider)

        # refresh button
        # self.refreshButton = qt.QPushButton("Refresh")
        # scrollingFormLayout.addRow(self.refreshButton)

        # make connections
        # self.slider.connect('valueChanged(double)', self.onSliderValueChanged)
        # self.refreshButton.connect('clicked()', self.onRefresh)

        # make an instance of the logic for use by the slots
        # self.logic = VolumeScrollerLogic()
        # call refresh the slider to set it's initial state
        # self.onRefresh()

        # Add vertical spacer
        self.layout.addStretch(1)

    def createModuleButtons(self, parent):
        count = 1
        while hasattr(self, "Module%d" % count):
            currentModule = getattr(self, "Module%d" % count)
            button = qt.QPushButton()
            button.text = currentModule._name
            button.toolTip = "Show Quality Assurance module %s" % currentModule._name
            button.name = currentModule._name
            parent.addWidget(button)
            self.moduleButtonMapper.setMapping(button, "Module%d" % count)
            button.connect('clicked()', self.moduleButtonMapper, "map()")
            count += 1

    def setupModuleGUI(self, name):
        self.logger.debug("call")
        self.layout.removeWidget(self.moduleWidget)
        self.moduleWidget = eval("self.%s._getGUI()" % name) # Returns ctkCollapsibleButton widget
        self.layout.insertWidget(1, self.moduleWidget)

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = self.inputSelector.currentNode() and self.outputSelector.currentNode()

    def onApplyButton(self):
        logic = QualityAssuranceLogic()
        print("Run the algorithm")
        logic.run(self.inputSelector.currentNode(), self.outputSelector.currentNode())

    def onReload(self,moduleName="QualityAssurance"):
        """Generic reload method for any scripted module.
        ModuleWizard will subsitute correct default moduleName.
        """
        import imp, sys, os, slicer

        widgetName = moduleName + "Widget"

        # reload the source code
        # - set source file path
        # - load the module to the global space
        filePath = eval('slicer.modules.%s.path' % moduleName.lower())
        p = os.path.dirname(filePath)
        if not sys.path.__contains__(p):
            sys.path.insert(0,p)
        fp = open(filePath, "r")
        globals()[moduleName] = imp.load_module(
                moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
        fp.close()

        # rebuild the widget
        # - find and hide the existing widget
        # - create a new widget in the existing parent
        parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent().parent()
        for child in parent.children():
            try:
                child.hide()
            except AttributeError:
                pass
        # Remove spacer items
        item = parent.layout().itemAt(0)
        while item:
            parent.layout().removeItem(item)
            item = parent.layout().itemAt(0)

        # delete the old widget instance
        if hasattr(globals()['slicer'].modules, widgetName):
            getattr(globals()['slicer'].modules, widgetName).cleanup()

        # create new widget inside existing parent
        globals()[widgetName.lower()] = eval(
                'globals()["%s"].%s(parent)' % (moduleName, widgetName))
        globals()[widgetName.lower()].setup()
        setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

    def onReloadAndTest(self,moduleName="QualityAssurance"):
        try:
            self.onReload()
            evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
            tester = eval(evalString)
            tester.runTest()
        except Exception, e:
            import traceback
            traceback.print_exc()
            qt.QMessageBox.warning(slicer.util.mainWindow(),
                    "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")


#
# QualityAssuranceLogic
#

class QualityAssuranceLogic:
    """This class should implement all the actual
    computation done by your module.    The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget
    """
    def __init__(self):
        pass

    def hasImageData(self,volumeNode):
        """This is a dummy logic method that
        returns true if the passed in volume
        node has valid image data
        """
        if not volumeNode:
            print('no volume node')
            return False
        if volumeNode.GetImageData() == None:
            print('no image data')
            return False
        return True

    def run(self,inputVolume,outputVolume):
        """
        Run the actual algorithm
        """
        return True


class QualityAssuranceTest(unittest.TestCase):
    """
    This is the test case for your scripted module.
    """

    def delayDisplay(self,message,msec=1000):
        """This utility method displays a small dialog and waits.
        This does two things: 1) it lets the event loop catch up
        to the state of the test so that rendering and widget updates
        have all taken place before the test continues and 2) it
        shows the user/developer/tester the state of the test
        so that we'll know when it breaks.
        """
        print(message)
        self.info = qt.QDialog()
        self.infoLayout = qt.QVBoxLayout()
        self.info.setLayout(self.infoLayout)
        self.label = qt.QLabel(message,self.info)
        self.infoLayout.addWidget(self.label)
        qt.QTimer.singleShot(msec, self.info.close)
        self.info.exec_()

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_QualityAssurance1()

    def test_QualityAssurance1(self):
        """ Ideally you should have several levels of tests.    At the lowest level
        tests sould exercise the functionality of the logic with different inputs
        (both valid and invalid).    At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.    For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
                ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
                )

        for url,name,loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                print('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                print('Loading %s...\n' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading\n')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = QualityAssuranceLogic()
        self.assertTrue( logic.hasImageData(volumeNode) )
        self.delayDisplay('Test passed!')
