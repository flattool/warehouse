from gi.repository import Adw, Gtk
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/gtk/installation_chooser.ui")
class InstallationChooser(Adw.ActionRow):
    __gtype_name__ = 'InstallationChooser'
    gtc = Gtk.Template.Child