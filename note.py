import os
import datetime

from config import Config


class Note(object):

    def __init__(self, tags: list[str], people: list[str], title: str, timestamp: int):
        self.tags = tags
        self.people = people
        self.title = title
        self.timestamp = timestamp

    def to_json(self) -> dict:
        return {'tags': self.tags, 'people': self.people, 'title': self.title, 'timestamp': self.timestamp}

    def get_file_name(self, cfg: Config) -> str:
        dttm = datetime.datetime.fromtimestamp(self.timestamp)
        y, m, d = str(dttm).split()[0].split('-')
        path = os.path.join(cfg.get_base_path(), cfg.get_notes_dir(), y, m, d)
        fn = os.path.join(path, "{0}.md".format(self.timestamp))
        return fn

    def __str__(self):
        return "{0}: {1} ({2}, {3})".format(self.timestamp, self.title, ', '.join(self.tags), ', '.join(self.people))
