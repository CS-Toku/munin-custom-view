
import json

from munincustom.plugin import BaseAnalysisClass
from munincustom import State


class Analysis(BaseAnalysisClass):

    def analysis(self):
        f = lambda x: x.update({'data': x['data'] if len(x['data']) <= 5 else x['data'][-5:], 'series': str(x['series'])}) or x
        g = lambda y: (y[0], map(f, y[1]))
        h = lambda y: (y[0], dict(map(g, y[1].items())))
        self.analyzed_data = dict(map(h, self.rrd_data.items()))

        return dict([(x, State.SUCCESS) for x in self.rrd_data])

    def make_view(self):
        return dict([(k, '<pre>'+json.dumps(v, indent=4)+'</pre>')
                    for k, v in self.analyzed_data.items()])


