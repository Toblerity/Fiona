# String API functions.

cdef extern from "cpl_string.h":
    char ** CSLSetNameValue (char **list, char *name, char *value)
    void    CSLDestroy (char **list)
