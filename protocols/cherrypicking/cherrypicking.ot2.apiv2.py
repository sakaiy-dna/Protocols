metadata = {
    'protocolName': 'Extended Cherrypicking',
    'author': 'Yusuke Sakai <yusuke.sakai@riken.jp>',
    'source': 'Modified from Opentrons Cherrypicking',
    'apiLevel': '2.10'
}

class OT2_state_class():
    def __init__(self):
        self.name_dict = {}
        self.current_mount = ''
        self.last_mount = ''
        self.tipracks_dict = {'left':[],'right':[]}
        self.tip_count_dict = {'left':0,'right':0}
        self.tip_last_dict = {}
        self.used_rack_dict = {'left':True,'right':True}
        self.tip_max_dict = {}
        self.first_tiprack_dict = {}
        self.max_dict = {}
        self.min_dict = {}
        self.pipette_dict = {}
        self.pipette = None

    def mount(self,hand):
        if not hand == self.current_mount:
            self.last_mount = self.current_mount
            self.last_pipette = self.pipette
            self.current_mount = hand
            self.name = self.name_dict[hand]
            self.tipracks = self.tipracks_dict[hand]
            self.tip_count = self.tip_count_dict[hand]
            self.tip_last = self.tip_last_dict[hand]
            self.used_rack = self.used_rack_dict[hand]
            self.tip_max = self.tip_max_dict[hand]
            self.first_tiprack = self.first_tiprack_dict[hand]
            self.max = self.max_dict[hand]
            self.min = self.min_dict[hand]
            self.pipette = self.pipette_dict[hand]
            self.swap = True
        else:
            self.swap = False

    def select_mount (self,volume):
        # In case only one pipette is installed.
        if len(self.name_dict) == 1:
            for hand in self.name_dict.keys():
                self.mount(hand)
        # In case left pipette is smaller (default)
        elif self.min_dict['left'] < self.min_dict['right']:
            if volume <= self.max_dict['left'] :
                self.mount('left')
            elif volume < self.min_dict['right'] :
                self.mount('left')
            elif volume <= self.max_dict['right'] :
                self.mount('right')
            else :
                self.mount('right')
        # In case left pipette is larger
        else :
            if volume <= self.max_dict['right'] :
                self.mount('right')
            elif volume < self.min_dict['left'] :
                self.mount('right')
            elif volume <= self.max_dict['left'] :
                self.mount('left')
            else :
                self.mount('left')

