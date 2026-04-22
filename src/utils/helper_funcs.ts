import GObject from "gi://GObject?version=2.0"
import Gio from "gi://Gio?version=2.0"
import Gtk from "gi://Gtk?version=4.0"
import Adw from "gi://Adw?version=1"

import { SharedVars } from "./shared_vars.js"
import { LineProcess } from "./cli.js"

export function ask_to_continue(
	heading: string,
	body: string,
	continue_label: string,
	response_appearance?: Adw.ResponseAppearance,
	extra_child?: Gtk.Widget,
): Promise<boolean> {
	const CANCEL = "cancel"
	const CONTINUE = "continue"
	const dialog = new Adw.AlertDialog({ heading, body })
	dialog.add_response(CANCEL, _("Cancel"))
	dialog.add_response(CONTINUE, continue_label)
	if (response_appearance) {
		dialog.set_response_appearance(CONTINUE, response_appearance)
	}
	if (extra_child) {
		dialog.extra_child = extra_child
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

export function make_signal_factory<Widget extends Gtk.Widget, Data extends GObject.Object>(
	widget_class: abstract new (...args: any[]) => Widget,
	data_class: abstract new (...args: any[]) => Data,
	callbacks: {
		readonly setup: (item: Gtk.ListItem) => Widget,
		readonly bind: (widget: Widget, data: Data, item: Gtk.ListItem) => void,
		readonly unbind?: (widget: Widget, data: Data, item: Gtk.ListItem) => void,
		readonly tear_down?: (widget: Widget) => void,
	},
): Gtk.SignalListItemFactory {
	void widget_class, data_class
	const factory = new Gtk.SignalListItemFactory()
	factory.connect("setup", (__, list_item: Gtk.ListItem) => list_item.set_child(callbacks.setup(list_item)))
	factory.connect("bind", (__, list_item: Gtk.ListItem) => callbacks.bind(
		list_item.get_child() as Widget,
		list_item.item as Data,
		list_item,
	))
	factory.connect("unbind", (__, list_item: Gtk.ListItem) => callbacks.unbind?.(
		list_item.get_child() as Widget,
		list_item.item as Data,
		list_item,
	))
	factory.connect("teardown", (__, list_item: Gtk.ListItem) => callbacks.tear_down?.(list_item.get_child() as Widget))
	return factory
}

export function *iterate_list_model<T extends GObject.Object>(model: Gio.ListModel<T>): Generator<T, void, unknown> {
	for (let i = 0; i < model.get_n_items(); i += 1) {
		const item: T | null = model.get_item(i)
		if (item !== null) yield item
	}
}

export function remove_host_prefix(path: string): string {
	return path.startsWith(SharedVars.host_prefix) ? path.replace(SharedVars.host_prefix, "") : path
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

export async function is_dbus_name_present(bus_name: string): Promise<boolean> {
	const command: string[] = [
		"gdbus",
		"call",
		"--session",
		"--dest",
		"org.freedesktop.DBus",
		"--object-path",
		"/org/freedesktop/DBus",
		"--method",
		"org.freedesktop.DBus.ListActivatableNames",
	]
	try {
		const response: string = (await LineProcess.run(command)).stdout.join("\n")
		return response.includes(bus_name)
	} catch (e) {
		print(`Failed to check presence of DBus name '${bus_name}':`, e)
		return false
	}
}

export async function activate_flatseal(app_id: string): Promise<void> {
	const command: string[] = [
		"gdbus",
		"call",
		"--session",
		"--dest",
		"com.github.tchx84.Flatseal",
		"--object-path",
		"/com/github/tchx84/Flatseal",
		"--method",
		"org.gtk.Actions.Activate",
		"show",
		`[<string '${app_id}'>]`,
		"{}",
	]
	await LineProcess.run(command)
}
