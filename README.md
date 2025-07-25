# homelab

Inspired by [makerun/nerdbox](https://gitlab.com/makerun/nerdbox) , my [homelab](homelab.md) hosts a number of tools used for my personal learning and re-learning of things I used to have more time to do.

* [homelab.md](homelab.md) lists details of the hardware, and some lessons learned during its build.
* [os.md](os.md) list details of the operating system install (Ubuntu Desktop) and tuning.
* [lab_setup_notes](lab_setup_notes) a random collection of links for tools set up.

*__Note that these URLs are only accessible on my home network__*

# Lab services
Services hosted on lab.yeungs.net
* https://openwebui.lab.yeungs.net - openwebui Ollama UI
* https://portainer.lab.yeungs.net - portainer.io docker ui
* https://npm.lab.yeungs.net - Nginx Proxy Manager
* https://zonos.lab.yeungs.net - Zonos voice generator

# Proxmox mini pc
Services mostly LXCs using Helper-Scripts from https://tteck.github.io/Proxmox/
Services hosts on proxmox.yeungs.net
* https://proxmox.yeungs.net - Proxmox
* https://homeassistant.yeungs.net - Home assistant
* http://pihole.yeungs.net/admin - Pi Hole DNS on 192.168.50.135
* https://npm.yeungs.net - Nginx Proxy Manager for services
* http://prometheus.yeungs.net:9090 - Prometheus LXC - script in prometheus/pull_compare_reload.sh to activate new prometheus config
* https://grafana.yeungs.net - Grafana LXC
