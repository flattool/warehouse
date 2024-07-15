from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo
from .error_toast import ErrorToast
from .data_box import DataBox

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/user_data_page/user_data_page.ui")
class UserDataPage(Adw.BreakpointBin):
    __gtype_name__ = 'UserDataPage'
    gtc = Gtk.Template.Child
    select_button = gtc()
    flow_box = gtc()
    sort_pop = gtc()
    sort_list = gtc()
    sort_name = gtc()
    sort_id = gtc()
    sort_size = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None

    def set_selection_mode(self, is_enabled):
        i = 0
        while row := self.flow_box.get_child_at_index(i):
            i += 1
            row = row.get_child()
            row.check_button.set_visible(is_enabled)
            row.check_button.set_active(False)

    def sort_handler(self, button):
        if button.get_active() == False:
            return
        self.sort_name.set_active(self.sort_name is button)
        self.sort_id.set_active(self.sort_id is button)
        self.sort_size.set_active(self.sort_size is button)
        if button is self.sort_name:
            self.sort_id.grab_focus()
        else:
            self.sort_name.grab_focus()

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)
        
        # Apply
        self.__class__.instance = self

        for i in range(10):
            box = DataBox(main_window, "/home/heliguy/.var/app/io.github.io.github.flattool.Warehouse/")
            self.flow_box.append(box)
            self.flow_box.get_child_at_index(i).set_focusable(False)

        # self.select_button.connect("toggled", lambda *_: self.set_selection_mode(self.select_button.get_active()))
        # self.flow_box.connect("child-activated", lambda _, item: (cb := (row := item.get_child()).check_button).set_active((not cb.get_active()) if row.get_activatable() else False))

        self.sort_name.connect("toggled", self.sort_handler)
        self.sort_id.connect("toggled", self.sort_handler)
        self.sort_size.connect("toggled", self.sort_handler)