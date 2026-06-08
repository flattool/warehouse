/*!
 * GObjectify 1.0.1 - A type-safe, declarative TypeScript library for writing & interacting with GObject classes in GNOME JavaScript (GJS)
 * https://github.com/flattool/gobjectify
 *
 * MIT License
 *
 * Copyright (c) 2026 flattool
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 */
// @ts-nocheck - Skip checking, to ensure this library wont cause issues for users with different TypeScript setups.
import GObject from 'gi://GObject?version=2.0';
import Gio from 'gi://Gio?version=2.0';
import Gtk from 'gi://Gtk?version=4.0';
import GLib from 'gi://GLib?version=2.0';

declare const CHILD_SYMBOL: unique symbol;
type ChildDescriptor<_TypeHolder extends GObject.Object> = {
    child_symbol: typeof CHILD_SYMBOL;
};
type ExtractChildren<D> = {
    readonly [Key in keyof D as D[Key] extends ChildDescriptor<any> ? Key : never]: D[Key] extends ChildDescriptor<infer T> ? T : never;
};
/**
 * Creates a **ChildDescriptor** for use with `from()` and `GClass`, describing an internal Gtk Template Child.
 *
 * `from()` and `GClass` will see this descriptor and register the subclass as having this child type.
 *
 * @template ChildType The GObject type of the child.
 *
 * @example
 * ```ts
 * @GClass({ template: "resource:///path/to/some/UI.ui" })
 * class MyBox extends from(Gtk.Box, {
 *     _some_child: Child<Gtk.Button>(),
 * }) {}
 * ```
 */
declare function Child<ChildType extends GObject.Object>(): ChildDescriptor<ChildType>;

