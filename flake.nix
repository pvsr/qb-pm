{
  description = "A tool for creating and managing qutebrowser profiles";

  outputs = { self, nixpkgs }: {

    packages.x86_64-linux.qbpm = import ./. {
      pkgs = import nixpkgs { system = "x86_64-linux"; };
    };

    defaultPackage.x86_64-linux = self.packages.x86_64-linux.qbpm;

  };
}
