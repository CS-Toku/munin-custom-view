#!/bin/env python
#-*- encoding: utf-8 -*-

import datetime

from pyrrd.rrd import RRD
from pyrrd.backend import bindings


class BaseAnalysisClass(object):

    def __init__(self, tag, mt_rrd_dict, cf='AVERAGE',start=None, end=None, resolution=None, **kargs):
        self.rrd_data = {}
        for mt, paths in mt_rrd_dict.items():
            if isinstance(paths, list):
                self.rrd_data[mt] = []
                for rrdfilepath in paths:
                    data = self.load_rrd(rrdfilepath,
                                            cf=cf,
                                            start=start,
                                            end=end, 
                                            resolution=resolution)
                    self.rrd_data[mt].append(data)

            elif isinstance(paths, dict):
                self.rrd_data[mt] = {}
                for k, rrdfilepath in paths:
                    data = self.load_rrd(rrdfilepath,
                                            cf=cf,
                                            start=start,
                                            end=end, 
                                            resolution=resolution)
                    self.rrd_data[mt][k] = data

            else:
                raise TypeError("This type doesn't support")

        self.tag = tag
        self.start = start
        self.end = end
        self.cf = cf
        self.kargs = kargs


    def load_rrd(self, filepath, **kargs):
        rrd = RRD(filepath, mode='r', backend=bindings)
        rrd_data = rrd.fetch(**kargs)
        return rrd_data['42']


    def analysis(self):
        """
        データから、マシンの状態
        * Success = 0
        * Warning = 1
        * Error = 2
        の3つの状態を辞書で返す
        {
            ('localhost', 'localhost'): 0,
            ('machine', 'm1'): 1,
            ('machine', 'm2'): 2
        }
        """
        pass
    
    def make_view(self):
        """
        解析データから、Webページを生成し
        MachineTupleと文字列の辞書で返す
        {
            ('localhost', 'localhost'): '<HTML>~~',
            ('machine', 'm1'):  '<HTML>~~',
            ('machine', 'm2'):  '<HTML>~~'
        }
        """
        pass

