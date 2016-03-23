
from munincustom.plugin import BaseAnalysisClass
from munincustom import utils, State


class Analysis(BaseAnalysisClass):

    default_options = utils.load_default_options(__file__)

    def analysis(self):
        g = lambda x: (x[0], None)
        self.analyzed_data = dict(map(g, self.rrd_data.items()))

        return dict([(x, State.ERROR) for x in self.rrd_data])

    def make_view(self):
        return dict([(k, 'Error State.')
                    for k, v in self.analyzed_data.items()])


