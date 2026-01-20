import { defineConfig } from "eslint/config"
import tsParser from "@typescript-eslint/parser"
import tsPlugin from "@typescript-eslint/eslint-plugin"
import stylistic from "@stylistic/eslint-plugin"
import eslintPluginJsonc from "eslint-plugin-jsonc"
import importPlugin from "eslint-plugin-import"

// Rules that apply to both JS and TS
const sharedJsTsRules = {
	"@stylistic/array-bracket-newline": ["error", { multiline: true }],
	"@stylistic/array-bracket-spacing": ["error", "never"],
	"@stylistic/array-element-newline": ["error", { consistent: true, multiline: true }],
	"@stylistic/arrow-parens": ["error", "always"],
	"@stylistic/arrow-spacing": ["error", { before: true, after: true }],
	"@stylistic/block-spacing": ["error", "always"],
	"@stylistic/brace-style": ["error", "1tbs", { allowSingleLine: true }],
	"@stylistic/comma-dangle": ["error", "always-multiline"],
	"@stylistic/comma-spacing": ["error", { before: false, after: true }],
	"@stylistic/comma-style": ["error", "last"],
	"@stylistic/computed-property-spacing": ["error", "never"],
	"@stylistic/dot-location": ["error", "property"],
	"@stylistic/eol-last": ["error", "always"],
	"@stylistic/function-call-argument-newline": ["error", "consistent"],
	"@stylistic/function-call-spacing": ["error", "never"],
	"@stylistic/function-paren-newline": ["error", "multiline-arguments"],
	"@stylistic/generator-star-spacing": "error",
	"@stylistic/implicit-arrow-linebreak": ["error", "beside"],
	"@stylistic/indent": ["error", "tab", { MemberExpression: 0, SwitchCase: 1 }],
	"@stylistic/indent-binary-ops": ["error", "tab"],
	"@stylistic/key-spacing": ["error", { beforeColon: false, afterColon: true, mode: "strict" }],
	"@stylistic/keyword-spacing": ["error", { before: true, after: true }],
	"@stylistic/linebreak-style": ["error", "unix"],
	"@stylistic/max-len": [
		"error",
		{
			code: 120,
			tabWidth: 4,
			ignoreComments: false,
			ignoreTrailingComments: false,
			ignoreUrls: false,
			ignoreStrings: false,
			ignoreTemplateLiterals: false,
			ignoreRegExpLiterals: true,
		},
	],
	"@stylistic/max-statements-per-line": ["error", { max: 1 }],
	"@stylistic/member-delimiter-style": [
		"error",
		{
			multiline: { delimiter: "comma", requireLast: true },
			singleline: { delimiter: "comma", requireLast: false },
			overrides: { interface: { multiline: { delimiter: "none" } } },
		},
	],
	"@stylistic/multiline-comment-style": ["error", "separate-lines"],
	"@stylistic/multiline-ternary": ["error", "always-multiline"],
	"@stylistic/new-parens": ["error", "always"],
	"@stylistic/no-confusing-arrow": ["error", { allowParens: true }],
	"@stylistic/no-extra-semi": "error",
	"@stylistic/no-floating-decimal": "error",
	"@stylistic/no-mixed-operators": "error",
	"@stylistic/no-mixed-spaces-and-tabs": "error",
	"@stylistic/no-multi-spaces": "error",
	"@stylistic/no-multiple-empty-lines": ["error", { max: 1, maxBOF: 0, maxEOF: 0 }],
	"@stylistic/no-trailing-spaces": "error",
	"@stylistic/no-whitespace-before-property": "error",
	"@stylistic/nonblock-statement-body-position": ["error", "beside"],
	"@stylistic/object-curly-newline": ["error", { multiline: true, consistent: true }],
	"@stylistic/object-curly-spacing": ["error", "always"],
	"@stylistic/object-property-newline": ["error", { allowAllPropertiesOnSameLine: true }],
	"@stylistic/operator-linebreak": ["error", "before"],
	"@stylistic/padded-blocks": ["error", "never", { allowSingleLineBlocks: true }],
	"@stylistic/quote-props": ["error", "as-needed"],
	"@stylistic/quotes": ["error", "double", { avoidEscape: true, allowTemplateLiterals: "avoidEscape" }],
	"@stylistic/rest-spread-spacing": ["error", "never"],
	"@stylistic/semi": ["error", "never"],
	"@stylistic/semi-spacing": ["error", { before: false, after: true }],
	"@stylistic/semi-style": ["error", "first"],
	"@stylistic/space-before-blocks": ["error", "always"],
	"@stylistic/space-before-function-paren": [
		"error",
		{ anonymous: "always", named: "never", asyncArrow: "always", catch: "always" },
	],
	"@stylistic/space-in-parens": ["error", "never"],
	"@stylistic/space-infix-ops": "error",
	"@stylistic/space-unary-ops": ["error"],
	"@stylistic/spaced-comment": "error",
	"@stylistic/switch-colon-spacing": "error",
	"@stylistic/template-curly-spacing": ["error", "never"],
	"@stylistic/template-tag-spacing": "error",
	"@stylistic/type-annotation-spacing": ["error", { before: false, after: true }],
	"@stylistic/type-generic-spacing": "error",
	"@stylistic/type-named-tuple-spacing": "error",

	// Require module imports to be relative and end in `.js`, to make GNOME JS happy
	"import/extensions": ["error", "always", { ignorePackages: true }],
	"no-restricted-imports": [
		"error",
		{
			patterns: [
				{
					group: ["src/*", "test/*"],
					message: "Use relative imports that end in `.js` instead!",
				},
			],
		},
	],

	"object-shorthand": ["error", "always"],
	"no-case-declarations": "error",
}

