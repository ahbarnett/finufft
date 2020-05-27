# finufftpy module, ie python-user-facing access to (no-data-copy) interfaces
#
# This is where default opts are stated (in arg list, but not docstring).

# todo: pass opts as python double array, neater?
# Note: this JFM code is an extra level of wrapping beyond DFM's style.
# Barnett 10/31/17: changed all type-2 not to have ms,etc as an input but infer
#                   from size of f.
# Lu 03/10/20: added guru interface calls

# google-style docstrings for napoleon

import finufftpy.finufftpy_cpp as finufftpy_cpp
import numpy as np

from finufftpy_cpp import default_opts
from finufftpy_cpp import destroy
from finufftpy_cpp import nufft_opts
from finufftpy_cpp import finufft_plan
from finufftpy_cpp import fftwopts
from finufftpy_cpp import get_max_threads

# default opts for simple interface
opts_default = nufft_opts()
default_opts(opts_default)
debug_def=opts_default.debug
spread_debug_def=opts_default.spread_debug
spread_sort_def=opts_default.spread_sort
fftw_def=0
modeord_def=opts_default.modeord
chkbnds_def=opts_default.chkbnds
upsampfac_def=opts_default.upsampfac

## David Stein's functions for checking input and output variables
def _rchk(x):
  """
  Check if array x is of the appropriate type
  (float64, F-contiguous in memory)
  If not, produce a copy
  """
  return np.array(x, dtype=np.float64, order='F', copy=False)
def _cchk(x):
  """
  Check if array x is of the appropriate type
  (complex128, F-contiguous in memory)
  If not, produce a copy
  """
  return np.array(x, dtype=np.complex128, order='F', copy=False)
def _copy(_x, x):
  """
  Copy _x to x, only if the underlying data of _x differs from that of x
  """
  if _x.data != x.data:
    x[:] = _x

## makeplan
def makeplan(tp,n_dims,n_modes,iflag,n_transf,tol,plan,opts):
  return finufftpy_cpp.makeplan(tp,n_dims,n_modes,iflag,n_transf,tol,plan,opts)

## setpts
def setpts(plan,M,xj,yj,zj,N,s,t,u):
  global _xj,_yj,_zj,_s,_t,_u
  _xj = _rchk(xj)
  _yj = _rchk(yj)
  _zj = _rchk(zj)
  _s = _rchk(s)
  _t = _rchk(t)
  _u = _rchk(u)
  return finufftpy_cpp.setpts(plan,M,_xj,_yj,_zj,N,_s,_t,_u)

## execute
def execute(plan,weights,result):
  _weights = _cchk(weights)
  _result = _cchk(result)
  info = finufftpy_cpp.execute(plan,_weights,_result)
  _copy(_weights,weights)
  _copy(_result,result)
  return info

def set_opts(opts,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac):
  opts.debug = debug
  opts.spread_debug = spread_debug;
  opts.spread_sort = spread_sort
  opts.fftw = fftwopts(fftw)
  opts.modeord = modeord
  opts.chkbnds = chkbnds
  opts.upsampfac = upsampfac

def invoke_guru(x,y,z,c,isign,eps,s,t,u,f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,tp,ndim,n_modes,ntransf,M,nk):
  #opts
  opts = nufft_opts()
  set_opts(opts,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac)

  #plan
  plan = finufft_plan()
  info = makeplan(tp,ndim,n_modes,isign,ntransf,eps,plan,opts)

  #setpts
  info = setpts(plan,M,x,y,z,nk,s,t,u)

  #excute
  info = execute(plan,c,f)

  #destroy
  info = destroy(plan)

  return info