type GClass$1<T extends GObject.Object = GObject.Object> = {
    $gtype: GObject.GType;
} & (abstract new (...args: any[]) => T);
type GEnum<T extends number = number> = {
    $gtype: GObject.GType<T>;
};
declare const PROPERTY_SYMBOL: unique symbol;
declare const FLAG_PRESETS: {
    readonly readwrite: number;
    readonly readonly: number;
    readonly computed: GObject.ParamFlags.READWRITE;
    readonly const: GObject.ParamFlags.READABLE;
};
type FlagStrings = keyof typeof FLAG_PRESETS;
type PropDescriptor<T, F extends FlagStrings> = {
    readonly value?: T | undefined;
    readonly flag: F;
    readonly property_symbol: typeof PROPERTY_SYMBOL;
    readonly min?: number;
    readonly max?: number;
    create(name: string): GObject.ParamSpec;
    validate_value(value: any, spec: GObject.ParamSpec): T;
};
type PrimitiveCastable<Wide, Default, F extends FlagStrings> = {
    /**
     * Type helper to allow narrowing of a property descriptor's type.
     * A default value is required to exist, and the default value must extend the narrowed value.
     *
     * @template Narrow The narrowed type
     *
     * @example
     * ```ts
     * Property.rw.string("user").as<"user" | "admin">() // This property now only allows "user" or "admin", instead of all strings
     * ```
     */
    as<Narrow extends Wide>(): (Default extends Narrow ? PropDescriptor<Narrow, F> : [
        never
    ] & void);
};
type NarrowablePrimitiveDescriptor<T, Default, F extends FlagStrings> = (PropDescriptor<T, F> & PrimitiveCastable<T, Default, F>);
type ExtractWriteableProps<D> = {
    [Key in keyof D as D[Key] extends PropDescriptor<any, "readwrite" | "computed"> ? Key : never]: D[Key] extends PropDescriptor<infer T, any> ? T : never;
};
type ExtractReadonlyProps<D> = {
    readonly [Key in keyof D as D[Key] extends PropDescriptor<any, "readonly" | "const"> ? Key : never]: D[Key] extends PropDescriptor<infer T, any> ? T : never;
};
type ExtractConstructProps<D> = {
    [Key in keyof D as D[Key] extends PropDescriptor<any, "readonly" | "readwrite"> ? Key : never]: D[Key] extends PropDescriptor<infer T, any> ? T : never;
};
type Primitives = {
    int32: number;
    uint32: number;
    double: number;
    string: string;
    bool: boolean;
};
type PrimitiveTypes = {
    [K in keyof Primitives]: Primitives[K];
}[keyof Primitives];
type PrimitiveNeedsDefault<T extends PrimitiveTypes, F extends FlagStrings> = (T extends GEnum ? true : F extends "const" ? true : false);
type PrimitiveFactory<T extends PrimitiveTypes, F extends FlagStrings> = <const Default extends T>(...args: F extends "computed" ? [] : PrimitiveNeedsDefault<T, F> extends true ? [default_value: Default, ...(T extends number ? [config?: {
    min: number;
    max: number;
}] : [])] : [default_value?: Default, ...(T extends number ? [config?: {
    min: number;
    max: number;
}] : [])]) => NarrowablePrimitiveDescriptor<T, Default, F>;
type PrimitiveFactoriesEnsurer<F extends FlagStrings, C extends {
    [K in keyof Primitives]: PrimitiveFactory<Primitives[K], F>;
}> = C;
type PrimitiveFactories<F extends FlagStrings> = PrimitiveFactoriesEnsurer<F, {
    /**
     * Creates a number property descriptor, known to GObject as an int32, for use with `from` and `GClass`.
     * The largest possible range for this property is that of a signed 32-bit integer, but this can be reduced with the `min` and `max` config options.
     *
     * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
     * `"computed"` properties cannot accept a default, `const` properties require a default.
     * @param config Extra configuration options. `computed` properties cannot accept a config.
     * @param config.min Minimum allowed value. Defaults to `MIN_INT32`
     * @param config.max Maximum allowed value. Defaults to `MAX_INT32`
     */
    int32: PrimitiveFactory<number, F>;
    /**
     * Creates a number property descriptor, known to GObject as a uint32, for use with `from` and `GClass`.
     * The largest possible range for this property is that of an unsigned 32-bit integer, but this can be reduced with the `min` and `max` config options.
     *
     * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
     * `"computed"` properties cannot accept a default, `const` properties require a default.
     * @param config Extra configuration options. `computed` properties cannot accept a config.
     * @param config.min Minimum allowed value. Defaults to `0`
     * @param config.max Maximum allowed value. Defaults to `MAX_UINT32`
     */
    uint32: PrimitiveFactory<number, F>;
    /**
     * Creates a number property descriptor, known to GObject as a double, for use with `from` and `GClass`.
     * The largest possible range for this property is that of a double precision float (the same as JS number), but this can be reduced with the `min` and `max` config options.
     *
     * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
     * `"computed"` properties cannot accept a default, `const` properties require a default.
     * @param config Extra configuration options. `computed` properties cannot accept a config.
     * @param config.min Minimum allowed value. Defaults to `-Number.MAX_VALUE`
     * @param config.max Maximum allowed value. Defaults to `Number.MAX_VALUE`
     */
    double: PrimitiveFactory<number, F>;
    /**
     * Creates a string property descriptor for use with `from` and `GClass`.
     *
     * @param default_value The default value to give to the property. Defaults to `""` (an empty string).
     * `computed` properties cannot accept a default, `const` properties require a default.
     */
    string: PrimitiveFactory<string, F>;
    /**
     * Creates a boolean property descriptor for use with `from` and `GClass`.
     *
     * @param default_value The default value to give to the property. Defaults to `false`.
     * `computed` properties cannot accept a default, `const` properties require a default.
     */
    bool: PrimitiveFactory<boolean, F>;
}> & {
    /**
     * Creates a GObject Enum property descriptor for use with `from` and `GClass`.
     *
     * @param kind The GObject Enum class that this property will be typed to
     * @param default_value The default value given to the property. It is required, because Enums do not have a reliable 0-value
     *
     * GEnum properties cannot be `computed`
     */
    genum<T extends number, E extends GEnum<T>>(genum: E, default_member: keyof E): E extends GEnum<infer I> ? PropDescriptor<I, F> : never;
};
type ObjectFactories<F extends FlagStrings> = {
    /**
     * Creates a GObject.Object property descriptor for use with `from` and `GClass`.
     *
     * All GObject.Object properties are also nullable, because GObject cannot ensure that a null value isn't set.
     * The default value for GObject.Object properties is always null, and cannot be changed.
     *
     * @param kind The GObject class that this property will be typed to
     */
    gobject<G extends GClass$1>(kind: G): PropDescriptor<InstanceType<G> | null, F> & {
        /**
         * Type helper to allow narrowing of a property descriptor's type.
         * A default value is required to exist, and the default value must extend the narrowed value.
         *
         * @template Narrow The narrowed type
         *
         * @example
         * ```ts
         * Property.rw.gobject(Gtk.Widget).as<Gtk.ListBox | Gtk.Box>() // This property now only allows instances of Box or ListBox, instead of all widgets
         * ```
         */
        as<Narrow extends InstanceType<G>>(): PropDescriptor<Narrow | null, F>;
    };
    /**
     * Creates a JavaScript Object property descriptor for use with `from` and `GClass`.
     *
     * All JS object properties are also nullable, because GObject cannot ensure that a null value isn't set.
     * The default value for JS object properties is always null, and cannot be changed.
     */
    jsobject(): PropDescriptor<object | null, F> & {
        /**
         * Type helper to allow narrowing of a property descriptor's type.
         * A default value is required to exist, and the default value must extend the narrowed value.
         *
         * @template Narrow The narrowed type
         *
         * @example
         * ```ts
         * Property.jsobject().as<TypeOne | TypeTwo>() // This property now only allows instances of TypeOne or TypeTwo, instead of all objects
         * ```
         */
        as<Narrow extends object>(): PropDescriptor<Narrow | null, F>;
    };
};
/**
 * Create properties for use with `from` and `GClass`.
 *
 * Properties are the main way to have reactive state stored in a GObject subclass.
 *
 * The following modifiers determine if and when properties can be written to, and how they may be written.
 */
