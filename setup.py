from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import sys
import setuptools
import glob
import os
from os.path import join as pjoin
from pathlib import Path
import subprocess

__version__ = '0.0.1'

#os.system("sudo apt-get install libboost-coroutine1.65-dev")

def find_in_path(name, path):
    """Find a file in a search path"""

    # Adapted fom http://code.activestate.com/recipes/52224
    for dir in path.split(os.pathsep):
        binpath = pjoin(dir, name)
        if os.path.exists(binpath):
            return os.path.abspath(binpath)
    return None

def locate_boost():
    command = 'ldconfig -p | grep boost_coroutine' 
    p =subprocess.Popen(    command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines  = p.stdout.readlines()
    if len(lines) == 0:
        raise ValueError("libboost_coroutine is not installed. Please install e.g. via sudo apt-get install libboost-coroutine1.65-dev  or sudo apt-get install libboost-coroutine-dev ")
    #for i, line in enumerate(iter(p.stdout.readline, b'')):
    for line in lines:
        return os.path.dirname(line.decode("UTF-8").split("=>")[1].strip())


def locate_gfortran():
    from shutil import which
    if which("gfortran") is not None:
        return which("gfortran")
    else:
        raise ValueError('gfortran could not be found. Please install gfortran e.g. via sudo apt-get install gfortran')

def locate_cuda():
    """Locate the CUDA environment on the system
    Returns a dict with keys 'home', 'nvcc', 'include', and 'lib64'
    and values giving the absolute path to each directory.
    Starts by looking for the CUDAHOME env variable. If not found,
    everything is based on finding 'nvcc' in the PATH.
    """

    # First check if the CUDAHOME env variable is in use
    if 'CUDAHOME' in os.environ:
        home = os.environ['CUDAHOME']
        nvcc = pjoin(home, 'bin', 'nvcc')
    else:
        # Otherwise, search the PATH for NVCC
        nvcc = find_in_path('nvcc', os.environ['PATH'])
        if nvcc is None:
            raise EnvironmentError('The nvcc binary could not be '
                'located in your $PATH. Either add it to your path, '
                'or set $CUDAHOME')
        home = os.path.dirname(os.path.dirname(nvcc))

    cudaconfig = {'home': home, 'nvcc': nvcc,
                  'include': pjoin(home, 'include'),
                  'lib64': pjoin(home, 'lib64')}
    for k, v in iter(cudaconfig.items()):
        if not os.path.exists(v):
            raise EnvironmentError('The CUDA %s path could not be '
                                   'located in %s' % (k, v))

    return cudaconfig


class get_pybind_include(object):
    """Helper class to determine the pybind11 include path

    The purpose of this class is to postpone importing pybind11
    until it is actually installed, so that the ``get_include()``
    method can be invoked. """

    def __str__(self):
        import pybind11
        return pybind11.get_include()


CUDA = locate_cuda()
GFORTRAN = locate_gfortran()
BOOST_PATH = locate_boost()

ext_modules = [
    Extension(
        'CrosslinkDocking',
        # Sort input source files to ensure bit-for-bit reproducible builds
        #sorted(['src/CrosslinkDocking.cpp']),
        sources = [str(file) for file in Path('src').glob('**/*.cpp')] 
        + [str(file) for file in Path('src').glob('**/*.cu')]
        + [str(file) for file in Path('src').glob('**/*.f')],
        library_dirs = [CUDA['lib64'], BOOST_PATH],
        libraries = ['cudart','boost_coroutine', 'gfortran', "nvToolsExt", 'pthread'],
        runtime_library_dirs = [CUDA['lib64']],
        define_macros = [('CUDA',None)],
        include_dirs=[
            # Path to pybind11 headers
            "src/server",
            "src/service",
            "src/model",
            'src/apps/em',
            'src/commons',
            'src/allocator',
            'src/cli',
            'src/apps',
            'src/fileIO',
            get_pybind_include(),
            CUDA['include'],
            'usr/include/boost'
        ],
         extra_compile_args= {
            'g++': ['-O3', '-DNDEBUG'],
            'nvcc': ['-O3', '-DNDEBUG',
                '-arch=sm_61', '--ptxas-options=-v', '-c',
                '--compiler-options', "'-fPIC'"
                ],
                'gfortran':[
                    '-O2','-DNDEBUG', '-fcray-pointer', '-fPIC' ]
            },
        language='c++'
    ),
]


# cf http://bugs.python.org/issue26689
def has_flag(compiler, flagname):
    """Return a boolean indicating whether a flag name is supported on
    the specified compiler.
    """
    import tempfile
    import os
    with tempfile.NamedTemporaryFile('w', suffix='.cpp', delete=False) as f:
        f.write('int main (int argc, char **argv) { return 0; }')
        fname = f.name
    try:
        compiler.compile([fname], extra_postargs=[flagname])
    except setuptools.distutils.errors.CompileError:
        return False
    finally:
        try:
            os.remove(fname)
        except OSError:
            pass
    return True


def cpp_flag(compiler):
    """Return the -std=c++[11/14/17] compiler flag.

    The newer version is prefered over c++11 (when it is available).
    """
    flags = ['-std=c++17', '-std=c++14', '-std=c++11']

    for flag in flags:
        if has_flag(compiler, flag):
            return flag

    raise RuntimeError('Unsupported compiler -- at least C++11 support '
                       'is needed!')




def customize_compiler_for_nvcc(self):
    """Inject deep into distutils to customize how the dispatch
    to gcc/nvcc works.
    If you subclass UnixCCompiler, it's not trivial to get your subclass
    injected in, and still have the right customizations (i.e.
    distutils.sysconfig.customize_compiler) run on it. So instead of going
    the OO route, I have this. Note, it's kindof like a wierd functional
    subclassing going on.
    """

    # Tell the compiler it can processes .cu
    self.src_extensions.append('.cu')
    self.src_extensions.append('.f')

    # Save references to the default compiler_so and _comple methods
    default_compiler_so = self.compiler_so
    super = self._compile

    # Now redefine the _compile method. This gets executed for each
    # object but distutils doesn't have the ability to change compilers
    # based on source extension: we add it.
    def _compile(obj, src, ext, cc_args, extra_postargs, pp_opts):
        print("\n\n\n COMPILING:", src.upper())

        print(obj," 1 ", src, " 2 ",ext," 3 ", cc_args," 4 ", extra_postargs," 5 ", pp_opts)
        if os.path.splitext(src)[1] == '.cu':
            # use the cuda for .cu files
            self.set_executable('compiler_so', CUDA['nvcc'])
            # use only a subset of the extra_postargs, which are 1-1
            # translated from the extra_compile_args in the Extension class
            postargs = extra_postargs['nvcc']
        elif os.path.splitext(src)[1] == '.f':
            # use the cuda for .cu files
            self.set_executable('compiler_so', GFORTRAN)
            # use only a subset of the extra_postargs, which are 1-1
            # translated from the extra_compile_args in the Extension class
            postargs = extra_postargs['gfortran']
        else:
            postargs = extra_postargs['g++']

        super(obj, src, ext, cc_args, postargs, pp_opts)
        # Reset the default compiler_so, which we might have changed for cuda
        self.compiler_so = default_compiler_so

    # Inject our redefined _compile method into the class
    self._compile = _compile


class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    # c_opts = {
    #     'msvc': ['/EHsc'],
    #     'unix': [],
    # }
    # l_opts = {
    #     'msvc': [],
    #     'unix': [],
    # }

    # if sys.platform == 'darwin':
    #     darwin_opts = ['-stdlib=libc++', '-mmacosx-version-min=10.7']
    #     c_opts['unix'] += darwin_opts
    #     l_opts['unix'] += darwin_opts

    def build_extensions(self):
        #ct = self.compiler.compiler_type
        # opts = self.c_opts.get(ct, [])
        #link_opts = self.l_opts.get(ct, [])
        # if ct == 'unix':
        #     opts.append(cpp_flag(self.compiler))
        #     if has_flag(self.compiler, '-fvisibility=hidden'):
        #         opts.append('-fvisibility=hidden')

        for ext in self.extensions:
            print("\n\n\n SOURCE FILES:", ext.sources)
            #ext.define_macros = [('CUDA', None),('VERSION_INFO', '"{}"'.format(self.distribution.get_version()))]
            #ext.extra_compile_args = opts
            #ext.extra_link_args = link_opts

        customize_compiler_for_nvcc(self.compiler)
        build_ext.build_extensions(self)




setup(
    name='CrosslinkDocking',
    version=__version__,
    author='Glenn Glashagen',
    author_email='glenn.glashagen@gmail.com',
    description='GPU accelerated Crosslink docking tool',
    long_description='',
    ext_modules=ext_modules,
    setup_requires=['pybind11>=2.5.0'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)
