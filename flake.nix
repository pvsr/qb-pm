{
  description = "A tool for creating and managing qutebrowser profiles";

  inputs.nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  inputs.flake-utils.url = "github:numtide/flake-utils";
  inputs.treefmt-nix.url = "github:numtide/treefmt-nix";
  inputs.treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";

  outputs = {
    self,
    nixpkgs,
    flake-utils,
    treefmt-nix,
  }:
    flake-utils.lib.eachDefaultSystem (
      system: let
        pkgs = nixpkgs.legacyPackages.${system};
        treefmt = treefmt-nix.lib.evalModule pkgs {
          projectRootFile = "flake.nix";
          programs.mypy.enable = true;
          programs.mypy.directories."." = {
            modules = ["qbpm" "tests"];
            extraPythonPackages = self.packages.x86_64-linux.default.propagatedBuildInputs;
          };
          programs.ruff.check = true;
          programs.ruff.format = true;
          programs.alejandra.enable = true;
        };
      in rec {
        packages = flake-utils.lib.flattenTree rec {
          qbpm = import ./. {inherit pkgs;};
          default = qbpm;
        };
        apps = rec {
          qbpm = flake-utils.lib.mkApp {drv = packages.qbpm;};
          default = qbpm;
        };
        devShells.default = pkgs.mkShell {
          packages = with pkgs;
            [
              ruff
              scdoc
              xdg-utils
              (python3.withPackages (ps:
                with ps; [
                  pytest
                  mypy
                  pylsp-mypy
                  ruff-lsp
                  types-pillow
                ]))
            ]
            ++ self.packages.x86_64-linux.default.propagatedBuildInputs;
        };
        formatter = treefmt.config.build.wrapper;
        checks.formatting = treefmt.config.build.check self;
      }
    );
}
