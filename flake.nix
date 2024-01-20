{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-22.11";
  };
  outputs = { self, nixpkgs }:
    let
      supportedSystems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forEachSupportedSystem = f: nixpkgs.lib.genAttrs supportedSystems (system: f {
        pkgs = import nixpkgs {
          inherit system; 
          config.allowUnfree = true;
        };
      });
    in
    {
      packages = forEachSupportedSystem ({pkgs }: {
        default = pkgs.darkice;
      });
      devShells = forEachSupportedSystem ({ pkgs }: {
        default = (import ./shell.nix) { inherit pkgs;};
      });
    };
}
