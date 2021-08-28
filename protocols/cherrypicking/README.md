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
* `Left First Rack Well`: Specify number of the tips in the first tiprack for the left pipette. The first rack is to be loaded on slot with youngest number.
* `Right First Rack Well`: Specify number of the tips in the first tiprack for the right pipette. The first rack is to be loaded on slot with youngest number.
* `Mode`: Specify preset of following advanced parameters, or select custom to specify details below.
* `Tip Usage Strategy (default = Always)`: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol. Mode overides this parameter.
* `Blow out threshold (default = 50)`: Specify the threshold in µL to blow out (higher) or pipetting (lower) at destination well. Mode overides this parameter.
* `Destination Pipetting Cycle (default = 1)`: Specify the cycle of pipetting in the destination well when the transfering volume is below blow out threshold. Mode overides this parameter.
* `Light Setting (default = Light On During Manual Process)`: Specify how you want to light deck. Mode overides this parameter.
* `Tip Type`: Specify whether you want to use filter tips. Mode overides this parameter.
* `Initial Verification (default = Yes)`: Specify if you run initial verification step before main protocol. This verify the last tip well parameters of installed pipette(s) and the right first tiprack slot (if used). Mode overides this parameter.
* `Profile (Text file)`: Here, you may upload profile text file to apply your custom parameters above, apart from right tipracks start slot, left first rack well, and right first rack well, those have to be specified everytime.

---


### Labware
* Any verified labware found in our [Labware Library](https://labware.opentrons.com/?category=wellPlate)
* You may use custom labwares by adding them to Opentrons.app. 
* If you use third-party tipracks, make sure to modify the tiprack map and tiplimit_map in the output protocol file correctly.

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
* Example deck setup - Source and destination labwares are assined automatically according to CSV file. The tipracks for left pipette fills remaining slot from youngest slot number. The tipracks for right pipette is loaded from manually specified slot.
![deck layout](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/Screen+Shot+2021-04-29+at+3.10.02+PM.png)

---

### Protocol Steps
1. Optional verification step picks up the LAST tip(s) from the FIRST tiprack(s) by installed pipette(s) to double-check the user input correct parameter and installed labwares to deck appropriately.
2. Pipette will mix a user-specified volume for 10 times at the source labware and well according to the imported csv file. Slot of the labware and the aspirating postion from bottom of the well is also specified. If no volume is specified this step 1 is skipped. Specifying the mixing volume "0" pauses the robot at this step to enable user to mix the source manually. If the mixing volume exceeded the largest installed pipette capacity, the mixing cycle is increased to get an equivalent circulation. 
3. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file. Slot, aspiration height from the bottom of the well are also specified. If the volume exceeds pipette capacity and user allows carryover, transfering volume is split into smaller volume.
4. Optionally, pipette will perform "touch tip" at the user-specified place in the source well to remove external droplet on tip.
5. Pipette will dispense the content into user-specified labware and well according to the imported csv file. Slot is also specified. Here, user can specify threshold to designate if the remainign liquid is blown out above or pipetted user-specified times in destination well. 
6. Optionally, pipette will perform "touch tip" at the user-specified place in the destination well to remove external droplet on tip.
7. If the user-specified transfering volume exceeds pipette capacity and user allows carryover, repeat steps 3-6 to complete transfer.
8. Steps 2 and 7 are repeated over the duration of the CSV.

### Process
1. Input your protocol parameters above.
2. Download your protocol and unzip if needed.
3. Upload your custom labware to the [OT App](https://opentrons.com/ot-app) by navigating to `More` > `Custom Labware` > `Add Labware`, and selecting your labware files (.json extensions) if needed.
4. Upload your protocol file (.py extension) to the [OT App](https://opentrons.com/ot-app) in the `Protocol` tab.
5. Set up your deck according to the deck map.
6. Calibrate your labware, tiprack and pipette using the OT App. For calibration tips, check out our [support articles](https://support.opentrons.com/en/collections/1559720-guide-for-getting-started-with-the-ot-2).
7. Hit 'Run'.

### Additional Notes
The used tiprack should be put north-side-south to keep 'A1' filled for labware calibration. After cherrypicking completes, the robot will rearrange tips on the last tiprack to make either 'A1' or 'H12' filled for your next use.  
Monitoring the robot behavior during initial verification phase is highly recommended to minimize human error of setup.   
If you have any questions about this protocol, please contact the Protocol Development Team by filling out the [Troubleshooting Survey](https://protocol-troubleshooting.paperform.co/).

###### Internal
cherrypicking
