GDBUS_APPS = bmcctl \
	     hostwatchdog \
	     op-flasher \
	     op-pwrctl \
	     pwrbutton \
	     idbutton \
	     cable-led \
	     op-pwrctl-sthelens

SDBUS_APPS = gpu \
	     pex9797_ctl \
	     pmbus

SUBDIRS = hacks \
	  libopenbmc_intf \
	  libopenbmc_sdbus \
	  ledctl \
	  fanctl \
	  fan_tool \
	  pychassisctl \
	  pydownloadmgr \
	  pyeventctl \
	  pyfanctl \
	  pyflashbmc \
	  pyhwmon \
	  pyinventorymgr \
	  pyipmitest \
	  pysensormgr \
	  pystatemgr \
	  pysystemmgr \
	  pytools \
	  fan_algorithm \
	  info \
	  node-init-sthelens \
	  pybmchealth_ctl \
	  pybmclogevent_ctl \
	  gpu_utility

REVERSE_SUBDIRS = $(shell echo $(SUBDIRS) $(GDBUS_APPS) $(SDBUS_APPS) | tr ' ' '\n' | tac |tr '\n' ' ')

.PHONY: subdirs $(SUBDIRS) $(GDBUS_APPS) $(SDBUS_APPS)

subdirs: $(SUBDIRS) $(GDBUS_APPS) $(SDBUS_APPS)

$(SUBDIRS):
	$(MAKE) -C $@

$(GDBUS_APPS): libopenbmc_intf
	$(MAKE) -C $@ CFLAGS="-I ../$^" LDFLAGS="-L ../$^"

$(SDBUS_APPS): libopenbmc_sdbus
	$(MAKE) -C $@ CFLAGS="-I ../$^" LDFLAGS="-L ../$^"

$(GDBUS_APPS): pwrbutton
	$(MAKE) -C $@ LDFLAGS="-lpthread"

install: subdirs
	@for d in $(SUBDIRS) $(GDBUS_APPS) $(SDBUS_APPS); do \
		$(MAKE) -C $$d $@ DESTDIR=$(DESTDIR) PREFIX=$(PREFIX) || exit 1; \
	done
clean:
	@for d in $(REVERSE_SUBDIRS); do \
		$(MAKE) -C $$d $@ || exit 1; \
	done
