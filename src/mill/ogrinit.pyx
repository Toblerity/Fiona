
import atexit

cdef extern from "ogr_api.h":
    void OGRRegisterAll()
    void OGRCleanupAll()

def cleanup():
    OGRCleanupAll()

atexit.register(cleanup)

OGRRegisterAll()

