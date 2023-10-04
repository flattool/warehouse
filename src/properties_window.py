from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .common import myUtils
import subprocess
import os

def show_properties_window(widget, index, window):
    properties_window = Adw.Window(title=_("{} Properties").format(window.host_flatpaks[index][0]))
    properties_window.set_default_size(350, 600)
    properties_window.set_size_request(260, 230)
    properties_window.set_modal(True)
    properties_window.set_resizable(True)
    outer_box = Gtk.Box(orientation="vertical")
    properties_window.set_transient_for(window)
    properties_scroll = Gtk.ScrolledWindow()
    properties_toast_overlay = Adw.ToastOverlay()
    properties_toast_overlay.set_child(outer_box)
    properties_box = Gtk.Box(orientation="vertical", vexpand=True)
    properties_clamp = Adw.Clamp()
    eol_app_banner = Adw.Banner(title=_("This Flatpak has reached its End of Life and will not receive any security updates"))
    eol_runtime_banner = Adw.Banner(title=_("The runtime used by this app has reached its End of Life and will not receive any security updates"))
    outer_box.append(eol_app_banner)
    outer_box.append(eol_runtime_banner)
    outer_box.append(properties_scroll)
    properties_scroll.set_child(properties_clamp)
    properties_clamp.set_child(properties_box)
    properties_title_bar = Adw.ToolbarView()
    properties_title_bar.add_top_bar(Gtk.HeaderBar())
    properties_title_bar.set_content(properties_toast_overlay)
    user_data_list = Gtk.ListBox(selection_mode="none", margin_top=12, margin_bottom=0, margin_start=12, margin_end=12)
    user_data_row = Adw.ActionRow(title="No User Data")
    user_data_list.append(user_data_row)
    user_data_list.add_css_class("boxed-list")

    my_utils = myUtils(window)

    def key_handler(_a, event, _c, _d):
        if event == Gdk.KEY_Escape:
            properties_window.close()

    event_controller = Gtk.EventControllerKey()
    event_controller.connect("key-pressed", key_handler)
    properties_window.add_controller(event_controller)

    app_name = window.host_flatpaks[index][0]
    app_id = window.host_flatpaks[index][2]
    data_folder = window.user_data_path + app_id

    def on_response(_a, response_id, _b):
        if response_id != "continue":
            return
        if my_utils.trashFolder(data_folder) == 0:
            properties_toast_overlay.add_toast(Adw.Toast.new(_("Trashed user data")))
            user_data_list.remove(user_data_row)
            user_data_list.append(Adw.ActionRow(title="No User Data"))
        else:
            properties_toast_overlay.add_toast(Adw.Toast.new(_("Can't trash data")))

    def clean_button_handler(_widget):
        dialog = Adw.MessageDialog.new(window, _("Send {}'s User Data to the Trash?").format(app_name))
        dialog.set_body(_("Your user files and data for this app will be sent to the trash."))
        dialog.set_close_response("cancel")
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("continue", _("Trash Data"))
        dialog.set_response_appearance("continue", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.set_transient_for(properties_window)
        dialog.connect("response", on_response, dialog.choose_finish)
        Gtk.Window.present(dialog)

    def open_button_handler(_widget):
        try:
            Gio.AppInfo.launch_default_for_uri(f"file://{path}", None)
        except GLib.GError:
            properties_toast_overlay.add_toast(Adw.Toast.new(_("Can't open folder")))

    def copy_button_handler(widget, title, to_copy):
        window.clipboard.set(to_copy)
        properties_toast_overlay.add_toast(Adw.Toast.new(_("Copied {}").format(title)))
    
    image = my_utils.findAppIcon(window.host_flatpaks[index][2])
    image.add_css_class("icon-dropshadow")
    image.set_margin_top(6)
    image.set_pixel_size(100)
    properties_box.append(image)

    properties_list = Gtk.ListBox(selection_mode="none", margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
    properties_list.add_css_class("boxed-list")

    path = str(window.user_data_path) + window.host_flatpaks[index][2]

    def size_thread(path):
        size = f"{path}\n~{my_utils.getSizeWithFormat(path)}"
        user_data_row.set_subtitle(size)

    def calc_size(path):
        task = Gio.Task.new(None, None, None)
        task.run_in_thread(lambda _task, _obj, _data, _cancellable: size_thread(path))

    def test(button, query):
        for i in range(len(window.host_flatpaks)):
            if query in window.host_flatpaks[i][8]:
                show_properties_window(button, i, window)

    if os.path.exists(path):
        user_data_row.set_title("User Data")
        # user_data_row.set_subtitle(f"{path}\n~{my_utils.getSizeWithFormat(path)}")
        calc_size(path)

        open_button = Gtk.Button(icon_name="document-open-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Open Data Folder"))
        open_button.add_css_class("flat")
        open_button.connect("clicked", open_button_handler)
        user_data_row.add_suffix(open_button)

        clean_button = Gtk.Button(icon_name="brush-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Send User Data to the Trash"))
        clean_button.add_css_class("flat")
        clean_button.connect("clicked", clean_button_handler)
        user_data_row.add_suffix(clean_button)

    properties_box.append(user_data_list)

    column_headers = [_('Name'), _('Description'), _('App ID'), _('Version'), _('Branch'), _('Arch'), _('Origin'), _('Installation'), _('Ref'), _('Active Commit'), _('Latest Commit'), _('Installed Size'), _('Options'), _('Runtime')]
    for column in range(len(window.host_flatpaks[index])):
        visible = True
        if window.host_flatpaks[index][column] == "":
            visible = False
        row_item = Adw.ActionRow(title=column_headers[column])
        row_item.set_subtitle(GLib.markup_escape_text(window.host_flatpaks[index][column]))

        properties_copy_button = Gtk.Button(icon_name="edit-copy-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Copy {}").format(column_headers[column]))
        properties_copy_button.add_css_class("flat")
        properties_copy_button.connect("clicked", copy_button_handler, column_headers[column], window.host_flatpaks[index][column])

        if column == 13:
            runtime_properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
            runtime_properties_button.add_css_class("flat")
            runtime_properties_button.connect("clicked", test, row_item.get_subtitle())
            row_item.add_suffix(runtime_properties_button)

            if row_item.get_subtitle() in window.eol_list:
                row_item.add_css_class("error")
                eol_runtime_banner.set_revealed(True)

        row_item.add_suffix(properties_copy_button)

        row_item.set_visible(visible)
        properties_list.append(row_item)

    properties_box.append(properties_list)

    if "eol" in window.host_flatpaks[index][12]:
        eol_app_banner.set_revealed(True)

    properties_window.set_content(properties_title_bar)
    properties_window.present()
