import Gio from "gi://Gio?version=2.0"

export class SwitchTask {
	get is_running(): boolean { return this.#running }

	#cancellable: Gio.Cancellable | undefined
	#generation = 0
	#running = false

	constructor(
		private on_running_changed?: (running: boolean) => void,
	) {}

	async run_batch<T>(
		tasks: Iterable<(cancellable: Gio.Cancellable) => Promise<T>>,
		on_error: (e: unknown) => void = (e) => { throw e },
	): Promise<T[] | undefined> {
		this.#cancellable?.cancel()
		const cancellable = new Gio.Cancellable()
		this.#cancellable = cancellable
		const generation = this.#generation += 1

		this.#set_running(true)
		try {
			type SettltedPromise = Promise<{ ok: true, value: T } | { ok: false }>
			const settled_promises: SettltedPromise[] = []
			for (const fn of tasks) {
				settled_promises.push((async (): SettltedPromise => {
					try {
						return { ok: true as const, value: await fn(cancellable) }
					} catch (e) {
						if (!cancellable.is_cancelled()) {
							on_error(e)
						}
						return { ok: false as const }
					}
				})())
			}
			const settled = await Promise.all(settled_promises)
			return (generation === this.#generation
				? settled.flatMap((s) => (s.ok ? [s.value] : []))
				: undefined
			)
		} finally {
			if (generation === this.#generation) {
				this.#set_running(false)
			}
		}
	}

	async run<T>(fn: (cancellable: Gio.Cancellable) => Promise<T>): Promise<T | undefined> {
		const results = await this.run_batch([fn])
		return results?.[0]
	}

	// async run(fn: (cancellable: Gio.Cancellable) => Promise<T>): Promise<T | undefined> {
	// 	this.#cancellable?.cancel()
	// 	const cancellable = new Gio.Cancellable()
	// 	this.#cancellable = cancellable
	// 	const generation = this.#generation += 1

	// 	this.#set_running(true)
	// 	try {
	// 		const result = await fn(cancellable)
	// 		return generation === this.#generation ? result : undefined
	// 	} catch (e) {
	// 		if (cancellable.is_cancelled()) return undefined
	// 		throw e
	// 	} finally {
	// 		if (generation === this.#generation) {
	// 			this.#set_running(false)
	// 		}
	// 	}
	// }

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
