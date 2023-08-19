{ lib
, stdenv
, buildPythonPackage
, fetchPypi
, python3
}:

buildPythonPackage rec {
  pname = "stft";
  version = "0.5.2";

  src = fetchPypi {
    inherit pname version;
    sha256 = "b6411afb45e286de412e352b8bc4a59c3a997904b0b8f3945cb767f0b7347e06";
  };
  propagatedBuildInputs = [
    python3.pkgs.numpy
    python3.pkgs.scipy
    stdenv.cc.cc.lib
  ];
  doCheck = false;

  meta = with lib; {
    description = "Short Time Fourier transform for NumPy";
    license = licenses.mit;
    # maintainers = [ maintainers. ];
  };
}
