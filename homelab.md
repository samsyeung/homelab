# Homelab hardware

My shopping list

| Component | Model | Notes |
| --- | --- | --- |
| Motherboard | [AsRock Romed8-2T](https://www.asrockrack.com/general/productdetail.asp?Model=ROMED8-2T#Specifications) | Chosen because it has 6 PCIe4.0x16 slots, the 7ths is split between OcuLink/M.2 |
| CPU | [EPYC 7532](https://en.wikipedia.org/wiki/Epyc#Second_generation_Epyc_(Rome)) | 32/64 core/theads, 256MB L3,  200W TDP, 2.4Ghz base clock, 3.3Ghz boost |
| Heatsink | Artic Freezer 4U SP3 | Well reviewed, and in practice running ambient + 30 under load |
| Memory | 8 x Kingston 9965754-053.C00G (32GB DDR4 ECC Reg 3200 MT/s) | For a total of 256GB of system memory |
| GPU | 4 x Nvidia RTX 3090 Founders Edition (part 2204-300-A1, 24GB GDDR6X) | Ebay and CEX |
| PCIe Riser cables | Cooler Master Riser Cable PCIe 4.0 x16 200mm | [PCIe 4.0 x16 to x16 90° riser, 200mm](https://www.amazon.co.uk/dp/B09GBFX5R7). I originally tried cheaper PCIe4.0 riser cables which caused many headaches! |
| Case | Open Air Mining Rig Frame (8 GPU, ATX) | [Thickened open chassis](https://www.amazon.co.uk/dp/B0CQJQV6V9) supporting ITX/Mini-ATX/ATX, holds up to 8 GPUs. GPUs mount on an elevated rail requiring PCIe riser cables to connect to the motherboard. |
| Rack | Tecmojo 20U Open Frame Server & AV Rack | [4-post mobile rack with casters](https://www.amazon.co.uk/dp/B0DBF9TK62), 2x 1U shelves, fits 19" servers and network gear. Replaced the original open-air GPU frame. |
| Power Supply | T.F.Skywindl 2000W modular | Marketed as Mining PSU.  It ony comes with 1 4+4pin CPU cable, so an extra one needed to be ordered as the motherboard has a 4+4 pin CPU and a separate 4 pin CPU power socket, that leaves 6 PCIe 8 (6+2) pin power cables for 3 power hungry GPUs.  Markings suggest it is rated for 1920W on +12V rail. Powers two GPUs and the motherboard. |
| Power Supply 2 | GameMax 850W Rampage | [Full-modular, 80 Plus Bronze, 88% efficiency](https://www.amazon.co.uk/dp/B0CJ9TFFF3). Powers the remaining two GPUs. |
| Extra Fans | 1 Noctua NF-A15 PWM, 4 x Artic P12 PWM | Noctua fan was used to replace the loud PSU fan, and 4 12cm Artic P12s were used to assist with moving hot exhaust air from CPU and GPUs |

My home lab was encouraged and inspired by [makerun/nerdbox](https://gitlab.com/makerun/nerdbox) . 

It was build primarily to setup and learn about AI.  

![home lab photo](assets/IMG_8307.jpg "Home Lab Photo")


