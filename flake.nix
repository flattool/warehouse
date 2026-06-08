{
	description = "Ignition develion environment";

	inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

	outputs = { self, nixpkgs, ... }: let
		system = "x86_64-linux";
		pkgs = import nixpkgs { inherit system; };
	in {
		devShells.${system}.default = pkgs.mkShell {
			packages = with pkgs; [
				meson
				ninja
				pkg-config
				gjs
				gtk4
				libadwaita
				nodejs_22
				blueprint-compiler
				python3
				typescript
				desktop-file-utils
				appstream
			];
		};
	};
}
