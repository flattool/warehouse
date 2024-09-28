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
            print("Called Error in Compress Thread")
            self.do_cancel(cpe.stderr.decode(), [f'{self.new_path}/{self.file_name}.tar.zst', f'{self.new_path}/{self.file_name}.json'])  # stderr is in bytes, so decode it
            
        except Exception as e:
            print("Exception in Compress Thread")
            self.do_cancel(str(e), [f'{self.new_path}/{self.file_name}.tar.zst', f'{self.new_path}/{self.file_name}.json'])
            
    def extract_thread(self, *args):
        try:
            if os.path.exists(self.new_path):
                subprocess.run(['gio', 'trash', self.new_path], capture_output=True, check=True) # trash the current user data, because new data will go in its place
                
            os.makedirs(self.new_path) # create the new user data path
                
            self.total = int(subprocess.run(['du', '-s', self.existing_path], check=True, text=True, capture_output=True).stdout.split('\t')[0])
            self.total *= 2.2 # estimate from space savings
            self.process = subprocess.Popen(['tar', '--zstd', '-xvf', self.existing_path, '-C',  self.new_path],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            stdout, stderr = self.process.communicate()
            if self.process.returncode != 0:
                raise subprocess.CalledProcessError(self.process.returncode, self.process.args, output=stdout, stderr=stderr)
                
            self.stop = True # tell the check timeout to stop, because we know the file is done being made
                
        except subprocess.CalledProcessError as cpe:
            print("Called Error in Extract Thread")
            self.do_cancel(cpe.stderr.decode(), [self.new_path])
            
        except Exception as e:
            print("Exception in Extract Thread")
            self.do_cancel(str(e), [self.new_path])

    def do_cancel(self, error_str, files_to_trash=None):
        self.process.terminate()
        self.process.wait()
        if not files_to_trash is None:
            try:
                subprocess.run(['gio', 'trash'] + files_to_trash, capture_output=True, check=True)

            except Exception:
                pass

        self.stop = True
        print("Error in cancelling:", error_str)
            
    def check_size(self, check_path):
        try:
            output = subprocess.run(['du', '-s', check_path], check=True, text=True, capture_output=True).stdout.split('\t')[0]
            working_total = int(output)
            self.fraction = working_total / self.total
            return not self.stop
            
        except subprocess.CalledProcessError as cpe:
            return not self.stop # continue the timeout or stop the timeout
            
    def compress(self):
        self.stop = False
        Gio.Task.new(None, None, None).run_in_thread(self.compress_thread)
        GLib.timeout_add(200, self.check_size, f"{self.new_path}/{self.file_name}.tar.zst")
        
    def extract(self):
        self.stop = False
        Gio.Task.new(None, None, None).run_in_thread(self.extract_thread)
        GLib.timeout_add(200, self.check_size, self.new_path)
