import Gio from "gi://Gio"
import GLib from "gi://GLib"
import Adw from "gi://Adw?version=1"

import { SharedVars } from "./shared_vars.js"
import { LineProcess } from "./cli.js"

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
	const size: string | undefined = (await LineProcess.run(cmd)).stdout.join("\n").split("\t")[0]
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
