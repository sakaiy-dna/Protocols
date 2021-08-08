metadata = {
    'protocolName': 'Cherrypicking',
    'author': 'Nick <protocols@opentrons.com>',
    'source': 'Custom Protocol Request',
    'apiLevel': '2.3'
}


def run(ctx):

    [left_pipette_type, right_pipette_type, tip_type,
     tip_reuse, right_pipette_tiprack, transfer_csv] = get_values(  # noqa: F821
        "left_pipette_type", "right_pipette_type", "tip_type", "tip_reuse", "rigth_pipette_tiprack
        "transfer_csv")

    tiprack_map = {
        'p10_single': {
            'standard': 'opentrons_96_tiprack_10ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p50_single': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p300_single': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        },
        'p20_single_gen2': {
            'standard': 'opentrons_96_tiprack_20ul',
            'filter': 'opentrons_96_filtertiprack_20ul'
        },
        'p300_single_gen2': {
            'standard': 'opentrons_96_tiprack_300ul',
            'filter': 'opentrons_96_filtertiprack_200ul'
        },
        'p1000_single_gen2': {
            'standard': 'opentrons_96_tiprack_1000ul',
            'filter': 'opentrons_96_filtertiprack_1000ul'
        }
    }

    # select labware
    
    
    
    
    
    # load labware
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    for line in transfer_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[4:6]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                ctx.load_labware(lw.lower(), slot)

    # load tipracks to slots from backward order for right pipette. Max slot = 11.
    tiprack_type = tiprack_map[right_pipette_type][tip_type]
    right_tipracks = []
    slot_start = 12 - right_pipette_tiprack
    for slot in range(slot_start, 13):
        if slot not in ctx.loaded_labwares:
            right_tipracks.append(ctx.load_labware(tiprack_type, str(slot)))
                
    # load tipracks for left pipette in remaining slots
    tiprack_type = tiprack_map[left_pipette_type][tip_type]
    left_tipracks = []
    for slot in range(1, 13):
        if slot not in ctx.loaded_labwares:
            left_tipracks.append(ctx.load_labware(tiprack_type, str(slot)))

    # load pipette
    left_pip = ctx.load_instrument(left_pipette_type, 'left', tip_racks=left_tipracks)
    right_pip = ctx.load_instrument(right_pipette_type, 'right', tip_racks=right_tipracks)

    left_tip_count = 0
    left_tip_max = len(left_tipracks*96)

    right_tip_count = 0
    right_tip_max = len(right_tipracks*96)

    def pick_up():
        nonlocal tip_count
        nonlocal tip_count
        if tip_count == tip_max:
            ctx.pause('Please refill tipracks for left pipette before resuming.')
            pip.reset_tipracks()
            tip_count = 0
        pip.pick_up_tip()
        tip_count += 1

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    if tip_reuse == 'never':
        pick_up()
    for line in transfer_info:
        _, s_slot, s_well, h, _, d_slot, d_well, vol = line[:8]
        source = ctx.loaded_labwares[
            int(s_slot)].wells_by_name()[parse_well(s_well)].bottom(float(h))
        dest = ctx.loaded_labwares[
            int(d_slot)].wells_by_name()[parse_well(d_well)]
        if tip_reuse == 'always':
            pick_up()
        pip.transfer(float(vol), source, dest, new_tip='never')
        if tip_reuse == 'always':
            pip.drop_tip()
    if pip.hw_pipette['has_tip']:
        pip.drop_tip()
