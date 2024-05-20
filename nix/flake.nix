{
  description = "Application packaged using poetry2nix";

  inputs = {
    flake-utils.url = "github:numtide/flake-utils";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";
    poetry2nix = {
      url = "github:nix-community/poetry2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        # see https://github.com/nix-community/poetry2nix/tree/master#api for more functions and examples.
        pkgs = nixpkgs.legacyPackages.${system};
        inherit (poetry2nix.lib.mkPoetry2Nix { inherit pkgs; }) mkPoetryApplication defaultPoetryOverrides;
      in
      {
        packages = {
          myapp = mkPoetryApplication {
            projectDir = self;
            overrides = defaultPoetryOverrides.extend
            (final: prev: {
              openai-whisper = pkgs.python3.pkgs.openai-whisper;
              torchaudio = pkgs.python3.pkgs.torchaudio;
              torch = pkgs.python3.pkgs.torch;
              pyyaml = pkgs.python3.pkgs.pyyaml;
              silero = prev.silero.overridePythonAttrs
              (
                old: {
                  src = pkgs.fetchFromGitHub {
                    owner = "makefu";
                    repo = "silero-models";
                    rev = "7d51338";
                    hash = "sha256-o8UI0TUXY7iTudgd3FRFxZY34i7Cxip4hT1a8mkW9Y0";
                    #hash = pkgs.lib.fakeHash;
                  };
                }
              );
            });
          };
          default = self.packages.${system}.myapp;
        };

        # Shell for app dependencies.
        #
        #     nix develop
        #
        # Use this shell for developing your app.
        devShells.default = pkgs.mkShell {
          inputsFrom = [ self.packages.${system}.myapp ];
        };

        # Shell for poetry.
        #
        #     nix develop .#poetry
        #
        # Use this shell for changes to pyproject.toml and poetry.lock.
        devShells.poetry = pkgs.mkShell {
          packages = [ pkgs.poetry ];
        };
      });
}
