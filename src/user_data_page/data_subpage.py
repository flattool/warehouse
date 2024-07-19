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
        return int(subprocess.run(['du', '-s', path], capture_output=True, text=True).stdout.split("\t")[0])

    def show_size(self, data):
        def thread(*args):
            for folder in data:
                self.total_size += self.get_size(f"{HostInfo.home}/.var/app/{folder}")

        def callback(*args):
            self.size_label.set_label(self.human_readable_size(self.total_size))
            self.spinner.set_visible(False)

        Gio.Task.new(None, None, callback).run_in_thread(thread)

    def sort_func(self, box1, box2):
        i1 = None
        i2 = None
        if self.sort_mode == "name":
            i1 = box1.get_child().title.lower()
            i2 = box2.get_child().title.lower()

        if self.sort_mode == "id":
            i1 = box1.get_child().subtitle.lower()
            i2 = box2.get_child().subtitle.lower()

        if self.sort_mode == "size" and self.ready_to_sort_size:
            i1 = box1.get_child().size
            i2 = box2.get_child().size

        if i1 is None or i2 is None:
            return 0

        return i1 > i2 if self.sort_ascend else i1 < i2

    def box_size_callback(self):
        self.finished_boxes += 1
        if self.finished_boxes == self.total_items:
            self.ready_to_sort_size = True
            self.flow_box.invalidate_sort()

    def generate_list(self, flatpaks, data, sort_mode):
        self.boxes.clear()
        self.ready_to_sort_size = False
        self.finished_boxes = 0
        self.sort_mode = sort_mode
        self.total_items = len(data)
        self.subtitle.set_label(_("{} Items").format(self.total_items))
        if flatpaks:
            for i, pak in enumerate(flatpaks):
                box = DataBox(pak.info["name"], pak.info["id"], pak.data_path, pak.icon_path, self.box_size_callback)
                self.boxes.append(box)
                self.flow_box.append(box)
        else:
            for i, folder in enumerate(data):
                self.flow_box.append(DataBox(folder.split('.')[-1], folder, f"{HostInfo.home}/.var/app/{folder}"))

    def __init__(self, title, main_window, **kwargs):
        super().__init__(**kwargs)

        GLib.idle_add(lambda *_: self.title.set_label(title))

        # self.select_button.connect("toggled", lambda *_: self.set_selection_mode(self.select_button.get_active()))
        # self.flow_box.connect("child-activated", lambda _, item: (cb := (row := item.get_child()).check_button).set_active((not cb.get_active()) if row.get_activatable() else False))

        # Extra Object Creation
        self.main_window = main_window
        self.sort_mode = ""
        self.sort_ascend = False
        self.total_size = 0
        self.total_items = 0
        self.boxes = []
        self.ready_to_sort_size = False
        self.finished_boxes = 0

        # Apply
        self.flow_box.set_sort_func(self.sort_func)

        # Connections