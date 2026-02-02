import GLib from "gi://GLib?version=2.0"

declare global {
	interface String {
		markup_escape_text(this: string): string
		normalize_path(this: string): string
		split_n_times(this: string, split_by: string, amount: number): string[]
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

String.prototype.split_n_times = function (split_by: string, amount: number): string[] {
	if (amount <= 0) return [this]
	const parts = this.split(split_by)
	return parts.length <= amount ? parts : [...parts.slice(0, amount), parts.slice(amount).join(split_by)]
}
