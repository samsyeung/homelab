# Enabling GPU P2P on 4× RTX 3090 / ASRock ROMED8-2T (AMD EPYC Rome)

Setup completed 2026-04-25. End result: BAR1 P2P over PCIe between all four
GPUs at ~50 GB/s bidirectional, ~1.2 µs latency.

## Hardware / starting state

- Motherboard: ASRock ROMED8-2T (single-socket EPYC Rome)
- GPUs: 4× RTX 3090, one per PCIe x16 slot, each on its own root complex
  (`0000:01`, `0000:46`, `0000:81`, `0000:c1`)
- OS: Ubuntu 24.04, kernel 6.17.0-20-generic
- Initial driver: NVIDIA 590.48.01 (proprietary closed module, apt/DKMS)
- Initial CUDA toolkit: 12.9 at `/usr/local/cuda-12.9`

`nvidia-smi topo -p2p r` reported **CNS** (Chipset Not Supported) — the closed
driver enforces a chipset whitelist that excludes consumer Ampere on AMD EPYC.

## Why each piece is needed

| Blocker | Fix |
|---|---|
| IOMMU in translated mode rewrites peer DMA addresses, blocking P2P | `iommu=pt` (passthrough — identity mapping) |
| ACS on root ports forces peer traffic through the CPU | `pci=noacs` |
| BAR1 too small (256 MiB) to expose full VRAM as a peer aperture | BIOS: Above 4G Decoding + Resizable BAR (yields 32 GiB BAR1) |
| Closed driver hardcodes a chipset whitelist that rejects EPYC consumer P2P | Replace with patched `aikitoria/open-gpu-kernel-modules` (geohot's P2P mod, updated for 595) |

## Steps

### 1. Kernel command line

Edit `/etc/default/grub`:

```
GRUB_CMDLINE_LINUX_DEFAULT="text iommu=pt pci=noacs"
```

Then `sudo update-grub && sudo reboot`. Verify with `cat /proc/cmdline`.

### 2. BIOS

Enable in UEFI:
- Advanced → PCI Subsystem Settings → **Above 4G Decoding: Enabled**
- Advanced → PCI Subsystem Settings → **Re-Size BAR Support: Enabled**
- Advanced → AMD CBS → NBIO → **PCIe ARI Support: Enabled**

After reboot, `lspci -vvs 0000:01:00.0` Region 1 should report `size=32G`
(was 256M before).

### 3. Purge the closed NVIDIA driver

Stop services holding GPU handles first:

```
sudo systemctl stop nvidia-persistenced nvitop-exporter
```

Then purge the apt-installed 590 stack:

```
sudo apt-get purge -y \
  libnvidia-cfg1-590 libnvidia-common-590 libnvidia-compute-590 \
  libnvidia-decode-590 libnvidia-encode-590 libnvidia-extra-590 \
  libnvidia-fbc1-590 libnvidia-gl-590 nvidia-compute-utils-590 \
  nvidia-dkms-590 nvidia-driver-590 nvidia-firmware-590-590.48.01 \
  nvidia-kernel-common-590 nvidia-kernel-source-590 nvidia-utils-590 \
  xserver-xorg-video-nvidia-590
```

apt will pull in `libnvidia-compute-535` as a placeholder dependency for
`nvidia-cuda-dev` / `python3-pynvml` / `libnvidia-ml-dev` / `libcuinj64-12.0`.
Harmless — gets shadowed by the .run installer's userspace.

### 4. Install matching NVIDIA userspace (no kernel modules)

```
wget https://us.download.nvidia.com/XFree86/Linux-x86_64/595.58.03/NVIDIA-Linux-x86_64-595.58.03.run
sudo sh NVIDIA-Linux-x86_64-595.58.03.run --no-kernel-modules --no-dkms --silent
```

This places `libcuda.so.595.58.03`, `libnvidia-ml.so.595.58.03`, `nvidia-smi`
etc. in `/usr/lib/x86_64-linux-gnu/` and `/usr/bin/`. Leaves the kernel side
alone for the patched modules.

### 5. Build and install the patched open kernel modules

Repo: `https://github.com/aikitoria/open-gpu-kernel-modules` — tracks NVIDIA
open-gpu-kernel-modules and applies the geohot/tinygrad P2P patch on top.

```
git clone https://github.com/aikitoria/open-gpu-kernel-modules
cd open-gpu-kernel-modules
git checkout 595.58.03-p2p   # must match the .run version exactly
./install.sh
```

`install.sh` does: `rmmod nvidia*` → `make modules` → `make modules_install`
→ `depmod` → `nvidia-smi`. Requires `linux-headers-$(uname -r)`.

If `rmmod` silently fails (refcount > 0), find and stop the holder:

```
sudo lsof /dev/nvidia*
```

Common offenders: `nvidia-persistenced`, `nvitop-exporter`, any running CUDA
process.

### 6. Clean up stale modprobe options

The closed-driver-era `/etc/modprobe.d/nvidia-p2p.conf` had registry-key
overrides like `DmaRemapPeerMmio`, `ForceP2P`, `RMForceP2PType`,
`GrdmaPciTopoCheckOverride`. None of these are recognised by the patched 595
open module — comment the line out or delete the file.

### 7. Reboot and verify

```
nvidia-smi topo -p2p r       # all OK (was CNS)
nvidia-smi topo -p2p w       # all OK
/usr/local/bin/p2pBandwidthLatencyTest
```

Expected results on this hardware:

| Metric | Disabled | Enabled |
|---|---|---|
| Unidirectional write | ~10.7 GB/s | ~25.9 GB/s |
| Bidirectional | ~16.2 GB/s | ~50.3 GB/s |
| Latency | ~14 µs | ~1.2 µs |

P2P atomics (`nvidia-smi topo -p2p n`) report **NS** — expected, BAR1 P2P on
consumer 3090s does not support peer atomics. NCCL collectives don't need it.

## Maintenance / gotchas

- **Driver upgrades**: when a newer NVIDIA release comes out, P2P breaks
  until aikitoria publishes a matching `-p2p` branch. Plan: don't blindly
  reinstall the closed driver. Pin/hold `nvidia-driver-*` in apt if needed.
- **Re-running `install.sh`** after a kernel upgrade rebuilds the modules
  against the new kernel headers. There is no DKMS hook here — you must do
  it manually.
- **`nvidia-persistenced` systemd unit** was provided by the purged
  `nvidia-compute-utils-590`. The .run installer ships the binary but no
  unit file. If desired, write `/etc/systemd/system/nvidia-persistenced.service`
  manually.
- **Required kernel cmdline persists across reboots** via grub config — but
  any future tool that rewrites `/etc/default/grub` must preserve
  `iommu=pt pci=noacs`.

## Reference

- aikitoria fork: https://github.com/aikitoria/open-gpu-kernel-modules
- Original tinygrad approach: https://github.com/tinygrad/open-gpu-kernel-modules/blob/550.54.15-p2p/README.md
