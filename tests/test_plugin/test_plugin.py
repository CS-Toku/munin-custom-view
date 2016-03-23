
import unittest
import os
import os.path

from munincustom.utils import MachineTuple
from munincustom.plugin import BaseAnalysisClass


class TestBaseAnalysisClass(unittest.TestCase):

    rrd_file = os.path.dirname(__file__) + '/' + 'test.rrd'

    def test_load_rrd(self):
        options = {'start': '-5minutes', 'cf': 'AVERAGE'}
        default = {'start': '-10minutes', 'cf': 'AVERAGE'}
        rrd_data1 = BaseAnalysisClass.load_rrd(self.rrd_file, options, {})
        rrd_data2 = BaseAnalysisClass.load_rrd(self.rrd_file, {}, default)
        rrd_data3 = BaseAnalysisClass.load_rrd(self.rrd_file, options, default)
        self.assertTrue([x[0] for x in rrd_data1] == [x[0] for x in rrd_data3])
        self.assertTrue(len(rrd_data1) < len(rrd_data2))

    def test_BaseAnalysisClass(self):
        tag = 'test'
        mt = MachineTuple('domain', 'host')
        options = {'start': '-5minutes', 'cf': 'AVERAGE'}
        mt_rrd_list = {mt: [(self.rrd_file, options)]}
        mt_rrd_dict = {mt: {'test': (self.rrd_file, options)}}
        rrd_data_list = BaseAnalysisClass(tag, mt_rrd_list)
        rrd_data_dict = BaseAnalysisClass(tag, mt_rrd_dict)
        self.assertTrue(isinstance(rrd_data_list.rrd_data[mt], list))
        self.assertEqual(rrd_data_list.tag, tag)
        self.assertTrue(isinstance(rrd_data_dict.rrd_data[mt], dict))
        self.assertEqual(rrd_data_dict.tag, tag)



