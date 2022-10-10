import os
import json


class Config(object):

    def __init__(self):
        # defaults
        self.BASE_PATH = ""
        self.NOTES_DIR = ""
        self.LINK_COLOR = "#000000"
        self.ALERT_COLOR = "#000000"
        self.FOCAL_COLOR = "#000000"
        self.DEFAULT_NN = 10
        self.HTTP_PORT = 8080

        self.PLOT_LIMIT_DAYS = 30
        self.PLOT_LIMIT_WEEKS = 30

    def load(self) -> None:
        with open(os.path.join(os.getcwd(), "config.json"), "r") as fp:
            b = fp.read()
            cfg = json.loads(b)
            self.BASE_PATH = cfg.get('BASE_PATH', self.BASE_PATH)
            self.NOTES_DIR = cfg.get('NOTES_DIR', self.NOTES_DIR)
            self.LINK_COLOR = cfg.get('LINK_COLOR', self.LINK_COLOR)
            self.ALERT_COLOR = cfg.get('ALERT_COLOR', self.ALERT_COLOR)
            self.FOCAL_COLOR = cfg.get('FOCAL_COLOR', self.FOCAL_COLOR)
            self.DEFAULT_NN = cfg.get('DEFAULT_NN', self.DEFAULT_NN)
            self.HTTP_PORT = cfg.get('HTTP_PORT', self.HTTP_PORT)

            self.PLOT_LIMIT_DAYS = cfg.get('PLOT_LIMIT_DAYS', self.PLOT_LIMIT_DAYS)
            self.PLOT_LIMIT_WEEKS = cfg.get('PLOT_LIMIT_DAYS', self.PLOT_LIMIT_WEEKS)

    def get_num_notes_per_page(self) -> int:
        return self.DEFAULT_NN

    def get_base_path(self) -> str:
        return self.BASE_PATH

    def get_notes_dir(self) -> str:
        return self.NOTES_DIR

    def get_alert_color(self) -> str:
        return self.ALERT_COLOR

    def get_link_color(self) -> str:
        return self.LINK_COLOR

    def get_focal_color(self) -> str:
        return self.FOCAL_COLOR

    def get_http_port(self) -> int:
        return self.HTTP_PORT