def run(ctx):
    import math

    [transfer_csv, profile, mode] = get_values("transfer_csv","profile","mode")

    parameters = ["left_pipette_type", "right_pipette_type", "tip_type", "tip_reuse", "right_tipracks_start", "left_tip_last_well", "right_tip_last_well", "mode", "initial_verification", "blowout_above", "blowout_cycle", "max_carryover", "light_on", "mix_after_cycle", "drop_dirtytip", "mix_cycle_limit", "touch_new_dest", "pipette_rate","step_delay"]

    mode_map = {
        'safe_mode':{
            'tip_reuse':'always',
            'initial_verification':True,
            'blowout_above':1001,       # Always make pipetting in destination well.
            'blowout_cycle':3,          # Three times of pipetting is always performed in destination well.
            'max_carryover':5,          # Carryover cycle is limited by this value.
            'mix_after_cycle':2,        # Pipetting cycle after dispensing to make sure all tip content is transfered to the destination.
            'drop_dirtytip':True,       # If drop tip on inactive pipette when the otehr pipette is in use. 
            'mix_cycle_limit':100,      # Mix cycle is autoomatically adjusted when specified value is above pipette max limit. Specify the maximum number.
            'distribute_threshold':True,
            'return_source':False,      # Not return source if distribute occur. Minimum of volume used pipette will be discarded.
            'touch_new_dest':True,      # Assume tip is not contaminated yet when the destination well is not filled in CSV file as of transfer.
            'step_delay':1,             # robot will pause specified seconds after aspiration and before blowout for viscous reagent.
            'pipette_rate':1
        },
        'simple_mode':{
            'tip_reuse':'once',
            'initial_verification':False,
            'blowout_above':50,      # Transfering 50 µL or less than 50 µL will be performed with a pipetting in destination well
            'blowout_cycle':2,
            'max_carryover':5,
            'mix_after_cycle':1,
            'drop_dirtytip':False,
            'mix_cycle_limit':100,
            'distribute_threshold':True,
            'return_source':True,
            'touch_new_dest':True,
            'step_delay':0,
            'pipette_rate':1
        },
        'test_mode':{
            'tip_reuse':'never',
            'initial_verification':True,
            'blowout_cycle':1,
            'max_carryover':0,
            'mix_after_cycle':0,
            'drop_dirtytip':False,
            'mix_cycle_limit':0,
            'touch_new_dest':True,
            'safety_catch':False,
            'detail_comment':True,
            'step_delay':0,
            'pipette_rate':1
        },
        'custom_mode':{
        },
        'debug_mode':{                   # This mode remove safety lines (script lines to return error during simulation phase) allows user to read detail comments to find error.
        'safety_catch':False,
        'detail_comment':True
        }
    }

    default_dict={'safety_catch':True,'detail_comment':False}

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

    def pick_up():
        # First used rack counting
        hand = OT2_state.current_mount
        # In case all the tipracks are empty
        if OT2_state.tip_count_dict[hand] == OT2_state.tip_max_dict[hand] :
            ctx.pause('Please refill tipracks for the ' + hand + ' pipette before resuming.')
            if bool(initial_verification) :
                ctx.set_rail_lights(light_map[light_on][0])
                OT2_state.pipette.pick_up_tip(OT2_state.first_tiprack_dict[hand][0]['A1'])
                if detail_comment:
                    ctx.comment('Tiprack verification step: The ' + hand + ' pipette will pick up a tip from the first tiprack.')
                OT2_state.pipette.return_tip()
                ctx.set_rail_lights(light_map[light_on][2])
                ctx.pause('Resume OT-2 once you confirm the first tip(s) are picked up from the first tiprack(s) by individual pipette(s)')
            OT2_state.pipette.reset_tipracks()
            OT2_state.tip_count_dict[hand] = 1
            OT2_state.pipette.pick_up_tip()
        # In case the first tiprack gets empty
        elif ( OT2_state.tip_count_dict[hand]  < OT2_state.tip_last_dict[hand] ) and OT2_state.used_rack_dict[hand] :
            OT2_state.tip_count_dict[hand] += 1
            if OT2_state.tip_last_dict[hand] == 96:
                tip_well = converter96well(OT2_state.tip_count_dict[hand])
            else:
                tip_well = converter96well(OT2_state.tip_last_dict[hand] - OT2_state.tip_count_dict[hand] + 1)
            OT2_state.pipette.pick_up_tip(OT2_state.first_tiprack_dict[hand][0][tip_well])
        # Other cases
        else :
            OT2_state.tip_count_dict[hand] += 1
            OT2_state.pipette.pick_up_tip()
        if ( OT2_state.tip_count_dict[hand] == OT2_state.tip_last_dict[hand] ) and OT2_state.used_rack_dict[hand] :
            OT2_state.used_rack_dict[hand] = False  # Secound round ignores last-tip fork for used rack.
            if detail_comment:
                ctx.comment('Debug: ' + hand + ' first tiprack is empty. Tip rearrangement step for this tiprack will be skipped.')

    def transfer(vol,source,dest,source_height,destination_height,*,blowout_above=1001,max_carryover=5,mix_after=None,touchtip='',touchtip_d=5,tip_replace=True, blowout_cycle=2, pipette_rate=1) :
        # carryover assignment. mix_after is a tapple (mix cycle, mix volume). tip_replace specify if tip will be replaced during carryover.
        transfer_volume = [float(vol)]
        transfer_cycle = 1
        tip_dirty = False
        if touchtip_d == '':
            touchtip_d = 5
        if OT2_state.max < float(vol) :
            transfer_cycle = math.ceil(float(vol)/OT2_state.max)
            if transfer_cycle > int(max_carryover):
                ctx.comment('WARNING: Too many carryover cycles:' + str(transfer_cycle) + ' are required. Install appropriate pipettes or modify configurations.')
            if safety_catch :
                transfer_cycle = min (transfer_cycle,int(max_carryover))    # If carryover is more than user specificed carryover limit, the protocol will return error before run.
            transfer_unit_vol = math.ceil(float(vol)/transfer_cycle)
            transfer_volume[0] = transfer_volume[0] - (transfer_cycle - 1) * transfer_unit_vol
            for num in range(transfer_cycle - 1):
                transfer_volume.append(transfer_unit_vol)
            if detail_comment:
                ctx.comment('Debug: Carryover happend to transfer ' + str(vol) + ' µL. The transfer volume is split into ' + str(transfer_volume) + '.')
        # transfering step
        for unit_vol in transfer_volume:
            if not OT2_state.pipette.has_tip:
                pick_up()
            OT2_state.pipette.aspirate(volume=unit_vol,location=source.bottom(int(source_height)),rate=float(pipette_rate))
            ctx.delay(seconds=float(step_delay))                                                                         # does it happen in tip dipped in or out?
            if touchtip == 'both' or touchtip == 'before':
                OT2_state.pipette.touch_tip(location=source,v_offset=(-1*int(touchtip_d)))
            if unit_vol >= blowout_above:                               # Dispense to destination well from above or at the bottom of the well.
                OT2_state.pipette.dispense(volume=unit_vol,location=dest.top(-5),rate=float(pipette_rate))
            else:
                OT2_state.pipette.dispense(volume=unit_vol,location=dest.bottom(int(destination_height)),rate=float(pipette_rate))
                tip_dirty = True
                if detail_comment:
                    ctx.comment('Debug: Tip is dipping into destination well.')
            if not mix_after == None:   # If mix_after is specified...
                OT2_state.pipette.mix(mix_after[0],mix_after[1],dest.bottom(int(destination_height)),rate=float(pipette_rate))
                tip_dirty = True
                if detail_comment:
                    ctx.comment('Debug: Tip is used for pipetting in destination well.')
            ctx.delay(seconds=float(step_delay))
            for i in range (int(blowout_cycle)) :
                OT2_state.pipette.blow_out(location=dest.top(-5))    #Blow out user specified times (default = 2), as official blow_out setting is too weak. Blow out is executed every transfering movement including carryover to avoid accumulating remainig liquid.
            if touchtip == 'both' or touchtip == 'after':
                OT2_state.pipette.touch_tip(location=dest,v_offset=(-1*int(touchtip_d)))
                tip_dirty = True
                if detail_comment:
                    ctx.comment('Debug: Tip touched the wall of destination well.')
            if transfer_cycle > 1 and tip_dirty and tip_replace and not tip_reuse == 'never':  # replace tip if carryover occur and tip might be dirty
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced during a set of carryover process everytime the since tip might be contaminated.')
                OT2_state.pipette.drop_tip()

    # load labware
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    for line in transfer_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[4:6]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                ctx.load_labware(lw.lower(), slot)

    OT2_state = OT2_state_class()
    OT2_state.tip_last_dict = {'left':converter96well_invert(parse_well(left_tip_last_well)),'right':converter96well_invert(parse_well(right_tip_last_well))}

    # load tipracks to remaining empty slots. Used tack of each pipette is installed to slot with youngest number. Pipettes are installed.
    if not right_tipracks_start == 1 and not left_pipette_type == '':
        for slot in range(1,right_tipracks_start) :
            if not int(slot) in ctx.loaded_labwares:
                OT2_state.tipracks_dict['left'].append(ctx.load_labware(tiprack_map[left_pipette_type][tip_type], str(slot)))
        OT2_state.tipracks_dict['left'] = OT2_state.tipracks_dict['left'][1:] + OT2_state.tipracks_dict['left'][0:1]
        OT2_state.pipette_dict['left'] = ctx.load_instrument(left_pipette_type, 'left', tip_racks=OT2_state.tipracks_dict['left'])
        OT2_state.name_dict['left'] = left_pipette_type
    if not right_pipette_type == '' :
        for slot in range(right_tipracks_start,12) :
            if not int(slot) in ctx.loaded_labwares:
                OT2_state.tipracks_dict['right'].append(ctx.load_labware(tiprack_map[right_pipette_type][tip_type], str(slot)))
        OT2_state.tipracks_dict['right'] = OT2_state.tipracks_dict['right'][1:] + OT2_state.tipracks_dict['right'][0:1]
        OT2_state.pipette_dict['right'] = ctx.load_instrument(right_pipette_type, 'right', tip_racks=OT2_state.tipracks_dict['right'])
        OT2_state.name_dict['right'] = right_pipette_type 
       

    for hand in OT2_state.name_dict.keys():
        OT2_state.tip_max_dict[hand] = ( len(OT2_state.tipracks_dict[hand]) - 1 ) * 96 + OT2_state.tip_last_dict[hand]
        OT2_state.first_tiprack_dict[hand] = OT2_state.tipracks_dict[hand][len(OT2_state.tipracks_dict[hand]) - 1:]
        OT2_state.max_dict[hand] = tiplimit_map[OT2_state.name_dict[hand]][tip_type]['max']
        OT2_state.min_dict[hand] = tiplimit_map[OT2_state.name_dict[hand]][tip_type]['min']

    # Initial verification phase
    if bool(initial_verification) :
        ctx.set_rail_lights(light_map[light_on][0])
        for hand in OT2_state.name_dict.keys():
            OT2_state.pipette_dict[hand].pick_up_tip(OT2_state.first_tiprack_dict[hand][0][parse_well(tip_last_well[hand])])
            OT2_state.pipette_dict[hand].aspirate(location=ctx.loaded_labwares[
            int(transfer_info[0][1])].wells_by_name()[parse_well(transfer_info[0][2])].top())
            ctx.delay(seconds=3)
            OT2_state.pipette_dict[hand].return_tip()
        ctx.comment('Initial verification: Pause manually when calibration or configurations are incorrect. Installed pipette(s) are now picking up the last tip of the first tiprack(s) and move to the center of the top of the first source well. ')
        ctx.set_rail_lights(light_map[light_on][2])
    
    ctx.comment('Transfering phase has started.')
    last_source = {'left':[],'right':[]}
    dest_history = []
    if detail_comment:
        ctx.comment('Debug: Source cashe and destination history are initialized')
    ctx.set_rail_lights(light_map[light_on][1])
    for line in transfer_info:
        try:
            _, s_slot, s_well, h, _, d_slot, d_well, vol, d_h, mix, touchtip, touchtip_d, pipetting_override, distribute_override = line[:14]
        except:
            _, s_slot, s_well, h, _, d_slot, d_well, vol = line[:8]
            d_h = '' 
            mix = ''
            touchtip = ''
            touchtip_d = ''
            pipetting_override = ''
            distribute_override = ''
            ctx.comment('CAUTION: Only required columns of input CSV file was read. No options were applied.')
        source = ctx.loaded_labwares[int(s_slot)].wells_by_name()[parse_well(s_well)]
        dest = ctx.loaded_labwares[int(d_slot)].wells_by_name()[parse_well(d_well)]
        if d_h == '':
            d_h = min(3,max(1,2*(float(vol)/(4*math.pi())*3)^(1/3) - 1)) # spheric droplet diameter - 1 mm, but ranging between 1 mm - 3 mm.
            if detail_comment:
                ctx.comment('Debug: Unspecified destination height is set to ' + str(d_h) + ' mm from the bottom according to dispensing volume.')
        # Mix source solution before transfering
        mix_cycle = 10     # Default mixing cycle is 10.
        if mix == '0' :  #In case of 0, pause and manual mixing will be added.
            ctx.set_rail_lights(light_map[light_on][2])
            ctx.pause('Please mix destination labwares manually, spin them down, and resume the robot. The destination paused the robot is:' + s_well + ' in ' + str(s_slot) + '.')
            ctx.set_rail_lights(light_map[light_on][1])
        elif not mix == '' :
            OT2_state.select_mount(float(mix))
            if OT2_state.swap: # Dirty tip on not-selected pipette won't fly above labwares if user specifiy.
                if detail_comment:
                    ctx.comment('Debug: ' + OT2_state.current_mount + ' pipette is selected.')
                if OT2_state.last_pipette.has_tip and bool(drop_dirtytip) and not tip_reuse == 'never':
                    OT2_state.last_pipette.drop_tip()
                    if detail_comment:
                        ctx.comment('Debug: Dirty tip on ' + OT2_state.last_mount + ' pipette is dropped into trash.')
            mix_cycle = max(10, round(10*float(mix)/OT2_state.max))
            mix_volume = min(float(mix),OT2_state.max)
            if mix_cycle > int(mix_cycle_limit):
                ctx.comment('WARNING: Too many mixing cycle (' + str(mix_cycle) + ' cycles) is required to mix source well:' + s_well + ' in Slot ' + s_slot +'. Consider to pause OT-2 to vortex manually (input "0" in the mix configuration column of CSV file) as a faster option or install appropriate pipettes.') 
                if safety_catch :
                    mix_volume = float(mix) # If mix cycle is more than user specificed limit, the protocol will return error before run.
                    mix_cycle = int(mix_cycle_limit)
            if OT2_state.pipette.has_tip:
                if tip_reuse == 'always' :
                    OT2_state.pipette.drop_tip()
                    if detail_comment:
                        ctx.comment('Debug: Tip is replaced before mixing as tip_reuse rule is "always"')
                    pick_up()
                elif tip_reuse == 'once' and not last_source[OT2_state.current_mount] == [s_slot,s_well] and not last_source[OT2_state.current_mount] == []:
                    if detail_comment:
                        ctx.comment('Debug: Tip is replaced before mixing since the source well changed (or the tip is contaminated in destination well).')
                    selected_pipette.drop_tip()
                    pick_up()
            else :
                pick_up()
            OT2_state.pipette.mix(mix_cycle,mix_volume,source.bottom(float(h)),float(pipette_rate))
            ctx.delay(seconds=float(step_delay))
            for i in range (int(blowout_cycle)) : 
                OT2_state.pipette.blow_out(source.top(-5))
            last_source[OT2_state.current_mount] = [s_slot,s_well]

        # Main Transfer step
        OT2_state.select_mount(float(vol))
        if OT2_state.swap: # Dirty tip on not-selected pipette won't fly above labwares if user specifiy.
            if detail_comment:
                ctx.comment('Debug: ' + OT2_state.current_mount + ' pipette is selected.')
            if not OT2_state.last_pipette == None:
                if OT2_state.last_pipette.has_tip and bool(drop_dirtytip) and not tip_reuse == 'never':
                    OT2_state.last_pipette.drop_tip()
                    if detail_comment:
                        ctx.comment('Debug: Dirty tip on ' + OT2_state.last_mount + ' pipette is dropped into trash.')
        if OT2_state.pipette.has_tip:
            if tip_reuse == 'always' :
                OT2_state.pipette.drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced before transfer as tip_reuse rule is "always"')
                pick_up()
            elif tip_reuse == 'once' and not last_source[OT2_state.current_mount] == [s_slot,s_well] and not last_source[OT2_state.current_mount] == [] :
                OT2_state.pipette.drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced before transfer since the source well changed (or the tip is contaminated in destination well).')
                pick_up()
        else :
            pick_up()

        last_source[OT2_state.current_mount] = [s_slot,s_well]    #This variable is to control drop_tip rule in tip_reuse=once case
        if not [d_slot,d_well] in dest_history and bool(touch_new_dest):         #If destination well is clean, destination pipetting is replaced by once of blow out above the bottom of destination.
            if detail_comment :
                ctx.comment('Debug: The destnation of next transfer is empty. Tip is assumed to be clean and not replaced if tip_reuse rule is "once"')
            if not pipetting_override == '' : 
                if detail_comment :
                    ctx.comment('Debug: Pipetting cycle is overridden by CSV value')
                transfer(float(vol),source,dest,h,d_h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False,blowout_cycle=int(blowout_cycle),mix_after=(int(pipetting_override),min(float(vol),OT2_state.max)),pipette_rate=float(pipette_rate))
            elif float(vol) < float(blowout_above) :     # The threshold should vary depending on solution viscosity etc.
                transfer(float(vol),source,dest,h,d_h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False,blowout_cycle=int(blowout_cycle),pipette_rate=float(pipette_rate))
            else:
                transfer(float(vol),source,dest,h,d_h,blowout_above=float(blowout_above),blowout_cycle=int(blowout_cycle),max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,tip_replace=False,pipette_rate=float(pipette_rate))
        else:
            if float(vol) < float(blowout_above) :     # The threshold should vary depending on solution viscosity etc.
                transfer(float(vol),source,dest,h,d_h,max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,mix_after=(int(mix_after_cycle),min(float(vol),OT2_state.max)),blowout_cycle=int(blowout_cycle),pipette_rate=float(pipette_rate))
                last_source[OT2_state.current_mount] = ['tip','dipped']
            else:
                transfer(float(vol),source,dest,h,d_h,blowout_above=float(blowout_above),blowout_cycle=int(blowout_cycle),max_carryover=int(max_carryover),touchtip=touchtip.lower(),touchtip_d=touchtip_d,pipette_rate=float(pipette_rate))

        if touchtip.lower() == 'both' or touchtip.lower() == 'after':
            last_source[OT2_state.current_mount] = ['tip','touched']
        dest_history.append([d_slot,d_well])

    for hand in OT2_state.name_dict.keys():
        if mode == 'test_mode':                              # In case of test mode, tip will be returned to tipracks.
            OT2_state.pipette_dict[hand].return_tip()
        if OT2_state.pipette_dict[hand].has_tip:
            OT2_state.pipette_dict[hand].drop_tip()
            if detail_comment:
                ctx.comment('Debug: Tip on ' + hand + ' pipette is dropped into trash as all job completed.')
    ctx.set_rail_lights(light_map[light_on][3])
    ctx.comment('All job completed.')
