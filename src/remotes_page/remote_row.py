from gi.repository import Adw, Gtk, GLib, Gio, Pango
from .host_info import HostInfo

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/remote_row.ui")
class RemoteRow(Adw.ActionRow):
    __gtype_name__ = 'RemoteRow'
    gtc = Gtk.Template.Child

    suffix_label = gtc()
    menu_pop = gtc()
    menu_listbox = gtc()

    copy_title = gtc()
    copy_name = gtc()
    remove = gtc()

    def on_menu_action(self, listbox, row):
        row = row.get_child()
        if row is self.copy_title:
            HostInfo.clipboard.set(self.get_title())
            self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Copied title")))
        elif row is self.copy_name:
            HostInfo.clipboard.set(self.get_subtitle())
            self.parent_page.toast_overlay.add_toast(Adw.Toast(title=_("Copied name")))
        elif row is self.remove:
            print("remove")
        self.menu_pop.popdown()

    def idle_stuff(self):
        self.set_title(self.remote.title)
        self.set_subtitle(_("Installation: {}").format(self.installation))
        self.suffix_label.set_label(self.remote.name)

    def __init__(self, parent_page, installation, remote, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.parent_page = parent_page
        self.remote = remote
        self.installation = installation

        # Apply
        GLib.idle_add(lambda *_: self.idle_stuff())

        # Connections
        self.menu_listbox.connect("row-activated", self.on_menu_action)