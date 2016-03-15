#!/bin/env python
# -*- encoding: utf-8 -*-

from pyrrd.rrd import RRD
from pyrrd.backend import bindings


class BaseAnalysisClass(object):

    default_options = {}

    def __init__(self, tag, mt_rrd_dict, **kargs):
        self.rrd_data = {}
        for mt, paths in mt_rrd_dict.items():
            if isinstance(paths, list):
                self.rrd_data[mt] = []
                for i in range(len(paths)):
                    default_options = self.default_options[i] \
                                        if i in self.default_options else {}
                    rrdfilepath, options = paths[i]
                    data = self.load_rrd(rrdfilepath,
                                         options,
                                         default_options)
                    self.rrd_data[mt].append(data)

            elif isinstance(paths, dict):
                self.rrd_data[mt] = {}
                for i, (rrdfilepath, options) in paths.items():
                    default_options = self.default_options[i] \
                                        if i in self.default_options else {}
                    data = self.load_rrd(rrdfilepath,
                                         options,
                                         default_options
                                         )
                    self.rrd_data[mt][i] = data

            else:
                raise TypeError("This type doesn't support")

        self.tag = tag
        self.kargs = kargs

    def load_rrd(self, filepath, options, default_options):
        take_param = lambda k: (k, options[k] if k in options
                                else default_options[k] if k in default_options
                                else None)
        kargs = dict(map(take_param, ['start', 'end', 'resolution', 'cf']))
        rrd = RRD(filepath, mode='r', backend=bindings)
        rrd_data = rrd.fetch(**kargs)
        return rrd_data['42']

    @classmethod
    def load_default_options(cls):
        print(__file__)

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
