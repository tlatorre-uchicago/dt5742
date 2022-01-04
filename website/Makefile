default: build

INSTALL=install

.DEFAULT:
	./setup.py $@

install:
	mkdir -p /opt/btl-testing
	rsync -a --chown=nginx:nginx . /opt/btl-testing
	$(INSTALL) gunicorn.service /etc/systemd/system
	$(INSTALL) nginx.conf /etc/nginx/conf.d/btl-testing.conf
	systemctl start gunicorn
	systemctl enable gunicorn

.PHONY: install
