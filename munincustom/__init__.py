
class State(object):
    SUCCESS = 0
    WARNING = 1
    ERROR = 2
    INFO = 3

    @classmethod
    def get_state_dict(cls):
        return {
                'SUCCESS': State.SUCCESS,
                'INFO': State.INFO,
                'WARNING': State.WARNING,
                'ERROR': State.ERROR,
            }

    @classmethod
    def get_high_priority_state(cls, *args):
        acc = cls.SUCCESS
        for s in args:
            if acc == cls.SUCCESS:
                acc = s
            elif acc == cls.INFO:
                if s == cls.WARNING or s == cls.ERROR:
                    acc = s
            elif acc == cls.WARNING:
                if s == cls.ERROR:
                    acc = s
            elif acc == cls.ERROR:
                continue
            else:
                print(acc)
                print(s)
                raise ValueError('Invalid state.')

        return acc
