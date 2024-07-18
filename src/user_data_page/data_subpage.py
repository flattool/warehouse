from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .error_toast import ErrorToast
from .data_box import DataBox
from .host_info import HostInfo
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/data_subpage.ui")
class DataSubpage(Gtk.ScrolledWindow):
    __gtype_name__ = 'DataSubpage'
    gtc = Gtk.Template.Child

    title = gtc()
    subtitle = gtc()
    spinner = gtc()
    size_label = gtc()
    flow_box = gtc()

    def human_readable_size(self, size):
        units = ['KB', 'MB', 'GB', 'TB']
        # size *= 1024
        for unit in units:
            if size < 1024:
                return f"~ {round(size)} {unit}"
            size /= 1024
        return f"~ {round(size)} PB"

    def get_size(self, path):
        sed = "sed 's/K/ KB/; s/M/ MB/; s/G/ GB/; s/T/ TB/; s/P/ PB/;'"
        self.total_size += int(subprocess.run(['du', '-s', path], capture_output=True, text=True).stdout.split("\t")[0])

    def show_size(self, data):
        for folder in data:
            self.get_size(f"{HostInfo.home}/.var/app/{folder}")

        self.size_label.set_label(self.human_readable_size(self.total_size))
        self.spinner.set_visible(False)

    def generate_list(self, sort_mode, data=None, paks=None):
        self.total_size = 0
        Gio.Task().run_in_thread(lambda *_: self.show_size(data))
        self.flow_box.remove_all()
        total = len(data)
        GLib.idle_add(lambda *_z: self.subtitle.set_label(_("{} Items").format(total)))
        self.boxes.clear()

        def thread(sort_mode, data, paks):
            if paks:
                for package in paks:
                    folder = package.info["id"]
                    box = DataBox(package.info["name"], folder, f"{HostInfo.home}/.var/app/{folder}", package.icon_path)
                    self.boxes.append(box)
            else:
                for folder in data:
                    box = DataBox(folder.split('.')[-1], folder, f"{HostInfo.home}/.var/app/{folder}")
                    self.boxes.append(box)

        def callback(sort_mode):
            if sort_mode == "name":
                self.boxes = sorted(self.boxes, key=lambda box: box.title)
            elif sort_mode == "id":
                self.boxes = sorted(self.boxes, key=lambda box: box.subtitle)
            else:
                pass

            for box in self.boxes:
                self.flow_box.append(box)
        
        Gio.Task.new(None, None, lambda *_: callback(sort_mode)).run_in_thread(lambda *_: thread(sort_mode, data, paks))

    def __init__(self, title, main_window, **kwargs):
        super().__init__(**kwargs)

        GLib.idle_add(lambda *_: self.title.set_label(title))

        # self.select_button.connect("toggled", lambda *_: self.set_selection_mode(self.select_button.get_active()))
        # self.flow_box.connect("child-activated", lambda _, item: (cb := (row := item.get_child()).check_button).set_active((not cb.get_active()) if row.get_activatable() else False))

        # Extra Object Creation
        self.main_window = main_window
        self.total_size = 0
        self.boxes = []

        # Apply

        # Connections