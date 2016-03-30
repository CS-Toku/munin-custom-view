

class ParseError(Exception):
    pass

class FileNotFoundError(OSError):

    def __init__(self, *args, **kargs):
        args = list(args)
        args[0] = 'File not found: ' + args[0]
        super(FileNotFoundError, self).__init__(*args, **kargs)





