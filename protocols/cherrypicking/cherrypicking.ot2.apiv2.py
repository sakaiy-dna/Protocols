metadata = {
    'protocolName': 'Extended Cherrypicking',
    'author': 'Yusuke Sakai <yusuke.sakai@riken.jp>',
    'source': 'Modified from Opentrons Cherrypicking',
    'apiLevel': '2.10'

}


def run(ctx):
    import math

    [transfer_csv, profile, mode] = get_values("transfer_csv","profile","mode")

    parameters = ["left_pipette_type", "right_pipette_type", "tip_type", "tip_reuse", "right_tipracks_start", "left_tip_last_well", "right_tip_last_well", "mode", "initial_verification", "blowout_threshold", "blowout_cycle", "max_carryover", "distribute_threshold", "light_on", "mix_after_cycle", "drop_dirtytip", "mix_cycle_limit"]

    mode_map = {
        'safe_mode':{
            'tip_reuse':'always',
            'initial_verification':True,
            'blowout_threshold':1000,
            'blowout_cycle':2,          # Twice of pipetting is always performed in destination well
            'allow_carryover':False,
            'mix_after_cycle':2,        # Pipetting cycle after dispensing to make sure all tip content is transfered to the destination.
            'drop_dirtytip':True,
            'distribute_threshold':1000,
            'mix_cycle_limit':100
        },
        'simple_mode':{
            'tip_reuse':'once',
            'initial_verification':False,
            'blowout_threshold':50,      # Transfering 50 µL or less than 50 µL will be performed with a pipetting in destination well
            'blowout_cycle':2,
            'allow_carryover':'True',
            'mix_after_cycle':1,
            'drop_dirtytip':False
            'distribute_threshold':1000,
            'mix_cycle_limit':100
        },
        'custom_mode':{
        },
        'debug_mode':{                   # This mode remove safety lines (script lines to return error during simulation phase) allows user to read detail comments to find error.
        'safety_line':False,
        'detail_comment':True
        }
    }

    default_dict={'safety_line':True,'detail_comment':False}

    parameter_dict = {}
    for name in parameters:
        parameter_dict[name]=get_values(name)[0]

    # Profile overides mode and other parameters apart from right/left last_tip_well and right tipracks start
    profile_dict = {}
    if not profile == 'No Profile' :
        for line in profile.splitlines() :
            profile_dict[line.split(':')[0]] = line.split(':')[1]

    parameter_dict.update(default_dict)     # default values are applied
    parameter_dict.update(mode_map[mode])   # mode setting has priority than individual parameter or default values
    parameter_dict.update(profile_dict)     # user specified profile has priority than other setting

    globals().update(parameter_dict)

    # here last tip wells and start slot should be here.
    tip_last_well={'left':left_tip_last_well,'right':right_tip_last_well}

    light_map = {       # During initialization, during run, during pause, after run
        'always_on':(True,True,True,True),
        'start_end':(True,False,False,True),
        'start_only':(True,False,False,False),
        'run_off':(True,False,True,True),
        'always_off':(False,False,False,False)
    }

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
    OT2_state = {'name':{},'mount':'','last_mount':'','tipracks':{'left':[],'right':[]}}
    if not right_tipracks_start == 1 :
        for slot in range(1,right_tipracks_start) :
            if not int(slot) in ctx.loaded_labwares:
                OT2_state['tipracks']['left'].append(ctx.load_labware(tiprack_map[left_pipette_type][tip_type], str(slot)))
        OT2_state['tipracks']['left'] = OT2_state['tipracks']['left'][1:] + OT2_state['tipracks']['left'][0:1]
    for slot in range(right_tipracks_start,12) :
        if not int(slot) in ctx.loaded_labwares:
            OT2_state['tipracks']['right'].append(ctx.load_labware(tiprack_map[right_pipette_type][tip_type], str(slot)))
    OT2_state['tipracks']['right'] = OT2_state['tipracks']['right'][1:] + OT2_state['tipracks']['right'][0:1]

    # load pipettes
    if not left_pipette_type == '' :
        OT2_state['left'] = ctx.load_instrument(left_pipette_type, 'left', tip_racks=OT2_state['tipracks']['left'])
        OT2_state['name']['left'] = left_pipette_type
    if not right_pipette_type == '' :
        OT2_state['right'] = ctx.load_instrument(right_pipette_type, 'right', tip_racks=OT2_state['tipracks']['right'])
        OT2_state['name']['right'] = right_pipette_type        

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


    OT2_state['tip_count'] = {'left':0,'right':0}
    OT2_state['tip_last'] = {}
    OT2_state['used_rack'] = {}
    OT2_state['tip_max'] = {}
    OT2_state['first_tiprack'] = {}
    OT2_state['max'] = {}
    OT2_state['min'] = {}
    for hand in OT2_state['name'].keys():
        OT2_state['tip_last'][hand] = converter96well_invert(tip_last_well[hand])
        OT2_state['used_rack'][hand] = True
        OT2_state['tip_max'][hand] = ( len(OT2_state['tipracks'][hand]) - 1 ) * 96 + OT2_state['tip_last'][hand]
        OT2_state['first_tiprack'][hand] = OT2_state['tipracks'][hand][len(OT2_state['tipracks'][hand]) - 1:]
        OT2_state['max'][hand] = tiplimit_map[OT2_state['name'][hand]][tip_type]['max']
        OT2_state['min'][hand] = tiplimit_map[OT2_state['name'][hand]][tip_type]['min']


    def select_mount (volume):
        current_state = OT2_state
        current_state['carryover'] = False

        # In case only one pipette was installed.
        if len(current_state['name']) == 1:
            for hand in current_state['name'].keys():
                current_state['mount'] = hand
            if float(volume) > current_state['max'][current_state['mount']]:
                current_state['carryover'] = True

        # In case left pipette is smaller (default)
        elif tiplimit_map[left_pipette_type][tip_type]['min'] < tiplimit_map[right_pipette_type][tip_type]['min']:
            if volume <= tiplimit_map[left_pipette_type][tip_type]['max'] :
                current_state['mount'] = 'left'
            elif volume < tiplimit_map[right_pipette_type][tip_type]['min'] :
                current_state['mount'] = 'left'
                current_state['carryover'] = True
            elif volume <= tiplimit_map[right_pipette_type][tip_type]['max'] :
                current_state['mount'] = 'right'
            else :
                current_state['mount'] = 'right'
                current_state['carryover'] = True
        # In case left pipette is larger
        else :
            if volume <= tiplimit_map[right_pipette_type][tip_type]['max'] :
                current_state['mount'] = 'right'
            elif volume < tiplimit_map[left_pipette_type][tip_type]['min'] :
                current_state['mount'] = 'right'
                current_state['carryover'] = True
            elif volume <= tiplimit_map[left_pipette_type][tip_type]['max'] :
                current_state['mount'] = 'left'
            else :
                current_state['mount'] = 'left'
                current_state['carryover'] = True
        if not current_state['mount'] == current_state['last_mount']: # Dirty tip on not-selected pipette won't fly above labwares if user specifiy.
            if detail_comment:
                ctx.comment('Debug: ' + current_state['mount'] + ' pipette is selected.')
            if current_state[current_state['mount']].has_tip and drop_dirtytip: #bool(drop_dirtytip) and
                current_state['pipette'].drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Dirty tip on ' + last_mount + ' pipette is dropped into trash.')
        current_state['pipette'] = current_state[current_state['mount']]      # Update pipette object with current mount.
        current_state['last_mount'] = current_state['mount']
        return current_state
        
    def pick_up(state):
        # First used rack counting
        for hand in state['name'].keys():
            if OT2_state['mount'] == hand :
                # In case all the tipracks are empty
                if state['tip_count'][hand] == OT2_state['tip_max'][hand] :
                    ctx.pause('Please refill tipracks for the ' + hand + ' pipette before resuming.')
                    if bool(initial_verification) :
                        ctx.set_rail_lights(light_map[light_on][0])
                        state['pipette'].pick_up_tip(state['first_tiprack'][hand][0]['A1'])
                        if detail_comment:
                            ctx.comment('Tiprack verification step: The ' + hand + ' pipette will pick up a tip from the first tiprack.')
                        state['pipette'].return_tip()
                        ctx.set_rail_lights(light_map[light_on][2])
                        ctx.pause('Resume OT-2 once you confirm the first tip(s) are picked up from the first tiprack(s) by individual pipette(s)')
                    state['pipette'].reset_tipracks()
                    state['tip_count'][hand] = 1
                    state['pipette'].pick_up_tip()
                # In case the first tiprack gets empty
                elif ( state['tip_count'][hand]  < state['tip_last'][hand] ) and state['used_rack'][hand] :
                    state['tip_count'][hand] += 1
                    tip_well = converter96well(state['tip_count'][hand])
                    state['pipette'].pick_up_tip(state['first_tiprack'][hand][0][tip_well])
                # Other cases
                else :
                    state['tip_count'][hand] += 1
                    state['pipette'].pick_up_tip()
                if ( state['tip_count'][hand] == state['tip_last'][hand] ) and OT2_state['used_rack'][hand] :
                    OT2_state['used_rack'][hand] = False  # Secound round ignores last-tip fork for used rack.
                    if detail_comment:
                        ctx.comment('Debug: ' + hand + ' first tiprack is empty. Tip rearrangement step for this tiprack will be skipped.')
        return state

    def transfer(vol,source,dest,source_height,*,blow_out=False,max_carryover=5,mix_after=None,touchtip='',touchtip_d=5,tip_replace=True, blowout_cycle=2) :
        # carryover assignment. mix_after is a tapple (mix cycle, mix volume). tip_replace specify if tip will be replaced during carryover.
        nonlocal OT2_state  # nonlocal外したかったんだが...
        transfer_volume = [float(vol)]
        transfer_cycle = 1
        tip_dirty = False
        if touchtip_d == '':
            touchtip_d = 5
        if OT2_state['max'][OT2_state['mount']] < float(vol) and max_carryover > 1 :  # APIから呼び出せるなら呼び出したい
            transfer_cycle = math.ceil(float(vol)/OT2_state['max'][OT2_state['mount']])
            if transfer_cycle > max_carryover:
                ctx.comment('WARNING: Too many carryover cycles:' + str(transfer_cycle) + ' are required. Install appropriate pipettes or modify configurations.')
            if safety_line :
                transfer_cycle = min (transfer_cycle,int(max_carryover))    # If carryover is more than user specificed carryover limit, the protocol will return error before run.
            transfer_unit_vol = math.ceil(float(vol)/transfer_cycle)
            transfer_volume[0] = transfer_volume[0] - (transfer_cycle - 1) * transfer_unit_vol
            for num in range(transfer_cycle - 1):
                transfer_volume.append(transfer_unit_vol)
            if detail_comment:
                ctx.comment('Debug: Carryover happend to transfer ' + str(vol) + ' µL. The transfer volume is split into ' + str(transfer_volume) + '.')
        # transfering step
        for unit_vol in transfer_volume:
            if not OT2_state['pipette'].has_tip:
                OT2_state = pick_up(OT2_state)
            OT2_state['pipette'].aspirate(volume=unit_vol,location=source.bottom(int(source_height)))
            if touchtip == 'both' or touchtip == 'before':
                OT2_state['pipette'].touch_tip(location=source,v_offset=(-1*int(touchtip_d)))
            if bool(blow_out):      # Dispense to destination well from above or at the bottom of the well.
                OT2_state['pipette'].dispense(volume=unit_vol,location=dest.top(-5))
            else: 
                OT2_state['pipette'].dispense(volume=unit_vol,location=dest)
                tip_dirty = True
                if detail_comment:
                    ctx.comment('Debug: Tip is dipping into destination well.')
            if not mix_after == None:   # If mix_after is specified...
                OT2_state['pipette'].mix(mix_after[0],mix_after[1],dest)
                tip_dirty = True
                if detail_comment:
                    ctx.comment('Debug: Tip is used for pipetting in destination well.')
            for i in range (blowout_cycle) :
                OT2_state['pipette'].blow_out(location=dest.top(-5))    #Blow out user specified times (default = 2), as official blow_out setting is too weak. Blow out is executed every transfering movement including carryover to avoid accumulating remainig liquid.
            if touchtip == 'both' or touchtip == 'after':
                OT2_state['pipette'].touch_tip(location=dest,v_offset=(-1*int(touchtip_d)))
                tip_dirty = True
                if detail_comment:
                    ctx.comment('Debug: Tip touched the wall of destination well.')
            if transfer_cycle > 1 and tip_dirty and tip_replace and not tip_reuse == 'never':  # replace tip if carryover occur and tip might be dirty
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced during a set of carryover process everytime the since tip might be contaminated.')
                OT2_state['pipette'].drop_tip()

    # Initial verification phase
    if bool(initial_verification) :
        if detail_comment:
            ctx.comment('Initial verification phase: Testing tiprack calibration of both pipettes (to avoid a rare gantry crane error and to double-check the configurations of the first tipracks for both pipettes).')
        ctx.set_rail_lights(light_map[light_on][0])
        for hand in OT2_state['name'].keys():
            OT2_state[hand].pick_up_tip(OT2_state['first_tiprack'][hand][0][parse_well(tip_last_well[hand])])
            OT2_state[hand].return_tip()
        ctx.set_rail_lights(light_map[light_on][2])
        ctx.pause('Resume OT-2 protocol once you confirm optimal calibration of installed pipette(s) and the last tip(s) are picked up from the first rack(s) by individual pipette(s)')

    last_source = {'left':[],'right':[]}
    dest_history = []
    if detail_comment:
        ctx.comment('Debug: Source cashe and destination history are initialized')

    ctx.set_rail_lights(light_map[light_on][1])
    for line in transfer_info:
        _, s_slot, s_well, h, _, d_slot, d_well, vol, mix, touchtip, touchtip_d = line[:11]
        source = ctx.loaded_labwares[
            int(s_slot)].wells_by_name()[parse_well(s_well)]
        dest = ctx.loaded_labwares[
                    int(d_slot)].wells_by_name()[parse_well(d_well)]
        mix_cycle = 10     # Default mixing cycle is 10.

        # Mix source solution before transfering
        if mix == '0' :  #In case of 0, pause and manual mixing will be added.
            ctx.set_rail_lights(light_map[light_on][2])
            ctx.pause('Please mix destination tubes manually, spin them down, and resume the robot.')
            ctx.set_rail_lights(light_map[light_on][1])
        elif not mix == '' :
            OT2_state = select_mount(float(mix))
            mix_cycle = max(10, round(10*float(mix)/OT2_state['max'][OT2_state['mount']]))
            mix_volume = min(float(mix),OT2_state['max'][OT2_state['mount']])
            if mix_cycle > mix_cycle_limit:
                ctx.comment('WARNING: Too many mixing cycle (' + str(mix_cycle) + ' cycles) is required to mix source well:' + s_well + ' in Slot ' + s_slot +'. Consider to pause OT-2 to vortex manually (input "0" in the mix configuration column of CSV file) as a faster option or install appropriate pipettes.') 
                if safety_line :
                    mix_volume = float(mix) # If mix cycle is more than user specificed limit, the protocol will return error before run.
            if OT2_state['pipette'].has_tip:
                if tip_reuse == 'always' :
                    OT2_state['pipette'].drop_tip()
                    if detail_comment:
                        ctx.comment('Debug: Tip is replaced before mixing as tip_reuse rule is "always"')
                    OT2_state = pick_up(OT2_state)
                elif tip_reuse == 'once' and not last_source[OT2_state['mount']] == [s_slot,s_well] and not last_source[OT2_state['mount']] == []:
                    if detail_comment:
                        ctx.comment('Debug: Tip is replaced before mixing since the source well changed (or the tip is contaminated in destination well).')
                    selected_pipette.drop_tip()
                    OT2_state = pick_up(OT2_state)
            else :
                OT2_state = pick_up(OT2_state)
            OT2_state['pipette'].mix(mix_cycle,mix_volume,source.bottom(float(h)))
            for i in range (int(blowout_cycle)) : 
                OT2_state['pipette'].blow_out(source.top(-5))
            last_source[OT2_state['mount']] = [s_slot,s_well]

        # Main Transfer step
        OT2_state = select_mount(float(vol))

        if OT2_state['pipette'].has_tip:
            if tip_reuse == 'always' :
                OT2_state['pipette'].drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced before transfer as tip_reuse rule is "always"')
                OT2_state = pick_up(OT2_state)
            elif tip_reuse == 'once' and not last_source[OT2_state['mount']] == [s_slot,s_well] and not last_source[OT2_state['mount']] == [] :
                OT2_state['pipette'].drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced before transfer since the source well changed (or the tip is contaminated in destination well).')
                OT2_state = pick_up(OT2_state)
        else :
            OT2_state = pick_up(OT2_state)

        last_source[OT2_state['mount']] = [s_slot,s_well]    #This variable is to control drop_tip rule in tip_reuse=once case
        if not [d_slot,d_well] in dest_history:         #If destination well is clean, destination pipetting is replaced by once of blow out above the bottom of destination.
            if detail_comment :
                ctx.comment('Debug: The destnation of next transfer is empty. Tip is assumed to be clean and not replaced if tip_reuse rule is "once"')
            if float(vol) < float(blowout_threshold) :     # The threshold should vary depending on solution viscosity etc.
                transfer(float(vol),source,dest,h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False)
            else:
                transfer(float(vol),source,dest,h,blow_out=True,blowout_cycle=int(blowout_cycle),max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False)
        else:
            if float(vol) < float(blowout_threshold) :     # The threshold should vary depending on solution viscosity etc.
                transfer(float(vol),source,dest,h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,mix_after=(mix_after_cycle,min(float(vol),OT2_state['max'][OT2_state['mount']])))
                last_source[OT2_state['mount']] = ['tip','dipped']
            else:
                transfer(float(vol),source,dest,h,blow_out=True,blowout_cycle=int(blowout_cycle),max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d)
        if touchtip.lower() == 'both' or touchtip.lower() == 'after':
            last_source[OT2_state['mount']] = ['tip','touched']
        dest_history.append([d_slot,d_well])

    for hand in OT2_state['name'].keys():
        if OT2_state[hand].has_tip:
            OT2_state[hand].drop_tip()
            if detail_comment:
                ctx.comment('Debug: Tip on ' + hand + ' pipette is dropped into trash as all liquid handling process completed.')

    # Rearrange remaining tips in the first tipracks
    if detail_comment:
        ctx.comment('Debug: Tips are rearranged for future use. Either A1 or H12 will be filled.')

    for hand in OT2_state['name'].keys():
        if OT2_state['used_rack'][hand]:
            if OT2_state['tip_count'][hand] > 96 - OT2_state['tip_last'][hand]:
                for well_num in range (int(OT2_state['tip_last'][hand]) + 1, 97) :
                    OT2_state[hand].pick_up_tip(OT2_state['first_tiprack'][hand][0][converter96well(OT2_state['tip_count'][hand] + 97 - well_num)])
                    OT2_state[hand].drop_tip(left_first_tiprack[0][converter96well(well_num)])
            else :
                for well_num in range (1 , left_tip_count + 1) :
                    OT2_state[hand].pick_up_tip(OT2_state['first_tiprack'][hand][0][converter96well(OT2_state['tip_last'][hand] - well_num + 1)])
                    OT2_state[hand].drop_tip(OT2_state['first_tiprack'][hand][0][converter96well(well_num)])
    ctx.set_rail_lights(light_map[light_on][3])
    if detail_comment:
        ctx.comment('Debug: Job completed.')
