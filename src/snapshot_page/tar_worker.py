from gi.repository import GLib, Gio
from src.host_info import HostInfo
from src.gtk.error_toast import ErrorToast
import os, subprocess, json
import gettext

_ = gettext.gettext


class TarWorker:
	def compress_thread(self, *args):
		try:
			if not os.path.exists(self.new_path):
				os.makedirs(self.new_path)

			self.total = int(subprocess.run(["du", "-s", self.existing_path], check=True, text=True, capture_output=True).stdout.split("\t")[0])
			self.total /= 2.2  # estimate for space savings
			self.process = subprocess.Popen(
				["tar", "cafv", f"{self.new_path}/{self.file_name}.tar.zst", "-C", self.existing_path, "."], stdout=subprocess.PIPE, stderr=subprocess.PIPE
			)
			stdout, stderr = self.process.communicate()
			if self.process.returncode != 0:
				raise subprocess.CalledProcessError(self.process.returncode, self.process.args, output=stdout, stderr=stderr)

			with open(f"{self.new_path}/{self.file_name}.json", "w") as file:
				data = {
					"snapshot_version": 1,
					"name": self.name,
				}
				json.dump(data, file, indent=4)

			self.stop = True  # tell the check timeout to stop, because we know the file is done being made
			HostInfo.main_window.remove_refresh_lockout("managing snapshot")

		except subprocess.CalledProcessError as cpe:
			self.do_cancel(cpe.stderr.decode())  # stderr is in bytes, so decode it

		except Exception as e:
			self.do_cancel(str(e))

	def extract_thread(self, *args):
		try:
			if os.path.exists(self.new_path):
				subprocess.run(
					["gio", "trash", self.new_path], capture_output=True, check=True
				)  # trash the current user data, because new data will go in its place

			os.makedirs(self.new_path)  # create the new user data path

			self.total = int(subprocess.run(["du", "-s", self.existing_path], check=True, text=True, capture_output=True).stdout.split("\t")[0])
			self.total *= 2.2  # estimate from space savings
			self.process = subprocess.Popen(["tar", "--zstd", "-xvf", self.existing_path, "-C", self.new_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			stdout, stderr = self.process.communicate()
			if self.process.returncode != 0:
				raise subprocess.CalledProcessError(self.process.returncode, self.process.args, output=stdout, stderr=stderr)

			self.stop = True  # tell the check timeout to stop, because we know the file is done being made
			HostInfo.main_window.remove_refresh_lockout("managing snapshot")

		except subprocess.CalledProcessError as cpe:
			self.do_cancel(cpe.stderr.decode())

		except Exception as e:
			self.do_cancel(str(e))

	def do_cancel(self, error_str):
		if self.has_cancelled or self.stop:
			return

		self.has_cancelled = True
		self.process.terminate()
		self.process.wait()
		if len(self.files_to_trash_on_cancel) > 0:
			try:
				subprocess.run(["gio", "trash"] + self.files_to_trash_on_cancel, capture_output=True, check=True)

			except Exception:
				pass

		self.stop = True
		HostInfo.main_window.remove_refresh_lockout("managing snapshot")
		if self.toast_overlay and error_str != "manual_cancel":
			self.toast_overlay.add_toast(ErrorToast(_("Error in snapshot handling"), error_str).toast)

	def check_size(self, check_path):
		try:
			output = subprocess.run(["du", "-s", check_path], check=True, text=True, capture_output=True).stdout.split("\t")[0]
			working_total = float(output)
			self.fraction = working_total / self.total
			return not self.stop

		except subprocess.CalledProcessError:
			return not self.stop  # continue the timeout or stop the timeout

	def compress(self):
		self.stop = False
		self.files_to_trash_on_cancel = [f"{self.new_path}/{self.file_name}.tar.zst", f"{self.new_path}/{self.file_name}.json"]
		HostInfo.main_window.add_refresh_lockout("managing snapshot")
		Gio.Task.new(None, None, None).run_in_thread(self.compress_thread)
		GLib.timeout_add(200, self.check_size, f"{self.new_path}/{self.file_name}.tar.zst")

	def extract(self):
		self.stop = False
		self.files_to_trash_on_cancel = [self.new_path]
		HostInfo.main_window.add_refresh_lockout("managing snapshot")
		Gio.Task.new(None, None, None).run_in_thread(self.extract_thread)
		GLib.timeout_add(200, self.check_size, self.new_path)

	def __init__(self, existing_path, new_path, file_name="", name="", toast_overlay=None):
		self.existing_path = existing_path
		self.new_path = new_path
		self.file_name = file_name
		self.name = name
		self.should_check = False
		self.stop = False
		self.fraction = 0.0
		self.total = 0
		self.process = None
		self.toast_overlay = toast_overlay
		self.has_cancelled = False
		self.files_to_trash_on_cancel = []
