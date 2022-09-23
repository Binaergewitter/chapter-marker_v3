{ pkgs ? import <nixpkgs> {}}:

pkgs.mkShell {
  nativeBuildInputs = with pkgs; [ 
    flac
    (python3.withPackages (ps: with ps; with python3Packages; [
      jupyter
      ipython
      pydub
      docopt
      #pytorch
      omegaconf
      torchaudio-bin
      (callPackage ./speech_recognition.nix {})

    ]))
  ];
}
