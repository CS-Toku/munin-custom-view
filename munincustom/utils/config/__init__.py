
import os.path
from ConfigParser import ConfigParser

import munincustom
from munincustom.utils.parser import MuninConfigParser

from munincustom.exceptions import FileNotFoundError


class ConfigReader(object):
    default_path = os.path.dirname(__file__)+'/default.conf'
    
    def __init__(self, conf_path=None):
        self.config = ConfigParser()
        self.default_config = ConfigParser()
        self.default_config.read(self.default_path)

        if conf_path is None:
            conf_path = self.default_config.get('mc', 'mc_conf')

        if os.path.isfile(conf_path):
            self.config.read(conf_path)
        else:
            raise FileNotFoundError(conf_path)

    def get(self, sec, opt, default_value=None):
        if self.config.has_section(sec) and self.config.has_option(sec, opt):
            return self.config.get(sec, opt)
        elif default_value is not None:
            return default_value
        elif self.default_config.has_section(sec) and self.default_config.has_option(sec, opt):
            value = self.default_config.get(sec, opt)
            return value.format(__path__=munincustom.__path__[0])
        else:
            return None

    def items(self, sec):
        options = self.config.items(sec) if self.config.has_section(sec) else []
        default_options = self.default_config.items(sec) if self.default_config.has_section(sec) else []

        for opt in default_options:
            if reduce(lambda acc, x: acc and opt[0] != x[0], options, True):
                options.append(opt)

        return options
        


        