export default defineConfig([
	{
		ignores: [
			"**/.*",
			"**/*.d.ts",
			"**/__pycache__",
			"**/gobjectify",
			"_build",
			".flatpak-builder",
			"node_modules",
			"package.json",
			"package-lock.json",
			"gi-types",
			"src/gobjectify/**",
		],
	},
	{
		// JavaScript
		files: ["**/*.js"],
		languageOptions: {
			parserOptions: { sourceType: "module" },
		},
		plugins: { "@stylistic": stylistic, import: importPlugin },
		rules: { ...sharedJsTsRules },
	},
	{
		// TypeScript
		files: ["**/*.ts"],
		languageOptions: {
			parser: tsParser,
			parserOptions: {
				ecmaVersion: 2022,
				sourceType: "module",
				project: "./tsconfig.json",
			},
		},
		plugins: { "@typescript-eslint": tsPlugin, "@stylistic": stylistic, import: importPlugin },
		rules: {
			...sharedJsTsRules,
			"@typescript-eslint/explicit-function-return-type": "error",
			"@typescript-eslint/explicit-member-accessibility": ["error", { accessibility: "no-public" }],
		},
	},
	// JSON (default from JSONC)
	...eslintPluginJsonc.configs["flat/recommended-with-json"],
	{
		// JSON (adding on to JSONC)
		files: ["**/*.json", "**/*.json.in"],
		languageOptions: {
			parser: eslintPluginJsonc,
		},
		rules: {
			"jsonc/array-bracket-newline": "error",
			"jsonc/array-bracket-spacing": ["error", "never"],
			"jsonc/array-element-newline": ["error", { multiline: true }],
			"jsonc/comma-style": "error",
			"jsonc/indent": ["error", "tab"],
			"jsonc/key-spacing": "error",
			"jsonc/no-irregular-whitespace": "error",
			"jsonc/object-curly-newline": ["error", "always"],
			"jsonc/object-property-newline": "error",
		},
	},
    {
		// Allow comments in TSConfig
		files: ["**tsconfig.json"],
		languageOptions: {
			parser: eslintPluginJsonc,
		},
		rules: {
			"jsonc/no-comments": ["off"],
		},
	},
])
