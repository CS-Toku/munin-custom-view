
import unittest
import os
import tempfile

from munincustom import utils


class TestSplitDomainhost(unittest.TestCase):

    def test_split_domainhost_with_arg_domain_host(self):
        expected = utils.MachineTuple('domain', 'host')
        self.assertEqual(expected, utils.split_domainhost('domain;host'))

    def test_split_domainhost_with_arg_domain_(self):
        expected = utils.MachineTuple('domain', None)
        self.assertEqual(expected, utils.split_domainhost('domain;'))

    def test_split_domainhost_with_arg_domain(self):
        expected = utils.MachineTuple('domain', 'domain')
        self.assertEqual(expected, utils.split_domainhost('domain'))


class TestLoadDefaultOptions(unittest.TestCase):
    
    temp_file = tempfile.gettempdir() + '/option.yaml'

    def make_sample(self, content):
        open(self.temp_file, 'w').write(content)
        return utils.load_default_options(self.temp_file)
        
    def rm_sample(self):
        os.remove(self.temp_file)

    def test_load_default_options_with_dict(self):
        content = '\n'.join([
                'test:',
                '  param1: a',
                '  param2: b',
                '  param3: c',
                'test2:',
                '  param1: 1',
                '  param2: 2',
                '  param3: 3'
                ])
        obj = self.make_sample(content)
        self.assertTrue(isinstance(obj, dict))
        self.assertTrue('test' in obj)
        self.assertTrue('test2' in obj)
        self.rm_sample()

    def test_load_default_options_with_list(self):
        content = '\n'.join([
                '- param1: a',
                '  param2: b',
                '  param3: c',
                '- param1: 1',
                '  param2: 2',
                '  param3: 3'
                ])
        obj = self.make_sample(content)
        self.assertTrue(isinstance(obj, dict))
        self.assertTrue(0 in obj)
        self.assertTrue(1 in obj)
        self.rm_sample()

    def test_load_default_options_with_invaliddata(self):
        content = ''
        obj = self.make_sample(content)
        self.assertTrue(isinstance(obj, dict))
        self.assertFalse(obj)
        self.rm_sample()

