import os
from collections import Counter, defaultdict
import time
import datetime
import json
from operator import itemgetter
import math
import re

from note import Note
from config import Config


class Index(object):

    def __init__(self):

        self.cfg = None

        self.notes = []
        self.tags = Counter()
        self.people = Counter()

        self.tfidf_vocab = []
        self.tfidf_dfs = []
        self.tfidf_inv_idx = []

        self.stopwords = set()

    def load(self, cfg: Config):
        self.cfg = cfg
        try:
            with open(os.path.join(self.cfg.get_base_path(), self.cfg.get_notes_dir(), 'index.json'), 'r') as fp:
                b = fp.read()
                obj = json.loads(b)
        except FileNotFoundError:
            # create an empty index
            obj = {'notes': [], 'tags': [], 'people': [], 'tfidf_vocab': [], 'tfidf_dfs': [], 'tfidf_inv_idx': []}

        self.notes = [Note(n['tags'], n['people'], n['title'], n['timestamp']) for n in obj['notes']]
        self.people = Counter(dict(obj['people']))
        self.tags = Counter(dict(obj['tags']))
        self.tfidf_vocab = obj['tfidf_vocab']
        self.tfidf_dfs = obj['tfidf_dfs']
        self.tfidf_inv_idx = obj['tfidf_inv_idx']

        with open(os.path.join(self.cfg.get_base_path(), 'resources', 'stopwords.txt'), 'r') as fp:
            sw = fp.read().strip().split('\n')
            self.stopwords = set(sw)

    def save(self) -> None:
        with open(os.path.join(self.cfg.get_base_path(), self.cfg.get_notes_dir(), 'index.json'), 'w') as fp:
            fp.write(json.dumps({
                "notes": [n.to_json() for n in self.notes],
                "people": [(t, self.people[t]) for t in self.people],
                "tags": [(t, self.tags[t]) for t in self.tags],
                "tfidf_vocab": self.tfidf_vocab,
                "tfidf_dfs": self.tfidf_dfs,
                "tfidf_inv_idx": self.tfidf_inv_idx,
            }))

    def get_tags(self) -> list[(str, int)]:
        tag_list = [(t, self.tags[t]) for t in self.tags]
        tag_list.sort(key=itemgetter(1), reverse=True)
        return tag_list

    def get_people(self) -> list[(str, int)]:
        people_list = [(t, self.people[t]) for t in self.people]
        people_list.sort(key=itemgetter(1), reverse=True)
        return people_list

    def get_notes(self) -> list[Note]:
        d = self.notes.copy()
        fn = (lambda d: d.timestamp)
        d.sort(key=fn, reverse=True)  # descending by time
        return d

    def get_notes_search(self, query: str) -> list[Note]:

        doc_scores = self._search(query)  # dict of { doc: score }
        note_list = [n for n in self.notes if n.timestamp in doc_scores]
        f = (lambda note: doc_scores[note.timestamp])
        note_list.sort(key=f, reverse=True)
        return note_list

    def _search(self, query: str) -> dict:

        doc_scores = {}

        words = re.split("[^a-z']", query.lower())
        for w in set(words):
            if len(w) == 0:
                continue
            try:
                widx = self.tfidf_vocab.index(w)
            except ValueError:
                # word doesn't exist in index
                continue

            # loop over the (doc, score) pairs
            for doc, score in self.tfidf_inv_idx[widx]:
                doc_scores[doc] = doc_scores.get(doc, 0) + score

        return doc_scores

    def body_to_words(self, txt: str) -> list[str]:

        txt2 = re.sub("<!-- tags: (.*) -->", "", txt)
        txt2 = re.sub("<!-- attendees: (.*) -->", "", txt2)
        txt2 = re.sub("<!-- time: (.*) -->", "", txt2)

        words = re.split("[^a-z0123456789']", txt2.lower())
        words = [w for w in words if w != '' and w not in self.stopwords]
        return words

    def build(self, cfg: Config) -> None:
        self.cfg = cfg

        self.notes = []
        self.tags = Counter()
        self.people = Counter()

        self.tfidf_vocab = []
        self.tfidf_dfs = []

        word_indices = {}
        tfs = {}
        doc_freq = {}
        for (dirpath, dirnames, filenames) in os.walk(os.path.join(self.cfg.get_base_path(), self.cfg.get_notes_dir())):
            for fn in filenames:
                if fn.strip().endswith(".md"):
                    # index the note metadata
                    timestamp = int(os.path.split(fn)[-1][:-3])
                    note, note_text = Index.read_note_file(timestamp, self.cfg)
                    self.add_note_to_index(note, save=False, add_to_search_index=False)

                    # insert all the words into the dictionary
                    words = self.body_to_words(note_text)
                    for w in set(words):
                        idx = word_indices.get(w, -1)
                        if idx == -1:
                            word_indices[w] = len(word_indices)
                        doc_freq[word_indices[w]] = doc_freq.get(word_indices[w], 0) + 1
                    subset = [word_indices[_] for _ in words]
                    tfs[timestamp] = Counter(subset)

        # create the inverted index
        # word -> [(doc, count), (doc, count)]
        inv_idx = defaultdict(list)
        for doc in tfs:
            # print("Doc: " + str(doc))
            for word_idx in tfs[doc]:
                my_tf = tfs[doc][word_idx]  # note: not normalizing for document length
                my_idf = math.log(len(tfs) / doc_freq[word_idx], 10)
                t = (doc, my_tf * my_idf)
                if t[1] > 0:
                    inv_idx[word_idx].append(t)

        # create a more space efficient vocab for storage
        self.tfidf_vocab = sorted(word_indices.items(), key=itemgetter(1))
        self.tfidf_vocab = list(map(itemgetter(0), self.tfidf_vocab))
        self.tfidf_dfs = [doc_freq[i] for i in range(len(self.tfidf_vocab))]
        self.tfidf_inv_idx = [inv_idx[i] for i in range(len(self.tfidf_vocab))]

        self.save()

    @staticmethod
    def read_note_file(timestamp: int, cfg: Config) -> (Note, str):
        path = Index.get_path_from_timestamp(timestamp, cfg)
        fn = os.path.join(path, "{0}.md".format(timestamp))
        with open(fn, 'r') as fp:
            b = fp.read()

        tags = re.search("<!-- tags: (.*) -->", b)
        people = re.search("<!-- attendees: (.*) -->", b)

        if tags is not None:
            tags = set([t.lower() for t in tags.group(1).strip().split() if t.startswith('#')])
        else:
            tags = set()

        if people is not None:
            people = set([p.lower() for p in people.group(1).strip().split() if p.startswith('@')])
        else:
            people = set()

        title = '(untitled)'
        for line in b.split('\n'):
            if line.startswith('# '):
                title = line[2:]
                break

        # include tags inside the text
        other_tags = map((lambda s: s.lower()), re.findall("#\w+", b))
        tags.update(other_tags)

        # TODO: figure out what to do with people mentioned in the text, but not attendees
        # people.update(re.findall("@\w+", b))

        ts = int(os.path.split(fn)[-1][:-3])

        n = Note(sorted(tags), sorted(people), title, ts)
        return n, b

    def add_note_to_index(self, note: Note, save=True, add_to_search_index=True) -> None:
        self.notes.append(note)
        for t in note.tags:
            self.tags[t] += 1
        for p in note.people:
            self.people[p] += 1

        # if this is being added as part of rebuilding the index, we do not
        # want to do this, because the search index is actually in the process of
        # getting created.  This is just if we want to add to an existing
        # search index
        if add_to_search_index:
            tmp_dict = dict(zip(self.tfidf_vocab, range(len(self.tfidf_vocab))))
            _, body = self.read_note_file(note.timestamp, self.cfg)
            words = self.body_to_words(body)
            ctr = Counter(words)
            for w in ctr:

                # add words not currently in the vocabulary to the index
                widx = tmp_dict.get(w, -1)
                if widx == -1:
                    self.tfidf_vocab.append(w)
                    widx = len(self.tfidf_vocab) - 1
                    self.tfidf_dfs.append(0)
                    self.tfidf_inv_idx.append([])

                # add to document frequencies
                self.tfidf_dfs[widx] += 1

                tf = ctr[w]
                idf = math.log(len(self.notes) / self.tfidf_dfs[widx], 10)
                t = (note.timestamp, tf * idf)
                if t[1] > 0:
                    self.tfidf_inv_idx[widx].append(t)

        if save:
            self.save()

    def remove_note_from_index(self, timestamp: int, save=True) -> None:
        my_note = None
        for note in self.notes:
            if note.timestamp == timestamp:
                my_note = note
                break
        if my_note:

            # remove doc from search index
            tmp_dict = dict(zip(self.tfidf_vocab, range(len(self.tfidf_vocab))))
            _, body = self.read_note_file(note.timestamp, self.cfg)
            words = self.body_to_words(body)
            ctr = Counter(words)
            for w in ctr:

                # skip words not currently in the vocabulary
                # (this will get fixed upon reindexing)
                widx = tmp_dict.get(w, -1)
                if widx == -1:
                    continue

                # remove from document frequencies
                self.tfidf_dfs[widx] -= 1

                # remove from the inverted index
                self.tfidf_inv_idx[widx] = [_ for _ in self.tfidf_inv_idx[widx] if _[0] != note.timestamp]

            # remove note's tags from tag and people counts (and list if necessary)
            for t in my_note.tags:
                self.tags[t] -= 1
                if self.tags[t] == 0:
                    del self.tags[t]
            for p in my_note.people:
                self.people[p] -= 1
                if self.people[p] == 0:
                    del self.people[p]

            # finally, remove the note from the list of notes
            self.notes.remove(my_note)

        if save:
            self.save()

    @staticmethod
    def delete_note_file(timestamp: int, cfg: Config) -> None:
        path = Index.get_path_from_timestamp(timestamp, cfg)
        fn = os.path.join(path, '{0}.md'.format(timestamp))
        os.unlink(fn)

    @staticmethod
    def save_note_file(timestamp: int, text: str, cfg: Config) -> None:
        path = Index.get_path_from_timestamp(timestamp, cfg)
        fn = os.path.join(path, '{0}.md'.format(timestamp))
        try:
            os.makedirs(path)
        except FileExistsError as e:
            pass
        with open(fn, 'w') as fp:
            text = re.sub("\r\n", "\n", text)
            fp.write(text)

    @staticmethod
    def get_path_from_timestamp(timestamp: int, cfg: Config) -> str:
        dttm = datetime.datetime.fromtimestamp(timestamp)
        y, m, d = str(dttm).split()[0].split('-')
        path = os.path.join(cfg.get_base_path(), cfg.get_notes_dir(), y, m, d)
        return path

    def new_file(self, tag_list=None, people_list=None, title=None, body=None, override_timestamp=None) -> int:

        dttm = datetime.datetime.now()
        u = int(time.mktime(dttm.timetuple()))

        if override_timestamp:
            u = override_timestamp
            while os.path.exists(os.path.join(Index.get_path_from_timestamp(u, self.cfg), "{0}.md".format(u))):
                u += 1

        tags = ' '.join(tag_list or [])
        people = ' '.join(people_list or [])

        template = """<!-- tags: {0} -->
<!-- attendees: {1} -->

# {2}

{3}

""".format(tags, people, (title or "(untitled)"), (body or ""))

        Index.save_note_file(u, template, self.cfg)
        n = Note((tag_list or []), (people_list or []), (title or '(untitled)'), u)
        self.add_note_to_index(n)
        return u
