# Cherrypicking

### Author
Yusuke Sakai

## Categories
* Featured
	* Cherrypicking

## Description

Thoroughly customizable liquid handling protocol is derived from Official Cherrypicking protocol. Two different single channel pipettes can be installed to handle liquid according to CSV input, including mixing source before transfer, pipetting in destination, distributing to multiple destination at once, etc. It accepts one used tiprack per pipette, makes your life easier. CSV file will specify labware, slot, well by name of source and destination, heigth from bottom to aspirate, and transfering volume. The user can add source mixing step with specified volume (or pause for manual vortexing), which allows you to arrange a cascade mixing in a single run. For viscous samples, pipetting in destination for user-specified cycle at user-specified position from bottom, touch-tip at either or both source and destination can be optionally specified.

![Cherrypicking Example](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/cherrypicking/cherrypicking_example.png)

Explanation of complex parameters below:

* `input .csv file`: Here, you should upload a .csv file formatted in the [following way](https://opentrons-protocol-library-website.s3.amazonaws.com/custom-README-images/1211/example.csv), making sure to include headers in your csv file. Refer to our [Labware Library](https://labware.opentrons.com/?category=wellPlate) to copy API names for labware to include in the `Source Labware` and `Dest Labware` columns of the .csv. Custom labwares can be added here once your JSON file is stored in your Opentrons app.
* `Left Pipette Model`: Select which single channel pipette on left mount you will use for this protocol. (GEN1 is not tested)
* `Right Pipette Model`: Select which single channel pipette on right mount you will use for this protocol. (GEN1 is not tested)
* `Right Tipracks Start Slot (Slot 1-11)`: Specify starting slot of tipracks for right pipette to set the boarder between two types of tipracks.
* `Last Tip Well (Left)`: Specify well by name (`H12` if filled) of the tips in the first tiprack for the left pipette. The first rack is to be loaded on slot with youngest number.
* `Right Tip Well (Right)`: Specify well by name (`H12` if filled) of the tips in the first tiprack for the right pipette. The first rack is to be loaded on the specified slot as above.
* `Mode`: Specify preset of following advanced parameters, or select custom to specify details below.
* `Tip Usage Strategy (default = Always)`: Specify whether you'd like to use a new tip for each transfer, or keep the same tip throughout the protocol. `Once` automatically assesses if the tip is contaminated in both source (source change) and destination (pipetting or touch tip). `Mode` overides this parameter.
* `Blow Out Above Threshold (default = 100)`: Specify the threshold in µL for blowing out (higher) or pipetting (lower) at destination well. `Mode` overides this parameter. Specifying above pipette capacity forces pipetting everytime.
* `Blow Out Cycle (default = 2)`: How many times to repeat blow out, especially when you feel the official default is too weak. `Mode` overides this parameter.
* `Step Delay (default = 0)`: Specify in seconds if you want to wait a moment before blow out. It is also applied to short pause between aspirate to transfer. `Mode` overides this parameter. Consider if you handle viscous reagent.
* `Pipetting rate (default = 1)`:Specify the gloval rate of pipette, relative to official speed. `Mode` overides this parameter. You can control the value sample speficially by filling the option in the CSV file (highest priority). Consider if you handle viscous reagent.
* `Destination Pipetting Cycle (default = 2)`: Specify the cycle of pipetting in the destination well when the transfering volume is below the above-specified threshold. `Mode` overides this parameter. You can control the value sample speficially by filling the option in the CSV file (highest priority). Consider if you handle viscous reagent.
* `Light Setting (default = Light On During Manual Process)`: Specify how you want to light the deck. `Mode` overides this parameter.
* `Tip Type`: Specify whether you want to use filter tips. `Mode` overides this parameter. Third party tip is accepted though it needs edit `tiprack_map` in the protocol file.
* `Initial Verification (default = Yes)`: Specify if you run initial verification step (20 seconds) before main protocol. This verify the last tip well parameters of installed pipette(s) and the right first tiprack slot (if used), as well as the calibration of the first labware to minimize human error risk. `Mode` overides this parameter.
* `Destribute Above Trheshold (default = 1001)`: Specify the threshold in µL to allow distributing to multiple destination at once. In CSV rows above this volume, the protocol automatically assesses if the pipette tip is not contaminated and convert transfer to distibute. `Mode` overides this parameter. Specifying above pipette capacity forces the function inactive.
* `Return Destribute Disposal To Source (default = Yes)`: Specify if you'll return disposal volume to source after distirbute. `Mode` overides this parameter.
* `Destination History (default = Active)`: Specify if you allow pipetting and touch tip in new destination. It will useful to control `Tip Usage Strategy` = `Once` or Distribute.
* `Max Carryover Cycle (default = 5)`: Safety setting to specify maximum limit of carryover. `Mode` overides this parameter. It will be inactivated when the mode is set to debug mode or test mode.
* `Max Mix Cycle (default = 100)`: Safety setting to specify maximum limit of carryover. `Mode` overides this parameter. It will be inactivated when the mode is set to debug mode or test mode.
* `Drop Unused Pipette Tip (default = Yes)`: Safety setting to avoid contamination. Specify if you'll drop tip on the pipette when the other pipette is in use. `Mode` overides this parameter.
* `Profile (Text file)`: Here, you may upload profile text file to apply your preferences to specify parameters above. The profile file overide input values (including `mode`) above. Unspecified values, apart from right tipracks start slot, left first rack well, and right first rack well, those have to be specified everytime.

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

### Standard Protocol Steps
1. Optional verification step picks up the LAST tip(s) from the FIRST tiprack(s) by installed pipette(s) to double-check the user input correct parameter and installed labwares to deck appropriately.
2. Optionally, pipette will mix a user-specified volume for 10 times at the source labware and well according to the imported csv file. Slot of the labware and the aspirating postion from bottom of the well is also specified. If no value is specified, this step 1 is skipped. Specifying the mixing volume "0" pauses the robot at this step to enable user to mix the source manually. If the mixing volume exceeds the largest installed pipette capacity, the mixing cycle is multiplied to get an equivalent circulation. 
3. Pipette will aspirate a user-specified volume at the designated labware and well according to the imported csv file. Slot, aspiration height from the bottom of the well is also specified. If the volume exceeds pipette capacity and user allows carryover, transfering volume is split into smaller volume.
4. Optionally, pipette will perform "touch tip" at the user-specified place in the source well to remove external droplet on tip.
5. Pipette will dispense the content into user-specified labware and well according to the imported csv file. Slot is also specified. Here, user can specify threshold to designate if the remainign liquid is blown out above or pipetted user-specified times in destination well. 
6. Optionally, pipette will perform "touch tip" at the user-specified place in the destination well to remove external droplet on tip.
7. If the user-specified transfering volume exceeds pipette capacity and user allows carryover, repeat steps 3-6 to complete transfer.
8. Steps 2 and 7 are repeated over the duration of the CSV.

### Protocol Steps When Distribute Is Activated
1. Optional verification step picks up the LAST tip(s) from the FIRST tiprack(s) by installed pipette(s) to double-check the user input correct parameter and installed labwares to deck appropriately.
2. Optionally, pipette will mix a user-specified volume for 10 times at the source labware and well according to the imported csv file. Slot of the labware and the aspirating postion from bottom of the well is also specified. If no value is specified, this step 1 is skipped. Specifying the mixing volume "0" pauses the robot at this step to enable user to mix the source manually. If the mixing volume exceeds the largest installed pipette capacity, the mixing cycle is multiplied to get an equivalent circulation. 
3. In case the row of CSV file meets criteria, the transfering row is bundled as much as possible. Criteria: solusion is not contaminated, volume is within the range of pipette and all optional rows are consistent among bandled rows.
4. Pipette will aspirate a sum of user-specified volumes with additional disposal volume (minimum volume of pipette) at the designated labware and well according to the imported csv file. Slot, aspiration height from the bottom of the well is also specified.
5. Optionally, pipette will perform "touch tip" at the user-specified place in the source well to remove external droplet on tip.
6. Pipette will distribute the content into user-specified labwares and wells according to the imported csv file. Slots are also specified. Here, distirbute is allowed only when destination is new if the volume of the specific destination is below the `Blow Out Above Threshold`. The remaining volume in pipette is returend to source or disposed to trash bin as user specified.
7. Optionally, pipette will perform "touch tip" at the user-specified place in the destination well to remove external droplet on tip if the destination is new.
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
