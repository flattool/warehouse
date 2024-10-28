from gi.repository import GLib, Gio
from .host_info import HostInfo
import subprocess, re

class ChangeVersionWorker:
	process = None
	callback = None
	error_callback = None
	loading_status = None
	did_error = False

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
		try:
			cmd = ['flatpak-spawn', '--host', 'pkexec', 'sh', '-c']

			installation = package.info['installation']
			real_installation = ""
			if installation == "user" or installation == "system":
				real_installation = f"--{installation}"
			else:
				real_installation = f"--installation={installation}"

			suffix = ""
			unmask_cmd = f"flatpak mask --remove {real_installation} {package.info['id']} && "
			change_version_cmd = f"flatpak update {package.info['ref']} --commit={commit} {real_installation} -y"
			mask_cmd = f" && flatpak mask {real_installation} {package.info['id']}"
			if package.is_masked:
				suffix += unmask_cmd

			suffix += change_version_cmd
			if should_mask:
				suffix += mask_cmd

			cmd.append(suffix)
			this.process = subprocess.Popen(cmd, stdout=subprocess.PIPE,  stderr=subprocess.PIPE, text=True)
			percent_pattern = r'\d{1,3}%'
			amount_pattern = r'(\d+)/(\d+)'
			for line in this.process.stdout:
				line = line.strip()
				percent_match = re.search(percent_pattern, line)
				if percent_match:
					ratio = int(percent_match.group()[0:-1]) / 100.0
					amount_match = re.search(amount_pattern, line)
					if amount_match:
						amount = amount_match.group().split('/')
						complete = int(amount[0]) - 1
						total = int(amount[1])
						this.update_status(ratio, complete, total)
					else:
						this.update_status(ratio, 0, 1)

			this.process.wait(timeout=10)
			if error := this.process.communicate()[1].strip():
				this.on_error(_("Error occurred while changing version"), error)

		except subprocess.TimeoutExpired as te:
			this.process.terminate()
			this.on_error(_("Error occurred while changing version"), _("Failed to exit cleanly"))

		except Exception as e:
			this.process.terminate()
			this.on_error(_("Error occurred while changing version"), str(e))

	@classmethod
	def cancel(this):
		if this.process is None:
			return

		try:
			this.process.terminate()
			this.process.wait(timeout=10)
		except Exception as e:
			this.on_error(_("Could not cancel version change"), str(e))

	@classmethod
	def on_done(this, *args):
		this.process = None
		HostInfo.main_window.remove_refresh_lockout("changing version")
		if not this.loading_status is None:
			this.loading_status.progress_bar.set_fraction(0.0)

		if not this.callback is None:
			this.callback(this.did_error)

	@classmethod
	def on_error(this, user_facing_label, error_message):
		this.did_error = True
		if not this.error_callback is None:
			this.error_callback(user_facing_label, error_message)

	@classmethod
	def change_version(this, should_mask, package, commit, loading_status=None, callback=None, error_callback=None):
		if not this.process is None:
			this.on_error(_("Could not change version"), _("Another package is changing version."))
			return False

		this.loading_status = loading_status
		this.callback = callback
		this.error_callback = error_callback
		HostInfo.main_window.add_refresh_lockout("changing version")
		Gio.Task.new(None, None, this.on_done).run_in_thread(lambda *_: this.change_version_thread(should_mask, package, commit))
		return True
