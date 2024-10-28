from gi.repository import Adw, Gtk, Gdk, GLib

class ErrorToast:
	main_window = None
	def __init__(self, display_msg, error_msg):
		def on_response(dialog, response_id):
			if response_id == "copy":
				self.clipboard.set(error_msg)

		# Extra Object Creation
		self.toast = Adw.Toast(title=display_msg, button_label=_("Details"))
		popup = Adw.AlertDialog.new(display_msg)
		self.clipboard = Gdk.Display.get_default().get_clipboard()

		# Apply
		print(display_msg)
		print(error_msg)
		popup.add_response("copy", _("Copy"))
		popup.add_response("ok", _("OK"))
		lb = Gtk.Label(selectable=True, wrap=True)#, natural_wrap_mode=Gtk.NaturalWrapMode.WORD)
		lb.set_markup(f"<tt>{GLib.markup_escape_text(error_msg)}</tt>")
		# lb.set_label(error_msg)
		# lb.set_selectable(True)
		popup.set_extra_child(lb)

		# Connections
		self.toast.connect("button-clicked", lambda *_: popup.present(self.main_window))
		popup.connect("response", on_response)
