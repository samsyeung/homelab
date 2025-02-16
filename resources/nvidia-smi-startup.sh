#!/bin/sh
/usr/bin/nvidia-smi -i 0 -pm 1
/usr/bin/nvidia-smi -i 1 -pm 1
/usr/bin/nvidia-smi -i 0 -lgc 0,1600
/usr/bin/nvidia-smi -i 1 -lgc 0,1600
