#!/bin/sh

#lock gpu clock min,max
lgc=0,1600

#persistence mode 0 or 1
pm=1
for i in $(/usr/bin/nvidia-smi --query-gpu=index --format=csv,noheader,nounits); do
        /usr/bin/nvidia-smi -i $i -pm $pm
        /usr/bin/nvidia-smi -i $i -lgc $lgc
done