{ lib
, buildPythonPackage
, fetchPypi
, swig2
, pocketsphinx
, pulseaudio
, alsaLib
}:

buildPythonPackage rec {
  pname = "pocketsphinx";
  version = "0.1.15";

  src = fetchPypi {
    inherit pname version;
    sha256 = "34d290745c7dbe6fa2cac9815b5c19d10f393e528ecd70e779c21ebc448f9b63";
  };

  nativeBuildInputs = [
    swig2
  ];
  propagatedBuildInputs = [
    pocketsphinx
  ];
  buildInputs = [
    pulseaudio
    alsaLib
  ];
  doCheck = false;

  meta = with lib; {
    description = "Python interface to CMU Sphinxbase and Pocketsphinx libraries";
    homepage = https://github.com/bambocher/pocketsphinx-python;
  };
}
