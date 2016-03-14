

class Graph(object):
    def __init__(self, domain, host, path, **kargs):
        for k, v in kargs.items():
            setattr(self, k, v)

        self.domain = domain
        self.host = host
        self.path = path
        self.child = []
        self.series = []

    def add_child(self, child_graph):
        self.child.append(child_graph)

    def add_series(self, series):
        series.set_graph(self)
        self.series.append(series)







class Series(object):

    def __init__(self, name, **kargs):
        for k, v in kargs.items():
            setattr(self, k, v)
        if not hasattr(self, 'type'):
            setattr(self, 'type', 'GAUGE')

        self.name = name
        self.in_graph = None

    def set_graph(self, graph):
        self.in_graph = graph

    def get_rrd_filepath(self):
        domain = self.in_graph.domain
        host = self.in_graph.host
        path = self.in_graph.path.replace('.', '-')
        series_type = self.type[0].lower()
        folder = domain + '/'
        filename = '-'.join([host, path, self.name, series_type])
        return folder + filename + '.rrd'




