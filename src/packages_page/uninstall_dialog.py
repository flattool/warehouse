from gi.repository import Adw, Gtk, GLib, Gio, Pango

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/packages_page/uninstall_dialog.ui")
class UninstallDialog(Adw.AlertDialog):
    __gtype_name__ = "UninstallDialog"
    gtc = Gtk.Template.Child

    group = gtc()
    trash = gtc()

    def on_response(self, dialog, response):
        if response != "continue":
            return
        
        self.continue_callback(self.trash.get_active())

    def __init__(self, continue_callback, show_trash_option, package_name=None, **kwargs):
        super().__init__(**kwargs)

        if package_name:
            self.set_heading(GLib.markup_escape_text(_("Uninstall {}?").format(package_name)))
            self.set_body(GLib.markup_escape_text(_("It will not be possible to use {} after removal").format(package_name)))
        else:
            self.set_heading(GLib.markup_escape_text(_("Uninstall Packages?")))
            self.set_body(GLib.markup_escape_text(_("It will not be possible to use these packages after removal")))

        self.continue_callback = continue_callback
        self.add_response("cancel", _("Cancel"))
        self.add_response("continue", _("Uninstall"))
        self.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        self.connect("response", self.on_response)
        self.group.set_title(GLib.markup_escape_text(_("App Settings & Content")))
        self.group.set_visible(show_trash_option)