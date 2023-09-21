from gi.repository import Gtk, Adw, GLib, Gdk, Gio
from .functions import functions
import subprocess
import os

def show_properties_window(widget, index, window):
    properties_window = Adw.Window(title=_("Properties of {}").format(window.host_flatpaks[index][0]))
    properties_window.set_default_size(350, 600)
    properties_window.set_size_request(260, 230)
    properties_window.set_modal(True)
    properties_window.set_resizable(True)
    properties_window.set_transient_for(window)
    properties_scroll = Gtk.ScrolledWindow()
    properties_toast_overlay = Adw.ToastOverlay()
    properties_toast_overlay.set_child(properties_scroll)
    properties_box = Gtk.Box(orientation="vertical", vexpand=True)
    properties_clamp = Adw.Clamp()
    properties_scroll.set_child(properties_clamp)
    properties_clamp.set_child(properties_box)
    properties_title_bar = Adw.ToolbarView()
    properties_title_bar.add_top_bar(Gtk.HeaderBar())
    properties_title_bar.set_content(properties_toast_overlay)
    user_data_list = Gtk.ListBox(selection_mode="none", margin_top=12, margin_bottom=0, margin_start=12, margin_end=12)
    user_data_row = Adw.ActionRow(title="No User Data")
    user_data_list.append(user_data_row)
    user_data_list.add_css_class("boxed-list")

    func = functions(window)

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
        if func.trash_folder(data_folder) == 0:
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
        dialog.add_response("continue", _("Send Data to Trash"))
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
    
    image = func.find_app_icon(window.host_flatpaks[index][2])
    image.add_css_class("icon-dropshadow")
    image.set_margin_top(12)
    image.set_pixel_size(100)
    properties_box.append(image)

    properties_list = Gtk.ListBox(selection_mode="none", margin_top=12, margin_bottom=12, margin_start=12, margin_end=12)
    properties_list.add_css_class("boxed-list")

    path = str(window.user_data_path) + window.host_flatpaks[index][2]
    
    if os.path.exists(path):
        user_data_row.set_title("User Data")
        user_data_row.set_subtitle(f"{path}\n~{func.get_size_format(func.get_directory_size(path))}")

        open_button = Gtk.Button(icon_name="document-open-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Open Data Folder"))
        open_button.add_css_class("flat")
        open_button.connect("clicked", open_button_handler)
        user_data_row.add_suffix(open_button)

        clean_button = Gtk.Button(icon_name="brush-symbolic", valign=Gtk.Align.CENTER, tooltip_text="Send User Data to the Trash")
        clean_button.add_css_class("flat")
        clean_button.connect("clicked", clean_button_handler)
        user_data_row.add_suffix(clean_button)

    properties_box.append(user_data_list)

    column_headers = [_('Name'), _('Description'), _('App ID'), _('Version'), _('Branch'), _('Arch'), _('Origin'), _('Installation'), _('Ref'), _('Active Commit'), _('Latest Commit'), _('Installed Size'), _('Options')]
    for column in range(len(window.host_flatpaks[index])):
        if window.host_flatpaks[index][column] == "":
            continue
        row_item = Adw.ActionRow(title=column_headers[column])
        row_item.set_subtitle(GLib.markup_escape_text(window.host_flatpaks[index][column]))

        properties_copy_button = Gtk.Button(icon_name="edit-copy-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("Copy {}").format(column_headers[column]))
        properties_copy_button.add_css_class("flat")
        properties_copy_button.connect("clicked", copy_button_handler, column_headers[column], window.host_flatpaks[index][column])
        row_item.add_suffix(properties_copy_button)

        properties_list.append(row_item)

    properties_box.append(properties_list)

    properties_window.set_content(properties_title_bar)
    properties_window.present()
