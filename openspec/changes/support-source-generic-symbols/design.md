# Design

## Behavior

The regex-based outline will accept an optional generic parameter block between a symbol name or arrow assignment and its parameter list:

- `function parse<T>(value: T) { ... }`
- `private createModel<T extends Base>(value: T) { ... }`
- `const load = <T>(value: T) => { ... }`
- `private makeModel = <T>(value: T) => { ... }`

Generic syntax is not interpreted. It is only recognized enough to identify the surrounding symbol range.

## Boundaries

Only `src/cr/source/outline.py` changes in behavior. Browser commands continue to call the same outline APIs.

## Validation

- Outline tests verify labels for generic methods, functions, and arrow functions.
- Browser tests verify `copy source symbol` copies a generic method range without adjacent methods.
