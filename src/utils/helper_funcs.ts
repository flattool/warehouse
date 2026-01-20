import Gio from "gi://Gio"
import GLib from "gi://GLib"

import { SharedVars } from "./shared_vars.js"

type RequireAtLeastOne<T> = (T extends any
	? { [K in keyof T]-?: Required<Pick<T, K>> & Partial<Omit<T, K>> }[keyof T]
	: never
)

export async function run_command_async(
	command: string[],
	config?: RequireAtLeastOne<{
		run_on_host?: boolean,
		cancellable?: Gio.Cancellable,
		on_stdout_line?: (line: string) => void,
		on_stderr_line?: (line: string) => void,
	}>,
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
