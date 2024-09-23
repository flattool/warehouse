from gi.repository import Adw, Gtk, GLib, Gio
from .host_info import HostInfo
from .error_toast import ErrorToast
import os, tarfile, subprocess, json

class TarWorker:
    def __init__(self, existing_path, new_path, file_name, name=""):
        self.existing_path = existing_path
        self.new_path = new_path
        self.file_name = file_name
        self.name = name
        self.should_check = False
        self.stop = False
        self.fraction = 0.0
        self.total = 0
        self.process = None
        
    def compress_thread(self, *args):
        try:
            if not os.path.exists(self.new_path):
                os.makedirs(self.new_path)
                
            self.total = int(subprocess.run(['du', '-s', self.existing_path], check=True, text=True, capture_output=True).stdout.split('\t')[0])
            self.total /= 2.2 # estimate for space savings
            self.process = subprocess.Popen(['tar', 'cafv', f'{self.new_path}/{self.file_name}.tar.zst', '-C', self.existing_path, '.'],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = self.process.communicate()
            if self.process.returncode != 0:
                raise subprocess.CalledProcessError(self.process.returncode, self.process.args, output=stdout, stderr=stderr)
            
            with open(f"{self.new_path}/{self.file_name}.json", 'w') as file:
                data = {
                    'snapshot_version': 1,
                    'name': self.name,
                }
                json.dump(data, file, indent=4)
                
            self.stop = True # tell the check timeout to stop, because we know the file is done being made
            
        except subprocess.CalledProcessError as cpe:
            print("Called Error")
            self.do_cancel(cpe.stderr.decode())  # stderr is in bytes, so decode it
            
        except Exception as e:
            print("Exception")
            self.do_cancel(str(e))

    def do_cancel(self, error_str=None):
        self.process.terminate()
        self.process.wait()
        if error_str == "manual_cancel":
            try:
                subprocess.run(['gio', 'trash', f'{self.new_path}/{self.file_name}.tar.zst'],capture_output=True)
                subprocess.run(['gio', 'trash', f'{self.new_path}/{self.file_name}.json'],capture_output=True)

            except Exception:
                pass

        self.stop = True
        print("Error in compression:", error_str)
            
    def check_size(self):
        try:
            output = subprocess.run(['du', '-s', f"{self.new_path}/{self.file_name}.tar.zst"], check=True, text=True, capture_output=True).stdout.split('\t')[0]
            working_total = int(output)
            self.fraction = working_total / self.total
            return not self.stop
            
        except subprocess.CalledProcessError as cpe:
            return not self.stop # continue the timeout or stop the timeout
            
    def compress(self):
        self.stop = False
        Gio.Task.new(None, None, None).run_in_thread(self.compress_thread)
        GLib.timeout_add(200, self.check_size)
        
