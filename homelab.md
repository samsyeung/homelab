# Homelab hardware

My shopping list

| Component | Model | Notes |
| --- | --- | --- |
| Motherboard | [AsRock Romed8-2T](https://www.asrockrack.com/general/productdetail.asp?Model=ROMED8-2T#Specifications) | Chosen because it has 6 PCIe4.0x16 slots, the 7ths is split between OcuLink/M.2 |
| CPU | [EPYC 7532](https://en.wikipedia.org/wiki/Epyc#Second_generation_Epyc_(Rome)) | 32/64 core/theads, 256MB L3,  200W TDP, 2.4Ghz base clock, 3.3Ghz boost |
| Heatsink | Artic Freezer 4U SP3 | Well reviewed, and in practice running ambient + 30 under load |
| Memory | 8 x Kingston DDR4 ECC Reg | For a total of 256GB of system memory |
| GPU | 2 x Nvidia RTX 3090 Founders Editition | Ebay and CEX |
| PCIe Riser cables | Coolermaster PCIe4 20cm Riser cables | I originally tried cheaper PCIe4.0 riser cables which caused many headaches! |
| Case | Ebay GPU Frame | Unlike open air PC cases, these require mounting GPUs on a elevated rail - so PCIe riser cables are used to connect them to the motherboard | 
| Power Supply | T.F.Skywindl 2000W modular | Marketed as Mining PSU.  It ony comes with 1 4+4pin CPU cable, so an extra one needed to be ordered as the motherboard has a 4+4 pin CPU and a separate 4 pin CPU power socket, that leaves 6 PCIe 8 (6+2) pin power cables for 3 power hungry GPUs.  Markings suggest it is rated for 1920W on +12V rail. |
| Extra Fans | 1 Noctua NF-A15 PWM, 4 x Artic P12 PWM | Noctua fan was used to replace the loud PSU fan, and 4 12cm Artic P12s were used to assist with moving hot exhaust air from CPU and GPUs |

My home lab was encouraged and inspired by [makerun/nerdbox](https://gitlab.com/makerun/nerdbox) . 

It was build primarily to setup and learn about AI.  

![home lab photo](assets/IMG_6425.jpg "Home Lab Photo")


