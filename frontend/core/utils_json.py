import datetime
from json import JSONDecoder, JSONEncoder


class DateTimeEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime.date, datetime.datetime)):
            return o.isoformat()
        if isinstance(o, datetime.time):
            return o.isoformat()


class DateTimeDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, *args, object_hook=self.object_hook, **kwargs)

    def object_hook(self, obj):
        ret = {}
        for key, value in obj.items():
            if key in {"date", "creationDate"}:
                ret[key] = datetime.datetime.fromisoformat(value)
            elif key == "time":
                if value is not None:
                    ret[key] = datetime.time.fromisoformat(value)
            else:
                ret[key] = value
        return ret
