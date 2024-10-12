from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
import subprocess, re

class ChangeVersionWorker:
	process = None
	callback = None
	error_callback = None
	loading_status = None
	cancelled = False
	
	@classmethod
	def update_status(this, package_ratio, complete, total):
		final_ratio = (package_ratio + complete) / (total or 1)
		
		print(f"fr: {final_ratio:.2f}")
		print("r:", package_ratio, ", c:", complete, ", t:", total)
		print("=======================================")
		
		if not this.loading_status is None:	
			GLib.idle_add(lambda *_: this.loading_status.progress_bar.set_fraction(final_ratio))
			
	@classmethod
	def change_version_thread(this, should_mask, package, commit):
		cmd = ['flatpak-spawn', '--host', 'pkexec', 'sh', '-c']
		
		installation = package.info['installation']
		real_installation = ""
		if installation == "user" or installation == "system":
			real_installation = f"--{installation}"
		else:
			real_installation = f"--installation={installation}"
			
		suffix = ""
		unmask_cmd = f"flatpak mask --remove {real_installation} {package.info['id']} && "
		change_version_cmd = f"flatpak update {package.info['ref']} --commit={commit} {real_installation}"
		mask_cmd = f" && flatpak mask {real_installation} {package.info['id']}"
		if package.is_masked:
			suffix += unmask_cmd
			
		suffix += change_version_cmd
		if should_mask:
			suffix += mask_cmd
			
		cmd.append(suffix)
		print(cmd)
		
	@classmethod
	def cancel(this):
		if this.process is None:
			return
			
		try:
			this.cancelled = True
			this.process.terminate()
			this.process.wait(timeout=10)
		except Exception as e:
			this.on_error(_("Could not cancel installation"), str(e))
			
	@classmethod
	def on_done(this, *args):
		this.process = None
		this.cancelled = False
		HostInfo.main_window.remove_refresh_lockout("changing version")
		if not this.loading_status is None:
			this.loading_status.progress_bar.set_fraction(0.0)
			
		if not this.callback is None:
			this.callback()
			
	@classmethod
	def on_error(this, user_facing_label, error_message):
		if not this.error_callback is None:
			this.error_callback(user_facing_label, error_message)
			
	@classmethod
	def change_version(this, should_mask, package, commit, loading_status=None, callback=None, error_callback=None):
		if not this.process is None:
			this.on_error(_("Could not install packages"), _("Packages are currently being installed."))
			return False
			
		this.loading_status = loading_status
		this.callback = callback
		this.error_callback = error_callback
		HostInfo.main_window.add_refresh_lockout("changing version")
		Gio.Task.new(None, None, this.on_done).run_in_thread(lambda *_: this.change_version_thread(should_mask, package, commit))
		return True
