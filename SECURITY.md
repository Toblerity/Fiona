# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.9.x   | :white_check_mark: |
| < 1.9   | :x:                |

## Reporting a Vulnerability

Fiona includes C extension modules that link [GDAL](https://gdal.org/), which in turn links a number of other libraries such as libgeos, libproj, and libcurl.
The exact list depends on the features included when GDAL is built and varies across distributions.

The Fiona project publishes binary wheels to the Python Package Index for 4 different platforms. The wheels contain 27-35 libraries.
The exact list depends on the platform and the versions of package managers and tooling used for each platform. Details can be found at https://github.com/sgillies/fiona-wheels.

To report a vulnerability in fiona or in one of the libraries that is included in a binary wheel on PyPI, please email sean.gillies@gmail.com.
In the case of a vulnerability in fiona code, please provide the kind of details we ask for in a GitHub issue.
In the case of a vulnerability in a dependency, please provide a link to a published CVE or other description of the issue.
Users will be notified at https://github.com/Toblerity/Fiona/discussions.
