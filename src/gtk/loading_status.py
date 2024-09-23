from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/gtk/loading_status.ui")
class LoadingStatus(Gtk.ScrolledWindow):
    __gtype_name__ = 'LoadingStatus'
    gtc = Gtk.Template.Child

    title_label = gtc()
    description_label = gtc()
    progress_clamp = gtc()
    progress_bar = gtc()
    progress_label = gtc()
    button = gtc()
    
    def set_progress_label(self, *args):
        text = self.progress_bar.get_fraction() * 100
        self.progress_label.set_label(f"{text:.0f}%")

    def __init__(self, title, description, show_progress=False, on_cancel=None, **kwargs):
        super().__init__(**kwargs)

        self.title_label.set_label(GLib.markup_escape_text(title))
        self.description_label.set_label(GLib.markup_escape_text(description))
        self.progress_clamp.set_visible(show_progress)
        if on_cancel is None:
            self.button.set_visible(False)
        else:
            self.button.connect("clicked", lambda *_: on_cancel)
            
        # self.progress_bar.connect("notify::fraction", self.set_progress_label)
