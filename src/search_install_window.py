from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os
import pathlib


class RemoteRow(Adw.ActionRow):
    def __init__(self, remote, **kwargs):
        super().__init__(**kwargs)
        my_utils = myUtils(self)
        self.install_type = my_utils.get_install_type(remote[7])
        if self.install_type == "disabled":
            self.set_visible(False)
            return
        self.set_activatable(True)
        self.remote = remote
        if remote[1] == "-":
            self.set_title(remote[0])
        else:
            self.set_title(remote[1])
        self.set_subtitle(_("{} wide").format(self.install_type))
        self.add_suffix(Gtk.Image.new_from_icon_name("right-large-symbolic"))


class ResultRow(Adw.ActionRow):
    def __init__(self, flatpak, **kwargs):
        super().__init__(**kwargs)
        my_utils = myUtils(self)
        name = flatpak[0]
        description = flatpak[1]
        app_id = flatpak[2]
        version = flatpak[3]
        self.flatpak = flatpak
        self.set_title(GLib.markup_escape_text(f"{name}"))
        self.set_subtitle(GLib.markup_escape_text(f"{app_id}\n{description}"))
        self.check = Gtk.CheckButton()
        self.check.add_css_class("selection-mode")
        self.add_suffix(
            Gtk.Label(
                label=GLib.markup_escape_text(version),
                wrap=True,
                hexpand=True,
                justify=Gtk.Justification.RIGHT,
            )
        )
        self.add_suffix(self.check)
        self.set_activatable_widget(self.check)


