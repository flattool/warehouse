from gi.repository import Adw, Gtk, Gdk, GLib, Pango
clipboard = Gdk.Display.get_default().get_clipboard()

class ErrorToast:
    def __init__(self, display_msg, error_msg, parent_window, format=True):

        def on_response(dialog, response_id):
            if response_id == "copy":
                clipboard.set(error_msg)

        popup = Adw.AlertDialog.new(display_msg, None if format else error_msg)
        popup.add_response("copy", _("Copy"))
        popup.add_response("ok", _("OK"))
        popup.connect("response", on_response)

        if format:
            lb = Gtk.Label(selectable=True, wrap=True)#, natural_wrap_mode=Gtk.NaturalWrapMode.WORD)
            lb.set_markup(f"<tt>{GLib.markup_escape_text(error_msg)}</tt>")
            # lb.set_label(error_msg)
            # lb.set_selectable(True)
            popup.set_extra_child(lb)

        self.toast = Adw.Toast(title=display_msg, button_label=_("Details"))
        self.toast.connect("button-clicked", lambda *_: popup.present(parent_window))