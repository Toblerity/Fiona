RFC 0: Fiona RFC template
=========================

Request for comments: 0
Author: Sean Gillies, sean.gillies@gmail.com
Date: 2019-03-28
Obsoleted by: none
Obsoletes: none

## Abstract

This document is a template for future requests for comments (RFC).

## Introduction

Requests for comments (RFC) are more useful if they have consistent structure.
This document lays out the basic structure for project RFCs. It may be changed
by a future RFC.

## Details

RFCs are to be formatted using Markdown and kept under docs/rfc. RFC docs shall
be named like `0000-template.md`, `0001-the-next-rfc.md`, &c so that docs can
be easily sorted in order of creation.

A RFC shall have a title formatted like the one at the top of this template, 5
metadata fields (RFC number, author, date, obsoleted by, obsoletes), and 5
sections: abstract, introduction, implementation details, considerations, and
references. If the RFC does not make a previous RFC obsolete or has not been
made obsolete by a subsequent RFC, these metadata fields can be omitted.

## Considerations

This RFC has no compatibility or security considerations. If it did propose a
breaking change for the API or project access, that would be discussed here.

## References

This RFC template has no references, but if it did, they would be listed here.
