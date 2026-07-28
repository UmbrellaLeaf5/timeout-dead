"""Windows API structures (ctypes)."""

import ctypes

from timeout_dead.constants import _Const


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
  _fields_ = [
    (
      _Const.STRUCT_BASIC_LIMIT_INFORMATION,
      ctypes.c_ulonglong * _Const.STRUCT_BASIC_LIMIT_INFORMATION_SIZE,
    ),
    (_Const.STRUCT_IO_INFO, ctypes.c_ulonglong * _Const.STRUCT_IO_INFO_SIZE),
    (_Const.STRUCT_PROCESS_MEMORY_LIMIT, ctypes.c_size_t),
    (_Const.STRUCT_JOB_MEMORY_LIMIT, ctypes.c_size_t),
    (_Const.STRUCT_PEAK_PROCESS_MEMORY_USED, ctypes.c_size_t),
    (_Const.STRUCT_PEAK_JOB_MEMORY_USED, ctypes.c_size_t),
  ]
