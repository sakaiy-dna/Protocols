metadata = {
    'protocolName': 'Extended Cherrypicking',
    'author': 'Yusuke Sakai <yusuke.sakai@riken.jp>',
    'source': 'Modified from Opentrons Cherrypicking',
    'apiLevel': '2.10'

}

def run(ctx):
    import math
    [left_pipette_type, right_pipette_type, tip_type, tip_reuse, transfer_csv, right_tipracks_start, left_tip_last_well, right_tip_last_well, mode, initial_verification, blowout_threshold, max_carryover, light_on, mix_after_cycle] = get_values(
        "left_pipette_type", "right_pipette_type", "tip_type", "tip_reuse",
        "transfer_csv", "right_tipracks_start","left_tip_last_well","right_tip_last_well","mode", "initial_verification", "blowout_threshold", "max_carryover", "light_on", "mix_after_cycle")

    # Mode overrides custom variables for pipetting rule, unless the mode is 'custom_mode'
    if mode == 'safe_mode' :
        tip_reuse = 'always'
        initial_verification = 'True'
        blowout_threshold = 1000    # One cycle of pipetting is always performed in destination well
        allow_carryover = 'False'
        mix_after_cycle = 2
    elif mode == 'simple_mode' :
        tip_reuse = 'once'
        initial_verification = 'False'
        blowout_threshold = 50     # Transfering 50 µL or less than 50 µL will be performed with a pipetting in destination well
        allow_carryover = 'True'
        mix_after_cycle = 1

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

    # load labware
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    for line in transfer_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[4:6]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                ctx.load_labware(lw.lower(), slot)

    # load tipracks to remaining empty slots. Used tack of each pipette is installed to slot with youngest number
    left_tipracks = []
    right_tipracks = []
    if not right_tipracks_start == 1 :
        for slot in range(1,right_tipracks_start) :
            if not int(slot) in ctx.loaded_labwares:
                left_tipracks.append(ctx.load_labware(tiprack_map[left_pipette_type][tip_type], str(slot)))
        left_tipracks = left_tipracks[1:] + left_tipracks[0:1]
    for slot in range(right_tipracks_start,12) :
        if not int(slot) in ctx.loaded_labwares:
            right_tipracks.append(ctx.load_labware(tiprack_map[right_pipette_type][tip_type], str(slot)))
    right_tipracks = right_tipracks[1:] + right_tipracks[0:1]

    # load pipettes
    pipette_name = {}
    if not left_pipette_type == "" :
        left_pipette = ctx.load_instrument(left_pipette_type, 'left', tip_racks=left_tipracks)
        pipette_name['left'] = left_pipette_type
    if not right_pipette_type == "" : 
        right_pipette = ctx.load_instrument(right_pipette_type, 'right', tip_racks=right_tipracks)
        pipette_name['right'] = right_pipette_type        

    def parse_well(well):
        letter = well[0]
        number = well[1:]
        return letter.upper() + str(int(number))

    def converter96well(number):
        column_number = (number - 1) // 8 + 1
        row_text = 'ABCDEFGH'
        row_letter = row_text[ number % 8 - 1 ]
        well_position = row_letter + str(column_number)
        return well_position

    def converter96well_invert(well):
        letter = well[0].upper()
        column = int(well[1:])
        row_text = 'ABCDEFGH'
        row_num = row_text.find(letter) + 1
        well_position_num = (column - 1) * 8 + row_num
        return well_position_num

    carryover = False
    current_mount = ''
    def pipette (volume):
        nonlocal current_mount, carryover
        carryover = False
        last_mount = current_mount
        # In case only one pipette was installed.
        if left_pipette_type == '' :
            current_mount = 'right'
            selected_pipette = right_pipette     
        elif right_pipette_type == '' :
            current_mount = 'left'
            selected_pipette = left_pipette

        # In case left pipette is smaller (default)
        elif tiplimit_map[left_pipette_type][tip_type]['min'] < tiplimit_map[right_pipette_type][tip_type]['min']:
            if volume <= tiplimit_map[left_pipette_type][tip_type]['max'] :
                current_mount = 'left'
                selected_pipette = left_pipette
            elif volume < tiplimit_map[right_pipette_type][tip_type]['min'] :
                current_mount = 'left'
                selected_pipette = left_pipette
                carryover = True
            elif volume <= tiplimit_map[right_pipette_type][tip_type]['max'] :
                current_mount = 'right'
                selected_pipette = right_pipette
            else :
                current_mount = 'right'
                selected_pipette = right_pipette
                carryover = True
        # In case left pipette is larger
        else :
            if volume <= tiplimit_map[right_pipette_type][tip_type]['max'] :
                current_mount = 'right'
                selected_pipette = right_pipette
            elif volume < tiplimit_map[left_pipette_type][tip_type]['min'] :
                current_mount = 'right'
                selected_pipette = right_pipette
                carryover = True
            elif volume <= tiplimit_map[left_pipette_type][tip_type]['max'] :
                current_mount = 'left'
                selected_pipette = left_pipette
            else :
                current_mount = 'left'
                selected_pipette = left_pipette
                carryover = True
        if mode == 'safe_mode' and not last_mount == current_mount : # In safe mode, dirty tip on not-selected pipette won't fly above labwares.
            last_mount = current_mount
            selected_pipette.drop_tip()
        return selected_pipette

    left_tip_count = 0
    right_tip_count = 0
    left_tip_last = converter96well_invert(left_tip_last_well)
    right_tip_last = converter96well_invert(right_tip_last_well)
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
                left_tip_count = 1
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


    def transfer(pipette,vol,source,dest,source_height,*,blow_out=False,max_carryover=5,mix_after=None,touchtip='',touchtip_d='',tip_replace=True) :
        # carryover assignment. mix_after is a tapple (mix cycle, mix volume). tip_replace specify if tip will be replaced during carryover.
        transfer_volume = [float(vol)]
        transfer_cycle = 1
        tip_dirty = False
        if tiplimit_map[pipette_name[current_mount]][tip_type]['max'] < float(vol) and max_carryover > 1 :
            transfer_cycle = math.ceil(float(vol)/tiplimit_map[pipette_name[current_mount]][tip_type]['max']) 
            transfer_unit_vol = math.ceil(float(vol)/transfer_cycle)
            transfer_volume[0] = transfer_volume[0] - (transfer_cycle - 1) * transfer_unit_vol
            for num in range(transfer_cycle - 1):
                transfer_volume.append(transfer_unit_vol)
            if transfer_cycle > max_carryover :
                ctx.comments('Too many carryover cycle is required. Install appropriate pipettes.')
        # transfering step
        for unit_vol in transfer_volume:
            if not pipette.has_tip:
                pick_up(float(vol))
            pipette.aspirate(volume=unit_vol,location=source.bottom(int(source_height)))
            if touchtip == 'both' or touchtip == 'before':
                pipette.touch_tip(location=source_well,v_offset=(-1*int(touchtip_d)))
            if bool(blow_out):
                pipette.dispense(volume=unit_vol,location=dest.top(-5))
                pipette.blow_out(location=dest.top(-5))
                pipette.blow_out(location=dest.top(-5))    #Blow out twice as official blow_out setting is too weak. Blow out is executed every transfering during carryover to avoid accumulating remainig liquid.
            else:
                pipette.dispense(volume=unit_vol,location=dest)
                tip_dirty = True
            if not mix_after == None:
                pipette.mix(mix_after[0],mix_after[1],dest)
                tip_dirty = True
            if touchtip == 'both' or touchtip == 'after':
                pipette.touch_tip(location=source_well,v_offset=(-1*int(touchtip_d)))
                tip_dirty = True
            if transfer_cycle > 1 and tip_dirty and tip_replace:  # replace tip if carryover occur and tip might be dirty
                pipette.drop_tip()

    # Test tiprack calibrations of both pipette (to avoid a rare gantry crane error and to confirm the position of the first tiprack for right pipette).
    if bool(initial_verification) :
        if bool(light_on) :
            ctx.set_rail_lights(True)
        if not left_pipette_type == '' :
            left_pipette.pick_up_tip(left_first_tiprack[0]['A1'])
            left_pipette.return_tip()
        if not right_pipette_type == '' :
            right_pipette.pick_up_tip(right_first_tiprack[0]['A1'])
            right_pipette.return_tip()
        ctx.pause('Resume OT-2 protocol once you confirm optimal calibration and the tips are picked up from the first rack(s) of individual pipette(s)')
        ctx.set_rail_lights(False)

    last_source = {'left':[],'right':[]}
    dest_history = []

    for line in transfer_info:
        _, s_slot, s_well, h, _, d_slot, d_well, vol, mix, touchtip, touchtip_d = line[:11]
        source = ctx.loaded_labwares[
            int(s_slot)].wells_by_name()[parse_well(s_well)]
        dest = ctx.loaded_labwares[
                    int(d_slot)].wells_by_name()[parse_well(d_well)]
        mix_cycle = 10

        # Mix source solution before transfering
        if mix == '0' :  #In case of 0, pause and manual mixing will be added.
            ctx.pause('Please mix destination tubes manually, spin them down, and resume the robot.')
        elif not mix == '' :
            selected_pipette = pipette (float(mix))
            mix_cycle = max(10, 10*round(float(mix)/tiplimit_map[pipette_name[current_mount]][tip_type]['max']))
            mix_volume = min(float(mix),tiplimit_map[pipette_name[current_mount]][tip_type]['max'])
            if selected_pipette.has_tip:
                if tip_reuse == 'always' :
                    selected_pipette.drop_tip()
                    pick_up(float(mix))
                elif tip_reuse == 'once' and not last_source[current_mount] == [s_slot,s_well] :
                    selected_pipette.drop_tip()
                    pick_up(mix_volume)
            else :
                pick_up(float(mix))
            selected_pipette.mix(mix_cycle,mix_volume,source.bottom(float(h)))
            selected_pipette.blow_out(source.top(-5))
            last_source[current_mount] = [s_slot,s_well]

        # Main Transfer step
        selected_pipette = pipette (float(vol))

        if selected_pipette.has_tip:
            if tip_reuse == 'always' :
                selected_pipette.drop_tip()
                pick_up(float(vol))
            elif tip_reuse == 'once' and not last_source[current_mount] == [s_slot,s_well] :
                selected_pipette.drop_tip()
                pick_up(float(vol))
            else :
                selected_pipette.blow_out(ctx.fixed_trash['A1'])
        else :
            pick_up(float(vol))

        last_source[current_mount] = [s_slot,s_well]    #This variable is to control drop_tip rule in tip_reuse=once case
        if not [d_slot,d_well] in dest_history:         #If destination well is clean
            if float(vol) < float(blowout_threshold) :     # The threshold should vary depending on solution viscosity etc.
                transfer(selected_pipette,float(vol),source,dest,h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False)
            else:
                transfer(selected_pipette,float(vol),source,dest,h,blow_out=True,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False)
        else:
            if float(vol) < float(blowout_threshold) :     # The threshold should vary depending on solution viscosity etc.
                transfer(selected_pipette,float(vol),source,dest,h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,mix_after=(mix_after_cycle,min([float(vol),tiplimit_map[pipette_name[current_mount]][tip_type]['max']])))
                last_source[current_mount] = ['tip','dipped']
            else:
                transfer(selected_pipette,float(vol),source,dest,h,blow_out=True,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d)
        if touchtip.lower() == 'both' or 'after':
            last_source[current_mount] = ['tip','touched']
        dest_history.append([d_slot,d_well])

    if not left_pipette_type == "" :
        if left_pipette.has_tip:
            left_pipette.drop_tip()
    if not right_pipette_type == "" :
        if right_pipette.has_tip:
            right_pipette.drop_tip()

    # Rearrange remaining tips in the first tipracks
    if left_used_rack :
        if left_tip_count > 96 - left_tip_last:
            for well_num in range (int(left_tip_last) + 1, 97) :
                left_pipette.pick_up_tip(left_first_tiprack[0][converter96well(left_tip_count + 97 - well_num)])
                left_pipette.drop_tip(left_first_tiprack[0][converter96well(well_num)])
        else :
            for well_num in range (1 , left_tip_count + 1) :
                left_pipette.pick_up_tip(left_first_tiprack[0][converter96well(left_tip_last - well_num + 1)])
                left_pipette.drop_tip(left_first_tiprack[0][converter96well(well_num)])
    if right_used_rack :
        if right_tip_count > 96 - right_tip_last:
            for well_num in range (int(right_tip_last) + 1, 97) :
                right_pipette.pick_up_tip(right_first_tiprack[0][converter96well(right_tip_count + 97 - well_num)])
                right_pipette.drop_tip(right_first_tiprack[0][converter96well(well_num)])
        else :
            for well_num in range (1 , right_tip_count + 1) :
                right_pipette.pick_up_tip(right_first_tiprack[0][converter96well(right_tip_last - well_num + 1)])
                right_pipette.drop_tip(right_first_tiprack[0][converter96well(well_num)])
    if bool(light_on) :
        ctx.set_rail_lights(True)
