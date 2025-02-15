#!/bin/sh

workdir=~/homelab/prometheus
target=/etc/prometheus/prometheus.yml
cd $workdir

git pull

if cmp -s prometheus.yml $target; then
	echo "No changes"
else
	if promtool check config prometheus.yml; then
		echo "Prometheus config changed"
		( cp prometheus.yml $target && killall -HUP prometheus && echo Synced to $target and HUPed prometheus ) || echo Error syncing or hupping prometheus
		journalctl -u prometheus -n 10 --no-pager
	else
		echo "Prometheus config is broken"
	fi
fi

