import ConfigParser as cParser
import logging, logging.handlers
import os

import slicer

class QAUtil(object):

    def init(self):
        self.CONFIG_FILE = ""

    def findModules(self):
        """

        Reads the Names value from QAUtil.CONFIG_FILE and return a list

        Returns a list module names
        """
        cfile = self.CONFIG_FILE
        modules = []
        config = cParser.SafeConfigParser()
        config.read(cfile)
        assert config.has_section('Module1'), "Error: Configuration file error: %s" % cfile
        count = 1
        while config.has_section("Module%s" % count):
            modules.append("Module%s" % count)
            count += 1
        assert len(modules) > 0, "Error: No module configuration files found!"
        return modules

    def getLogger(self):
        logFile = os.path.join(os.environ['TMPDIR'],  'qualityassurance.log')
        logging.basicConfig(filename=logFile,
                            level=logging.DEBUG,
                            format='%(module)s.%(funcName)s - %(levelname)s: %(message)s')

        logger = logging.getLogger(__name__)
        return logger


def parseList(parserStr):
    output = parserStr.split(',')
    output = [out.strip() for out in output]
    return output
