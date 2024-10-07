from gi.repository import Adw, Gtk, GLib, Gio
import subprocess, re

class PackageInstallWorker:
	""" Expect Package Installation Request Data to be Formatted as Such
		[
			{
				"remote": "<remote name>",
				"installation": "<installation name>",
				"package_names": ["<pkg id 1>", "<pkg id 2>", ...],
			},
			{
				...
			},
		]
	"""
	
	groups = None
	process = None
	callback = None
	error_callback = None
	loading_status = None
	total_groups = 0
	cancelled = False
	
	@classmethod
	def on_error(this, user_facing_label, error_message):
		print("\nPackageInstallWorker error:", user_facing_label)
		print(error_message, "\n")
		if not this.error_callback is None:
			this.error_callback(user_facing_label, error_message)
	
	@classmethod
	def update_status(this, index, package_ratio, complete, total):
		group_ratio = (package_ratio + complete) / (total or 1)
		final_ratio = (group_ratio + index) / (this.total_groups or 1)
		
		print(f"gr: {(package_ratio + complete) / (total or 1):.2f}, fr: {((package_ratio + complete) / (total or 1) + index) / (this.total_groups or 1):.2f}")
		print("i:", index, ", g:", this.total_groups, ", r:", package_ratio, ", c:", complete, ", t:", total)
		print("=======================================")
		
		if not this.loading_status is None:	
			GLib.idle_add(lambda *_: loading_status.progress_bar.set_fraction(final_ratio))
			
	@classmethod
	def install_thread(this):
		try:
			errors = []
			for index, group in enumerate(this.groups):
				if this.cancelled:
					return
					
				real_installation = ""
				installation = group['installation']
				if installation == "user" or installation == "system":
					real_installation = f"--{installation}"
				else:
					real_installation = f"--installation={installation}"
					
				this.process = subprocess.Popen(
					['flatpak-spawn', '--host', 'flatpak', 'install', '-y', group['remote'], real_installation] + group['package_names'],
					stdout=subprocess.PIPE,  stderr=subprocess.PIPE, text=True,
				)
				print(group['remote'], group['package_names'], "\n\n\n\n\n\n\n\n")
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
							this.update_status(index, ratio, complete, total)
						else:
							this.update_status(index, ratio)
							
				this.process.wait(timeout=10)
				if error := this.process.communicate()[1].strip():
					errors.append(error)
					
			if len(errors) > 0:
				this.on_error("\n".join(errors))
				
		except subprocess.TimeoutExpired as te:
			this.process.terminate()
			this.on_error(_("Could not install some packages"), _("Failed to exit cleanly"))
				
		except Exception as e:
			this.process.terminate()
			this.on_error(_("Could not install some packages"), str(e))
		
	@classmethod
	def cancel(this):
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
		if not this.callback is None:
			this.callback()
			
	@classmethod
	def install(this, groups, loading_status=None, callback=None, error_callback=None):
		if not this.process is None:
			this.on_error(_("Could not install packages"), _("Packages are currently being installed."))
			return False
			
		this.callback = callback
		this.groups = groups
		this.total_groups = len(groups)
		this.loading_status = loading_status
		this.error_callback = error_callback
		
		if this.total_groups < 1:
			this.on_error(_("Could not install packages"), _("No packages were asked to be installed."))
			return False
			
		Gio.Task.new(None, None, callback).run_in_thread(lambda *_: this.install_thread())
		return True
