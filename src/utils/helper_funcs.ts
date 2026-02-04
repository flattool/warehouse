import Gio from "gi://Gio"
import GLib from "gi://GLib"
import Adw from "gi://Adw?version=1"

import { SharedVars } from "./shared_vars.js"

type RunCommandConfig = {
	run_on_host?: boolean,
	cancellable?: Gio.Cancellable,
	on_stdout_line?: (line: string) => void,
	on_stderr_line?: (line: string) => void,
}

export function ask_to_continue(
	heading: string,
	body: string,
	continue_label: string,
	response_appearance?: Adw.ResponseAppearance,
): Promise<boolean> {
	const CANCEL = "cancel"
	const CONTINUE = "continue"
	const dialog = new Adw.AlertDialog({ heading, body })
	dialog.add_response(CANCEL, _("Cancel"))
	dialog.add_response(CONTINUE, continue_label)
	if (response_appearance !== undefined) {
		dialog.set_response_appearance(CONTINUE, response_appearance)
	}
	dialog.present(SharedVars.main_window)
	return new Promise((resolve, _reject) => {
		let resolve_id = 0
		resolve_id = dialog.connect("response", (__, response) => {
			dialog.disconnect(resolve_id)
			resolve(response === CONTINUE)
		})
	})
}

export async function get_file_size_bytes(path: string): Promise<number> {
	const cmd: string[] = ["du", "-B1", "-s", path.normalize_path()]
	const size: string | undefined = (await run_command_async(cmd)).split("\t")[0]
	if (!size) return 0
	return Number.parseFloat(size)
}

export async function get_readable_file_size(path: string): Promise<string> {
	let size: number = await get_file_size_bytes(path)
	const units: string[] = ["B", "KB", "MB", "GB", "TB"]
	const base = 1000
	let index: number = 0
	while (size >= base && index < units.length - 1) {
		size /= base
		index += 1
	}
	return `${size.toFixed(2)} ${units[index]}`
}

export async function run_command_async(
	command: string[],
	config?: RunCommandConfig,
): Promise<string> {
	const { run_on_host, cancellable, on_stdout_line, on_stderr_line } = config ?? {}
	const prefix = run_on_host && SharedVars.is_flatpak ? ["flatpak-spawn", "--host"] : []

	const fullCommand = [...prefix, ...command]

	const subprocess = new Gio.Subprocess({
		argv: fullCommand,
		flags: Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_PIPE,
	})

	try {
		subprocess.init(cancellable ?? null)
	} catch (e) {
		throw new Error(`Failed to launch command: ${e}`)
	}

	if (cancellable) {
		cancellable.connect(() => subprocess.force_exit())
	}

	const stdout_pipe = subprocess.get_stdout_pipe()
	const stderr_pipe = subprocess.get_stderr_pipe()

	if (!stdout_pipe) return ""

	const stdoutStream = new Gio.DataInputStream({ base_stream: stdout_pipe })
	const stderrStream = new Gio.DataInputStream(stderr_pipe ? { base_stream: stderr_pipe } : {})

	const textDecoder = new TextDecoder("utf-8", { fatal: false })

	// Read stdout line-by-line
	const read_stdout = new Promise<string>((resolve, reject) => {
		let output = ""

		function read_next_line(): void {
			stdoutStream.read_line_async(GLib.PRIORITY_DEFAULT, cancellable ?? null, (_stream, res) => {
				try {
					const [lineBytes] = stdoutStream.read_line_finish(res)
					if (lineBytes !== null) {
						const line = textDecoder.decode(lineBytes)
						output += line + "\n"
						if (on_stdout_line) on_stdout_line(line.trim())
						read_next_line()
					} else {
						resolve(output.trim())
					}
				} catch (err) {
					reject(err)
				}
			})
		}

		read_next_line()
	})

	// Read stderr fully (not line-by-line unless you need to)
	const read_stderr = new Promise<string>((resolve, reject) => {
		let output = ""

		function read_next_line(): void {
			stderrStream.read_line_async(GLib.PRIORITY_DEFAULT, cancellable ?? null, (_stream, res) => {
				try {
					const [lineBytes] = stderrStream.read_line_finish(res)
					if (lineBytes !== null) {
						const line = textDecoder.decode(lineBytes)
						output += line + "\n"
						if (on_stderr_line) on_stderr_line(line.trim())
						read_next_line()
					} else {
						resolve(output.trim())
					}
				} catch (err) {
					reject(err)
				}
			})
		}

		read_next_line()
	})

	const [stdout, stderr] = await Promise.all([read_stdout, read_stderr])

	await new Promise<void>((resolve, reject) => {
		subprocess.wait_check_async(cancellable ?? null, (_proc, res) => {
			try {
				subprocess.wait_check_finish(res)
				resolve()
			} catch (e) {
				reject(stderr || e)
			}
		})
	})

	return stdout
}

export async function run_command_async_pkexec_on_fail(
	command: string[],
	config?: RunCommandConfig,
): Promise<string> {
	try {
		return await run_command_async(command, config)
	} catch (error) {
		return await run_command_async(["pkexec", ...command], config)
	}
}
