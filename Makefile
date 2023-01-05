DEBVERSION=0.2.10~1
VERSION=$(DEBVERSION)_all

all:

deb:
	cp debian/control.template debian/control
	echo "Version: $(DEBVERSION)" >> debian/control
	rm -f pymegacli-$(VERSION).deb

	-mkdir -p pymegacli-$(VERSION)/DEBIAN
	cp -vdp debian/* pymegacli-$(VERSION)/DEBIAN
	-mkdir -p pymegacli-$(VERSION)/usr/bin
	-mkdir -p pymegacli-$(VERSION)/usr/share/pymegacli
	-mkdir -p pymegacli-$(VERSION)/usr/share/doc/pymegacli
	cp -vdp *.py pymegacli-$(VERSION)/usr/share/pymegacli
	cp -vdp mcli pymegacli-$(VERSION)/usr/bin
	gzip -c debian/changelog > pymegacli-$(VERSION)/usr/share/doc/pymegacli/changelog-Debian.gz
	cp -dvp cron.d.example pymegacli-$(VERSION)/usr/share/doc/pymegacli/

	fakeroot dpkg-deb --build pymegacli-$(VERSION)
