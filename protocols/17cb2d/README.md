# Plate Filling Master Mix in AB 384 Well Plate

### Author
[Opentrons](https://opentrons.com/)

## Categories
* Sample Prep
	* Plate Filling


## Description
This protocol fills [Applied Biosystems MicroAmp 384-well plates]([https://www.thermofisher.com/order/catalog/product/4343370#/4343370) with mastermix.</br>
</br>
The protocol can fill up to 9 plates and will dispense 7.5µL of mastermix 1 into all the odd rows (A/C/E...) and 7.5µL of mastermix 2 into all the even rows (B/D/F...).</br>
</br>
This protocol has been updated to use the GEN2 Multi-Channel Pipettes - please use corresponding tips.


---
![Materials Needed](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/materials.png)

To purchase tips, reagents, or pipettes, please visit our [online store](https://shop.opentrons.com/) or contact our sales team at [info@opentrons.com](mailto:info@opentrons.com)

* [Opentrons OT-2](https://shop.opentrons.com/collections/ot-2-robot/products/ot-2)
* [Opentrons OT-2 Run App (Version 3.19.0 or later)](https://opentrons.com/ot-app/)
* [Opentrons Multi-Channel Pipette](https://shop.opentrons.com/collections/ot-2-pipettes)
* [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)
* [USA Scientific 12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
* [Applied Biosystems MicroAmp 384-Well Plate](https://www.thermofisher.com/order/catalog/product/4343370#/4343370)
* Reagents (mastermix 1, mastermix 2)


---
![Setup](https://s3.amazonaws.com/opentrons-protocol-library-website/custom-README-images/001-General+Headings/Setup.png)

Slots 1 - 9: [Applied Biosystems MicroAmp 384-Well Plate](https://www.thermofisher.com/order/catalog/product/4343370#/4343370)

Slot 10: [Opentrons Tips](https://shop.opentrons.com/collections/opentrons-tips/products/opentrons-10ul-tips)

Slot 11: [USA Scientific 12-Well Reservoir](https://labware.opentrons.com/usascientific_12_reservoir_22ml?category=reservoir)
A1: Mastermix 1
A2: Mastermix 2

</br>
</br>
**Using the customizations field (below), set up your protocol.**
* **Pipette Type**: Select which GEN2 Multi-Channel Pipette (p300 or p20) will be used
* **Pipette Mount**: Select which mount (left or right) the Multi-Channel Pipette is attached to
* **Number of Plates (1-9)**: Specify the number of plates to fill



### Robot
* [OT-2](https://opentrons.com/ot-2)

## Process

1. Download your protocol. For help, please see [this article](https://support.opentrons.com/en/articles/3136506-using-labware-in-your-protocols).
2. Upload your protocol into the [OT App](https://opentrons.com/ot-app).
3. Set up your deck according to the deck map.
4. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
5. Hit "Run".

### Additional Notes
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
17cb2d