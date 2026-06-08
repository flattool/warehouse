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
import GObject from 'gi://GObject?version=2.0';
import Gio from 'gi://Gio?version=2.0';
import Gtk from 'gi://Gtk?version=4.0';
import GLib from 'gi://GLib?version=2.0';

const CHILD_SYMBOL = Symbol("Symbol for GObjectify Child descriptors");
function Child() {
    return { child_symbol: CHILD_SYMBOL };
}
function is_child_descriptor(item) {
    return item?.child_symbol === CHILD_SYMBOL;
}

class ConstMap {
    #map;
    constructor(...pairs) {
        this.#map = Object.freeze(new Map(pairs));
    }
    get(key) {
        return this.#map.get(key);
    }
    looseGet(key) {
        return this.#map.get(key);
    }
    asMap() {
        return this.#map;
    }
    *[Symbol.iterator]() {
        for (const pair of this.#map)
            yield pair;
    }
}

const PROPERTY_SYMBOL = Symbol("Symbol for GObjectify Property descriptors");
const FLAG_PRESETS = {
    readwrite: GObject.ParamFlags.CONSTRUCT | GObject.ParamFlags.READWRITE,
    readonly: GObject.ParamFlags.CONSTRUCT | GObject.ParamFlags.READWRITE,
    computed: GObject.ParamFlags.READWRITE,
    const: GObject.ParamFlags.READABLE,
};
const num_sizes_and_spec = new ConstMap(["int32", { min: GLib.MININT32, max: GLib.MAXINT32, spec: GObject.ParamSpec.int }], ["uint32", { min: 0, max: GLib.MAXUINT32, spec: GObject.ParamSpec.uint }], ["double", { min: -Number.MAX_VALUE, max: Number.MAX_VALUE, spec: GObject.ParamSpec.double }]);
function make_numeric_factory(kind, flag) {
    const { min: default_min, max: default_max, spec } = num_sizes_and_spec.get(kind);
    return (...args) => {
        const { min, max } = args[1] ?? { min: default_min, max: default_max };
        const default_value = args[0] ?? (0 >= min && 0 <= max ? 0 : min);
        if (default_value < min || default_value > max)
            throw new RangeError(`Default value '${default_value}' is out of range for property of type '${kind}' with min '${min}' and max '${max}'`);
        return {
            flag,
            property_symbol: PROPERTY_SYMBOL,
            min,
            max,
            create: (name) => spec(name, null, null, FLAG_PRESETS[flag], min, max, default_value),
            as() { return this; },
            validate_value: (value, _spec) => {
                value ??= default_value;
                if (value < min) {
                    value = min;
                }
                else if (value > max) {
                    value = max;
                }
                if (kind !== "double") {
                    value = Math.trunc(value);
                }
                return value;
            }
        };
    };
}
const make_primitive_factories = (flag) => ({
    uint32: make_numeric_factory("uint32", flag),
    int32: make_numeric_factory("int32", flag),
    double: make_numeric_factory("double", flag),
    string: (val) => {
        const default_value = val ?? "";
        return {
            flag,
            property_symbol: PROPERTY_SYMBOL,
            create: (name) => GObject.ParamSpec.string(name, null, null, FLAG_PRESETS[flag], default_value),
            as() { return this; },
            validate_value: (value, _spec) => value ?? default_value,
        };
    },
    bool: (val) => {
        const default_value = val ?? false;
        return {
            flag,
            property_symbol: PROPERTY_SYMBOL,
            create: (name) => GObject.ParamSpec.boolean(name, null, null, FLAG_PRESETS[flag], default_value),
            as() { return this; },
            validate_value: (value, _spec) => value ?? default_value,
        };
    },
    genum: (genum, default_member) => {
        const default_value = genum[default_member];
        return {
            flag,
            property_symbol: PROPERTY_SYMBOL,
            create: (name) => GObject.ParamSpec.enum(name, null, null, FLAG_PRESETS[flag], genum.$gtype, default_value),
            validate_value: (value, _spec) => value ?? default_value,
        };
    }
});
const make_object_factories = (flag) => ({
    gobject: (kind) => ({
        flag,
        property_symbol: PROPERTY_SYMBOL,
        create: (name) => GObject.ParamSpec.object(name, null, null, FLAG_PRESETS[flag], kind.$gtype),
        as() { return this; },
        validate_value: (value, _spec) => value ?? null,
    }),
    jsobject: () => ({
        flag,
        property_symbol: PROPERTY_SYMBOL,
        create: (name) => GObject.ParamSpec.jsobject(name, null, null, FLAG_PRESETS[flag]),
        as() { return this; },
        validate_value: (value, _spec) => value ?? null,
    }),
});
const make_factories = (flag) => (flag === "const"
    ? make_primitive_factories(flag)
    : { ...make_primitive_factories(flag), ...make_object_factories(flag) });
const Property = {
    readwrite: make_factories("readwrite"),
    readonly: make_factories("readonly"),
    computed: make_factories("computed"),
    const: make_factories("const"),
};
const is_property_descriptor = (item) => (item?.property_symbol === PROPERTY_SYMBOL);

const SIGNAL_SYMBOL = Symbol("Symbol for GObjectify Signal descriptors");
const signal_descriptor_args_to_gtypes = (item) => {
    if ("$gtype" in item)
        return item.$gtype;
    if (typeof item === "function")
        return GObject.TYPE_JSOBJECT;
    return item;
};
const Signal = (parameters, options) => ({
    ...(parameters && { param_types: parameters }),
    ...options,
    signal_symbol: SIGNAL_SYMBOL,
    create: () => ({
        param_types: parameters?.map(signal_descriptor_args_to_gtypes) ?? [],
        accumulator: options?.accumulator,
        flags: options?.flags,
        return_type: options?.return_type && signal_descriptor_args_to_gtypes(options.return_type),
    }),
});
function is_signal_descriptor(item) {
    return item?.signal_symbol === SIGNAL_SYMBOL;
}

const ACTION_SYMBOL = Symbol("Symbol for GObjectify SimpleAction descriptors");
function SimpleAction(params) {
    const { accels, ...args } = params ?? {};
    return {
        args,
        accels: accels ?? [],
        action_symbol: ACTION_SYMBOL,
    };
}
function is_action_descriptor(item) {
    return item?.action_symbol === ACTION_SYMBOL;
}

const GOBJECTIFY_FROM_SYMBOL = Symbol("GOBJECTIFY_FROM_SYMBOL");
const ACTION_GROUP_SYMBOL = Symbol("GObjectify_Action_Group_Symbol");
const INIT_FINISHED_SYMBOL = Symbol("GObjectify_GClass_Initialization_Finished_Symbol");
function is_base_metadata(item) {
    return item?.metadata_symbol === GOBJECTIFY_FROM_SYMBOL;
}
function from(extend, descriptor, ...implement) {
    class Base extends extend {
    }
    Base[GOBJECTIFY_FROM_SYMBOL] = {
        extend,
        metadata_symbol: GOBJECTIFY_FROM_SYMBOL,
        descriptor,
        implements: implement,
    };
    return Base;
}
const make_accessors = (class_name, prop_name, prop, desc, spec) => {
    let get;
    let set;
    if (prop.flag === "readonly") {
        get = function () {
            return prop.validate_value(desc.get.call(this), spec);
        };
        set = function (val) {
            if (this[INIT_FINISHED_SYMBOL]) {
                throw new Error(dedent `
					GClass: ${class_name}
					Readonly property '${prop_name}' cannot be set after initialization.
					}
				`);
            }
            desc.set.call(this, prop.validate_value(val, spec));
        };
    }
    else if (prop.flag === "computed") {
        get = function () {
            if (!this[INIT_FINISHED_SYMBOL]) {
                return prop.validate_value(spec.get_default_value(), spec);
            }
            return prop.validate_value(desc.get.call(this), spec);
        };
        set = function (val) {
            if (!this[INIT_FINISHED_SYMBOL]) {
                throw new Error(dedent `
					GClass: ${class_name}
					Computed property '${prop_name}' cannot be set during initialization.
				`);
            }
            desc.set.call(this, prop.validate_value(val, spec));
        };
    }
    else {
        get = function () {
            return prop.validate_value(desc.get.call(this), spec);
        };
        set = function (val) {
            desc.set.call(this, prop.validate_value(val, spec));
        };
    }
    return { get, set };
};
function GClass(options) {
    return function (target, _context) {
        const prototype = target.prototype;
        const parent = Object.getPrototypeOf(target);
        const maybe_metadata = parent?.[GOBJECTIFY_FROM_SYMBOL];
        const properties = {};
        const property_descriptors = {};
        const children = [];
        const actions = new Map();
        const signals = {};
        let implement = [];
        if (is_base_metadata(maybe_metadata)) {
            const real_base = maybe_metadata.extend.prototype;
            implement = maybe_metadata.implements;
            Object.defineProperty(prototype, "with_implements", {
                enumerable: true,
                configurable: false,
                get() {
                    return this;
                },
            });
            for (const [name, value] of Object.entries(maybe_metadata.descriptor)) {
                if (is_property_descriptor(value)) {
                    property_descriptors[name] = value;
                    const spec = value.create(name);
                    properties[name] = spec;
                    const is_flagged_computed = value.flag === "computed";
                    const has_get_or_set = (typeof (Object.getOwnPropertyDescriptor(prototype, name)?.get) === "function"
                        || typeof (Object.getOwnPropertyDescriptor(prototype, name)?.set) === "function");
                    if (is_flagged_computed && !has_get_or_set) {
                        throw new Error(dedent `
							GClass: ${target.name},
							"computed" flagged property '${name}' is missing a getter or a setter function.
						`);
                    }
                    if (!is_flagged_computed && has_get_or_set) {
                        throw new Error(dedent `
							GClass: ${target.name},
							Non-"computed" flagged property '${name}' has a getter or a setter function.
							To use a custom getter and setter, flag this property as "computed".
						`);
                    }
                    if ((spec.flags & GObject.ParamFlags.READABLE)
                        && !(spec.flags & GObject.ParamFlags.WRITABLE)) {
                        Object.defineProperty(prototype, name, {
                            enumerable: true,
                            configurable: false,
                            get() { return spec.get_default_value() ?? null; },
                        });
                    }
                }
                else if (is_child_descriptor(value)) {
                    children.push(name.replace("_", ""));
                }
                else if (is_action_descriptor(value)) {
                    actions.set(name, value);
                }
                else if (is_signal_descriptor(value)) {
                    signals[name.replaceAll("_", "-")] = value.create();
                }
            }
            Object.setPrototypeOf(prototype, real_base);
            Object.setPrototypeOf(target, maybe_metadata.extend);
        }
        for (const [name, spec] of Object.entries(options?.manual_properties ?? {})) {
            if (properties[name]) {
                throw new Error(`Manual property '${name}' in GClass decorated class '${target.name}' conflicts with a property of the same name defined in the 'from' base. Please rename one of them.`);
            }
            properties[name] = spec;
        }
        const original_init = prototype._init;
        prototype._init = function (...args) {
            const original_return_val = original_init?.apply?.(this, args);
            if (is_base_metadata(maybe_metadata) && actions.size > 0) {
                let action_addable;
                let accel_setter;
                if (this instanceof Gtk.ApplicationWindow) {
                    action_addable = this;
                }
                else if (this instanceof Gtk.Application) {
                    action_addable = this;
                    accel_setter = this.set_accels_for_action.bind(this);
                }
                else if (this instanceof Gtk.Widget) {
                    action_addable = (this[ACTION_GROUP_SYMBOL] ??= new Gio.SimpleActionGroup());
                    this.insert_action_group(target.name, action_addable);
                }
                if (action_addable !== undefined) {
                    for (const [name, value] of actions.entries()) {
                        const action = new Gio.SimpleAction({ name, ...value.args });
                        action_addable.add_action(action);
                        accel_setter?.(`app.${name}`, value.accels);
                        this[name] = action;
                    }
                }
            }
            this[INIT_FINISHED_SYMBOL] = true;
            return original_return_val;
        };
        GObject.registerClass({
            GTypeName: options?.manual_gtype_name || target.name,
            Implements: implement,
            Properties: properties,
            InternalChildren: options?.manual_internal_children?.concat(children) ?? children,
            Signals: signals,
            ...(options?.css_name && { CssName: options.css_name }),
            ...(options?.gtype_flags && { GTypeFlags: options.gtype_flags }),
            ...(options?.template && { Template: options.template }),
        }, target);
        for (const [key, spec] of Object.entries(properties)) {
            if (!(spec.flags & GObject.ParamFlags.WRITABLE)
                || spec.flags & GObject.ParamFlags.CONSTRUCT_ONLY)
                continue;
            const desc = Object.getOwnPropertyDescriptor(prototype, key);
            if (desc === undefined || typeof desc.get !== "function" || typeof desc.set !== "function") {
                throw new Error(dedent `
					GClass: ${target.name},
					Writeable custom GObject property '${key}' is missing a getter or a setter function.
				`);
            }
            const prop = property_descriptors[key];
            if (!prop)
                continue;
            const accessors = make_accessors(target.name, key, prop, desc, spec);
            Object.defineProperty(prototype, key, {
                configurable: desc.configurable ?? true,
                enumerable: desc.enumerable ?? true,
                ...accessors,
            });
        }
    };
}
function Debounce(milliseconds, params = { trigger: "trailing" }) {
    const leading = params.trigger.includes("leading");
    const trailing = params.trigger.includes("trailing");
    return (original_method, context) => {
        const timeout_symbol = Symbol(`DebounceDebouncerFor${context.name.toString()}`);
        const last_args_symbol = Symbol(`DebounceDebounceArgsFor${context.name.toString()}`);
        const should_call_trailing_symbol = Symbol(`DebounceShouldCallTrailingFor${context.name.toString()}`);
        const debounced = function (...args) {
            const has_scheduled = this[timeout_symbol] != null;
            if (leading && !has_scheduled) {
                original_method.apply(this, args);
            }
            else {
                this[last_args_symbol] = args;
                this[should_call_trailing_symbol] = true;
            }
            if (this[timeout_symbol]) {
                GLib.source_remove(this[timeout_symbol]);
            }
            this[timeout_symbol] = GLib.timeout_add(GLib.PRIORITY_DEFAULT, milliseconds, () => {
                this[timeout_symbol] = null;
                if (trailing && this[should_call_trailing_symbol]) {
                    original_method.apply(this, this[last_args_symbol] ?? []);
                    this[should_call_trailing_symbol] = false;
                }
                return GLib.SOURCE_REMOVE;
            });
        };
        return debounced;
    };
}
function Notify(target, context) {
    const field_name = String(context.name);
    const canonical_name = field_name.replaceAll("_", "-");
    return function (arg0) {
        target.call(this, arg0);
        this.notify(canonical_name);
    };
}
function OnSignal(signal_name) {
    return (target, context) => context.addInitializer(function () {
        this.connect(signal_name, target.bind(this));
    });
}
function OnSimpleAction(action_name) {
    return function (target, context) {
        context.addInitializer(function () {
            this[action_name].connect("activate", target.bind(this));
        });
    };
}
function WatchProp(prop_name) {
    const kebab = prop_name.replaceAll("_", "-");
    return (target, context) => {
        context.addInitializer(function () {
            this.connect(`notify::${kebab}`, target.bind(this));
            next_idle().then(() => target.call(this)).catch((e) => {
                print(`Error in @WatchProp method '${target.name}'`);
                print(e);
            });
        });
    };
}
const on_post_init_error = (method_name, class_name, e) => {
    print(`Error in @PostInit function '${method_name}' of '${class_name}':`);
    print(e);
};
function PostInit(target, context) {
    context.addInitializer(function () {
        next_idle().then(() => {
            try {
                const result = target.call(this);
                if (result instanceof Promise) {
                    result.catch((e) => on_post_init_error(target.name, this.constructor.name, e));
                }
            }
            catch (e) {
                on_post_init_error(target.name, this.constructor.name, e);
            }
        });
    });
}
async function next_idle() {
    return new Promise((resolve, _reject) => GLib.idle_add(GLib.PRIORITY_DEFAULT_IDLE, () => {
        resolve();
        return GLib.SOURCE_REMOVE;
    }));
}
async function timeout_ms(duration) {
    return new Promise((resolve, _reject) => {
        GLib.timeout_add(GLib.PRIORITY_DEFAULT_IDLE, duration, () => {
            resolve();
            return GLib.SOURCE_REMOVE;
        });
    });
}
function dedent(strings, ...values) {
    const full = strings.map((str, index) => str + (index < values.length ? values[index] : "")).join("");
    const lines = full.split("\n");
    while (lines.length && lines[0]?.trim() === "") {
        lines.shift();
    }
    while (lines.length && lines.at(-1)?.trim() === "") {
        lines.pop();
    }
    let mindent = Number.MAX_SAFE_INTEGER;
    for (const line of lines) {
        if (line.trim() === "")
            continue;
        const indent = line.search(/\S/);
        if (indent >= 0)
            mindent = Math.min(mindent, indent);
    }
    if (mindent === Number.MAX_SAFE_INTEGER)
        mindent = 0;
    return lines.map((line) => (line.trim() === "" ? line : line.slice(mindent))).join("\n");
}
GObject.Object.prototype.$connect = GObject.Object.prototype.connect;
GObject.Object.prototype.$connect_after = GObject.Object.prototype.connect_after;
GObject.Object.prototype.$emit = GObject.Object.prototype.emit;
GObject.Object.prototype.$connect_async = function (resolve_signal, reject_signal) {
    return new Promise((resolve, reject) => {
        let resolve_id;
        let reject_id;
        const cleanup = () => {
            if (resolve_id !== undefined)
                this.disconnect(resolve_id);
            if (reject_id !== undefined)
                this.disconnect(reject_id);
        };
        resolve_id = this.connect(resolve_signal, (_ob, ...args) => {
            cleanup();
            resolve(args);
        });
        if (!reject_signal)
            return;
        reject_id = this.connect(reject_signal, (_obj, ...args) => {
            cleanup();
            reject(new Error(`Rejection signal: '${String(reject_signal)}' triggered with args: ${args}`));
        });
    });
};

export { Child, ConstMap, Debounce, GClass, Notify, OnSignal, OnSimpleAction, PostInit, Property, Signal, SimpleAction, WatchProp, dedent, from, next_idle, timeout_ms };
