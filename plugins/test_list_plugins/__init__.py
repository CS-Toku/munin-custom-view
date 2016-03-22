
import json

from munincustom.plugin import BaseAnalysisClass
from munincustom import utils, state


class Analysis(BaseAnalysisClass):

    default_options = utils.load_default_options(__file__)

    def analysis(self):
        f = lambda x: x if len(x) <= 5 else x[-5:]
        g = lambda y: (y[0], map(f, y[1]))
        self.analyzed_data = dict(map(g, self.rrd_data.items()))

        return dict([(x, state.SUCCESS) for x in self.rrd_data])

    def make_view(self):
        return dict([(k, json.dumps(v, indent=4))
                    for k, v in self.analyzed_data.items()])


