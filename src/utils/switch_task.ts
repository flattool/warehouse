import Gio from "gi://Gio?version=2.0"

export class SwitchTask<T> {
	get is_running(): boolean { return this.#running }

	#cancellable: Gio.Cancellable | undefined
	#generation = 0
	#running = false

	constructor(
		private on_running_changed?: (running: boolean) => void,
	) {}

	async run(fn: (cancellable: Gio.Cancellable) => Promise<T>): Promise<T | undefined> {
		this.#cancellable?.cancel()
		const cancellable = new Gio.Cancellable()
		this.#cancellable = cancellable
		const generation = this.#generation += 1

		this.#set_running(true)
		try {
			const result = await fn(cancellable)
			return generation === this.#generation ? result : undefined
		} catch (e) {
			if (cancellable.is_cancelled()) return undefined
			throw e
		} finally {
			if (generation === this.#generation) {
				this.#set_running(false)
			}
		}
	}

	cancel(): void {
		this.#cancellable?.cancel()
		this.#generation += 1
		this.#set_running(false)
	}

	#set_running(value: boolean): void {
		if (this.#running === value) return
		this.#running = value
		this.on_running_changed?.(value)
	}
}
