{
  description = "Minimal Cargo dev shell for ./book subproject";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    rust-overlay.url = "github:oxalica/rust-overlay";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, rust-overlay, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = import nixpkgs {
          inherit system;
          overlays = [ rust-overlay.overlays.default ];
        };

        rustToolchain = pkgs.rust-bin.fromRustupToolchainFile ./book/rust-toolchain.toml;

        mdbook = pkgs.rustPlatform.buildRustPackage rec {
          pname = "mdbook";
          version = "0.5.3";
          src = pkgs.fetchCrate {
            inherit pname version;
            hash = "sha256-2j22rRehYPpyPk1REPhHnRZ05WP0KXcv5mlpMxC83yg=";
          };
          cargoLock.lockFile = "${src}/Cargo.lock";
          doCheck = false;
        };

        mdbookKatex = pkgs.rustPlatform.buildRustPackage rec {
          pname = "mdbook-katex";
          version = "0.10.0-alpha";
          src = pkgs.fetchCrate {
            inherit pname version;
            hash = "sha256-F6ozNlN8umagAWr+xeA61uf+QOae/y6VnyzWKDsFIhk=";
          };
          cargoLock.lockFile = "${src}/Cargo.lock";
        };

        mdbookToc = pkgs.rustPlatform.buildRustPackage rec {
          pname = "mdbook-toc";
          version = "0.15.4";
          src = pkgs.fetchCrate {
            inherit pname version;
            hash = "sha256-sCnHbIQQW7Xc2Z0w3auwx2ZsZ+gEU3tEJZ3Jk65K1cw=";
          };
          cargoLock.lockFile = "${src}/Cargo.lock";
          doCheck = false;
        };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            rustToolchain
            pkgs.rust-analyzer
            mdbook
            mdbookKatex
            mdbookToc
          ];

          CARGO_TARGET_DIR = "./book/target";

          shellHook = ''
            echo "🚀 Rust dev shell for ./book"
            export PATH=$PATH:$HOME/.cargo/bin
            if [ -d book ]; then
              cd book
              echo "📁 cwd => $(pwd)"
            fi
            rustc --version
            cargo --version
            mdbook --version
          '';
        };
      });
}
