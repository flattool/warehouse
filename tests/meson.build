test_deps = [ui_res, blueprints, jasmine]

unit_tests = {'example_test': {}}

tests = custom_target(
	'typescript-compile',
	build_by_default: true,
	build_always_stale: true,
	output: ['tsc-output'],
	command: [
		tsc,
		'-p', meson.project_source_root() / 'tsconfig.json',
		'--outDir', tsc_out,
	],
)
install_subdir(
	tsc_out,
	install_dir: pkgdatadir,
	strip_directory: true,
	install_tag: 'tsc-js',
)
foreach test, extra : unit_tests
	test(
		test,
		jasmine,
		args: [
			'--module',
			'--tap',
			'--no-config', '@0@.js'.format(tsc_out / 'tests' / 'sources' / test),
		],
		suite: 'unit',
		depends: [tests],
		env: environment(),
		protocol: 'tap',
		workdir: meson.current_source_dir(),
	)
endforeach
