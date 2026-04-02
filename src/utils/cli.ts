import Gio from "gi://Gio?version=2.0"
import GLib from "gi://GLib?version=2.0"

import { SharedVars } from "./shared_vars.js"

export class LineProcess {
	readonly process: Gio.Subprocess
	readonly #cancellable = new Gio.Cancellable()

	on_stdout_line?: (line: string) => void
	on_stderr_line?: (line: string) => void

	constructor(argv: string[], run_on_host = false) {
		if (run_on_host && SharedVars.is_flatpak) {
			argv = ["flatpak-spawn", "--host", ...argv]
		}
		this.process = new Gio.Subprocess({
			argv,
			flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
		})
	}

	cancel(): void {
		this.#cancellable.cancel()
		this.process.force_exit()
	}

	run(): Promise<{ exit_status: number, stdout: string[], stderr: string[], cancelled: boolean }> {
		return new Promise((resolve, _reject) => {
			this.process.init(this.#cancellable)
			const stdout_lines: string[] = []
			const stderr_lines: string[] = []
			this.#pump_lines(this.process.get_stdout_pipe()!, (line) => {
				if (!line) return
				stdout_lines.push(line)
				this.on_stdout_line?.(line)
			})
			this.#pump_lines(this.process.get_stderr_pipe()!, (line) => {
				if (!line) return
				stderr_lines.push(line)
				this.on_stderr_line?.(line)
			})
			this.process.wait_async(this.#cancellable, (_process, res) => {
				try {
					this.process.wait_finish(res)
					resolve({
						exit_status: this.process.get_exit_status(),
						stdout: stdout_lines,
						stderr: stderr_lines,
						cancelled: this.#cancellable.is_cancelled(),
					})
				} catch (e) {
					if (e instanceof GLib.Error && e.matches(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED)) {
						resolve({
							exit_status: -1,
							stdout: stdout_lines,
							stderr: stderr_lines,
							cancelled: true,
						})
					} else {
						console.error("Unexpected error while running process: " + e)
						resolve({
							exit_status: -1,
							stdout: stdout_lines,
							stderr: stderr_lines,
							cancelled: false,
						})
					}
				}
			})
		})
	}

	#pump_lines(stream: Gio.InputStream, callback: (line: string | null) => void): void {
		const data_stream = new Gio.DataInputStream({ base_stream: stream })
		const read_one = (): void => {
			data_stream.read_line_async(GLib.PRIORITY_DEFAULT_IDLE, this.#cancellable, (_data_stream, res) => {
				try {
					const [line] = data_stream.read_line_finish_utf8(res)
					if (line === null) {
						callback(null)
						return
					}
					callback(line)
					read_one()
				} catch (e) {
					callback(null)
				}
			})
		}
		read_one()
	}
}
