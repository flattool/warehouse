from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/data_box.ui")
class DataBox(Gtk.ListBox):
    __gtype_name__ = 'DataBox'
    gtc = Gtk.Template.Child

    image = gtc()
    title_label = gtc()
    subtitle_label = gtc()
    spinner = gtc()
    size_label = gtc()
    check_button = gtc()

    def human_readable_size(self):
        units = ['KB', 'MB', 'GB', 'TB']
        # size *= 1024
        for unit in units:
            if self.size < 1024:
                return f"~ {round(self.size)} {unit}"
            self.size /= 1024
        return f"~ {round(self.size)} PB"

    def get_size(self, *args):
        self.size = int(subprocess.run(['du', '-s', self.data_path], capture_output=True, text=True).stdout.split("\t")[0])

    def show_size(self):
        def callback(*args):
            self.size_label.set_label(self.human_readable_size())
            self.spinner.set_visible(False)
            if self.callback:
                self.callback()

        Gio.Task.new(None, None, callback).run_in_thread(self.get_size)

    def idle_stuff(self):
        self.title_label.set_label(self.title)
        self.subtitle_label.set_label(self.subtitle)
        if self.icon_path:
            self.image.add_css_class("icon-dropshadow")
            self.image.set_from_file(self.icon_path)

    def __init__(self, title, subtitle, data_path, icon_path=None, callback=None, **kwargs):
        super().__init__(**kwargs)

        self.title = title
        self.subtitle = subtitle
        self.icon_path = icon_path
        self.data_path = data_path
        self.callback = callback
        self.size = None

        self.idle_stuff()
        self.show_size()