declare const Property: {
    /**
     * Properties of this modifier are writeable at all times.
     */
    readwrite: {
        /**
         * Creates a number property descriptor, known to GObject as an int32, for use with `from` and `GClass`.
         * The largest possible range for this property is that of a signed 32-bit integer, but this can be reduced with the `min` and `max` config options.
         *
         * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
         * `"computed"` properties cannot accept a default, `const` properties require a default.
         * @param config Extra configuration options. `computed` properties cannot accept a config.
         * @param config.min Minimum allowed value. Defaults to `MIN_INT32`
         * @param config.max Maximum allowed value. Defaults to `MAX_INT32`
         */
        int32: PrimitiveFactory<number, "readwrite">;
        /**
         * Creates a number property descriptor, known to GObject as a uint32, for use with `from` and `GClass`.
         * The largest possible range for this property is that of an unsigned 32-bit integer, but this can be reduced with the `min` and `max` config options.
         *
         * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
         * `"computed"` properties cannot accept a default, `const` properties require a default.
         * @param config Extra configuration options. `computed` properties cannot accept a config.
         * @param config.min Minimum allowed value. Defaults to `0`
         * @param config.max Maximum allowed value. Defaults to `MAX_UINT32`
         */
        uint32: PrimitiveFactory<number, "readwrite">;
        /**
         * Creates a number property descriptor, known to GObject as a double, for use with `from` and `GClass`.
         * The largest possible range for this property is that of a double precision float (the same as JS number), but this can be reduced with the `min` and `max` config options.
         *
         * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
         * `"computed"` properties cannot accept a default, `const` properties require a default.
         * @param config Extra configuration options. `computed` properties cannot accept a config.
         * @param config.min Minimum allowed value. Defaults to `-Number.MAX_VALUE`
         * @param config.max Maximum allowed value. Defaults to `Number.MAX_VALUE`
         */
        double: PrimitiveFactory<number, "readwrite">;
        /**
         * Creates a string property descriptor for use with `from` and `GClass`.
         *
         * @param default_value The default value to give to the property. Defaults to `""` (an empty string).
         * `computed` properties cannot accept a default, `const` properties require a default.
         */
        string: PrimitiveFactory<string, "readwrite">;
        /**
         * Creates a boolean property descriptor for use with `from` and `GClass`.
         *
         * @param default_value The default value to give to the property. Defaults to `false`.
         * `computed` properties cannot accept a default, `const` properties require a default.
         */
        bool: PrimitiveFactory<boolean, "readwrite">;
    } & {
        /**
         * Creates a GObject Enum property descriptor for use with `from` and `GClass`.
         *
         * @param kind The GObject Enum class that this property will be typed to
         * @param default_value The default value given to the property. It is required, because Enums do not have a reliable 0-value
         *
         * GEnum properties cannot be `computed`
         */
        genum<T extends number, E extends GEnum<T>>(genum: E, default_member: keyof E): E extends GEnum<infer I extends number> ? PropDescriptor<I, "readwrite"> : never;
    } & ObjectFactories<"readwrite">;
    /**
     * Properties of this modifier are writeable during construction (via `super()` and `new`)
     * but cannot be written at any point post-construction
     */
    readonly: {
        /**
         * Creates a number property descriptor, known to GObject as an int32, for use with `from` and `GClass`.
         * The largest possible range for this property is that of a signed 32-bit integer, but this can be reduced with the `min` and `max` config options.
         *
         * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
         * `"computed"` properties cannot accept a default, `const` properties require a default.
         * @param config Extra configuration options. `computed` properties cannot accept a config.
         * @param config.min Minimum allowed value. Defaults to `MIN_INT32`
         * @param config.max Maximum allowed value. Defaults to `MAX_INT32`
         */
        int32: PrimitiveFactory<number, "readonly">;
        /**
         * Creates a number property descriptor, known to GObject as a uint32, for use with `from` and `GClass`.
         * The largest possible range for this property is that of an unsigned 32-bit integer, but this can be reduced with the `min` and `max` config options.
         *
         * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
         * `"computed"` properties cannot accept a default, `const` properties require a default.
         * @param config Extra configuration options. `computed` properties cannot accept a config.
         * @param config.min Minimum allowed value. Defaults to `0`
         * @param config.max Maximum allowed value. Defaults to `MAX_UINT32`
         */
        uint32: PrimitiveFactory<number, "readonly">;
        /**
         * Creates a number property descriptor, known to GObject as a double, for use with `from` and `GClass`.
         * The largest possible range for this property is that of a double precision float (the same as JS number), but this can be reduced with the `min` and `max` config options.
         *
         * @param default_value The default value to give to the property. Defaults to `0` or `min` if `0` is out of range.
         * `"computed"` properties cannot accept a default, `const` properties require a default.
         * @param config Extra configuration options. `computed` properties cannot accept a config.
         * @param config.min Minimum allowed value. Defaults to `-Number.MAX_VALUE`
         * @param config.max Maximum allowed value. Defaults to `Number.MAX_VALUE`
         */
        double: PrimitiveFactory<number, "readonly">;
        /**
         * Creates a string property descriptor for use with `from` and `GClass`.
         *
         * @param default_value The default value to give to the property. Defaults to `""` (an empty string).
         * `computed` properties cannot accept a default, `const` properties require a default.
         */
        string: PrimitiveFactory<string, "readonly">;
        /**
         * Creates a boolean property descriptor for use with `from` and `GClass`.
         *
         * @param default_value The default value to give to the property. Defaults to `false`.
         * `computed` properties cannot accept a default, `const` properties require a default.
         */
        bool: PrimitiveFactory<boolean, "readonly">;
    } & {
        /**
         * Creates a GObject Enum property descriptor for use with `from` and `GClass`.
         *
         * @param kind The GObject Enum class that this property will be typed to
         * @param default_value The default value given to the property. It is required, because Enums do not have a reliable 0-value
         *
         * GEnum properties cannot be `computed`
         */
        genum<T extends number, E extends GEnum<T>>(genum: E, default_member: keyof E): E extends GEnum<infer I extends number> ? PropDescriptor<I, "readonly"> : never;
    } & ObjectFactories<"readonly">;
    /**
     * Properties of this modifier are writeable at all times post-construction,
     * but are not allowed to be written to during construction (via `super()` or `new`).
     *
     * Computed properties require a `get` and `set` method to be present on the subclass,
     * and use those to read and write values. Early-reads that may happen before construction finishes
     * will see the fallback value of the property type (0, "", false, null).
     *
     * Computed properties do not support specifying default values, and GEnums cannot be computed.
     */
    computed: Omit<PrimitiveFactories<"computed">, "genum"> & ObjectFactories<"computed">;
    /**
     * Properties of this modifier may not be written to at all, and require default values to be set.
     * GObject and JSObject properties do not support being const, as they would always be null, forever.
     */
    const: PrimitiveFactories<"const">;
};

