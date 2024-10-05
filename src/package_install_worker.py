from gi.repository import Adw, Gtk, GLib, Gio

class PackageInstallWorker:
	process = None
	
	@classmethod
	def update_status(this, loading_status, ratio, complete=None, total=None):
		GLib.idle_add(lambda *_: loading_status.progress_bar.set_fraction(ratio))
		if (not complete is None) and (not total is None):
			GLib.idle_add(lambda *_: loading_status.progress_label.set_label(f'{int(ratio + complete / total)} / {total}'))
		elif loading_status.progress_label.get_visible():
			GLib.idle_add(lambda *_: loading_status.progress_label.set_visible(False))
			
	@classmethod
	def install_thread(this, loading_status, remote, installation, names, on_error):
		this.process = subprocess.Popen(
			['flatpak-spawn', '--host', 'flatpak', 'install', f'--installation={installation}', names],
			stdout=subprocess.PIPE, 
			stderr=subprocess.PIPE,
		)
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
					this.update_status(loading_status, ratio, complete, total)
				else:
					this.update_status(loading_status, ratio)
					
		this.process = None
		
	@classmethod
	def install(this, loading_status, remote, installation, names, callback=None, on_error=None):
		if not this.process is None:
			return "error, already installing something"
			
		Gio.Task.new(None, None, callback).run_in_thread(this.install_thread, loading_status, remote, installation, names, on_error)
		return ""
