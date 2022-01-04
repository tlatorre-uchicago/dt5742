default: build

INSTALL=install

.DEFAULT:
	./setup.py $@

install:
	$(INSTALL) -d -o nginx -g nginx btl-testing /opt/btl-testing
	$(INSTALL) gunicorn.service /etc/systemd/system

.PHONY: install
