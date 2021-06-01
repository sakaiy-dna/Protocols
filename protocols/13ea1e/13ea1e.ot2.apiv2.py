metadata = {
    'protodestName': 'Extraction Prep with Kingfisher Flex Extractor',
    'author': 'Rami Farawi <rami.farawi@opentrons.com>',
    'source': 'Custom Protodest Request',
    'apiLevel': '2.7'
}


def run(ctx):

    [num_samp, mix_reps, p300_mount, p1000_mount] = get_values(  # noqa: F821
        "num_samp", "mix_reps", "p300_mount", "p1000_mount")

    if not 0 <= num_samp <= 96:
        raise Exception("Enter a sample number between 1-96")

    # load labware
    reservoir = ctx.load_labware('nest_12_reservoir_15ml', '1')
    reservoir2 = ctx.load_labware('nest_12_reservoir_15ml', '2')
    npw4_block = ctx.load_labware('nest_96_wellplate_2200ul_flat', '3')
    sample_block = ctx.load_labware('nest_96_wellplate_2200ul_flat', '4')
    elution_block = ctx.load_labware('nest_96_wellplate_2200ul_flat', '5')
    ethanol_block = ctx.load_labware('nest_96_wellplate_2200ul_flat', '6')
    npw3_block = ctx.load_labware('nest_96_wellplate_2200ul_flat', '7')

    tiprack300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot)
                  for slot in ['9', '8']]
    tiprack1000 = [ctx.load_labware('opentrons_96_tiprack_1000ul', '10')]
    tuberack = ctx.load_labware(
            'opentrons_24_tuberack_1500ul', '11')

    # load instrument
    p1000 = ctx.load_instrument('p1000_single_gen2', p1000_mount,
                                tip_racks=tiprack1000)
    p300 = ctx.load_instrument('p300_multi_gen2', p300_mount,
                               tip_racks=tiprack300)

    num_channels_per_pickup = 1  # (only pickup tips on front-most channel)
    tips_ordered = [
        tip for rack in tiprack300
        for row in rack.rows()[
         len(rack.rows())-num_channels_per_pickup::-1*num_channels_per_pickup]
        for tip in row]
    tip_count = 0

    def pick_up(pip):
        nonlocal tip_count
        pip.pick_up_tip(tips_ordered[tip_count])
        tip_count += 1

    # reagents
    mag_beads = reservoir.rows()[0][:4]
    ethanol = reservoir.rows()[0][4:8]
    npw3 = reservoir.rows()[0][8:12]
    npw4 = reservoir2.rows()[0][:4]

    proteinase_k = tuberack.rows()[0][:2]
    ntc = tuberack.rows()[1][0]
    hsc = tuberack.rows()[2][0]
    elution_buffer = tuberack.rows()[3][:4]

    # add controls
    p1000.pick_up_tip()
    p1000.transfer(400, ntc, sample_block.wells()[0], new_tip='never')
    p1000.drop_tip()

    p1000.pick_up_tip()
    p1000.transfer(400, hsc, sample_block.wells()[1], new_tip='never')
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # add proteinase k and incubate for 15 minutes
    for s, d in zip(proteinase_k*num_samp, sample_block.wells()[:num_samp]):
        pick_up(p300)
        p300.aspirate(24, s)
        p300.dispense(24, d)
        p300.mix(mix_reps, 300, d)
        p300.drop_tip()
    ctx.delay(minutes=15)
    ctx.comment('\n\n\n\n\n')

    # add magnetic beads
    p1000.pick_up_tip()
    for mag_well, dest in zip(mag_beads*num_samp,
                              sample_block.wells()[:num_samp]):
        p1000.mix(5, 1000, mag_well)
        p1000.transfer(595, mag_well, dest.top(), new_tip='never')
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # make npw3, npw4 and ethanol npw3_block
    # ethanol
    p1000.pick_up_tip()
    for ethanol_well, dest in zip(ethanol*num_samp,
                                  ethanol_block.wells()[:num_samp]):
        p1000.transfer(600, ethanol_well, dest.top(), new_tip='never')
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # npw3
    p1000.pick_up_tip()
    for npw3_well, dest in zip(npw3*num_samp,
                               npw3_block.wells()[:num_samp]):
        p1000.transfer(600, npw3_well, dest.top(), new_tip='never')
    p1000.drop_tip()
    ctx.comment('\n\n\n\n\n')

    # npw4
    p1000.pick_up_tip()
    for npw4_well, dest in zip(npw4*num_samp, npw4_block.wells()[:num_samp]):
        p1000.transfer(600, npw4_well, dest.top(), new_tip='never')
    p1000.drop_tip()

    # elution buffer
    pick_up(p300)
    for elution_tubes, elution_well in zip(elution_buffer*num_samp,
                                           elution_block.wells()[:num_samp]):
        p300.aspirate(50, elution_tubes)
        p300.dispense(50, elution_well.top())
    p300.drop_tip()