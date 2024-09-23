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
        
    def compress_thread(self, *args):
        try:
            if not os.path.exists(self.new_path):
                os.makedirs(self.new_path)
                
            self.total = int(subprocess.run(['du', '-s', self.existing_path], check=True, text=True, capture_output=True).stdout.split('\t')[0])
            self.total /= 2.5 # estimate for space savings
            subprocess.run(['tar', 'cafv', f'{self.new_path}/{self.file_name}.tar.zst', '-C', self.existing_path, '.'], check=True, capture_output=True)
            
            with open(f"{self.new_path}/{self.file_name}.json", 'w') as file:
                data = {
                    'snapshot_version': 1,
                    'name': self.name,
                }
                json.dump(data, file, indent=4)
                
            self.stop = True # tell the check timeout to stop, because we know the file is done being made
            
        except subprocess.CalledProcessError as cpe:
            self.stop = True
            print(cpe.stderr)
            
        except Exception as e:
            self.stop = True
            print(f"Error during compression: {e}")
            
    def check_size(self):
        try:
            output = subprocess.run(['du', '-s', f"{self.new_path}/{self.file_name}.tar.zst"], check=True, text=True, capture_output=True).stdout.split('\t')[0]
            working_total = int(output)
            self.fraction = working_total / self.total
            return not self.stop
                
        except subprocess.CalledProcessError as cpe:
            return not self.stop # continue the timeout or stop the timeout
            
    def compress(self):
        self.compress = True
        self.stop = False
        Gio.Task.new(None, None, None).run_in_thread(self.compress_thread)
        GLib.timeout_add(10, self.check_size)
        
