import GLib from "gi://GLib?version=2.0"

declare global {
	interface String {
		markup_escape_text(this: string): string
		normalize_path(this: string): string
	}
}

String.prototype.markup_escape_text = function (): string {
	return GLib.markup_escape_text(this, -1)
}

String.prototype.normalize_path = function (): string {
	let normalized = this.replace(/\/+/g, "/")
	if (normalized.length > 1 && normalized.endsWith("/")) {
		normalized = normalized.slice(0, -1)
	}
	return normalized
}