declare const SIGNAL_SYMBOL: unique symbol;
type SignalArgument = (GObject.GType | {
    $gtype: GObject.GType;
} | (abstract new (...args: any[]) => any));
type RegisterableSignal = {
    flags: GObject.SignalFlags | undefined;
    param_types: GObject.GType[];
    return_type: GObject.GType | undefined;
    accumulator: GObject.AccumulatorType | undefined;
};
type SignalDescriptor<A extends SignalArgument[], R extends SignalArgument | void> = {
    param_types?: A;
    return_type?: R;
    flags?: GObject.SignalFlags;
    accumulator?: GObject.AccumulatorType;
    signal_symbol: typeof SIGNAL_SYMBOL;
    create(): RegisterableSignal;
};
type UnderscoreToHyphen<S> = S extends `${infer Head}_${infer Tail}` ? `${Head}-${UnderscoreToHyphen<Tail>}` : S;
type ExtractSignals<D> = {
    [Key in keyof D as D[Key] extends SignalDescriptor<any, any> ? UnderscoreToHyphen<Key> : never]: D[Key] extends SignalDescriptor<any, any> ? D[Key] : never;
};
type UnwrapSignalArg<T> = (T extends GObject.GType<infer G> ? UnwrapSignalArg<G> : T extends ObjectConstructor ? object | null : T extends NumberConstructor ? number : T extends StringConstructor ? string : T extends BooleanConstructor ? boolean : T extends abstract new (...args: any[]) => infer O ? O | null : T);
type UnwrapSignalArgs<T extends readonly unknown[]> = {
    [K in keyof T]: UnwrapSignalArg<T[K]>;
};
type SignalsOf<T extends GObject.Object> = {
    [K in keyof T["$signals"]]: T["$signals"][K];
};
type SignalOverrides<T extends GObject.Object, D> = {
    $connect<const Self extends GObject.Object, S extends keyof ExtractSignals<D> | keyof SignalsOf<T>>(signal_name: S, callback: SignalsOf<T>[S] extends (...args: infer Args) => infer Ret ? (self: Self, ...args: Args) => Ret : S extends keyof ExtractSignals<D> ? ExtractSignals<D>[S] extends SignalDescriptor<infer Args, infer Ret> ? (self: Self, ...args: UnwrapSignalArgs<Args>) => UnwrapSignalArg<Ret> : never : never): number;
    $connect_after<const Self extends GObject.Object, S extends keyof ExtractSignals<D> | keyof SignalsOf<T>>(signal_name: S, callback: SignalsOf<T>[S] extends (...args: infer Args) => infer Ret ? (self: Self, ...args: Args) => Ret : S extends keyof ExtractSignals<D> ? ExtractSignals<D>[S] extends SignalDescriptor<infer Args, infer Ret> ? (self: Self, ...args: UnwrapSignalArgs<Args>) => UnwrapSignalArg<Ret> : never : never): number;
    $emit<S extends keyof ExtractSignals<D> | keyof SignalsOf<T>>(signal_name: S, ...args: SignalsOf<T>[S] extends (...args: infer Args) => any ? Args : S extends keyof ExtractSignals<D> ? ExtractSignals<D>[S] extends SignalDescriptor<infer Args, any> ? UnwrapSignalArgs<Args> : never : never): void;
    /**
     * Connects to a GObject signal and returns a Promise that resolves the first time the signal is emitted.
     *
     * This function is an async wrapper for GObject signals, allowing you
     * to `await` the emission of a signal instead of using callbacks.
     * Optionally, you can provide a `reject_signal` that will reject the promise if that signal is emitted first.
     *
     * The connected signal handlers are automatically disconnected once the promise
     * resolves or rejects, preventing memory leaks or duplicate connections.
     *
     * @param resolve_signal The signal name whose emission will resolve the promise.
     * @param reject_signal Optional signal name whose emission will reject the promise.
     * @returns A promise that resolves with the arguments emitted by `resolve_signal`.
     *
     * @remarks
     * Only signals with a `void` return type can be awaited. Signals that return
     * a value cannot be used with `$connect_async`, as the return value is
     * provided by the handler rather than the emission. Use `$connect` directly
     * for non-void signals.
     *
     * @example
     * ```ts
     * // Wait for a Gtk.Button to be clicked once
     * const button = new Gtk.Button({ label: "Click me" })
     * await button.$connect_async("clicked")
     * print("Button clicked!")
     * ```
     *
     * @example
     * ```ts
     * // Handle a signal that could fail
     * try {
     *     const [result] = await obj.$connect_async("success-signal", "error-signal")
     *     print(`Success: ${result}`)
     * } catch (err) {
     *     print(`Error signal triggered: ${err.message}`)
     * }
     * ```
     */
    $connect_async<S extends keyof ExtractSignals<D> | keyof SignalsOf<T>>(resolve_signal: S, reject_signal?: keyof ExtractSignals<D> | keyof SignalsOf<T>): SignalsOf<T>[S] extends (...args: infer Args) => void ? Promise<Args> : S extends keyof ExtractSignals<D> ? ExtractSignals<D>[S] extends SignalDescriptor<infer Args, void> ? Promise<UnwrapSignalArgs<Args>> : never : never;
    $signals: {
        [Key in keyof ExtractSignals<D>]: ExtractSignals<D>[Key] extends SignalDescriptor<infer Args, infer Ret> ? (...args: UnwrapSignalArgs<Args>) => (Ret extends void ? void : UnwrapSignalArg<Ret>) : never;
    };
};
/**
 * Creates a Signal descriptor for use with `from` and `GClass`.
 *
 * `from` and `GClass` will register the signals on the subclass, allowing them to be connected and emitted.
 *
 * Note: any signals with underscores ('_') in their names will be remapped to hyphens ('-'). Example: `"user_added"` -> `"user-added"`.
 * Use these remapped names when connecting and emitting the signals.
 *
 * Tip: GObjectify's provided `$connect`, `$connect_after`, `$connect_async`, and `$emit` methods are type-aware,
 * and will give auto-complete suggestions for these signals, as well as ensure arguments and returned values match the declared types.
 *
 * @param parameters The types of values that must be emitted, and that will be passed to connected functions.
 * Allows for the following:
 * - `Number` (maps to GObject.TYPE_DOUBLE)
 * - `String` (maps to GObject.TYPE_STRING)
 * - `Boolean` (maps to GObject.TYPE_BOOLEAN)
 * - Any GObject.TYPE_*
 * - Any GObject subclass
 * - Any GObject enum
 * @param options Advanced signal configuration options. Refer to GObject Signal documentation for more information
 *
 * @example
 * ```ts
 * @GClass()
 * export class Example extends from(Gtk.Button, {
 *     user_added: Signal([String]),
 * }) {
 *     do_example(): void {
 *         this.$emit("user-added", "John Doe")
 *     }
 * }
 * ```
 */
