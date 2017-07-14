all: deb-build


# Install dependencies for generating a .deb package using stdeb
deb-bootstrap:
	apt-get install python-stdeb python-setuptools debhelper python-all fakeroot

# Generates a Debian package using stdeb
deb-build:
	@python setup.py sdist
	@py2dsc dist/bugsnag-*.tar.gz
	@cd deb_dist/bugsnag-* \
		&& dpkg-buildpackage -rfakeroot -uc -us
	@echo Generated $$(ls deb_dist/python-bugsnag_*_all.deb)
