{ pkgs ? import <nixpkgs> {}}:

pkgs.mkShell {
  nativeBuildInputs = with pkgs; [ 
    flac
    (python3.withPackages (ps: with ps; with python3Packages; [
      jupyter
      ipython
      pydub
      docopt
      (callPackage ./speech_recognition.nix {})

    ]))
  ];
}
