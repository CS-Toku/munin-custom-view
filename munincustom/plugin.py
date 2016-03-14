
from pyrrd.rrd import RRD
from pyrrd.backend import bindings


class BaseAnalysisClass(object):

    def __init__(self, mt_rrd_dict, cf='AVERAGE',start=None, end=None, resolution=None, **kargs):
        self.rrd_data = {}
        for mt, rrdfilepath in mt_rrd_dict.items():
            rrd = RRD(filepath, mode='r', backend=bindings)
            rrd_data = rrd.fetch(cf=cf, start=start, end=end, resolution=resolution)
            self.rrd_data[mt] = [(datetime.datetime.fromtimestamp(x[0]), x[1])
                                for x in rrd_data['42']]

        self.start = start
        self.end = end
        self.cf = cf
        self.kargs = kargs


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

