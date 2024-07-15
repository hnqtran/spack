# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os, shutil, subprocess

from spack.package import *


class SmokeOneapi(MakefilePackage):
    """The Sparse Matrix Operator Kernel Emissions (SMOKE) Modeling System"""

    homepage = "https://github.com/CEMPD/SMOKE/releases/tag/SMOKEv5_Jun2023"
    git = "https://github.com/CEMPD/SMOKE"
    version("5.0", branch="master")

    maintainers("hnqtran")

    depends_on("intel-oneapi-compilers")
    depends_on("ioapi-oneapi")

    def edit(self, spec, prefix):
        
        # Determine temporary source directory
        temp_source_dir = self.stage.source_path

        # Determine path to ioapi
        ioapi_dir = self.spec['ioapi-oneapi'].prefix

        # Determine linked library in netcdf
        # Execute the command `nc-config --libs` using subprocess
        try:
            result = subprocess.run(['nc-config', '--libs'], stdout=subprocess.PIPE, check=True)
            # Decode the output bytes to string assuming utf-8 encoding
            nclibs = result.stdout.decode('utf-8').strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Error running nc-config --libs: {e}")

        # Set Binary target
        BIN = 'Linux2_x86_64ifx'

        os.symlink("src/Makefile", "Makefile")
        makefile = FileFilter(os.path.join(temp_source_dir,'src','Makefile'))
        makefile.filter(r'^\s*(include\s*Makeinclude)',f'include {temp_source_dir}/src/Makeinclude')

        makeincl = FileFilter(os.path.join(temp_source_dir,'src','Makeinclude'))

        # Replace the specific commented line with the desired uncommented line
        makeincl.filter(r'^\s*(BASEDIR\s*=\s*\${SMK_HOME}/subsys/smoke/src)','BASEDIR = {0}/src'.format(temp_source_dir))
        makeincl.filter(r'^\s*IOBASE\s*=.*','IOBASE = {0}'.format(ioapi_dir))
        makeincl.filter(r'^\s*(OBJDIR\s*=\s*\${BASEDIR}/../\${BIN})',r'OBJDIR  = {0}/{1}'.format(temp_source_dir,BIN))
        makeincl.filter(r'^\s*(IOBIN\s*=\s*\${IOBASE}.*)','IOBIN  = {0}/{1}'.format(ioapi_dir,BIN))
        makeincl.filter(r'^\s*INSTDIR\s*=\s*/somewhere.*','INSTDIR = {0}/{1}'.format(prefix,BIN))

        makeincl.filter(r'^\s*(include\s*\${IODIR}/Makeinclude.\${BIN})','include {0}/ioapi/Makeinclude.{1}'.format(ioapi_dir,BIN))

        makeincl.filter(r'^\s*(IFLAGS\s*=\s*\-I${IOINC} -I${INCDIR} -I${IOBIN}.*)', r'IFLAGS = -I${IOINC} -I${INCDIR} -I${IOBIN} -traceback')
        makeincl.filter(r'^\s*(EFLAG\s*=\s*\-extend-source 132 -zero.*)',r'EFLAG = -extend-source 132 -zero -static-intel -debug')
        makeincl.filter(r'^\s*(IOLIB\s*=\s*\-L\$\(IOBIN\) -lioapi -lnetcdff -lnetcdf)','IOLIB = -L$(IOBIN) -lioapi -lnetcdff {0}'.format(nclibs))

        makefile.filter("^install:.*", "install:")

        make("dir")

    def install(self, spec, prefix):
        mkdirp(prefix.Linux2_x86_64ifx)
        make("lib")
        make("exe")
        make('install')
#       make('all')

#       # Ensure the Makefile is present in the correct subfolder
#       makefile_dir = os.path.join(self.stage.source_path, 'src')

        # Check if the Makefile exists in the specified directory
#       if not os.path.exists(os.path.join(makefile_dir, 'Makefile')):
#           raise RuntimeError(f"Makefile not found in {makefile_dir}")

        # Change directory to the subfolder containing the Makefile
#       with working_dir(makefile_dir):
            # Execute make install command
#           make('all', parallel=False)  # Adjust parallelism as needed
