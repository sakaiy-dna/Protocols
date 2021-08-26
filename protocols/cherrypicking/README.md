# Cherrypicking

### Author
Yusuke Sakai

## Categories
* Featured
	* Cherrypicking

## Description

Official Cherrypicking protocol is extended to use two different pipettes and used tipracks. Specify aspiration height, labware, pipette, as well as source and destination wells with this all inclusive cherrypicking protocol. You can add a mixing step of the source before the transfering, which allows you to make a cascade mixing in a single run.

![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Explanation of complex parameters below:

* `input .csv file`: Here, you should upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1211/example.csv), making sure to include headers in your csv file. Refer to our [Labware Library](https://labware.opentrons.com/?category=wellPlate) to copy API names for labware to include in the `Source Labware` and `Dest Labware` columns of the .csv.
* `Left Pipette Model`: Select which single channel pipette on left mount you will use for this protocol.
* `Right Pipette Model`: Select which single channel pipette on right mount you will use for this protocol.
* `Right Tipracks Start Slot (Slot 1-11)`: Specify starting slot of tipracks for right pipette to set the boarder between two pipettes.
* `Tip Type`: Specify whether you want to use filter tips.
* `Tip Usage Strategy`: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol.
* `Left Used Rack (1-96)`: Specify number of the tips in the first tiprack for the left pipette. The first rack is to be loaded on slot with youngest number.
* `Right Used Rack (1-96)`: Specify number of the tips in the first tiprack for the right pipette. The first rack is to be loaded on slot with youngest number.

---


### Labware
* Any verified labware found in our [Labware Library](https://labware.opentrons.com/?category=wellPlate)

### Pipettes
* [P20 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P300 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* [P1000 Single GEN2 Pipette](https://opentrons.com/pipettes/)
* P10 Single GEN1 Pipette
* P50 Single GEN1 Pipette
* P300 Single GEN1 Pipette
* P1000 Single GEN1 Pipette


---

### Deck Setup
* Example deck setup - All labwares including tip racks should be assigned manually.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/Screen+Shot+2021-04-29+at+3.10.02+PM.png)

---

### Protocol Steps
1. Pipette will mix a user-specified volume at the source labware and well according to the imported csv file. Slot of the labware and the aspirating postion from bottom of the well is also specified. If no volume is specified this step 1 is skipped. Specifying the mixing volume "0" pauses the robot at this step to enable user to mix the source manually.
2. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file. Slot is also specified, as well as aspiration height from the bottom of the well.
3. Pipette will dispense this volume into user-specified labware and well according to the imported csv file. Slot is also specified.
4. Steps 1 and 3 repeated over the duration of the CSV.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
The used tiprack should be put north-side-south to keep 'A1' filled for calibration. After cherrypicking completes, the robot will rearrange tips on the last tiprack to make either 'A1' or 'H12' filled for your next use.  
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
cherrypicking
