
import json

from munincustom.plugin import BaseAnalysisClass
from munincustom import utils, State


class Analysis(BaseAnalysisClass):

    def analysis(self):
        f = lambda x: x if len(x) <= 5 else x[-5:]
        g = lambda y: (y[0], map(f, y[1]))
        self.analyzed_data = dict(map(g, self.rrd_data.items()))

        return dict([(x, State.SUCCESS) for x in self.rrd_data])

    def make_view(self):
        return dict([(k, '<pre>'+json.dumps(v, indent=4)+'</pre>')
                    for k, v in self.analyzed_data.items()])

