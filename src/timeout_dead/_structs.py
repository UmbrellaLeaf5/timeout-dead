"""Windows API structures (ctypes)."""

import ctypes


class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
  _fields_ = [
    ("BasicLimitInformation", ctypes.c_ulonglong * 10),
    ("IoInfo", ctypes.c_ulonglong * 2),
    ("ProcessMemoryLimit", ctypes.c_size_t),
    ("JobMemoryLimit", ctypes.c_size_t),
    ("PeakProcessMemoryUsed", ctypes.c_size_t),
    ("PeakJobMemoryUsed", ctypes.c_size_t),
  ]
