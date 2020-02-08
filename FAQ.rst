Frequently asked questions and answers
======================================

What does "ValueError: Invalid field type <class 'cx_Oracle.LOB'>" mean?
------------------------------------------------------------------------

Fiona maps the built-in Python types to `field types of the OGR API <https://github.com/OSGeo/gdal/blob/master/gdal/ogr/ogr_core.h#L594-L611>`__ (``float`` to ``OFTReal``, etc.). Users may need to convert instances of other classes (like ``cx_Oracle.LOB``) to strings or bytes when writing data to new GIS datasets using fiona. 
