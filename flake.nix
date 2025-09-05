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
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            rustToolchain
            pkgs.rust-analyzer
            pkgs.mdbook
            pkgs.mdbook-katex
            pkgs.mdbook-toc
          ];

          CARGO_TARGET_DIR = "./book/target";

          shellHook = ''
            echo "🚀 Rust dev shell for ./book"
            export PATH=$HOME/.cargo/bin:$PATH
            if [ -d book ]; then
              cd book
              echo "📁 cwd => $(pwd)"
            fi
            rustc --version
            cargo --version
          '';
        };
      });
}
