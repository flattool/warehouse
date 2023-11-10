import os
import pathlib
import subprocess
import re

from gi.repository import Adw, Gdk, Gio, GLib, Gtk
from .properties_window import PropertiesWindow
from .filter_window import FilterWindow
from .common import myUtils

class AppRow(Adw.ActionRow):

    def __init__(self, parent_window, host_flatpaks, flatpak_index, **kwargs):
        super().__init__(**kwargs)
        self.my_utils = myUtils(parent_window)

        current_flatpak = host_flatpaks[flatpak_index]

        self.app_name = current_flatpak[0]
        self.app_id = current_flatpak[2]
        self.origin_remote = current_flatpak[6]
        self.install_type = current_flatpak[7]
        self.app_ref = current_flatpak[8]

        self.set_title(self.app_name)
        self.set_subtitle(self.app_id)
        self.add_prefix(self.my_utils.findAppIcon(self.app_id))
        
        properties_button = Gtk.Button(icon_name="info-symbolic", valign=Gtk.Align.CENTER, tooltip_text=_("View Properties"))
        properties_button.add_css_class("flat")
        properties_button.connect("clicked", lambda *_: PropertiesWindow(flatpak_index, host_flatpaks, parent_window))
        self.add_suffix(properties_button)
        
        select_flatpak_tickbox = Gtk.CheckButton() # visible=self.in_batch_mode
        select_flatpak_tickbox.add_css_class("selection-mode")
        # select_flatpak_tickbox.connect("toggled", self.rowSelectHandler, index)
        self.add_suffix(select_flatpak_tickbox)

        row_menu = Gtk.MenuButton(icon_name="view-more-symbolic", valign=Gtk.Align.CENTER) # visible=not self.in_batch_mode
        row_menu.add_css_class("flat")
        row_menu_model = Gio.Menu()
        copy_menu_model = Gio.Menu()
        advanced_menu_model = Gio.Menu()
        self.add_suffix(row_menu)

        parent_window.create_action(("copy-name" + str(flatpak_index)), lambda *_, name=self.app_name, toast=_("Copied name"): self.copyItem(name, toast))
        copy_menu_model.append_item(Gio.MenuItem.new(_("Copy Name"), f"win.copy-name{flatpak_index}"))

        row_menu_model.append_submenu(_("Copy"), copy_menu_model)

        row_menu.set_menu_model(row_menu_model)