## easy interfaces
## 1D
def nufft1d1(x,c,isign,eps,ms,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """1D type-1 (aka adjoint) complex nonuniform fast Fourier transform

  ::

             nj-1
    f(k1) =  SUM c[j] exp(+/-i k1 x(j))  for -ms/2 <= k1 <= (ms-1)/2
             j=0

  Args:
    x     (float[nj]): nonuniform source points, valid only in [-3pi,3pi]
    c     (complex[nj] or complex[nj,ntransf]): source strengths
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    ms    (int): number of Fourier modes requested, may be even or odd;
        in either case the modes are integers lying in [-ms/2, (ms-1)/2]
    f     (complex[ms] or complex[ms,ntransf]): output Fourier mode values. Should be initialized as a
              numpy array of the correct size
    debug (int, optional): 0 (silent), 1 (print timing breakdown).
    spread_debug (int, optional): 0 (silent), 1, 2... (prints spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (do sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    modeord (int, optional): 0 (CMCL increasing mode ordering), 1 (FFT ordering)
    chkbnds (int, optional): 0 (don't check NU points valid), 1 (do)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the f array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF,
       4 at least one NU point out of range (if chkbnds true)

  Example:
    see ``python_tests/demo1d1.py``
  """
  # f is the output and must have dtype=np.complex128
  # check input x and c array, use c to detect ntransf
  x = _rchk(x)
  c = _cchk(c)
  if c.ndim>1:
    assert c.ndim==2
    ntransf = c.shape[1]
  else:
    ntransf = 1
  assert c.shape[0]==x.size
  assert x.size*ntransf==c.size
  
  # check output f, if none _f is returned as output,
  # otherwise output is stored in f
  if f is None and c.ndim==2:
    _f = np.zeros([ms,ntransf], dtype=np.complex128, order='F')
  elif f is None:
    _f = np.zeros([ms], dtype=np.complex128, order='F')
  else:
    _f = _cchk(f)
  assert _f.size==ms*ntransf
  assert _f.shape[0]==ms
  assert _f.ndim==c.ndim
  if c.ndim==2:
    assert _f.shape[1]==c.shape[1]

  # number of input pts and modes info
  M = x.size
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = ms
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,None,None,c,isign,eps,None,None,None,_f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,1,1,n_modes,ntransf,M,0)

  # return _f if f is none else output is in f
  if f is None:
    return _f
  else:
    _copy(_f, f)
    return info