declare const Signal: <const A extends [] | SignalArgument[] = [], const R extends SignalArgument | void = void>(parameters?: A, options?: {
    return_type?: R;
    flags?: GObject.SignalFlags;
    accumulator?: GObject.AccumulatorType;
}) => ([] extends A ? void extends R ? SignalDescriptor<[], void> : SignalDescriptor<[], R> : void extends R ? SignalDescriptor<A, void> : SignalDescriptor<A, R>);

declare const ACTION_SYMBOL: unique symbol;
type ActionArgs = Omit<Partial<Gio.SimpleAction.ConstructorProps>, "name">;
type ActionDescriptor = {
    args: ActionArgs;
    accels: string[];
    action_symbol: typeof ACTION_SYMBOL;
};
type ExtractActions<D> = {
    readonly [Key in keyof D as D[Key] extends ActionDescriptor ? Key : never]: Gio.SimpleAction;
};
/**
 * Creates an **ActionDescriptor** for use with `from()` and `GClass`, describing a GioSimpleAction. This can only be
 * used if the resulting subclass is of a GtkApplication, GtkApplicationWindow, or a GtkWidget
 *
 * `from()` and `GClass` will see this descriptor and connect up the action to the instance on instantiation.
 *
 * @param params Optional parameters for the SimpleAction. See `new Gio.SimpleAction()` constructor parameters
 *
 * Note that `params.accels` is only used for classes extending Gtk.Application, it is ignored for all other base types.
 *
 * @example
 * ```ts
 * @GClass()
 * class MyBox extends from(Gtk.Box, {
 *     save_changes: SimpleAction({ accels: ["<Ctrl>S"] }),
 * }) {}
 * // MyBox instances now have a `save_changes` GioSimpleAction available
 * ```
 */
declare function SimpleAction(params?: ActionArgs & {
    accels?: string[];
}): ActionDescriptor;

/**
 * A fully type-safe, and compile-time const Map. Using a regular Map under the hood, ConstMap ensures that values
 * "gotten" from the map are always valid, because only valid, known keys are allowed to be passed
 */
declare class ConstMap<const Pairs extends [any, any][]> {
    #private;
    constructor(...pairs: Pairs);
    /**
     * Get the value from the map that corresponds to the key.
     *
     * This is similar to `Map.prototype.get`, but is fully typed as always returning a value, since it knows
     * what is and isn't allowed to be "gotten".
     *
     * @param key A key in the map. This value is typed as only ever allowing known values that are in the map.
     */
    get<K extends Pairs[number][0]>(key: K): Extract<Pairs[number], [K, any]>[1];
    /**
     * Get a value from the map that might correspond to the key.
     *
     * This is similar to `ConstMap.prototype.get`, but allows any type of key. The returned value is `undefined` if the
     * key is not present in the map.
     *
     * @param key
     */
    looseGet(key: any): Extract<Pairs[number], [any, any]>[1] | undefined;
    asMap(): ReadonlyMap<Pairs[number][0], Pairs[number][1]>;
    [Symbol.iterator](): IterableIterator<Pairs[number]>;
}

