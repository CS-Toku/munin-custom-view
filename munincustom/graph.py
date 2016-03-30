

class Graph(object):
    def __init__(self, domain, host, path, **kargs):
        for k, v in kargs.items():
            setattr(self, k, v)

        self.domain = domain
        self.host = host
        self.path = path
        self.child = []
        self.series = []
        self.__series_dict = None

    def add_child(self, child_graph):
        self.child.append(child_graph)

    def add_series(self, series):
        series.set_graph(self)
        self.series.append(series)

    def get_series(self, use_cache=True):
        if self.__series_dict is None or not use_cache:
            self.__series_dict = dict([(str(x), x)for x in self.series])
        return self.__series_dict







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

    def get_link(self):
        domain = self.in_graph.domain
        host = self.in_graph.host
        path = self.in_graph.path
        if '.' in path:
            path = path.replace('.', '/') + '.html'
        else:
            path += '/index.html' if len(self.in_graph.child) > 0 else '.html'
        link = '/'.join([domain, host, path])
        return link

    def __repr__(self):
        return '<munincustom.graph.Series object "{0}">'.format(str(self))

    def __str__(self):
        return '.'.join([self.in_graph.path, self.name])




