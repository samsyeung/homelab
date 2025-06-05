# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a homelab configuration repository containing monitoring infrastructure, service configurations, and documentation for a multi-node lab environment. The setup includes:

- **prometheus/**: Prometheus monitoring configuration with automatic config reload
- **go-tapo-exporter/**: Docker service for monitoring Tapo smart devices
- **resources/**: Systemd service files for various exporters (IPMI, NVIDIA, nvitop)
- **Hardware documentation**: Details about the EPYC-based server with dual RTX 3090s

## Network Architecture

The lab consists of multiple hosts across the yeungs.net domain:
- **lab.yeungs.net**: Main EPYC server (192.168.50.200)
- **lab2.yeungs.net**: Secondary lab machine  
- **proxmox.yeungs.net**: Proxmox hypervisor (192.168.50.135)
- **prometheus.yeungs.net**: Prometheus instance running in LXC
- **grafana.yeungs.net**: Grafana dashboard service

## Common Commands

### Prometheus Configuration
```bash
# Deploy and reload Prometheus config (run from prometheus LXC)
cd ~/homelab/prometheus
./pull_compare_reload.sh
```

This script:
1. Pulls latest config from git
2. Validates the config with `promtool check config`
3. Copies to `/etc/prometheus/prometheus.yml` if valid
4. Sends HUP signal to reload Prometheus

### Service Management
The repository includes systemd service files in `resources/` for:
- `ipmi_exporter.service`: IPMI hardware monitoring
- `nvidia-smi-startup.service`: NVIDIA GPU initialization
- `nvitop-exporter.service`: NVIDIA GPU metrics exporter

### Docker Services
Services are deployed using docker-compose. The go-tapo-exporter monitors TP-Link Tapo smart devices and exposes metrics on port 8086.

## Monitoring Stack

The monitoring setup scrapes metrics from:
- Node exporters (system metrics)
- NVIDIA GPU exporters (nvitop and nvidia_gpu_exporter)
- IPMI exporter (hardware health)
- Docker daemon metrics
- cAdvisor (container metrics)
- Home Assistant
- Grafana self-monitoring

All exporters feed into the central Prometheus instance which is visualized through Grafana dashboards.