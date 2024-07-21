from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .error_toast import ErrorToast
from .data_box import DataBox
from .host_info import HostInfo
import subprocess

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/data_subpage.ui")
class DataSubpage(Gtk.Stack):
    __gtype_name__ = 'DataSubpage'
    gtc = Gtk.Template.Child

    scrolled_window = gtc()
    
    label_box = gtc()
    subtitle_size_box = gtc()
    title = gtc()
    subtitle = gtc()
    spinner = gtc()
    size_label = gtc()
    flow_box = gtc()

    # Statuses
    loading_data = gtc()
    content_box = gtc()
    no_data = gtc()
    no_results = gtc()

    def human_readable_size(self):
        working_size = self.total_size
        units = ['KB', 'MB', 'GB', 'TB']
        # size *= 1024
        for unit in units:
            if working_size < 1024:
                return f"~ {round(working_size)} {unit}"
            working_size /= 1024
        return f"~ {round(working_size)} PB"

    def sort_func(self, box1, box2):
        import random
        # print(random.randint(1, 100), self.sort_mode, self.sort_ascend)
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

    def box_size_callback(self, size):
        self.finished_boxes += 1
        self.total_size += size
        if self.finished_boxes == self.total_items:
            self.size_label.set_label(self.human_readable_size())
            self.spinner.set_visible(False)
            self.ready_to_sort_size = True
            if self.sort_mode == "size":
                self.flow_box.invalidate_sort()
                self.set_visible_child(self.content_box)

    def trash_handler(self, trashed_box):
        self.flow_box.remove(trashed_box)
        if not self.flow_box.get_child_at_index(0):
            self.set_visible_child(self.no_data)

    def set_selection_mode(self, is_enabled):
        self.selected_boxes.clear()
        idx = 0
        while box := self.flow_box.get_child_at_index(idx):
            idx += 1
            box = box.get_child()
            if not is_enabled:
                # continue
                GLib.idle_add(lambda *_, box=box: box.check_button.set_active(False))
            GLib.idle_add(lambda *_, box=box: box.check_button.set_visible(is_enabled))
        # if not is_enabled:
        #     return

    def box_select_handler(self, _, box):
        box = box.get_child()
        if not box.check_button.get_visible():
            return
        cb = box.check_button
        if cb.get_active():
            GLib.idle_add(lambda *_: cb.set_active(False))
            self.selected_boxes.remove(box)
        else:
            GLib.idle_add(lambda *_: cb.set_active(True))
            self.selected_boxes.append(box)
        
        total = len(self.selected_boxes)
        self.parent_page.copy_button.set_sensitive(total)
        self.parent_page.trash_button.set_sensitive(total)

    def select_all_handler(self, *args):
        idx = 0
        while box := self.flow_box.get_child_at_index(idx):
            idx += 1
            if not box.get_child().check_button.get_active():
                self.box_select_handler(None, box)

    def generate_list(self, flatpaks, data):
        self.boxes.clear()
        self.selected_boxes.clear()
        self.ready_to_sort_size = False
        self.finished_boxes = 0
        self.total_size = 0
        self.total_items = len(data)

        if self.total_items == 1:
            self.subtitle.set_label(_("1 Item"))
        else:
            self.subtitle.set_label(_("{} Items").format(self.total_items))
                
        self.min_horizontal_label_width = self.label_box.get_preferred_size()[1].width
        if flatpaks:
            for i, pak in enumerate(flatpaks):
                box = DataBox(self.parent_page.toast_overlay, pak.info["name"], pak.info["id"], pak.data_path, pak.icon_path, self.box_size_callback, self.trash_handler)
                self.boxes.append(box)
                self.flow_box.append(box)
        else:
            for i, folder in enumerate(data):
                box = DataBox(self.parent_page.toast_overlay, folder.split('.')[-1], folder, f"{HostInfo.home}/.var/app/{folder}", None, self.box_size_callback, self.trash_handler)
                self.flow_box.append(box)
                child = self.flow_box.get_child_at_index(i)
                child.set_focusable(False)
        
        idx = 0
        while box := self.flow_box.get_child_at_index(idx):
            idx += 1
            box.set_focusable(False)
            child = box.get_child()
            child.set_focusable(False)
            child.row.set_focusable(child.check_button.get_visible())

        if idx == 0:
            self.set_visible_child(self.no_data)
        elif self.sort_mode != "size":
            self.set_visible_child(self.content_box)

    def filter_func(self, box):
        search_text = self.parent_page.search_entry.get_text().lower()
        box = box.get_child()
        if search_text in box.title.lower() or search_text in box.subtitle.lower():
            self.is_result = True
            return True

    def on_invalidate(self, box):
        current_status = self.get_visible_child()
        if not current_status is self.no_results:
            self.prev_status = self.get_visible_child()

        self.is_result = False
        self.flow_box.invalidate_filter()
        if self.is_result:
            self.set_visible_child(self.prev_status)
        else:
            self.set_visible_child(self.no_results)

        if self.parent_page.search_entry.get_text().lower() != "" and self.total_items == 0:
            self.set_visible_child(self.no_results)
        elif self.total_items == 0:
            self.set_visible_child(self.no_data)

    def label_orientation_handler(self, adj):
        current_page_width = adj.get_upper() - 24
        
        if self.label_box.get_allocated_width() < self.min_horizontal_label_width:
            GLib.idle_add(lambda *_: self.label_box.set_orientation(Gtk.Orientation.VERTICAL))
        else:
            GLib.idle_add(lambda *_: self.label_box.set_orientation(Gtk.Orientation.HORIZONTAL))

    def __init__(self, title, parent_page, is_active, main_window, **kwargs):
        super().__init__(**kwargs)

        GLib.idle_add(lambda *_: self.title.set_label(title))

        # self.select_button.connect("toggled", lambda *_: self.set_selection_mode(self.select_button.get_active()))
        # self.flow_box.connect("child-activated", lambda _, item: (cb := (row := item.get_child()).check_button).set_active((not cb.get_active()) if row.get_activatable() else False))

        # Extra Object Creation
        self.main_window = main_window
        self.parent_page = parent_page
        # self.is_active = is_active
        self.sort_mode = ""
        self.sort_ascend = False
        self.total_size = 0
        self.total_items = 0
        self.boxes = []
        self.selected_boxes = []
        self.ready_to_sort_size = False
        self.finished_boxes = 0
        self.min_horizontal_label_width = self.label_box.get_preferred_size()[1].width
        self.is_result = False
        self.prev_status = None

        # Apply
        self.flow_box.set_sort_func(self.sort_func)
        self.flow_box.set_filter_func(self.filter_func)

        if is_active:
            self.no_data.set_icon_name("error-symbolic")
            self.no_data.set_title(_("No Active Data"))
            self.no_data.set_description(_("Warehouse cannot see any active user data or your system has no active user data present"))
        else:
            self.no_data.set_icon_name("check-plain-symbolic")
            self.no_data.set_title(_("No Leftover Data"))
            self.no_data.set_description(_("There is no leftover user data"))

        # Connections
        parent_page.search_entry.connect("search-changed", self.on_invalidate)
        self.flow_box.connect("child-activated", self.box_select_handler)

        # self.title.get_preferred_size()[1].width + self.subtitle.get_preferred_size()[1].width
        self.scrolled_window.get_hadjustment().connect("changed", self.label_orientation_handler)