import os
import sys
import math
from flask import Flask, render_template, redirect, Response, request
from urllib.parse import quote, unquote

from typing import Union

import datetime
import markdown
import matplotlib
import matplotlib.pyplot as plt
from base64 import b64encode
import re
from io import BytesIO
from operator import itemgetter
from collections import Counter

from note import Note
from index import Index
from config import Config

app = Flask(__name__)
cfg: Config = None
idx: Index = None


def get_related_tags(note_list: list[Note], filter_: list[str]) -> list[(str, float)]:
    rt = Counter()
    for note in note_list:
        rt.update(note.tags)
    for f in filter_:
        if f in rt:
            del rt[f]
    rt = [(t, rt[t]) for t in rt]
    rt.sort(key=itemgetter(1), reverse=True)
    return rt


def make_date_histogram(note_list: list[Note], color: str) -> BytesIO:
    # grab the dates so we can make a histogram
    dates = [datetime.datetime.fromtimestamp(note.timestamp) for note in note_list]
    dates = Counter([datetime.date(dttm.year, dttm.month, dttm.day) for dttm in dates])  # e.g. "2022-04-01"
    today = datetime.date.today()
    if len(dates) == 0:  # starting from scratch
        dates[today] = 0
    min_date = min(dates)

    # zero-fill dates with no observations
    m = min_date
    while m <= today:
        if m not in dates:
            dates[m] = 0
        m += datetime.timedelta(days=1)

    dates = [(dt, dates[dt]) for dt in dates]
    dates.sort()

    matplotlib.rc('xtick', labelsize=8)
    matplotlib.rc('ytick', labelsize=8)
    plt.figure(figsize=(8, 2), dpi=100)
    plt.bar(list(range(len(dates))), list(map(itemgetter(1), dates)),
            tick_label=list(map(itemgetter(0), dates)), color=color)
    imgbytes = BytesIO()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(imgbytes, format='png')
    imgbytes.seek(0)
    imgbytes = imgbytes.getvalue()
    plt.close()
    return imgbytes


def matches_filter(note: Note, filter_list: list[str]):

    if len(filter_list) == 0:
        return True

    matched = [False for _ in range(len(filter_list))]

    for i, f in enumerate(filter_list):
        matched[i] = ((f in note.tags) or (f in note.people))

    return set(matched) == {True}


def get_bounds(num_elements: int, page_num: int, elem_per_page: int) -> (int, int, int):
    """
    Example: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    Page: 1
    elements: 5
    should return (0, 4, 2)
    """

    first_element = (page_num - 1) * elem_per_page
    if first_element > num_elements:
        first_element = 0

    last_element = (page_num * elem_per_page) - 1
    if last_element >= num_elements:
        last_element = max(num_elements - 1, 0)

    num_pages = math.ceil(num_elements / elem_per_page)

    return first_element, last_element, num_pages


@app.route('/', methods=['GET'])
def list_notes() -> (str, int):

    search: str = request.args.get('search', "", str)
    filter_raw: str = request.args.get('filter', "", str)
    pg: int = request.args.get('pg', 1, int)
    nn: int = request.args.get('nn', cfg.get_num_notes_per_page(), int)
    id_: int = request.args.get('id', 0, int)

    if len(search):
        search = unquote(search)

    filter_list: list = []
    if len(filter_raw):
        filter_list = [unquote(_) for _ in re.split("[, +]", filter_raw) if len(_) > 0]

    list_of_notes = idx.get_notes_search(search) if search else idx.get_notes()
    list_of_notes = [d for d in list_of_notes if matches_filter(d, filter_list)]

    # related tags
    related_tags = []
    if len(filter_list):
        related_tags = get_related_tags(list_of_notes, filter_list)

    # paginate
    total_notes = len(list_of_notes)
    min_, max_, n_pages = get_bounds(len(list_of_notes), pg, nn)
    note_subset: list[Note] = list_of_notes[min_:max_ + 1]

    all_tags = [(quote(t[0]), t[0], t[1]) for t in idx.get_tags()]
    all_people = [(quote(p[0]), p[0], p[1]) for p in idx.get_people()]

    # sort tags by count, descending
    all_tags.sort(key=itemgetter(2), reverse=True)

    # sort people by name
    all_people.sort(key=itemgetter(0))

    imgbytes = make_date_histogram(note_subset, cfg.get_focal_color())

    notes_list = []
    for n in note_subset:
        _, note_body = Index.read_note_file(n.timestamp, cfg)
        note_body_md = markdown.markdown(note_body, extensions=['tables', 'attr_list'])
        d = {
            'tag_list': [(quote(t), t) for t in n.tags],
            'people_list': [(quote(p), p) for p in n.people],
            'timestamp': n.timestamp,
            'dttm_str': str(datetime.datetime.fromtimestamp(n.timestamp))[:19],
            'note_body_md': note_body_md,
            'title': n.title
        }
        notes_list.append(d)

    page_title = ""
    if len(search):
        page_title += "\"" + search + "\""
    if len(filter_list):
        page_title += "\"" + ', '.join(filter_list) + "\""

    d = {'context': 'list',
         'page_title': page_title,
         'all_tags': all_tags, 'all_people': all_people,
         'link_color': cfg.get_link_color(), 'alert_color': cfg.get_alert_color(), 'focal_color': cfg.get_focal_color(),
         'min_note': min_, 'max_note': max_, 'n_pages': n_pages,
         'pg': pg, 'nn': nn, 'total_notes': total_notes,
         'search_str': search, 'filter_str': ', '.join(filter_list), 'id': id_,
         'notes_list': notes_list,
         'imgbytes': b64encode(imgbytes).decode()
         }

    return render_template('notes.html', **d), 200


