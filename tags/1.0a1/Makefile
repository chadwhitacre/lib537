# This Makefile is used to create an lib537 distribution. Before calling, set the
# VERSION environment variable.

VERSION=1.0a1
DATE=December 4, 2006

UPDATE_VERSION=sed -e 's/~~VERSION~~/$(VERSION)/g' -i ''
UPDATE_DATE=sed -e 's/~~DATE~~/$(DATE)/g' -i ''


clean:
# remove all of the cruft that gets auto-generated on doc/install/release
	rm -rf build
	rm -rf dist
	find . -name \*.pyc | xargs rm
	make -C doc/tex clean


# Target for building a distribution
# ==================================
# note the dependency on svneol: http://www.zetadev.com/svn/public/svneol/

stamp:
	$(UPDATE_VERSION) README
	$(UPDATE_VERSION) doc/tex/Makefile
	$(UPDATE_VERSION) doc/tex/lib537.tex
	$(UPDATE_VERSION) doc/tex/installation.tex
	$(UPDATE_VERSION) doc/HISTORY
	$(UPDATE_VERSION) setup.py
	$(UPDATE_VERSION) src/lib537/__init__.py

	$(UPDATE_DATE) doc/HISTORY
	$(UPDATE_DATE) doc/tex/lib537.tex

dist: clean
	mkdir dist
	mkdir dist/lib537-${VERSION}
	cp -r README \
	      src \
	      setup.py \
	      dist/lib537-${VERSION}

	make -C doc/tex all clean
	mkdir dist/lib537-${VERSION}/doc
	cp -r doc/html \
	      doc/lib537-${VERSION}.pdf \
	      doc/HISTORY \
	      dist/lib537-${VERSION}/doc

	tar --directory dist -zcf dist/lib537-${VERSION}.tgz lib537-${VERSION}
	tar --directory dist -jcf dist/lib537-${VERSION}.tbz lib537-${VERSION}

# ZIP archive gets different line endings
	svneol clean -w dist/lib537-${VERSION}
	cd dist && zip -9rq lib537-${VERSION}.zip lib537-${VERSION}
#	rm -rf dist/lib537-${VERSION}
