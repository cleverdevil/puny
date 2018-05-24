Puny: Pure-Python IndieWeb CMS
==============================

Puny is a [Python](http://www.python.org)-based project for building websites
for the [IndieWeb](https://www.indieweb.org). Puny implements:

* [Micropub](https://www.w3.org/TR/micropub/)
* [Micropub Media Endpoint](https://www.w3.org/TR/micropub/#media-endpoint)
* Content validation using [microformats2](https://github.com/cleverdevil/microformats2).

To use Puny, you'll need an [IndieAuth](https://indieweb.org/IndieAuth) server.
[PunyAuth](https://github.com/cleverdevil/punyauth) is a good choice!

Puny is very much in-progress at the moment, and was mostly written to help me
better understand Micropub, IndieAuth, microformats, and other IndieWeb building
blocks. I'd love it to eventually power my own (and many other) websites!

Implementation Details
----------------------

Puny makes use of:

* The [Pecan](http://www.pecanpy.org) Python web framework.
* [Mako](http://www.makotemplates.org) for templating.
* My [microformats2](https://github.com/cleverdevil/microformats2) library for
  validation and post type discovery.
* [Maya](https://github.com/kennethreitz/maya) for dealing with dates and times.
* [awesome-slugify](https://pypi.python.org/pypi/awesome-slugify) for slug gen.
* MySQL with JSON columns to store content.
* Amazon S3 for media uploads.

Project Status
--------------

Puny passes the vast majority of the [micropub.rocks](https://micropub.rocks)
test suite:

https://micropub.rocks/implementation-reports/servers/184/KD5Xbb6xfr5XRZsqwIvE

It renders some (though, not all) content, and has a very minimal timeline view.
