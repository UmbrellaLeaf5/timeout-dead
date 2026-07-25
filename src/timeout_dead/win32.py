"""Windows platform detection and Job Object helpers."""

import ctypes
from ctypes.wintypes import HANDLE

from timeout_dead._structs import JOBOBJECT_EXTENDED_LIMIT_INFORMATION
from timeout_dead.constants import _Const


# MARK: Job Object (process tree force-kill)
# ------------------------------------------------


def create_kill_on_close_job() -> HANDLE | None:
  """Create a Windows Job Object that kills processes when the handle is closed."""

  if _Const.KERNEL32 is None:
    return None

  job = _Const.KERNEL32.CreateJobObjectW(None, None)

  if not job:
    return None

  info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
  info.BasicLimitInformation[1] = _Const.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

  ok = _Const.KERNEL32.SetInformationJobObject(
    job,
    _Const.JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
    ctypes.byref(info),
    ctypes.sizeof(info),
  )

  if not ok:
    _Const.KERNEL32.CloseHandle(job)

    return None

  return job


def assign_process_to_job(job: HANDLE, pid: int) -> bool:
  """Assign a process to a Windows Job Object."""

  if _Const.KERNEL32 is None:
    return False

  access = _Const.PROCESS_SET_QUOTA | _Const.PROCESS_TERMINATE
  proc_handle = _Const.KERNEL32.OpenProcess(access, False, pid)

  if not proc_handle:
    return False

  ok = _Const.KERNEL32.AssignProcessToJobObject(job, proc_handle)
  _Const.KERNEL32.CloseHandle(proc_handle)

  return bool(ok)


def close_job(job: HANDLE | None) -> None:
  """Close a Job Object handle, killing all processes in the job."""

  if job is not None and _Const.KERNEL32 is not None:
    _Const.KERNEL32.CloseHandle(job)
