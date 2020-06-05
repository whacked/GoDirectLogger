with import <nixpkgs> {};

let
    gdx-python = (
      let
        src = fetchFromGitHub {
            owner = "VernierST";
            repo = "godirect-examples";
            rev = "master";
            sha256 = "1wghdkk0gy4hczwqy3x6zsdfdqyc9pmaqi4hp963lfbcj9zjlf43";
        };
      in stdenv.mkDerivation {
        name = "godirect-example-python-gdx-library";
        dontUnpack = true;
        installPhase = ''
          mkdir -p $out
          cp -r ${src}/python/gdx $out/
        '';
      }
    );
in stdenv.mkDerivation rec {
    name = "godirect-logger";
    env = buildEnv {
        name = name;
        paths = buildInputs;
    };

    nativeBuildInputs = [
        ~/setup/bash/nix_shortcuts.sh
    ];

    buildInputs = [
        libusb1
        python37Full
        python37Packages.ipython
        python37Packages.libusb1
        python37Packages.pexpect
        python37Packages.setuptools
        gdx-python
    ];

    shellHook = ''
      export C_INCLUDE_PATH=$C_INCLUDE_PATH:${libusb1.dev}/include/libusb-1.0
      export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${libusb1}/lib
      export PYTHONPATH=$PYTHONPATH:${gdx-python}

      function setup() {
          pip install bleak godirect[USB,BLE]
          if [ ! -e settings.ini ]; then
              cp example-settings.ini settings.ini
          fi
      }

      function ensure-rules-file() {
          RULES_FILE=/etc/udev/rules.d/99-vstlibusb.rules
          if [ ! -e $RULES_FILE ]; then
              echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="08f7", MODE="0666"' | tee -a $RULES_FILE
              echo 'SUBSYSTEM=="usb_device", ATTRS{idVendor}=="08f7", MODE="0666"' | tee -a $RULES_FILE
              udevadm control --reload-rules && udevadm trigger
          fi
      }

      ensure-venv setup
      alias run='./gdx_logger.py'
      echo-shortcuts
    '';
}

