cdef class Session:
    cdef void *cogr_ds
    cdef void *cogr_layer
    cdef object _fileencoding
    cdef object _encoding
    cdef object collection

cdef _deleteOgrFeature(void *cogr_feature)
