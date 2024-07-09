from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/widgets/status_box.ui")
class StatusBox(Gtk.Box):
    __gtype_name__ = 'StatusBox'
    gtc = Gtk.Template.Child
    spinner = gtc()
    title = gtc()
    description = gtc()
    progress_box = gtc()
    progress_bar = gtc()
    progress_label = gtc()
    cancel_button = gtc()
    cancel_button_content = gtc()
    
    def __init__(self, title, description, show_loading_bar=True, on_cancel=None, **kwargs):
        super().__init__(**kwargs)
        self.title.set_label(title)
        self.description.set_label(description)
        self.spinner.set_visible(not show_loading_bar)
        self.progress_box.set_visible(show_loading_bar)
        self.cancel_button.set_visible(on_cancel)

        if on_cancel:
            self.cancel_button.connect("clicked", lambda *_: on_cancel())