declare const no_override: unique symbol;
type Final<T> = T & typeof no_override;
type Finalize<D> = {
    [K in keyof D]: Final<D[K]>;
};
type Descriptor<D, T extends GObject.Object> = {
    [Key in keyof D as Key extends string ? Key : never]: Key extends keyof T ? never : (Key extends `_${string}` ? ChildDescriptor<GObject.Object> : Key extends keyof T["$signals"] ? PropDescriptor<any, any> : PropDescriptor<any, any> | SignalDescriptor<any[], any>) | (T extends Gtk.Application | Gtk.ApplicationWindow | Gtk.Widget ? ActionDescriptor : never);
};
type GClassFor<T extends GObject.Object> = new (...args: any[]) => T;
type AbstractGClassFor<T extends GObject.Object> = abstract new (...args: any[]) => T;
type ValidConstructorProps<D> = {
    [K in keyof ExtractConstructProps<D>]?: ExtractConstructProps<D>[K];
};
type ResultingConstructorParamsObj<T extends AbstractGClassFor<GObject.Object>, D extends Descriptor<D, InstanceType<T>>> = ConstructorParameters<T> extends [] ? [ValidConstructorProps<D>] : ConstructorParameters<T> extends [(infer First)?, ...infer Rest] ? undefined extends ConstructorParameters<T>[0] ? [(ValidConstructorProps<D> & First)?, ...Rest] : [(ValidConstructorProps<D> & First), ...Rest] : never;
type ResultingClass<T extends AbstractGClassFor<GObject.Object>, D extends Descriptor<D, InstanceType<T>>, I extends AbstractGClassFor<GObject.Object>[]> = {
    $gtype: GObject.GType<InstanceType<T> & {
        readonly $unique: unique symbol;
    }>;
    $params: ResultingConstructorParamsObj<T, D>[0];
} & (abstract new (...args: ResultingConstructorParamsObj<T, D>) => (SignalOverrides<InstanceType<T>, D> & InstanceType<T> & ExtractWriteableProps<D> & ExtractReadonlyProps<D> & Finalize<ExtractChildren<D>> & Finalize<ExtractActions<D>> & Finalize<{
    with_implements: I extends [] ? never : Instances<I>;
}>));
type ClassDecoratorParams = {
    template?: Uint8Array | GLib.Bytes | string;
    css_name?: string;
    gtype_flags?: GObject.TypeFlags;
    manual_gtype_name?: string;
    manual_properties?: Record<string, GObject.ParamSpec>;
    manual_internal_children?: string[];
};
type WatchPropKeys<T extends GObject.Object> = {
    [Key in keyof T]: Key extends string ? Key extends `_${string}` ? never : Key extends "with_implements" | "$signals" ? never : T[Key] extends Function ? never : Key : never;
}[keyof T];
type Instances<I extends (abstract new (...args: any) => any)[]> = I extends [infer First, ...infer Rest] ? First extends abstract new (...args: any) => any ? Rest extends (abstract new (...args: any) => any)[] ? InstanceType<First> & Instances<Rest> : InstanceType<First> : never : unknown;
/**
 * Used in tandem with `GClass`, this function creates an abstract base class used to declare
 * GObject properties, GioSimpleActions, and internal template children.
 * This function provides a strongly typed way of adding common GObject items to your extended classes via the
 * descriptor object passed in. Children, properties, and actions defined in here will be picked up by the `GClass`
 * decorator **for use in a subclass**.
 *
 * See Child, Property, Signal, and Action for info on defining members for the descriptor and your resulting subclass.
 *
 * This function does **not** make a usable class on its own! Do **not** create instances from the returned class.
 *
 * @param extend The GObject class being extended
 * @param descriptor The descriptor map describing GObject properties, internal children, and simple actions.
 * - The returned class will contain members defined in the descriptor.
 * - The descriptor may only contain definitions of these three GObject members, and also requires their names be
 * correct. Children's names must start with an underscore, `_`, and properties' names cannot.
 * - The `GClass` decorator is responsible for noticing these members and applying them to the final class.
 * - The descriptor may be empty, but in that case you can just extend the base GObject class directly.
 * @param implement A rest parameter for the list of GObject interfaces the subclass implements.
 * - With `this.with_implements`, you can access the subclass as the type of these interfaces.
 * - If no interfaces are provided, `with_implements` becomes type `never`.
 *
 * @remarks
 * The returned class will not function as expected on its own. **Always use `from` with a subclass and with the
 * `GClass` decorator**.
 *
 * The returned class exposes a static `$params` field purely for constructor type information. It has no runtime value.
 * It is purely useful for when overriding the constructor, to ensure you have all of the parameter type information.
 * You would use it via: `constructor(params: typeof MyClassName.$params) { super(params) }`
 */
declare function from<T extends abstract new (...args: any[]) => GObject.Object, D extends Descriptor<D, InstanceType<T>>, I extends (AbstractGClassFor<GObject.Object> & {
    $gtype: GObject.GType;
})[]>(extend: T, descriptor: D, ...implement: I): ResultingClass<T, D, I>;
/**
 * Class decorator to define a GObject/Gtk class with properties, children, actions, and signals.
 *
 * It wraps a standard GObject derived class and automatically handles:
 * - Sets the class name as the GType name (can be overridden with `options.manual_gtype_name`)
 * - Registering signals declared via the `Signal` decorator
 * - Registering an optional UI template file, custom CSS name, GType Flags, or interface implementations
 * - Registers and inits GObject properties provided by the `from` base and/or from `manual_properties`
 * - Registers internal children provided by the `from` base and/or from `manual_internal_children`
 * - Registers and hooks up GioSimpleActions provided by the `from` base
 *
 * This decorator allows a declarative approach to extending GObject classes, without having to manually call
 * `GObject.registerClass`, or manage signal/action setup.
 *
 * @template T - The base GObject class to extend.
 * @param options Optional configurations for the class.
 * @param options.template GTK template resource to use.
 * @param options.implements Interfaces to implement.
 * @param options.css_name CSS node name for GTK styling.
 * @param options.gtype_flags Flags for GType registration.
 * @param options.manual_gtype_name Provide a manual GType name instead of using the class name.
 * @param options.manual_properties Additional properties to register not provided by the `from` base.
 * @param options.manual_internal_children Additional internal child names not provided by the 'from' base.
 *
 * @example
 * ```ts
 * @GClass({ css_name: "my-widget", template: "resource:///org/my/app/ui/my_widget.ui" })
 * class MyWidget extends from(Gtk.Box, {
 *     title: Property.string({ default: "My Awesome Widget" }),
 * }) {
 *     constructor(params: typeof MyWidget.$params) {
 *         super(params)
 *         print(`${this.title} is created!`)
 *     }
 * }
 * ```
 *
 * @remarks
 * All properties defined with GObjectify's Property are marked as `CONSTRUCT` properties,
 * so they are guaranteed to be set after `super()` is finished in the constructor.
 */
