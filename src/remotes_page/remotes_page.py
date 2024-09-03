from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
from .remote_row import RemoteRow
from .add_remote_dialog import AddRemoteDialog
from .loading_status import LoadingStatus
import subprocess

class NewRemoteRow(Adw.ActionRow):
    __gtype_name__ = "NewRemoteRow"

    def idle_stuff(self, *args):
        self.set_title(self.info["title"])
        self.set_subtitle(self.info["description"])
        self.add_suffix(Gtk.Image.new_from_icon_name("plus-large-symbolic"))

    def __init__(self, info, **kwargs):
        super().__init__(**kwargs)
        self.info = info
        GLib.idle_add(self.idle_stuff)
        self.set_activatable(True)

@Gtk.Template(resource_path="/io/github/flattool/Warehouse/remotes_page/remotes_page.ui")
class RemotesPage(Adw.NavigationPage):

    # Preselected Remotes
    new_remotes = [
        {
            "title": "AppCenter",
            "name": "appcenter",
            "link": "https://flatpak.elementary.io/repo.flatpakrepo",
            "description": _("The open source, pay-what-you-want app store from elementary")
        },
        {
            "title": "Flathub",
            "name": "flathub",
            "link": "https://dl.flathub.org/repo/flathub.flatpakrepo",
            "description": _("Central repository of Flatpak applications"),
        },
        {
            "title": "Flathub beta",
            "name": "flathub-beta",
            "link": "https://flathub.org/beta-repo/flathub-beta.flatpakrepo",
            "description": _("Beta builds of Flatpak applications"),
        },
        {
            "title": "Fedora",
            "name": "fedora",
            "link": "oci+https://registry.fedoraproject.org",
            "description": _("Flatpaks packaged by Fedora Linux"),
        },
        {
            "title": "GNOME Nightly",
            "name": "gnome-nightly",
            "link": "https://nightly.gnome.org/gnome-nightly.flatpakrepo",
            "description": _("The latest beta GNOME Apps and Runtimes"),
        },
        {
            "title": "KDE Testing Applications",
            "name": "kdeapps",
            "link": "https://distribute.kde.org/kdeapps.flatpakrepo",
            "description": _("Beta KDE Apps and Runtimes"),
        },
        {
            "title": "WebKit Developer SDK",
            "name": "webkit-sdk",
            "link": "https://software.igalia.com/flatpak-refs/webkit-sdk.flatpakrepo",
            "description": _("Central repository of the WebKit Developer and Runtime SDK"),
        }
    ]

    __gtype_name__ = 'RemotesPage'
    gtc = Gtk.Template.Child

    search_button = gtc()
    search_bar = gtc()
    search_entry = gtc()
    toast_overlay = gtc()
    stack = gtc()
    current_remotes_group = gtc()
    show_disabled_button = gtc()
    show_disabled_button_content = gtc()
    new_remotes_group = gtc()
    file_remote_row = gtc()
    custom_remote_row = gtc()
    none_visible = gtc()

    # Statuses
    no_results = gtc()
    no_remotes = gtc()
    content_page = gtc()

    # Referred to in the main window
    #    It is used to determine if a new page should be made or not
    #    This must be set to the created object from within the class's __init__ method
    instance = None
    page_name = "remotes"
    
    def start_loading(self):
        self.search_button.set_active(False)
        self.search_button.set_sensitive(False)
        self.search_entry.set_editable(False)
        self.stack.set_visible_child(self.loading_remotes)
        self.total_disabled = 0
        for row in self.current_remote_rows:
            self.current_remotes_group.remove(row)

        self.current_remote_rows.clear()

    def end_loading(self):
        show_disabled = self.show_disabled_button.get_active()
        self.show_disabled_button.set_visible(False)
        total_visible = 0
        for installation, remotes in HostInfo.remotes.items():
            for remote in remotes:
                row = RemoteRow(self, installation, remote)
                self.current_remote_rows.append(row)
                self.current_remotes_group.add(row)
                if row.remote.disabled:
                    self.total_disabled += 1
                    self.show_disabled_button.set_visible(True)
                    if show_disabled:
                        total_visible += 1
                    else:
                        row.set_visible(False)
                else:
                    total_visible += 1

        self.none_visible.set_visible(total_visible == 0)

        if len(self.current_remote_rows) == 0:
            self.no_remotes.set_visible(True)
            self.none_visible.set_visible(False)
        else:
            self.no_remotes.set_visible(False)

        GLib.idle_add(lambda *_: self.stack.set_visible_child(self.content_page))
        self.search_button.set_sensitive(True)
        self.search_entry.set_editable(True)

    def none_visible_handler(self):
        any_visible = False
        for row in self.current_remote_rows:
            if row.get_visible():
                any_visible = True
                break
        
        self.none_visible.set_visible(not any_visible)

    def filter_remote(self, row):
        self.filter_setting.set_boolean("show-apps", True)
        self.filter_setting.set_boolean("show-runtimes", True)
        self.filter_setting.set_string("remotes-list", f"{row.remote.name}<>{row.installation};")
        self.filter_setting.reset("runtimes-list")
        packages_page = self.main_window.pages[self.main_window.packages_row]
        packages_page.filters_page.generate_filters()
        packages_page.apply_filters()
        GLib.idle_add(lambda *_: self.main_window.activate_row(self.main_window.packages_row))
        GLib.idle_add(lambda *args: packages_page.packages_toast_overlay.add_toast(Adw.Toast(title=_("Showing all packages from {}").format(row.remote.title))))
    
    def remove_remote(self, row):
        error = [None]
        def thread(*args):
            install = row.installation
            cmd = ['flatpak-spawn', '--host', 'flatpak', 'remote-delete', row.remote.name, '--force']
            if install == "user" or install == "system":
                cmd.append(f"--{install}")
            else:
                cmd.append(f"--installation={install}")

            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as cpe:
                error[0] = cpe.stderr
            except Exception as e:
                error[0] = e

        def callback(*args):
            if error[0]:
                self.toast_overlay.add_toast(ErrorToast(_("Could not remove remote"), str(error[0])).toast)
            else:
                filters_page = HostInfo.main_window.pages[HostInfo.main_window.packages_row].filters_page
                filters_page.settings.reset("remotes-list")
                filters_page.all_remotes_switch.set_active(False)
                # filters_page.packages_page.apply_filters()
                self.main_window.refresh_handler()
                self.toast_overlay.add_toast(Adw.Toast(title=_("Removed {}").format(row.remote.title)))

        def on_response(_, response):
            if response != "continue":
                return
            
            Gio.Task.new(None, None, callback).run_in_thread(thread)

        dialog = Adw.AlertDialog(heading=_("Remove {}?").format(row.remote.title), body=_("Any installed apps from {} will stop receiving updates").format(row.remote.name))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Remove"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", on_response)
        dialog.present(self.main_window)

    def on_search(self, entry):
        text = entry.get_text().lower()
        total = 0
        show_disabled = self.show_disabled_button.get_active()
        
        for row in self.current_remote_rows:
            title_match = text in row.get_title().lower()
            subtitle_match = text in row.get_subtitle().lower()
            visible = (title_match or subtitle_match) and (show_disabled or not row.remote.disabled)
            total += visible
            row.set_visible(visible)

        if text == "":
            self.stack.set_visible_child(self.content_page)
            return

        self.stack.set_visible_child(self.content_page if total > 0 else self.no_results)

    def file_callback(self, chooser, result):
        try:
            file = chooser.open_finish(result)
            path = file.get_path()
            name = path.split("/")[-1].split(".")[0]
            info = {
                "title": name.title(),
                "name": name,
                "description": "local file",
                "link": path,
            }
            AddRemoteDialog(self.main_window, self, info).present(self.main_window)
        except GLib.GError as ge:
            if "Dismissed by user" in str(ge):
                return
            self.toast_overlay.add_toast(ErrorToast(_("Could not open file"), str(ge)).toast)
        except Exception as e:
            self.toast_overlay.add_toast(ErrorToast(_("Could not open file"), str(e)).toast)

    def add_file_handler(self):
        file_filter = Gtk.FileFilter(name=_("Flatpak Repos"))
        file_filter.add_suffix("flatpakrepo")
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(file_filter)
        file_chooser = Gtk.FileDialog()
        file_chooser.set_filters(filters)
        file_chooser.set_default_filter(file_filter)
        file_chooser.open(self.main_window, None, self.file_callback)

    def show_disabled_handler(self, button):
        show_disabled = button.get_active()
        self.show_disabled_button_content.set_icon_name("eye-open-negative-filled-symbolic" if show_disabled else "eye-not-looking-symbolic")
        total_visible = 0
        for row in self.current_remote_rows:
            if row.remote.disabled:
                if show_disabled: # show disabled
                    row.set_visible(True)
                    total_visible += 1
                else:
                    row.set_visible(False)
            else:
                total_visible += 1

        self.none_visible.set_visible(total_visible == 0)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Extra Object Creation
        self.__class__.instance = self
        self.main_window = main_window
        self.loading_remotes = LoadingStatus(_("Loading Remotes"), _("This should only take a moment"))
        self.search_bar.set_key_capture_widget(main_window)
        self.current_remote_rows = []
        self.filter_setting = Gio.Settings.new("io.github.flattool.Warehouse.filter")
        self.total_disabled = 0

        # Connections
        self.file_remote_row.connect("activated", lambda *_: self.add_file_handler())
        self.custom_remote_row.connect("activated", lambda *_: AddRemoteDialog(main_window, self).present(main_window))
        self.search_entry.connect("search-changed", self.on_search)
        self.show_disabled_button.connect("toggled", self.show_disabled_handler)

        # Appply
        self.stack.add_child(self.loading_remotes)
        for item in self.new_remotes:
            row = NewRemoteRow(item)
            row.connect("activated", lambda *_, remote_info=item: AddRemoteDialog(main_window, self, remote_info).present(main_window))
            self.new_remotes_group.add(row)