def nufft1d2(x,c,isign,eps,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """1D type-2 (aka forward) complex nonuniform fast Fourier transform

  ::

    c[j] = SUM   f[k1] exp(+/-i k1 x[j])      for j = 0,...,nj-1
            k1

	where sum is over -ms/2 <= k1 <= (ms-1)/2.

  Args:
    x     (float[nj]): nonuniform target points, valid only in [-3pi,3pi]
    c     (complex[nj] or complex[nj,ntransf]): output values at targets. Should be initialized as a
        numpy array of the correct size
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    f     (complex[ms] or complex[ms,ntransf]): Fourier mode coefficients, where ms is even or odd
          In either case the mode indices are integers in [-ms/2, (ms-1)/2]
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (print spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    modeord (int, optional): 0 (CMCL increasing mode ordering), 1 (FFT ordering)
    chkbnds (int, optional): 0 (don't check NU points valid), 1 (do)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the c array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF,
       4 at least one NU point out of range (if chkbnds true)

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # c is the output and must have dtype=np.complex128
  # check input x and f array, use f to detect ntransf
  x = _rchk(x)
  f = _cchk(f)
  if f.ndim>1:
    assert f.ndim==2
    ntransf = f.shape[1]
  else:
    ntransf = 1
  
  ms = f.shape[0]
  M = x.size
  if c is None and f.ndim==2:
    _c = np.zeros([M,ntransf], dtype=np.complex128, order='F')
  elif c is None:
    _c = np.zeros([M], dtype=np.complex128, order='F')
  else:
    _c = _cchk(c)

  assert x.size*ntransf==_c.size
  assert x.size==_c.shape[0]
  if f.ndim==2:
    assert f.shape[1]==_c.shape[1]

  # number of input pts and modes info
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = ms
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,None,None,_c,isign,eps,None,None,None,f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,2,1,n_modes,ntransf,M,0)

  # return _f if f is none else output is in f
  if c is None:
    return _c
  else:
    _copy(_c, c)
    return info

def nufft1d3(x,c,isign,eps,s,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """1D type-3 (NU-to-NU) complex nonuniform fast Fourier transform

  ::

	     nj-1
    f[k]  =  SUM   c[j] exp(+-i s[k] x[j]),      for k = 0, ..., nk-1
	     j=0

  Args:
    x     (float[nj]): nonuniform source points, in R
    c     (complex[nj] or complex[nj,ntransf]): source strengths
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    s     (float[nk]): nonuniform target frequency points, in R
    f     (complex[nk] or complex[nk,ntransf]): output values at target frequencies.
       Should be initialized as a numpy array of the correct size
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (print spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the f array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # f is the output and must have dtype=np.complex128
  # check input x and c array, use c to detect ntransf
  x = _rchk(x)
  c = _cchk(c)
  s = _rchk(s)
  if c.ndim>1:
    assert c.ndim==2
    ntransf = c.shape[1]
  else:
    ntransf = 1
  assert x.size==c.shape[0]
  assert x.size*ntransf==c.size
  
  # check output f, if none _f is returned as output,
  # otherwise output is stored in f
  assert s.ndim==1
  nk=s.size
  if f is None and c.ndim==2:
    _f = np.zeros([nk,ntransf], dtype=np.complex128, order='F')
  elif f is None:
    _f = np.zeros([nk], dtype=np.complex128, order='F')
  else:
    _f = _cchk(f)
  assert _f.size==nk*ntransf
  assert _f.shape[0]==nk
  assert _f.ndim==c.ndim
  if c.ndim==2:
    assert _f.shape[1]==c.shape[1]

  # number of input pts and modes info
  M = x.size
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = nk
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,None,None,c,isign,eps,s,None,None,_f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,3,1,n_modes,ntransf,M,nk)

  # return _f if f is none else output is in f
  if f is None:
    return _f
  else:
    _copy(_f, f)
    return info

## 2D
def nufft2d1(x,y,c,isign,eps,ms,mt,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """2D type-1 (aka adjoint) complex nonuniform fast Fourier transform

  ::

	            nj-1
	f(k1,k2) =  SUM c[j] exp(+/-i (k1 x(j) + k2 y[j])),
	            j=0
	                  for -ms/2 <= k1 <= (ms-1)/2, -mt/2 <= k2 <= (mt-1)/2

  Args:
    x     (float[nj]): nonuniform source x-coords, valid only in [-3pi,3pi]
    y     (float[nj]): nonuniform source y-coords, valid only in [-3pi,3pi]
    c     (complex[nj] or complex[nj,ntransf]): source strengths
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    ms    (int): number of Fourier modes in x-direction, may be even or odd;
        in either case the modes are integers lying in [-ms/2, (ms-1)/2]
    mt    (int): number of Fourier modes in y-direction, may be even or odd;
        in either case the modes are integers lying in [-mt/2, (mt-1)/2]

    f     (complex[ms,mt] or complex[ms,mt,ntransf]): output Fourier mode values. Should be initialized as a Fortran-ordered (ie ms fast, mt slow) numpy array of the correct size
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (prints spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    modeord (int, optional): 0 (CMCL increasing mode ordering), 1 (FFT ordering)
    chkbnds (int, optional): 0 (don't check NU points valid), 1 (do)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the f array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF,
       4 at least one NU point out of range (if chkbnds true)

  Example:
    see ``python/tests/accuracy_speed_tests.py``
  """
  # f is the output and must have dtype=np.complex128
  # check input x and c array, use c to detect ntransf
  x = _rchk(x)
  y = _rchk(y)
  c = _cchk(c)
  if c.ndim>1:
    assert c.ndim==2
    ntransf = c.shape[1]
  else:
    ntransf = 1
  assert c.shape[0]==x.size
  assert x.size*ntransf==c.size
  assert y.size*ntransf==c.size
  
  # check output f, if none _f is returned as output,
  # otherwise output is stored in f
  if f is None and c.ndim==2:
    _f = np.zeros([ms,mt,ntransf], dtype=np.complex128, order='F')
  elif f is None:
    _f = np.zeros([ms,mt], dtype=np.complex128, order='F')
  else:
    _f = _cchk(f)
  assert _f.size==ms*mt*ntransf
  assert _f.shape[0]==ms
  assert _f.shape[1]==mt
  assert _f.ndim==(c.ndim+1)
  if c.ndim==2:
    assert _f.shape[2]==c.shape[1]

  # number of input pts and modes info
  M = x.size
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = ms
  n_modes[1] = mt
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,y,None,c,isign,eps,None,None,None,_f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,1,2,n_modes,ntransf,M,0)

  # return _f if f is none else output is in f
  if f is None:
    return _f
  else:
    _copy(_f, f)
    return info

def nufft2d2(x,y,c,isign,eps,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """2D type-2 (aka forward) complex nonuniform fast Fourier transform

  ::

    c[j] =   SUM   f[k1,k2] exp(+/-i (k1 x[j] + k2 y[j])),  for j = 0,...,nj-1
	    k1,k2

    where sum is over -ms/2 <= k1 <= (ms-1)/2, -mt/2 <= k2 <= (mt-1)/2

  Args:
    x     (float[nj]): nonuniform target x-coords, valid only in [-3pi,3pi]
    y     (float[nj]): nonuniform target y-coords, valid only in [-3pi,3pi]
    c     (complex[nj] or complex[nj,ntransf]): output values at targets. Should be initialized as a
        numpy array of the correct size
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    f     (complex[ms,mt] or complex[ms,mt,ntransf]): Fourier mode coefficients, where ms and mt are
          either even or odd; in either case
	  their mode range is integers lying in [-m/2, (m-1)/2], with
	  mode ordering in all dimensions given by modeord.  Ordering is Fortran-style, ie ms fastest.
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (print spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    modeord (int, optional): 0 (CMCL increasing mode ordering), 1 (FFT ordering)
    chkbnds (int, optional): 0 (don't check NU points valid), 1 (do)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the c array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF,
       4 at least one NU point out of range (if chkbnds true)

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # c is the output and must have dtype=np.complex128
  # check input x and f array, use f to detect ntransf
  x = _rchk(x)
  y = _rchk(y)
  f = _cchk(f)
  if f.ndim>2:
    assert f.ndim==3
    ntransf = f.shape[2]
  else:
    assert f.ndim==2
    ntransf = 1
  
  ms = f.shape[0]
  mt = f.shape[1]
  M = x.size
  if c is None and f.ndim==3:
    _c = np.zeros([M,ntransf], dtype=np.complex128, order='F')
  elif c is None:
    _c = np.zeros([M], dtype=np.complex128, order='F')
  else:
    _c = _cchk(c)

  assert x.size*ntransf==_c.size
  assert y.size*ntransf==_c.size
  assert x.size==_c.shape[0]
  if f.ndim==3:
    assert f.shape[2]==_c.shape[1]

  # number of input pts and modes info
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = ms
  n_modes[1] = mt
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,y,None,_c,isign,eps,None,None,None,f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,2,2,n_modes,ntransf,M,0)

  # return _f if f is none else output is in f
  if c is None:
    return _c
  else:
    _copy(_c, c)
    return info

def nufft2d3(x,y,c,isign,eps,s,t,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """2D type-3 (NU-to-NU) complex nonuniform fast Fourier transform

  ::

             nj-1
    f[k]  =  SUM   c[j] exp(+-i s[k] x[j] + t[k] y[j]),  for k = 0,...,nk-1
             j=0

  Args:
    x     (float[nj]): nonuniform source point x-coords, in R
    y     (float[nj]): nonuniform source point y-coords, in R
    c     (complex[nj] or complex[nj,ntransf]): source strengths
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    s     (float[nk]): nonuniform target x-frequencies, in R
    t     (float[nk]): nonuniform target y-frequencies, in R
    f     (complex[nk] or complex[nk,ntransf]): output values at target frequencies.
       Should be initialized as a numpy array of the correct size
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (print spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the f array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # f is the output and must have dtype=np.complex128
  # check input x and c array, use c to detect ntransf
  x = _rchk(x)
  y = _rchk(y)
  c = _cchk(c)
  s = _rchk(s)
  t = _rchk(t)
  if c.ndim>1:
    assert c.ndim==2
    ntransf = c.shape[1]
  else:
    ntransf = 1
  assert x.size==c.shape[0]
  assert x.size*ntransf==c.size
  assert y.size*ntransf==c.size
  
  # check output f, if none _f is returned as output,
  # otherwise output is stored in f
  assert s.ndim==1
  assert t.ndim==1
  assert s.size==t.size
  nk=s.size
  if f is None and c.ndim==2:
    _f = np.zeros([nk,ntransf], dtype=np.complex128, order='F')
  elif f is None:
    _f = np.zeros([nk], dtype=np.complex128, order='F')
  else:
    _f = _cchk(f)
  assert _f.size==nk*ntransf
  assert _f.shape[0]==nk
  assert _f.ndim==c.ndim
  if c.ndim==2:
    assert _f.shape[1]==c.shape[1]

  # number of input pts and modes info
  M = x.size
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = nk
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,y,None,c,isign,eps,s,t,None,_f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,3,2,n_modes,ntransf,M,nk)

  # return _f if f is none else output is in f
  if f is None:
    return _f
  else:
    _copy(_f, f)
    return info

## 3D
def nufft3d1(x,y,z,c,isign,eps,ms,mt,mu,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """3D type-1 (aka adjoint) complex nonuniform fast Fourier transform

  ::

	           nj-1
    f(k1,k2,k3) =  SUM c[j] exp(+/-i (k1 x(j) + k2 y[j] + k3 z[j])),
	           j=0
       for -ms/2 <= k1 <= (ms-1)/2,
	   -mt/2 <= k2 <= (mt-1)/2,  -mu/2 <= k3 <= (mu-1)/2

  Args:
    x     (float[nj]): nonuniform source x-coords, valid only in [-3pi,3pi]
    y     (float[nj]): nonuniform source y-coords, valid only in [-3pi,3pi]
    z     (float[nj]): nonuniform source z-coords, valid only in [-3pi,3pi]
    c     (complex[nj] or complex[nj,ntransf]): source strengths
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    ms    (int): number of Fourier modes in x-direction, may be even or odd;
        in either case the modes are integers lying in [-ms/2, (ms-1)/2]
    mt    (int): number of Fourier modes in y-direction, may be even or odd;
        in either case the modes are integers lying in [-mt/2, (mt-1)/2]
    mu    (int): number of Fourier modes in z-direction, may be even or odd;
        in either case the modes are integers lying in [-mu/2, (mu-1)/2]

    f     (complex[ms,mt,mu] or complex[ms,mt,mu,ntransf]): output Fourier mode values. Should be initialized as a Fortran-ordered (ie ms fastest) numpy array of the correct size
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (prints spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    modeord (int, optional): 0 (CMCL increasing mode ordering), 1 (FFT ordering)
    chkbnds (int, optional): 0 (don't check NU points valid), 1 (do)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the f array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF,
       4 at least one NU point out of range (if chkbnds true)

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # f is the output and must have dtype=np.complex128
  # check input x and c array, use c to detect ntransf
  x = _rchk(x)
  y = _rchk(y)
  z = _rchk(z)
  c = _cchk(c)
  if c.ndim>1:
    assert c.ndim==2
    ntransf = c.shape[1]
  else:
    ntransf = 1
  assert x.size==c.shape[0]
  assert x.size*ntransf==c.size
  assert y.size*ntransf==c.size
  assert z.size*ntransf==c.size
  
  # check output f, if none _f is returned as output,
  # otherwise output is stored in f
  if f is None and c.ndim==2:
    _f = np.zeros([ms,mt,mu,ntransf], dtype=np.complex128, order='F')
  elif f is None:
    _f = np.zeros([ms,mt,mu], dtype=np.complex128, order='F')
  else:
    _f = _cchk(f)
  assert _f.size==ms*mt*mu*ntransf
  assert _f.shape[0]==ms
  assert _f.shape[1]==mt
  assert _f.shape[2]==mu
  assert _f.ndim==(c.ndim+2)
  if c.ndim==2:
    assert _f.shape[3]==c.shape[1]

  # number of input pts and modes info
  M = x.size
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = ms
  n_modes[1] = mt
  n_modes[2] = mu
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,y,z,c,isign,eps,None,None,None,_f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,1,3,n_modes,ntransf,M,0)

  # return _f if f is none else output is in f
  if f is None:
    return _f
  else:
    _copy(_f, f)
    return info

def nufft3d2(x,y,z,c,isign,eps,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """3D type-2 (aka forward) complex nonuniform fast Fourier transform

  ::

    c[j] =   SUM   f[k1,k2,k3] exp(+/-i (k1 x[j] + k2 y[j] + k3 z[j])).
	   k1,k2,k3
	             for j = 0,...,nj-1,  where sum is over
    -ms/2 <= k1 <= (ms-1)/2, -mt/2 <= k2 <= (mt-1)/2, -mu/2 <= k3 <= (mu-1)/2

  Args:
    x     (float[nj]): nonuniform target x-coords, valid only in [-3pi,3pi]
    y     (float[nj]): nonuniform target y-coords, valid only in [-3pi,3pi]
    z     (float[nj]): nonuniform target z-coords, valid only in [-3pi,3pi]
    c     (complex[nj] or complex[nj,ntransf]): output values at targets. Should be initialized as a
        numpy array of the correct size
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    f     (complex[ms,mt,mu] or complex[ms,mt,mu,ntransf]): Fourier mode coefficients, where ms, mt and mu
          are either even or odd; in either case
	  their mode range is integers lying in [-m/2, (m-1)/2], with
	  mode ordering in all dimensions given by modeord. Ordering is Fortran-style, ie ms fastest.
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (print spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    modeord (int, optional): 0 (CMCL increasing mode ordering), 1 (FFT ordering)
    chkbnds (int, optional): 0 (don't check NU points valid), 1 (do)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the c array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF,
       4 at least one NU point out of range (if chkbnds true)

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # c is the output and must have dtype=np.complex128
  # check input x and f array, use f to detect ntransf
  x = _rchk(x)
  y = _rchk(y)
  z = _rchk(z)
  f = _cchk(f)
  if f.ndim>3:
    assert f.ndim==4
    ntransf = f.shape[3]
  else:
    ntransf = 1
  
  ms = f.shape[0]
  mt = f.shape[1]
  mu = f.shape[2]
  M = x.size
  if c is None and f.ndim==4:
    _c = np.zeros([M,ntransf], dtype=np.complex128, order='F')
  elif c is None:
    _c = np.zeros([M], dtype=np.complex128, order='F')
  else:
    _c = _cchk(c)

  assert x.size*ntransf==_c.size
  assert y.size*ntransf==_c.size
  assert z.size*ntransf==_c.size
  assert x.size==_c.shape[0]
  if f.ndim==4:
    assert f.shape[3]==_c.shape[1]

  # number of input pts and modes info
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = ms
  n_modes[1] = mt
  n_modes[2] = mu
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,y,z,_c,isign,eps,None,None,None,f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,2,3,n_modes,ntransf,M,0)

  # return _f if f is none else output is in f
  if c is None:
    return _c
  else:
    _copy(_c, c)
    return info

def nufft3d3(x,y,z,c,isign,eps,s,t,u,f,debug=debug_def,spread_debug=spread_debug_def,spread_sort=spread_sort_def,fftw=fftw_def,modeord=modeord_def,chkbnds=chkbnds_def,upsampfac=upsampfac_def):
  """3D type-3 (NU-to-NU) complex nonuniform fast Fourier transform

  ::

             nj-1
    f[k]  =  SUM   c[j] exp(+-i s[k] x[j] + t[k] y[j] + u[k] z[j]),
             j=0
	                                               for k = 0,...,nk-1

  Args:
    x     (float[nj]): nonuniform source point x-coords, in R
    y     (float[nj]): nonuniform source point y-coords, in R
    z     (float[nj]): nonuniform source point z-coords, in R
    c     (complex[nj] or complex[nj,ntransf]): source strengths
    isign (int): if >=0, uses + sign in exponential, otherwise - sign
    eps   (float): precision requested (>1e-16)
    s     (float[nk]): nonuniform target x-frequencies, in R
    t     (float[nk]): nonuniform target y-frequencies, in R
    u     (float[nk]): nonuniform target z-frequencies, in R
    f     (complex[nk] or complex[nk,ntransf]): output values at target frequencies.
       Should be initialized as a numpy array of the correct size
    debug (int, optional): 0 (silent), 1 (print timing breakdown)
    spread_debug (int, optional): 0 (silent), 1, 2... (print spreader info)
    spread_sort (int, optional): 0 (don't sort NU pts in spreader), 1 (sort),
       2 (heuristic decision to sort)
    fftw (int, optional): 0 (use FFTW_ESTIMATE), 1 (use FFTW_MEASURE)
    upsampfac (float): either 2.0 (default), or 1.25 (low RAM & small FFT size)

  .. note::

    The output is written into the f array.

  Returns:
    int: 0 if success, 1 if eps too small,
       2 if size of arrays to malloc exceed MAX_NF

  Example:
    see ``python_tests/accuracy_speed_tests.py``
  """
  # f is the output and must have dtype=np.complex128
  # check input x and c array, use c to detect ntransf
  x = _rchk(x)
  y = _rchk(y)
  z = _rchk(z)
  c = _cchk(c)
  s = _rchk(s)
  t = _rchk(t)
  u = _rchk(u)
  if c.ndim>1:
    assert c.ndim==2
    ntransf = c.shape[1]
  else:
    ntransf = 1
  assert x.size==c.shape[0]
  assert x.size*ntransf==c.size
  assert y.size*ntransf==c.size
  assert z.size*ntransf==c.size
  
  # check output f, if none _f is returned as output,
  # otherwise output is stored in f
  assert s.ndim==1
  assert t.ndim==1
  assert u.ndim==1
  assert s.size==t.size
  assert t.size==u.size
  nk=s.size
  if f is None and c.ndim==2:
    _f = np.zeros([nk,ntransf], dtype=np.complex128, order='F')
  elif f is None:
    _f = np.zeros([nk], dtype=np.complex128, order='F')
  else:
    _f = _cchk(f)
  assert _f.size==nk*ntransf
  assert _f.shape[0]==nk
  assert _f.ndim==c.ndim
  if c.ndim==2:
    assert _f.shape[1]==c.shape[1]

  # number of input pts and modes info
  M = x.size
  n_modes = np.ones([3], dtype=np.int64)
  n_modes[0] = nk
  blksize = get_max_threads()

  # invoke guruinterface
  info = invoke_guru(x,y,z,c,isign,eps,s,t,u,_f,debug,spread_debug,spread_sort,fftw,modeord,chkbnds,upsampfac,3,3,n_modes,ntransf,M,nk)

  # return _f if f is none else output is in f
  if f is None:
    return _f
  else:
    _copy(_f, f)
    return info