declare function GClass<T extends GObject.Object>(options?: ClassDecoratorParams): (target: GClassFor<T>, _context: ClassDecoratorContext) => void;
/**
 * Decorator factory that debounces a method.
 *
 * When applied to a class method, `Debounce(milliseconds, options)` ensures
 * that the method is not called more frequently than the specified interval.
 *
 * You can control whether the method is called on the leading edge, trailing edge, or both.
 *
 * This is useful in GTK/GJS applications for handling rapid events
 * like `notify` or `changed` without flooding your logic.
 *
 * @template T The class type containing the method.
 * @template U The type of the method being debounced.
 * @param milliseconds The debounce interval in milliseconds.
 * @param params Options to control when the method is triggered.
 * - { trigger: "leading" }: will call the function immediately, and then not call it again within the interval
 * - { trigger: "trailing" } (default): will wait to call the function until after the interval has passed
 * - { trigger: "leading+trailing" }:
 * will call the function immediately, and call it once more after the interval has passed
 */
declare function Debounce<T extends GObject.Object, U extends (this: T, ...args: any[]) => void>(milliseconds: number, params?: {
    trigger: "leading" | "trailing" | "leading+trailing";
}): (original_method: U, context: ClassMethodDecoratorContext) => U;
/**
 * Decorator for a setter method that automatically calls `this.notify`
 * for the corresponding GObject property after the setter runs.
 *
 * This ensures that GObject bindings or signals depending on the property
 * are correctly updated when the value changes. The property name used
 * in `notify` is the decorated setter's name with underscores replaced by hyphens,
 * which matches the typical GObject property naming convention.
 *
 * @template T The class type containing the property.
 * @template U The type of value being set.
 * @param target The original setter method.
 * @param context The decorator context.
 * @returns A wrapped setter that calls `this.notify()`.
 *
 * @example
 * ```ts
 * class MyWidget extends from(Gtk.Box, {
 *     count_value: Property.double({ flags: "computed" }),
 * }) {
 *     #count = 0
 *
 *     override get count_value(): number {
 *         return this.#count
 *     }
 *
 *     @Notify
 *     override set count_value(val: number) {
 *         print(`Setting count_value to ${val}`)
 *         this.#count = val
 *     }
 * }
 *
 * const widget = new MyWidget();
 * widget.count_value = 42; // Automatically calls widget.notify("count-value")
 * ```
 */
declare function Notify<T extends GObject.Object, U>(target: (this: T, arg0: U) => void, context: ClassSetterDecoratorContext<T>): (this: T, arg0: U) => void;
/**
 * Decorator that connects a method to a GObject signal emission.
 *
 * When applied to a class method, `OnSignal(signal_name)` ensures that the method
 * is automatically connected to the given signal_name on each instance. The decorated
 * method is bound to the instance, so `this` always refers to the object emitting
 * the signal_name.
 *
 * This is useful for GTK/GObject classes where you want to handle signals
 * declaratively without manually calling `connect`.
 *
 * @param signal_name The name of the GObject signal to connect to.
 * @returns A decorator for instance methods.
 *
 * @example
 * ```ts
 * class MyButton extends Gtk.Button {
 *     @OnSignal("clicked")
 *     handle_click() {
 *         print("I have been clicked!")
 *     }
 * }
 * ```
 *
 * @remarks
 * handle_click is automatically called when "clicked" is emitted
 */
declare function OnSignal<T extends GObject.Object, S extends keyof SignalsOf<T>>(signal_name: S): (target: (this: T, ...args: SignalsOf<T>[S] extends (...args: infer Args) => any ? Args : never) => SignalsOf<T>[S] extends (...args: any) => infer Ret ? Ret : never, context: ClassMethodDecoratorContext<T>) => void;
/**
 * Decorator that connects a method to a Gio simple action's event signal.
 *
 * This decorator expects a string for the name of the action, but this string is limited to action fields defined on
 * the instance type in the method's class. See `from` for info on how to easily add Simple Actions to
 * GObject subclasses.
 *
 * @param action_name - Name of the field containing a GioSimpleAction to connect to.
 */
declare function OnSimpleAction<T extends GObject.Object, K extends {
    [Key in keyof T]: Key extends "with_implements" ? never : T[Key] extends Gio.SimpleAction ? Key : never;
}[keyof T], U extends (((this: T) => any) | ((this: T, action: Gio.SimpleAction) => any) | ((this: T, action: Gio.SimpleAction, value: GLib.Variant) => any))>(action_name: K): (target: U, context: ClassMethodDecoratorContext<T>) => void;
/**
 * Decorator that connects a method to one or more GObject property change notifications.
 *
 * When applied to a class method, the method will be called asynchronously on idle after class initialization,
 * and then automatically connected to the `notify::prop-name` signal for the specified property,
 * which will cause the function to be ran whenever the property's value changes.
 *
 * Multiple `@WatchProp` decorators can be stacked on a single method to watch several properties,
 * however this will call the function multiple times on idle after initialization.
 *
 * @param prop_name The snake_case name of the GObject property to watch.
 *
 * @example
 * ```ts
 * @GClass()
 * class MyButton extends from(Gtk.Box, {
 *     header_title: Property.string(),
 * }) {
 *     @WatchProp("header_title")
 *     #on_header_title_changed(): void {
 *         print("title is:", this.header_title)
 *     }
 * }
 * ```
 *
 * @remarks
 * The property name is automatically converted from snake_case to kebab-case
 * when connecting to the notify signal, so you don't need to think about the
 * distinction. Property names must be valid, registered GObject properties.
 * Plain JavaScript fields are *not valid* and will *cause errors*.
 */
