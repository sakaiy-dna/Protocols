metadata = {
    'protocolName': 'Extended Cherrypicking',
    'author': 'Yusuke Sakai <yusuke.sakai@riken.jp>',
    'source': 'Modified from Opentrons Cherrypicking',
    'apiLevel': '2.8'

}

def run(ctx):

    [left_pipette_type, right_pipette_type, tip_type, tip_reuse, transfer_csv, labware_names, left_tip_last, right_tip_last] = get_values(
        "left_pipette_type", "right_pipette_type", "tip_type", "tip_reuse",
        "transfer_csv", "labware_names","left_tip_last","right_tip_last")

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

    tiplimit_map = {
        'p10_single': {
            'standard': {
                'min': 1,
                'max': 10
            },
            'filter': {
                'min': 1,
                'max': 10
            }
        },
        'p50_single': {
            'standard': {
                'min': 5,
                'max': 50
            },
            'filter': {
                'min': 5,
                'max': 50
            }
        },
        'p300_single': {
            'standard': {
                'min': 30,
                'max': 300
            },
            'filter': {
                'min': 30,
                'max': 200
            }
        },
        'p1000_single': {
            'standard': {
                'min': 100,
                'max': 1000
            },
            'filter': {
                'min': 100,
                'max': 1000
            }
        },
        'p20_single_gen2': {
            'standard': {
                'min': 1,
                'max': 20
            },
            'filter': {
                'min': 1,
                'max': 20
            }
        },
        'p300_single_gen2': {
            'standard': {
                'min': 20,
                'max': 300
            },
            'filter': {
                'min': 20,
                'max': 200
            }
        },
        'p1000_single_gen2': {
            'standard': {
                'min': 100,
                'max': 1000
            },
            'filter': {
                'min': 100,
                'max': 1000
            }
        }
    }


    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]


    # load labware, call the labware by slot_contents[slot_num - 1]
    slot_num = 1
    slot_contents = []
    for installed_labware in labware_names:
        if not installed_labware == '' :
            slot_contents.append(ctx.load_labware(installed_labware, slot_num))
            slot_num += 1

    # load tipracks according to tiprack_map and all_values
    left_tipracks = []
    right_tipracks = []
    if not left_pipette_type == '' :
        for installed_labware , slot_load in zip(labware_names,slot_contents):
            if installed_labware == tiprack_map[left_pipette_type][tip_type]:
                left_tipracks.append(slot_load)
        left_tipracks = left_tipracks[1:] + left_tipracks[0:1]
    if not right_pipette_type == '' :   
        for installed_labware , slot_load in zip(labware_names,slot_contents):
            if installed_labware == tiprack_map[right_pipette_type][tip_type]:
                right_tipracks.append(slot_load)
        right_tipracks = right_tipracks[1:] + right_tipracks[0:1]

    # load pipettes
    if not left_pipette_type == "" :
        left_pipette = ctx.load_instrument(left_pipette_type, 'left', tip_racks=left_tipracks)
    if not right_pipette_type == "" : 
        right_pipette = ctx.load_instrument(right_pipette_type, 'right', tip_racks=right_tipracks)

    def converter96well(number):
        column_number = (number - 1) // 8 + 1
        row_text = 'ABCDEFGH'
        row_letter = row_text[ number % 8 - 1 ]
        well_position = row_letter + str(column_number)
        return well_position

    current_mount = ''
    def pipette (volume):
        nonlocal current_mount
        # In case only one pipette was installed.
        if left_pipette_type == '' :
            current_mount = 'right'
            return right_pipette     
        elif right_pipette_type == '' :
            current_mount = 'left'
            return left_pipette

        # In case left pipette is smaller (default)
        elif tiplimit_map[left_pipette_type][tip_type]['min'] < tiplimit_map[right_pipette_type][tip_type]['min']:
            if volume <= tiplimit_map[left_pipette_type][tip_type]['max'] :
                current_mount = 'left'
                return left_pipette
            elif volume < tiplimit_map[right_pipette_type][tip_type]['min'] :
                current_mount = 'left'
                return left_pipette
            else :
                current_mount = 'right'
                return right_pipette

        # In case left pipette is larger
        else :
            if volume <= tiplimit_map[right_pipette_type][tip_type]['max'] :
                current_mount = 'right'
                return right_pipette
            elif volume < tiplimit_map[left_pipette_type][tip_type]['min'] :
                current_mount = 'right'
                return right_pipette
            else :
                current_mount = 'left'
                return left_pipette

    left_tip_count = 0
    right_tip_count = 0
    if not left_pipette_type == '' :
        left_tip_last = int(left_tip_last)
        left_used_rack = True
        left_tip_max = ( len(left_tipracks) - 1 ) * 96 + left_tip_last
        left_first_tiprack = left_tipracks[len(left_tipracks) - 1:]
    if not right_pipette_type == '' :
        right_tip_last = int(right_tip_last)
        right_used_rack = True
        right_tip_max = ( len(right_tipracks) - 1 ) * 96 + right_tip_last
        right_first_tiprack = right_tipracks[len(right_tipracks) - 1:]

    def pick_up(volume):
        if not left_pipette_type == '' :
            nonlocal left_tip_count, left_used_rack, left_tip_max, left_tipracks, left_pipette
        if not right_pipette_type == '' :
            nonlocal right_tip_count, right_used_rack, right_tip_max, right_tipracks, right_pipette

        selected_pipette = pipette(volume)  # select pipette according to volume and get mount direction.

        # First used rack counting
        if current_mount == 'left' :
            # In case all the tipracks are empty
            if left_tip_count == left_tip_max :
                ctx.pause('Please refill tipracks for the left pipette before resuming.')
                selected_pipette.reset_tipracks()
                left_tip_count = 0
                left_tip_count += 1
                selected_pipette.pick_up_tip()
            # In case the used rack gets empty
            elif ( left_tip_count  < left_tip_last ) and left_used_rack :
                left_tip_count += 1
                tip_well = converter96well(left_tip_count)
                selected_pipette = pipette(volume)
                selected_pipette.pick_up_tip(left_first_tiprack[0][tip_well])
            # Other cases
            else :
                left_tip_count += 1
                selected_pipette.pick_up_tip()
            if ( left_tip_count == left_tip_last ) and left_used_rack :
                left_used_rack = False  # Secound round ignores last-tip fork for used rack.
        elif current_mount == 'right' :
            # In case all the tipracks are empty
            if right_tip_count == right_tip_max :
                ctx.pause('Please refill tipracks for the right pipette before resuming.')
                selected_pipette.reset_tipracks()
                right_tip_count = 0
                right_tip_count += 1
                selected_pipette.pick_up_tip()
            # In case the used rack gets empty
            elif ( right_tip_count  < right_tip_last ) and right_used_rack :
                right_tip_count += 1
                tip_well = converter96well(right_tip_count)
                selected_pipette = pipette(volume)
                selected_pipette.pick_up_tip(right_first_tiprack[0][tip_well])
            # Other cases
            else :
                right_tip_count += 1
                selected_pipette.pick_up_tip()
            if ( right_tip_count == right_tip_last ) and right_used_rack :
                right_used_rack = False  # Secound round ignores last-tip fork for used rack.

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    last_source = {'left':[],'right':[]}

    if tip_reuse == 'never':
        vol = int(transfer_info[0][7])
        selected_pipette = pipette (vol)
        pick_up(vol)
    for line in transfer_info:
        _, s_slot, s_well, h, _, d_slot, d_well, vol, mix = line[:9]
        source = ctx.loaded_labwares[
            int(s_slot)].wells_by_name()[parse_well(s_well)].bottom(float(h))
        dest = ctx.loaded_labwares[
            int(d_slot)].wells_by_name()[parse_well(d_well)]

        # Mix source solution before transfering
        if mix == '0' :  #In case of 0, pause and manual mixing will be added.
            ctx.pause('Please mix destination tubes manually, spin them down, and resume the robot.')
        elif not mix == '' :
            selected_pipette = pipette (float(mix))
            if selected_pipette.hw_pipette['has_tip']:
                if tip_reuse == 'always' :
                    selected_pipette.drop_tip()
                    pick_up(float(mix))
                elif tip_reuse == 'once' and not last_source[current_mount] == source : # Need to be tested.
                    selected_pipette.drop_tip()
                    pick_up(float(mix))
            else :
                pick_up(float(mix))
            selected_pipette.mix(10,float(mix),slot_contents[int(s_slot) - 1][s_well.upper()])
            selected_pipette.blow_out()
            last_source[current_mount] = source
            if tip_reuse == 'always':
                selected_pipette.drop_tip()
        # Main Transfer step
        selected_pipette = pipette (int(vol))
        if tip_reuse == 'once' and not last_source[current_mount] == source and selected_pipette.hw_pipette['has_tip']: # Need to be tested.
            selected_pipette.drop_tip()
        if not selected_pipette.hw_pipette['has_tip']:
            pick_up(int(vol))
        selected_pipette.transfer(float(vol), source, dest, new_tip='never',blow_out=True,blowout_location='destination well')
        last_source[current_mount] = source
        if tip_reuse == 'always':
            selected_pipette.drop_tip()
    if not left_pipette_type == "" :
        if left_pipette.hw_pipette['has_tip']:
            left_pipette.drop_tip()
    if not right_pipette_type == "" :
        if right_pipette.hw_pipette['has_tip']:
            right_pipette.drop_tip()

    # Rearrange remaining tips
    if left_used_rack :
        if left_tip_count > 96 - left_tip_last:
            for well_num in range (int(left_tip_last) + 1, 97) :
                left_pipette.pick_up_tip()
                left_pipette.drop_tip(left_first_tiprack[0][converter96well(well_num)])
        else :
            for well_num in range (1 , left_tip_count + 1) :
                left_pipette.pick_up_tip(left_first_tiprack[0][converter96well(left_tip_last - well_num + 1)])
                left_pipette.drop_tip(left_first_tiprack[0][converter96well(well_num)])

    if right_used_rack :
        if right_tip_count > 96 - right_tip_last:
            for well_num in range (int(right_tip_last) + 1, 97) :
                right_pipette.pick_up_tip()
                right_pipette.drop_tip(right_first_tiprack[0][converter96well(well_num)])
        else :
            for well_num in range (1 , right_tip_count + 1) :
                right_pipette.pick_up_tip(right_first_tiprack[0][converter96well(right_tip_last - well_num + 1)])
                right_pipette.drop_tip(right_first_tiprack[0][converter96well(well_num)])
