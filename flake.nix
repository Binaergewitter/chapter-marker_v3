{
  inputs = {
    utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, utils }: utils.lib.eachDefaultSystem (system:
    let
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      devShell = pkgs.mkShell {
        buildInputs = with pkgs; [
	    flac
	    ffmpeg
	    gcc
	    python3.pkgs.torchaudio-bin
	    python3.pkgs.pytorch-bin
	    python3.pkgs.docopt
	    python3.pkgs.pip
	    python3.pkgs.pydub
	    python3.pkgs.openai-whisper
	    python3.pkgs.speechrecognition
	    pkgs.stdenv.cc.cc.lib
        ];
      };
    }
  );
}
