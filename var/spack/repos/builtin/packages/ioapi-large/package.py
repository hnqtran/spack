# Copyright 2013-2024 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

import os, shutil

from spack.package import *


class IoapiLarge(MakefilePackage):
    """Models-3/EDSS Input/Output Applications Programming Interface."""

    homepage = "https://www.cmascenter.org/ioapi/"
    url = "https://www.cmascenter.org/ioapi/download/ioapi-3.2-large-20200828.tar.gz"
    version("3.2", sha256="6c2c180f9ba3b3954dbc9ed9269dd028489156a07595d4d0b84c2723371b21f7")

    maintainers("hnqtran")

    depends_on("intel-oneapi-compilers")
    depends_on("hdf5")# %oneapi -shared -mpi +cxx +fortran +hl ^szip ^zlib")
    depends_on("netcdf-c")# %oneapi -mpi -shared -dap ^hdf5")
    depends_on("netcdf-fortran")#@4.6.1 %oneapi -shared ^netcdf-c")
    depends_on("sed", type="build")

    def edit(self, spec, prefix):
        
        # No default Makefile bundled; edit the template.
        os.symlink("Makefile.template", "Makefile")

        # Determine temporary source directory
        temp_source_dir = self.stage.source_path

        # Set Binary target
        BIN = 'Linux2_x86_64ifx'

        # The makefile uses stubborn assignments of = instead of ?= so
        # edit the makefile instead of using environmental variables.
        makefile = FileFilter("Makefile")

        # Replace the specific commented line with the desired uncommented line
        makefile.filter(r'^#\s*(BIN\s*=\s*Linux2_x86_64)',         'BIN     = {0}'.format(BIN))
        makefile.filter(r'^#\s*(BASEDIR\s*=\s*\${PWD})', r'BASEDIR = {0}'.format(temp_source_dir))
        makefile.filter(r'^#\s*(INSTALL\s*=\s*\${HOME})',          'INSTALL = {0}'.format(prefix))
        makefile.filter(r'^#\s*(LIBINST\s*=\s*\$\(INSTALL\)/\$\(BIN\))', r'\1')
        makefile.filter(r'^#\s*(BININST\s*=\s*\$\(INSTALL\)/\$\(BIN\))', r'\1')
        makefile.filter(r'^#\s*(CPLMODE\s*=\s*nocpl.*)', r'\1')#CPLMODE   = pncf')
        makefile.filter(r'^\s*(NCFLIBS\s*=\s*\-lnetcdff -lnetcdf)', r'#\1')
        makefile.filter(r'^#\s*(NCFLIBS\s*=\s*\-lnetcdff -lnetcdf -lhdf5_hl -lhdf5 -lz)',r'NCFLIBS = -lnetcdff -lnetcdf -lhdf5_hl -lhdf5 -lz -lm')
        makefile.filter(r'^#\s*(IOAPIDEFS\s*=\s*\"-DIOAPI_NCF4")',  r'\1')
        makefile.filter(r'^#\s*(PVMINCL\s*=\s*)(?!.*\$\(PVM_ROOT\)/conf/\$\(PVM_ARCH\).def)', r'\1')
        makefile.filter(r'^\s*(BASEDIR\s*=\s*\${PWD})', r'#\1')

        # Change the specific line to comment out ${IODIR}/Makefile and ${TOOLDIR}/Makefile
        # Fix circular dependency bug for generating subdirectory Makefiles.
        makefile.filter("^configure:.*", "configure:")

        # Modify ioapi/Make.$(CPLMODE).sed file
        makesed = FileFilter(os.path.join(temp_source_dir,'ioapi','Makefile.nocpl.sed'))
        makesed.filter(r'^\s*(BASEDIR\s*=\s*\${HOME}/ioapi-3.2)',r'BASEDIR = {0}'.format(temp_source_dir))
        makesed.filter(r'^\s*MAKEINCLUDE.\$\(BIN\)', r'MAKEINCLUDE.{0}'.format(BIN))
        makesed.filter(r'^#\s*(DEFINEFLAGS\s*=\s*\-DIOAPI_NCF4=1\s*\$\(ARCHFLAGS\)\s*\$\(PARFLAGS\))', r'\1') # Uncomment
        makesed.filter(r'^\s*(DEFINEFLAGS\s*=\s*\-DIOAPI_PNCF=1\s*\$\(ARCHFLAGS\)\s*\$\(PARFLAGS\))', r'#\1') # Comment out this line
        makesed.filter(r'^#(VFLAG\s*=\s*-DVERSION=\'3\.2-nocpl-ncf4\')', r'\1')
        makesed.filter(r'^\s*(VFLAG\s*=\s*\-DVERSION=\'3\.2-nocpl-mpi\')', r'#\1')

        # Modify m3tool/Make.$(CPLMODE).sed file
        m3toolsed = FileFilter(os.path.join(temp_source_dir,'m3tools','Makefile.nocpl.sed'))
        m3toolsed.filter(r'^\s*(BASEDIR\s*=\s*\${HOME}/ioapi-3.2)',r'BASEDIR = {0}'.format(temp_source_dir))

        # Modify ioapi/Makeinclude file
        shutil.copy("ioapi/Makeinclude.Linux2_x86_64ifort","ioapi/Makeinclude.{0}".format(BIN))
        makeinc = FileFilter(os.path.join(temp_source_dir,'ioapi',f'Makeinclude.{BIN}'))
        makeinc.filter(r'icc', r'icx')
        makeinc.filter(r'icpc', r'icpx')
        makeinc.filter(r'^\s*FC\s*=\s*ifort.*',r'FC = ifx  -auto -warn notruncated_source -Bstatic -static-intel')
        makeinc.filter(r'\s*(OMPFLAGS\s*=\s*\-openmp.*)',r'OMPFLAGS  = -qopenmp')
        makeinc.filter(r'\s*(OMPLIBS\s*=\s*\-openmp.*)',r'OMPLIBS   = -qopenmp -qopenmp-link=static -static-intel')
        makeinc.filter(r'#\s*(MFLAGS\s*=\s*\-traceback\s*# generic)',r'\1')
        makeinc.filter(r'\s*(MFLAGS\s*=\s*\-traceback -xHost \s*# this-machine)',r'#\1')
        makeinc.filter(r'-stack_temps', '-stack-temps')
        makeinc.filter(r'-safe_cray_ptr', '-safe-cray-ptr')

       # Modify ioapi/sortic.c
        with open(os.path.join(temp_source_dir,'ioapi','sortic.c'), 'r') as f:
            lines = f.readlines()

        # Find the line with #include "parms3.h"
        for i, line in enumerate(lines):
            if line.strip().startswith('#include "parms3.h"'):
                # Insert #include <stdlib.h> after #include "parms3.h"
                lines.insert(i + 1, '#include <stdlib.h>\n')
                break

        # Write the modified lines back 
        with open(os.path.join(temp_source_dir,'ioapi','sortic.c'), 'w') as f:
            f.writelines(lines)

        # Generate the subdirectory Makefiles.
        make("configure")
        make("dirs")
        make("fix")

    def install(self, spec, prefix):
        make("install")

        # Install the header files for downstream installation of SMOKE and CMAQ.
        mkdirp(prefix.ioapi.fixed_src)
        install("ioapi/*.EXT", prefix.ioapi)
        install("ioapi/Makeinclude.Linux2_x86_64ifx", prefix.ioapi)
        install("ioapi/*.EXT", prefix.ioapi)
        install("ioapi/fixed_src/*.EXT", prefix.ioapi.fixed_src)

        # Path to the source directory you want to copy
#       source_dir = os.path.join(self.stage.source_path,"ioapi")

        # Path to the destination directory (installation prefix)
#       destination_dir = os.path.join(prefix, 'ioapi')

        # Create the destination directory if it doesn't exist
#       os.makedirs(destination_dir, exist_ok=True)
#       try:
            # Copy the entire source directory to the destination directory
#           shutil.copytree(source_dir, destination_dir)
#           print(f"Copied {source_dir} to {destination_dir}")
#       except OSError as e:
#           raise RuntimeError(f"Error copying directory: {e}")