@Gtk.Template(
    resource_path="/io/github/flattool/Warehouse/../data/ui/search_install.ui"
)
class SearchInstallWindow(Adw.Dialog):
    __gtype_name__ = "SearchInstallWindow"

    nav_view = Gtk.Template.Child()
    search_page = Gtk.Template.Child()
    results_page = Gtk.Template.Child()
    remotes_list = Gtk.Template.Child()
    search_entry = Gtk.Template.Child()
    blank_page = Gtk.Template.Child()
    inner_stack = Gtk.Template.Child()
    outer_stack = Gtk.Template.Child()
    loading_page = Gtk.Template.Child()
    results_scroll = Gtk.Template.Child()
    results_list = Gtk.Template.Child()
    too_many = Gtk.Template.Child()
    action_bar = Gtk.Template.Child()
    search_button = Gtk.Template.Child()
    no_results = Gtk.Template.Child()
    install_button = Gtk.Template.Child()
    installing = Gtk.Template.Child()
    installing_status = Gtk.Template.Child()
    search_box = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()
    progress_bar = Gtk.Template.Child()

    is_open = False

    def reset(self):
        self.results = []
        self.results_list.remove_all()
        self.inner_stack.set_visible_child(self.blank_page)

    def check_handler(self, button, row):
        if button.get_active():
            self.selected.append(row.flatpak)
        else:
            self.selected.remove(row.flatpak)
        if len(self.selected) == 0:
            self.set_title(self.title)
            self.action_bar.set_revealed(False)
        else:
            self.set_title(_("{} Selected").format(len(self.selected)))
            self.action_bar.set_revealed(True)

    def generate_remotes_list(self):
        total = 0
        for rem in self.host_remotes:
            if self.my_utils.get_install_type(rem[7]) != "disabled":
                total += 1
        if total < 2:
            self.nav_view.push(self.results_page)
            self.results_page.set_can_pop(False)
            self.search_remote = self.host_remotes[0][0]
            self.install_type = self.host_remotes[0][7]
            if "user" in self.install_type:
                self.install_type = "user"
            if "system" in self.install_type:
                self.install_type = "system"

            if self.host_remotes[0][1] == "-":
                self.title = _("Search {}").format(self.host_remotes[0][0])
            else:
                self.title = _("Search {}").format(self.host_remotes[0][1])

            self.set_title(self.title)
            self.search_entry.set_placeholder_text(
                _("Search {}").format(self.search_remote)
            )
            self.search_entry.grab_focus()
            return
        self.nav_view.connect("popped", lambda *_: self.set_title(""))
        for remote in self.host_remotes:
            row = RemoteRow(remote)
            row.connect("activated", self.remote_choice)
            self.remotes_list.append(row)

    def generate_results_list(self):
        for pak in self.results:
            row = ResultRow(pak)
            row.check.set_active(row.flatpak in self.selected)
            row.check.connect("toggled", self.check_handler, row)
            row.set_tooltip_text(row.flatpak[2])
            if self.search_remote in row.flatpak[5].split(","):
                self.results_list.append(row)
        if self.results_list.get_row_at_index(0):
            self.inner_stack.set_visible_child(self.results_scroll)
        else:
            self.inner_stack.set_visible_child(self.no_results)

    def remote_choice(self, row):
        self.reset()
        self.selected = []
        self.install_type = row.install_type
        self.search_remote = row.remote[0]
        self.search_entry.set_placeholder_text(
            _("Search {}").format(self.search_remote)
        )
        self.title = _("Search {}").format(row.get_title())
        self.set_title(self.title)
        self.nav_view.push(self.results_page)
        self.search_entry.grab_focus()
        self.action_bar.set_revealed(len(self.selected) > 0)

    def search_handler(self, *args):
        self.cancel_search.cancel()
        self.reset()
        self.inner_stack.set_visible_child(self.loading_page)
        query = self.search_entry.get_text().strip()
        if query == "":
            self.inner_stack.set_visible_child(self.blank_page)
            return

        def search_thread(*args):
            command = [
                "flatpak-spawn",
                "--host",
                "flatpak",
                "search",
                "--columns=all",
                query,
            ]
            output = (
                subprocess.run(
                    command, capture_output=True, text=True, env=self.new_env
                )
                .stdout.strip()
                .split("\n")
            )
            for elm in output:
                self.results.append(elm.split("\t"))

        def done(*args):
            if len(self.results) > 50:
                self.inner_stack.set_visible_child(self.too_many)
                return
            if ["No matches found"] in self.results:
                self.inner_stack.set_visible_child(self.no_results)
                return
            self.generate_results_list()

        task = Gio.Task.new(None, self.cancel_search, done)
        task.run_in_thread(search_thread)

    def install_handler(self, *args):
        paks = []
        for pak in self.selected:
            paks.append(pak[2])
        self.outer_stack.set_visible_child(self.installing)
        self.set_title(_("Install From The Web"))

        def thread(*args):
            self.my_utils.install_flatpak(
                paks,
                self.search_remote,
                self.install_type,
                self.progress_bar,
                self.installing_status,
            )

        def done(*args):
            self.main_window.refresh_list_of_flatpaks(None)
            # Make window able to close
            self.set_can_close(True)
            if self.my_utils.install_success:
                self.close()
                self.main_window.toast_overlay.add_toast(
                    Adw.Toast.new(_("Installed successfully"))
                )
            else:
                self.progress_bar.set_visible(False)
                self.nav_view.pop()
                self.outer_stack.set_visible_child(self.nav_view)
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Some apps didn't install"))
                )

        # Make window unable to close
        self.set_can_close(False)
        task = Gio.Task.new(None, None, done)
        task.run_in_thread(thread)

    def __init__(self, main_window, **kwargs):
        super().__init__(**kwargs)

        # Create Variables
        self.my_utils = myUtils(self)
        self.new_env = dict(os.environ)
        self.new_env["LC_ALL"] = "C"
        self.host_remotes = self.my_utils.get_host_remotes()
        self.main_window = main_window
        self.results = []
        self.selected = []
        self.search_remote = ""
        self.install_type = ""
        self.title = _("Install From The Web")

        self.cancel_search = Gio.Cancellable()
        self.search_entry.connect("activate", self.search_handler)
        self.search_button.connect("clicked", self.search_handler)
        self.install_button.connect("clicked", self.install_handler)

        # Apply Widgets
        self.generate_remotes_list()

        def set_is_open_false(*args):
            self.__class__.is_open = False
        self.connect("closed", set_is_open_false)
        if self.__class__.is_open:
            return
        else:
            self.present(main_window)
            self.__class__.is_open = True