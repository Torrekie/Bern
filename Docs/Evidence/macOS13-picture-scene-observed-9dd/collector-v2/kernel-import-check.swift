import Darwin
var info = proc_bsdinfo()
let size = MemoryLayout<proc_bsdinfo>.stride
let result = proc_pidinfo(getpid(), PROC_PIDTBSDINFO, 0, &info, Int32(size))
let sec: UInt64 = info.pbi_start_tvsec
let usec: UInt64 = info.pbi_start_tvusec