declare function WatchProp<T extends GObject.Object, K extends WatchPropKeys<T>>(prop_name: K): (target: (this: T) => any, context: ClassMethodDecoratorContext<T>) => void;
/**
 * Decorator for a method that will be called on the next GLib idle iteration after the class has been instantiated.
 *
 * The method will be called via GLib.idle_add, which will ensure it waits for an idle cycle after the class
 * has been constructed. Properties, template children, and class members will all be available when its called.
 *
 * @template T The class type containing the property.
 * @template U The type of value being set.
 * @param target The original setter method.
 * @param context The decorator context.
 *
 * @example
 * ```ts
 * class MyWidget extends Gtk.Box {
 *     @PostInit
 *     setup(): void {
 *         print("MyWidget has been constructed, and an idle cycle has happened!")
 *     }
 * }
 * ```
 */
declare function PostInit<T extends GObject.Object>(target: (this: T) => any, context: ClassMethodDecoratorContext<T>): void;
/**
 * Schedules a callback to run on the next GLib idle iteration.
 *
 * This function returns a promise that resolves when the GLib main loop reaches the next idle cycle.
 *
 * @returns A promise that resolves on the next GLib idle iteration.
 *
 * @example
 * ```
 * await next_idle()
 * print("Runs at the next idle cycle!")
 * ```
 */
declare function next_idle(): Promise<void>;
/**
 * Wait for a specified duration in milliseconds.
 *
 * Returns a Promise that resolves after the given timeout. Internally,
 * it uses `GLib.timeout_add`, making it safe to use within GTK/GJS
 * main loop contexts without blocking the UI.
 *
 * @param duration The timeout duration in milliseconds
 * @returns A promise that resolves after the timeout.
 *
 * @example
 * ```ts
 * await timeout_ms(500)
 * print("It has been 500 milliseconds!")
 * ```
 */
declare function timeout_ms(duration: number): Promise<void>;
/**
 * Removes common leading indentation from a template string. Allowing for multi-line strings that don't have improper
 * indentation from source code.
 *
 * @param strings The literal portions of the template string.
 * @param values Interpolated values. Each value is concatenated with the corresponding
 * string segment using JavaScript's standard string coercion.
 *
 * @returns The dedented string with leading/trailing blank lines removed and common indentation stripped.
 *
 * This function is meant to be used as a template-tag:
 * @example
 * ```ts
 * const text = dedent`
 *     Hello,
 *         this line is indented relative to the block.
 *     Goodbye!
 * `
 * // Becomes:
 * // "Hello
 * //     this line is indented relative to the block.
 * // Goodbye!"
 * ```
 */
declare function dedent(strings: TemplateStringsArray, ...values: any[]): string;
declare module "gi://GObject?version=2.0" {
    namespace GObject {
        interface Object {
            $connect<const Self extends GObject.Object, S extends keyof Self["$signals"]>(this: Self, signal_name: S, callback: Self["$signals"][S] extends (...args: infer Args) => infer Ret ? (self: Self, ...args: Args) => Ret : never): number;
            $connect_after<const Self extends GObject.Object, S extends keyof Self["$signals"]>(this: Self, signal_name: S, callback: Self["$signals"][S] extends (...args: infer Args) => infer Ret ? (self: Self, ...args: Args) => Ret : never): number;
            $emit<const Self extends GObject.Object, S extends keyof Self["$signals"]>(this: Self, signal_name: S, ...args: Self["$signals"][S] extends (...args: infer Args) => any ? Args : never): void;
            /**
             * Connects to a GObject signal and returns a Promise that resolves the first time the signal is emitted.
             *
             * This function is an async wrapper for GObject signals, allowing you
             * to `await` the emission of a signal instead of using callbacks.
             * Optionally, you can provide a `reject_signal` that will reject the promise if that signal is emitted first.
             *
             * The connected signal handlers are automatically disconnected once the promise
             * resolves or rejects, preventing memory leaks or duplicate connections.
             *
             * @param resolve_signal The signal name whose emission will resolve the promise.
             * @param reject_signal Optional signal name whose emission will reject the promise.
             * @returns A promise that resolves with the arguments emitted by `resolve_signal`.
             *
             * @remarks
             * Only signals with a `void` return type can be awaited. Signals that return
             * a value cannot be used with `$connect_async`, as the return value is
             * provided by the handler rather than the emission. Use `$connect` directly
             * for non-void signals.
             *
             * @example
             * ```ts
             * // Wait for a Gtk.Button to be clicked once
             * const button = new Gtk.Button({ label: "Click me" })
             * await button.$connect_async("clicked")
             * print("Button clicked!")
             * ```
             *
             * @example
             * ```ts
             * // Handle a signal that could fail
             * try {
             *     const [result] = await obj.$connect_async("success-signal", "error-signal")
             *     print(`Success: ${result}`)
             * } catch (err) {
             *     print(`Error signal triggered: ${err.message}`)
             * }
             * ```
             */
            $connect_async<const Self extends GObject.Object, S extends keyof Self["$signals"]>(this: Self, resolve_signal: S, reject_signal?: keyof Self["$signals"]): Self["$signals"][S] extends (...args: infer Args) => void ? Promise<Args> : never;
        }
    }
}

export { Child, ConstMap, Debounce, GClass, Notify, OnSignal, OnSimpleAction, PostInit, Property, Signal, SimpleAction, WatchProp, dedent, from, next_idle, timeout_ms };
