
from munincustom.plugin import BaseAnalysisClass
from munincustom import utils, State


class Analysis(BaseAnalysisClass):

    def analysis(self):
        g = lambda x: (x[0], None)
        self.analyzed_data = dict(map(g, self.rrd_data.items()))

        return dict([(x, State.WARNING) for x in self.rrd_data])

    def make_view(self):
        return dict([(k, 'WARNING State.')
                    for k, v in self.analyzed_data.items()])


