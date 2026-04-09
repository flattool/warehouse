import Gio from "gi://Gio?version=2.0"
import GLib from "gi://GLib?version=2.0"

import { SharedVars } from "./shared_vars.js"

export class ProcessError extends Error {
	constructor(
		readonly stdout: string[],
		readonly stderr: string[],
		cause?: unknown,
	) {
		super(`stdout:\n${stdout.join("\n")}\nstderr:\n${stderr.join("\n")}`)
		this.name = "ProcessError"
		if (cause) {
			this.cause = cause
		}
	}
}

export class LineProcess {
	static async run(
		argv: string[],
		options?: {
			run_on_host?: boolean,
			on_stdout_line?: (line: string) => void,
			on_stderr_line?: (line: string) => void,
		},
	): Promise<{ exit_status: number, stdout: string[], stderr: string[], cancelled: boolean }> {
		const process = new LineProcess(argv, options?.run_on_host)
		if (options?.on_stdout_line) {
			process.on_stdout_line = options.on_stdout_line
		}
		if (options?.on_stderr_line) {
			process.on_stderr_line = options.on_stderr_line
		}
		return await process.run()
	}

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
		return new Promise((resolve, reject) => {
			try {
				this.process.init(this.#cancellable)
			} catch (e) {
				reject(e)
				return
			}
			const stdout_lines: string[] = []
			const stderr_lines: string[] = []

			let rejected = false
			let process_done = false
			let exit_status_result = -1
			let cancelled_result = false
			let streams_done = 0

			const try_resolve = (): void => {
				if (rejected || !process_done || streams_done < 2) return

				if (exit_status_result !== 0 && !cancelled_result) {
					rejected = true
					reject(new ProcessError(stdout_lines, stderr_lines))
					return
				}

				resolve({
					exit_status: exit_status_result,
					stdout: stdout_lines,
					stderr: stderr_lines,
					cancelled: cancelled_result,
				})
			}

			const on_stream_err = (e: unknown): void => {
				if (rejected) return
				rejected = true
				this.#cancellable.cancel()
				reject(new ProcessError(stdout_lines, stderr_lines, e))
			}

			this.#pump_lines(this.process.get_stdout_pipe()!, on_stream_err, (line) => {
				if (rejected) return
				if (line === null) {
					streams_done += 1
					try_resolve()
					return
				}
				stdout_lines.push(line)
				this.on_stdout_line?.(line)
			})
			this.#pump_lines(this.process.get_stderr_pipe()!, on_stream_err, (line) => {
				if (rejected) return
				if (line === null) {
					streams_done += 1
					try_resolve()
					return
				}
				stderr_lines.push(line)
				this.on_stderr_line?.(line)
			})

			this.process.wait_async(this.#cancellable, (_process, res) => {
				try {
					this.process.wait_finish(res)
					exit_status_result = this.process.get_exit_status()
					cancelled_result = this.#cancellable.is_cancelled()
				} catch (e) {
					if (e instanceof GLib.Error && e.matches(Gio.IOErrorEnum, Gio.IOErrorEnum.CANCELLED)) {
						exit_status_result = -1
						cancelled_result = true
					} else {
						exit_status_result = this.process.get_exit_status()
						cancelled_result = false
						rejected = true
						reject(new ProcessError(
							stdout_lines,
							stderr_lines,
							e,
						))
					}
				} finally {
					process_done = true
					try_resolve()
				}
			})
		})
	}

	#pump_lines(stream: Gio.InputStream, on_err: (e: unknown) => void, callback: (line: string | null) => void): void {
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
					on_err(e)
				}
			})
		}
		read_one()
	}
}