@app.route('/note', methods=['GET'])
def read_note() -> (str, int):

    id_: int = request.args.get('id', 0, int)

    try:
        note, note_body = Index.read_note_file(id_, cfg)
        note_body_md = markdown.markdown(note_body, extensions=['tables', 'attr_list'])
    except FileNotFoundError:
        return "<html><body>File not found: {0}</body></html>".format(id_), 404

    dttm = datetime.datetime.fromtimestamp(id_)
    last_edit_dttm = datetime.datetime.fromtimestamp(os.path.getmtime(note.get_file_name(cfg)))

    d = {'context': 'read',
         'id': id_,
         'tag_list': [(quote(t), t) for t in note.tags],
         'people_list': [(quote(p), p) for p in note.people],
         'timestamp_str': str(dttm)[:19],
         'filename': note.get_file_name(cfg),
         'note_body_md': note_body_md,
         'last_edit_dttm': str(last_edit_dttm)[:19],
         'page_title': note.title,
         'link_color': cfg.get_link_color(), 'alert_color': cfg.get_alert_color(), 'focal_color': cfg.get_focal_color()
         }

    return render_template("notes.html", **d), 200


@app.route('/edit', methods=['GET'])
def edit_note() -> (str, int):

    id_: int = request.args.get('id', 0, int)
    try:
        note, note_body = Index.read_note_file(id_, cfg)
    except FileNotFoundError:
        return "<html><body>File not found: {0}</body></html>".format(id_), 404

    pl = idx.get_people()
    pl = list(map(itemgetter(0), pl))

    d = {'context': 'edit',
         'id': id_,
         'note_body': note_body,
         'page_title': note.title,
         'people_list': pl,
         'link_color': cfg.get_link_color(), 'alert_color': cfg.get_alert_color(), 'focal_color': cfg.get_focal_color()
         }

    return render_template("notes.html", **d), 200


@app.route('/save', methods=['POST'])
def save_note() -> Union[Response, tuple[str, int]]:

    id_ = request.form.get('id', 0, int)
    text_ = request.form.get('text', "", str)

    try:
        # remove the old one from the index
        idx.remove_note_from_index(id_, save=False)

        # overwrite, then get a new note object
        Index.save_note_file(id_, text_, cfg)
        note, _ = Index.read_note_file(id_, cfg)

        # update the index for the revised note
        idx.add_note_to_index(note)

    except Exception as e:
        return "<html><body>Error: {0}</body></html>".format(str(e)), 500

    return redirect("/note?id={0}".format(id_), code=302)


@app.route('/delete', methods=['POST'])
def delete_note() -> Response:

    id_ = request.form.get('id', 0, int)
    delete_text = request.form.get('delete_text', "", str)

    if delete_text == 'delete':
        # do it
        idx.remove_note_from_index(id_)
        Index.delete_note_file(id_, cfg)
        return redirect("/", code=302)
    else:
        # go back
        url = "/note?id={0}".format(id_)
        return redirect(url, code=302)


@app.route('/new', methods=['GET'])
def new_note() -> Response:
    unix_time = idx.new_file()
    url = "/edit?id={0}".format(unix_time)
    return redirect(url, code=302)


@app.route('/clone', methods=['GET'])
def clone_note() -> Union[Response, tuple[str, int]]:
    id_: int = request.args.get('id', 0, int)
    try:
        note, _ = Index.read_note_file(id_, cfg)
    except FileNotFoundError:
        return "<html><body>File not found: {0}</body></html>".format(id_), 404

    unix_time = idx.new_file(tag_list=note.tags, people_list=note.people, title=note.title)
    url = "/edit?id={0}".format(unix_time)
    return redirect(url, code=302)


@app.route('/reindex', methods=['GET'])
def reindex() -> Response:
    idx.build(cfg)
    return redirect("/", code=302)


@app.route('/exit', methods=['GET'])
def exit_app() -> None:
    sys.exit()


def run_app(cfg_: Config) -> None:
    global app, cfg, idx
    cfg = cfg_
    idx = Index()
    idx.load(cfg)
    app.run(debug=True, port=cfg.get_http_port())
