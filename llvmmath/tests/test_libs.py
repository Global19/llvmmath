# -*- coding: utf-8 -*-
from __future__ import print_function, division, absolute_import

from functools import partial

import llvm.core as lc
import numpy as np

from .. import ltypes, libs
from . import support

# ______________________________________________________________________

np_integral = ['i', 'l', getattr(np, 'longlong', 'l')]
np_floating = ['f', 'd', getattr(np, 'float128', np.double)]
np_complexes = [np.complex64, np.complex128, getattr(np, 'complex256',
                                                     np.complex128)]

npy_typemap = {
    ltypes.integral: np_integral,
    ltypes.floating: np_floating,
    ltypes.complexes: np_complexes,
}

lower, upper = 1, 10

def get_idata(dtype):
    return np.arange(lower, upper, dtype=dtype) # poor test data

def get_cdata(dtype):
    return np.arange(lower, upper, dtype=dtype) + 0.2j

# ______________________________________________________________________

ufunc_map = {
    'asin': 'arcsin',
    'acos': 'arccos',
    'atan': 'arctan',
    'asinh': 'arcsinh',
    'acosh': 'arccosh',
    'atanh': 'arctanh',
    'atan2': 'arctan2',
}

def run(libm, name, sig, dtype):
    print("Running %s %s" % (name, sig))
    cname = libs.mathcode_mangler(name, sig)

    npy_name = ufunc_map.get(name, name)
    npy_func = getattr(np, npy_name)
    func = getattr(libm, cname)
    if sig.restype.kind == lc.TYPE_STRUCT:
        func = partial(support.call_complex_byref, func)

    test_data = get_idata(dtype)
    if npy_name.startswith('arc'):
        return

    out = np.empty(upper - lower, dtype)

    for i in range(upper - lower):
        out[i] = func(test_data[i])

    npy_out = npy_func(test_data)
    assert np.allclose(out, npy_out), (name, sig, dtype, npy_out - out)

# ______________________________________________________________________

def run_from_types(library, libm, types):
    for name, signatures in library.symbols.iteritems():
        for ty, dtype in zip(types, npy_typemap[types]):
            sig = types.Signature(ty, [ty])
            if sig in signatures:
                run(libm, name, sig, dtype)

def test_llvm_library():
    lib = libs.get_mathlib_so()
    libm = libs.get_mathlib_as_ctypes()
    assert not lib.missing, lib.missing

    print(libm.npy_sinl(10.0))

    # run_int_tests(libm)
    run_from_types(lib, libm, ltypes.floating)
    run_from_types(lib, libm, ltypes.complexes)