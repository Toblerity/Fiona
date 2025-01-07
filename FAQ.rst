Frequently asked questions and answers
======================================

Can you add X format support in the Fiona wheels?
-------------------------------------------------

The short answer is no, unless the question is about a completely builtin format driver with no extra library dependencies.

The wheels on PyPI are already painfully big at 17-24 MB. Adding Xerces (for GML) and libkml, for example, increases the size
of wheels and encumbers everyone whether they use these formats or not. That's one reason why the answer is no. The other
reason is the expense of maintaining and updating Fiona's wheel building infrastructure. Unlike conda-forge, which is a
fiscally sponsored project of NumFOCUS, the Fiona project has no budget for building wheels. We're at the limit of what we
can do for free on volunteer time.

Can you publish Fiona wheels for new platform X?
------------------------------------------------

The short answer is not until there is free native CI for that platform. Even then, the project may be slow to add a new platform
to the existing matrix. As explained above, the project has no funding for building wheels.

What does "ValueError: Invalid field type <class 'cx_Oracle.LOB'>" mean?
------------------------------------------------------------------------

Fiona maps the built-in Python types to `field types of the OGR API <https://github.com/OSGeo/gdal/blob/master/gdal/ogr/ogr_core.h#L594-L611>`__ (``float`` to ``OFTReal``, etc.). Users may need to convert instances of other classes (like ``cx_Oracle.LOB``) to strings or bytes when writing data to new GIS datasets using fiona. 
