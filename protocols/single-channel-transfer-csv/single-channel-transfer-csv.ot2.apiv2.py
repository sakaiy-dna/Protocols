metadata = {
    'protocolName': 'Single Channel Transfer from CSV',
    'author': 'Yusuke Sakai <yusuke.sakai@riken.jp>',
    'source': 'Modified from Opentrons Cherrypicking',
    'apiLevel': '2.10'
}

class OT2_state_class():
    def __init__(self,parameters):
        self.name_dict = {}    #API covers 
        self.current_mount = ''
        self.last_mount = ''
        self.tipracks_dict = {'left':[],'right':[]}    #API covers
        self.tip_count_dict = {'left':0,'right':0}
        self.tip_last_dict = {}
        self.used_rack_dict = {'left':True,'right':True}
        self.tip_max_dict = {}
        self.first_tiprack_dict = {}    #API covers
        self.max_dict = {}    #API covers
        self.min_dict = {}    #API covers
        self.pipette_dict = {}    #API covers
        self.pipette = None    #API covers
        self.last_source_dict = {'left':[],'right':[]}
        self.last_source = []
        self.tip_dirty_dict = {'left':[False],'right':[False]}
        self.tip_dirty = False
        self.dest_history = []    #API covers
        for k, v in parameters.items():
            setattr(self, k, v)

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

            self.last_source_dict[self.last_mount] = self.last_source
            self.last_source = self.last_source_dict[self.current_mount]
            self.tip_dirty_dict[self.last_mount] = self.tip_dirty
            self.last_source = self.last_source_dict[self.current_mount]
            
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

    parameters = ["left_pipette_type", "right_pipette_type", "tip_type", "tip_reuse", "right_tipracks_start", "left_tip_last_well", "right_tip_last_well", "mode", "initial_verification", "blowout_above", "distribute_above","blowout_cycle", "max_carryover", "light_on", "mix_after_cycle", "drop_dirtytip", "mix_cycle_limit", "store_dest_history", "pipette_rate","step_delay","return_source","mix_same_tip"]

    mode_map = {
        'safe_mode':{                       # slow setting with certain margin, though handling viscous samples would need more tuning.
            'tip_reuse':'always',           # Tip will be replaced every tranfering step.
            'initial_verification':True,    # Initial verification is active to minimize human error.
            'blowout_above':1001,           # Always make pipetting in destination well.
            'blowout_cycle':3,              # Three times of blowing out is always performed.
            'max_carryover':5,              # Carryover cycle is limited up to 5 time. (e.g. if you installed P300 pipette, transfering above 1500 µL returns error.)
            'mix_after_cycle':2,            # Twice of pipetting after dispensing to make sure all tip content is transfered to the destination. (usually skipped when transfering to empty destination)
            'drop_dirtytip':True,           # Drop tip on the unused pipette when the otehr pipette is in use. 
            'mix_cycle_limit':100,          # Mix cycle is automatically adjusted when specified value is above pipette capacity (up to 10 times, e.g. you can specify up to 3 mL when you isntall P300).
            'distribute_above':1000,        # Distribute is inactivated as the threshold is more than the half of the capacity of any of available pipette.
            'return_source':False,          # Distribute won't occur as the threshold above but here NOT to return source after distibute is specified. Minimum of volume of the used pipette will be discarded.
            'store_dest_history':True,      # Assume tip is not contaminated yet when the destination has not been specified as a destination as of the transfer.
            'step_delay':1,                 # Robot will pause for a second after aspiration and before blowout for content to be still.
            'pipette_rate':1,               # Relative pipette rate. 1 is default and the max. Keep in mind it may differ between version and API level.
            'mix_same_tip':False,           # Tip will be replaced between source mixing step and transfering step for best accuracy.
            'light_on':'always_off'         # Light is alway turned off for preserving light sensitive sample.
        },
        'simple_mode':{                     # Moderate setting with balanced resorce (time and tip) consumption.
            'tip_reuse':'once',             # tip will be replaced only when the tip might be contaminated.
            'initial_verification':True,
            'blowout_above':50,             # Transfering less than 50 µL will be performed with a pipetting in destination well
            'blowout_cycle':2,              # Twice of blowing out is always performed. (enough for most case)
            'max_carryover':5,
            'mix_after_cycle':1,            # Once of pipetting after dispensing to make sure all tip content is transfered to the destination. (usually skipped when transfering to empty destination)
            'drop_dirtytip':True,
            'mix_cycle_limit':30,           # Mixing volume up to three times of larger pipette capacity can be specified.
            'distribute_above':1000,
            'return_source':True,           # Distribute won't occur as the threshold above but here to return source after distibute is specified.
            'store_dest_history':True,
            'mix_same_tip':True,            # Keep using the same tip for source mixing step and transfering step if possible.
            'step_delay':0,                 # No step delay is applied.
            'pipette_rate':1,
            'light_on':'run_off'            # Light is turned on during potentially manual steps (initial verification, during pause and after the run) and turned off during fully automatic phase.
        },
        'rapid_mode':{                      # Faster setting with shorter margin. For not accuracy-demanidng nor viscous samples.
            'tip_reuse':'once',
            'initial_verification':False,   # Initial verification is skipped and there are no chance of double check.
            'blowout_above':20,             # Transfering 20 µL or more than 20 µL will be blown out above the destination (from 5 mm inside from the top of the well).
            'blowout_cycle':2,
            'max_carryover':5,
            'mix_after_cycle':0,            # No pipetting (just dispence in the bottom of destination) when lower than blowout_above
            'drop_dirtytip':False,
            'mix_cycle_limit':10,           # Specifying mixing volume larger than pipette capacity returns error.
            'distribute_above':100,         # Distribute is activated when the transfering volume of each destination is above 100 µL
            'return_source':True,           # Returning disposal volume (min volume of the pipette) to source after distibute is specified.
            'store_dest_history':True,
            'step_delay':0,
            'pipette_rate':1,
            'mix_same_tip':True,
            'light_on':'run_off'
        },
        'test_mode':{                       # To test labware clearance and protocol correctness in dry with shortest time. Tip will be returend to tipracks after run.
            'tip_reuse':'never',            # Tip will never replaced during run.
            'initial_verification':True,
            'blowout_cycle':1,              # Blowout cycle is minimum (Opentrons default).
            'mix_after_cycle':1,            # once of destination pipetting will be performed when the transfer volme is below blow out above threshold.
            'drop_dirtytip':False,          # Both pipette may have tips even during the other one is in use.
            'mix_cycle_limit':0,            # Specifying mixing volume retunrs error.
            'store_dest_history':True,
            'safety_catch':False,           # Safety catches are released. Passing simulation doesn't certify the validity of the procol.
            'detail_comment':True,          # Detail comment is 
            'step_delay':0,
            'pipette_rate':1,
            'mix_same_tip':True,
            'light_on':'always_on'          # Light is alway turned on thoughout the protocol.
        },
        'custom_mode':{
        },
        'debug_mode':{                      # This mode remove safety lines (script lines to return error during simulation phase) allows user to read detail comments to find error.
        'safety_catch':False,
        'detail_comment':True
        }
    }

    profile_dict = {}
    if not profile == 'No Profile' :
        for line in profile.splitlines() :
            profile_dict[line.split(':')[0]] = line.split(':')[1]
    
    default_dict={'safety_catch':True,'detail_comment':False}

    parameter_dict = {}                    # parameters from the form are applied
    for name in parameters:
        parameter_dict[name]=get_values(name)[0]

    parameter_dict.update(default_dict)     # default values are applied
    parameter_dict.update(mode_map[mode])   # mode setting has priority than individual parameters or default values
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
                for hand in OT2_state.name_dict.keys():
                    OT2_state.pipette_dict[hand].pick_up_tip(OT2_state.first_tiprack_dict[hand][0][parse_well(tip_last_well[hand])])
                    OT2_state.pipette_dict[hand].return_tip()
                ctx.delay(seconds=3)
                ctx.comment('Tiprack verification: Pause manually if pipette(s) did not pick up A1 of the first tiprack(s).')
                ctx.set_rail_lights(light_map[light_on][2])
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
                ctx.comment('Debug: ' + hand + ' first tiprack, from which normally tips are picked up in backward, is empty. Next tip will be picked up from A1 of next tiprack.')
    def transfer_step(vol,source,dest,source_height,dest_height,*,mix_after=None,touchtip='',touchtip_d=5,dest_filled=True,rate=1) :
        # carryover assignment. dest_filled specify if tip will be replaced during carryover.
        transfer_volume = [float(vol)]
        transfer_cycle = 1
        if touchtip_d == '':
            touchtip_d = 5
        if not mix_after == None:
            pipetting_cycle = mix_after
        else:
            pipetting_cycle = OT2_state.mix_after_cycle
        if not dest_height == '':
            mix_after = True                        # to specify pipetting after transfer
            dispense_height = float(dest_height)
            mix_height = float(dest_height)
        else:
            dispense_height = min(3,max(1,2*(float(vol)/(4*math.pi)*3)**(1/3) - 1)) # spheric droplet diameter - 1 mm, but ranging between 1 mm - 3 mm.
            mix_height = 1                                                          # Opentrons official default.
            if detail_comment:
                ctx.comment('Debug: Unspecified destination height is set to ' + str(dispense_height) + ' mm from the bottom according to dispensing volume. (Ignored when vol is above blowout_above.)')
 
        if OT2_state.max < float(vol) :
            transfer_cycle = math.ceil(float(vol)/OT2_state.max)
            if transfer_cycle > int(OT2_state.max_carryover):
                ctx.comment('WARNING: Too many carryover cycles:' + str(transfer_cycle) + ' are required. Install appropriate pipettes or modify configurations.')
            if safety_catch :
                transfer_cycle = min (transfer_cycle,int(OT2_state.max_carryover))    # If carryover is more than user specificed carryover limit, the protocol will return error before run.
            transfer_unit_vol = math.ceil(float(vol)/transfer_cycle)
            transfer_volume[0] = transfer_volume[0] - (transfer_cycle - 1) * transfer_unit_vol
            for num in range(transfer_cycle - 1):
                transfer_volume.append(transfer_unit_vol)
            if detail_comment:
                ctx.comment('Debug: Carryover is needed to transfer ' + str(vol) + ' µL. The transfer volume is split into ' + str(transfer_volume) + '.')
        # transfering step
        for unit_vol in transfer_volume:
            if not OT2_state.pipette.has_tip:
                pick_up()
            OT2_state.pipette.aspirate(volume=unit_vol,location=source.bottom(float(source_height)),rate=float(rate))
            if not OT2_state.step_delay == 0:
                ctx.delay(seconds=float(OT2_state.step_delay))                                                                         # does it happen where tip dipped in or above?
            if touchtip == 'both' or touchtip == 'source':
                OT2_state.pipette.touch_tip(location=source,v_offset=(-1*int(touchtip_d)))
            if unit_vol > OT2_state.blowout_above and mix_after == None:                               # Dispense to destination well from above or at the bottom of the well.
                OT2_state.pipette.dispense(volume=unit_vol,location=dest.top(-5),rate=float(rate))
            else:
                OT2_state.pipette.dispense(volume=unit_vol,location=dest.bottom(dispense_height),rate=float(rate))
                if dest_filled:
                    OT2_state.tip_dirty = True
                    if detail_comment:
                        ctx.comment('Debug: Tip is dipped into destination well and flagged dirty')
                if (dest_filled or not mix_after == None) and not pipetting_cycle == 0:
                    OT2_state.pipette.mix(pipetting_cycle,min(unit_vol,OT2_state.max),dest.bottom(mix_height),rate=float(rate))
            if not OT2_state.step_delay == 0:
                ctx.delay(seconds=float(OT2_state.step_delay))
            for i in range (int(OT2_state.blowout_cycle)) :
                OT2_state.pipette.blow_out(location=dest.top(-5))    #Blow out user specified times (default = 2), as official blow_out setting is too weak. Blow out is executed every transfering movement including carryover to avoid accumulating remainig liquid.
            if touchtip == 'both' or touchtip == 'dest' or touchtip == 'destination':
                OT2_state.pipette.touch_tip(location=dest,v_offset=(-1*int(touchtip_d)))
                if dest_filled:
                    OT2_state.tip_dirty = True
                    if detail_comment:
                        ctx.comment('Debug: Tip touched the wall of destination well and flagged dirty.')
            if transfer_cycle > 1 and OT2_state.tip_dirty and not OT2_state.tip_reuse == 'never':  # replace tip if carryover occur and tip might be dirty
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced during a set of carryover process everytime since the tip might be contaminated in destination.')
                OT2_state.pipette.drop_tip()
                OT2_state.tip_dirty = False

    def select_pipette(vol,s_slot,s_well,*,force_once=False):
        OT2_state.select_mount(float(vol))
        if OT2_state.swap: # Dirty tip on not-selected pipette won't fly above labwares if user specifiy.
            if detail_comment:
                ctx.comment('Debug: ' + OT2_state.current_mount + ' pipette is selected.')
            if not OT2_state.last_pipette == None:
                if OT2_state.last_pipette.has_tip and bool(OT2_state.drop_dirtytip) and not OT2_state.tip_reuse == 'never':
                    OT2_state.last_pipette.drop_tip()
                    if detail_comment:
                        ctx.comment('Debug: Dirty tip on the other pipette (' + OT2_state.last_mount + ') is dropped into trash to avoid contamination of deck.')
        if OT2_state.pipette.has_tip:
            if force_once and not OT2_state.swap and OT2_state.last_source == [s_slot,s_well]:
                if detail_comment:
                    ctx.comment('Debug: Tip is NOT replaced before next step as it was only used for mixing source')
            elif OT2_state.tip_reuse == 'always' :
                OT2_state.pipette.drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced before next step as tip_reuse policy is specified as "always"')
                pick_up()
                OT2_state.tip_dirty = False
            elif OT2_state.tip_reuse == 'once' and OT2_state.tip_dirty:
                OT2_state.pipette.drop_tip()
                if detail_comment and OT2_state.last_source == [s_slot,s_well]:
                    ctx.comment('Debug: Tip is replaced before next step as the tip might be contaminated in destination.')
                pick_up()
                OT2_state.tip_dirty = False
            elif not OT2_state.last_source == [s_slot,s_well]:
                OT2_state.pipette.drop_tip()
                if detail_comment:
                    ctx.comment('Debug: Tip is replaced as the source well changed. Last source: ' + str(OT2_state.last_source) + ' while new source: ' + str([s_slot,s_well]))
                pick_up()
                OT2_state.tip_dirty = False
        else :
            pick_up()
            OT2_state.tip_dirty = False
        OT2_state.last_source = [s_slot,s_well]

    def transfer(line):
        _, s_slot, s_well, h, _, d_slot, d_well, vol, d_h, mix, touchtip, touchtip_d, rate_override, mixafter_override, distribute_override = line[:15]
        source = ctx.loaded_labwares[int(s_slot)].wells_by_name()[parse_well(s_well)]
        dest = ctx.loaded_labwares[int(d_slot)].wells_by_name()[parse_well(d_well)]
        if rate_override == '':
            rate_override = OT2_state.pipette_rate  # set default pipette rate if unspecified.
        # Mix source solution before transfering
        mix_cycle = 10     # Default mixing cycle is 10.
        if mix == '0' :  #In case of 0, pause and user mixes the source manually.
            ctx.set_rail_lights(light_map[light_on][2])
            OT2_state.pipette.home()
            ctx.pause('Please mix destination labwares manually, spin them down, and resume the robot. The destination paused the robot is:' + s_well.upper() + ' in ' + str(s_slot) + '.')
            ctx.set_rail_lights(light_map[light_on][1])
        elif not mix == '' :
            select_pipette(float(mix),s_slot,s_well)
            mix_cycle = max(10, round(10*float(mix)/OT2_state.max))
            mix_volume = min(float(mix),OT2_state.max)
            if mix_cycle > int(mix_cycle_limit):
                ctx.comment('WARNING: Too many mixing cycle (' + str(mix_cycle) + ' cycles) is required to mix source well:' + s_well + ' in Slot ' + s_slot +'. Consider to pause OT-2 to vortex manually (input "0" in the mix configuration column of CSV file) as a faster option or install appropriate pipettes.') 
                if safety_catch :
                    mix_volume = float(mix) # If mix cycle is more than user specificed limit, the protocol will return error before run.
                    mix_cycle = int(mix_cycle_limit)
            if OT2_state.pipette.has_tip:
                if OT2_state.tip_reuse == 'always' :
                    OT2_state.pipette.drop_tip()
                    OT2_state.tip_dirty = False
                    if detail_comment:
                        ctx.comment('Debug: Tip is replaced before mixing as tip_reuse policy is "always"')
                    pick_up()
                elif OT2_state.tip_reuse == 'once' and OT2_state.tip_dirty:
                    if detail_comment:
                        ctx.comment('Debug: Tip is replaced before the mixing step as the tip might be contaminated.')
                    selected_pipette.drop_tip()
                    OT2_state.tip_dirty = False
                    pick_up()
            else :
                pick_up()
            OT2_state.pipette.mix(mix_cycle,mix_volume,source.bottom(float(h)),rate=float(rate_override))
            if not OT2_state.step_delay == 0:
                ctx.delay(seconds=float(OT2_state.step_delay))
            for i in range (int(OT2_state.blowout_cycle)) : 
                OT2_state.pipette.blow_out(source.top(-5))
            OT2_state.last_source = [s_slot,s_well]    #This variable is to control drop_tip rule in tip_reuse=once case

        # Main Transfer step
        select_pipette(vol,s_slot,s_well,force_once=(not (mix == '' or mix == 0) and mix_same_tip))     # If select_pipette is executed in mixing step (and mix_same_tip=True), force_once=True 

        if not [d_slot,d_well] in OT2_state.dest_history and bool(OT2_state.store_dest_history):         #If destination well is clean, destination pipetting is skipped.
            if detail_comment :
                ctx.comment('Debug: The destnation of line ' +  str(OT2_state.line_num) + ' is empty. Destination pipetting is skipped unless specifically overridden by CSV file. Tip is assumed to be clean after use and not replaced if tip_reuse rule is "once".')
            if not mixafter_override == '' :           # in case of pipetting override applied.
                if detail_comment :
                    ctx.comment('Debug: Special pipetting cycle: ' + str(mixafter_override) + ' is applied in line ' + str(OT2_state.line_num))
                transfer_step(float(vol),source,dest,h,d_h,touchtip=touchtip.lower(),touchtip_d=touchtip_d,dest_filled=False,rate=rate_override,mix_after=(int(mixafter_override)))
            else:
                transfer_step(float(vol),source,dest,h,d_h,touchtip=touchtip.lower(),touchtip_d=touchtip_d,dest_filled=False,rate=rate_override)
        else:
            if not mixafter_override == '' :           # in case of pipetting override applied.
                if detail_comment :
                    ctx.comment('Debug: Special pipetting cycle: ' + str(mixafter_override) + ' is applied in line ' + str(OT2_state.line_num))
                transfer_step(float(vol),source,dest,h,d_h,touchtip=touchtip.lower(),touchtip_d=touchtip_d,rate=rate_override,mix_after=(int(mixafter_override)))
            else:
                transfer_step(float(vol),source,dest,h,d_h,touchtip=touchtip.lower(),touchtip_d=touchtip_d,rate=rate_override)
        OT2_state.dest_history.append([d_slot,d_well])
        OT2_state.last_source = [s_slot,s_well]

    def distributable(line_cache):
        # volume evaluation
        aspiration_volume = 0
        for line in line_cache:
            try:
                min_vol = min(float(line[7]),min_vol)
            except:
                min_vol = float(line[7])
            aspiration_volume += float(line[7])
        pipette_capacity = False
        for hand in OT2_state.name_dict.keys():
            if min_vol >= OT2_state.min_dict[hand] and aspiration_volume + OT2_state.min_dict[hand] <= OT2_state.max_dict[hand]:
                pipette_capacity = True
        volume_threshold = min_vol >= OT2_state.distribute_above
        # source_test
        source_test = line_cache[len(line_cache)-1][1:3] == line_cache[0][1:3]
        # destination_test
        destination_test = (not line_cache[len(line_cache)-1][5:7] in OT2_state.dest_history and OT2_state.store_dest_history) or (int(line_cache[len(line_cache)-1][7]) > OT2_state.blowout_above and not (line_cache[len(line_cache)-1][10].lower() == 'dest' or line_cache[len(line_cache)-1][10].lower() == 'both' or line_cache[len(line_cache)-1][10].lower() == 'destination') and (line_cache[len(line_cache)-1][14] == '' or line_cache[len(line_cache)-1][14] == 0))
        # mix before test
        mix_test = line_cache[len(line_cache)-1][9] == '' or len(line_cache) == 1
        # touch_tip_source test
        touch_tip_times = 0
        for line in line_cache:
            if line[10].lower() == 'source' or line[10].lower() == 'both':
                touch_tip_times += 1
        touch_consistency = touch_tip_times == 0 or touch_tip_times == len(line_cache)
        options_consistency = [line_cache[0][3]] + line_cache[0][11:14] == [line_cache[len(line_cache)-1][3]] + line_cache[len(line_cache)-1][11:14]
        if line_cache[len(line_cache)-1][14] == '':
            if pipette_capacity and source_test and destination_test and not(mix_test and touch_consistency and options_consistency):
                ctx.comment('CAUTION: Automatic distribute is adopted and inconsitent optional parameters among distribution set were detected (source mix, touch tip in source, pipette rate override, or asspiration height). The safest parameters were adopted.')
            return pipette_capacity and source_test and destination_test and volume_threshold
        elif not (pipette_capacity and source_test and destination_test and volume_threshold) and not (OT2_state.tip_reuse == 'never') and OT2_state.safety_catch:   # If cross-contamination is not accepted (by specifying tip reuse to either once or always, the protocol will return error.)
            OT2_state.pipette.drop_tip()    # serious cross-contamination is worried and safety catch called error to stop careless run.
            OT2_state.pipette.drop_tip()
        else:
            if OT2_state.safety_catch and not OT2_state.tip_reuse == 'never':
                OT2_state.pipette.drop_tip()    # safety catch for avove comment exception.
                OT2_state.pipette.drop_tip()
            ctx.comment('WARNING: Distribute Override was forced by CSV file and cross-contamination may happen.')
            return source_test and pipette_capacity
    
    def distribute(line_cache): # Distribute line_cache[0:last]
        source = ctx.loaded_labwares[int(line_cache[0][1])].wells_by_name()[parse_well(line_cache[0][2])]
        dest_list = []
        dispense_vol = []
        dest_h_list = []
        source_mix = 0
        touchtip_dest_d = []
        rate_override_min = 1
        mixafter_override_list = []
        distribute_lines = line_cache[:(len(line_cache)-1)]
        aspirate_vol = 0
        touchtip_source_d = 0
        manual_mix = False
        source_touchtip = False
        dest_filled_list = []
        line_counter = 0
        for line in distribute_lines:
            _, s_slot, s_well, h, _, d_slot, d_well, vol, d_h, mix, touchtip, touchtip_d, rate_override, mixafter_override, distribute_override = line[:15]
            dest_list.append(ctx.loaded_labwares[int(d_slot)].wells_by_name()[parse_well(d_well)])
            try:
                source_h = min(source_h,float(h))
            except:
                source_h = float(h)
            aspirate_vol += float(vol)
            dispense_vol.append(float(vol))
            dest_h_list.append(d_h)
            if mix == 0:
                manual_mix = True
            elif not mix == '':
                source_mix = max(float(mix),source_mix)
            if touchtip.lower() == 'source' or touchtip.lower() == 'both':
                source_touchtip = True
                if touchtip_d == '':
                    touchtip_source_d = max(5,touchtip_source_d)
                else:
                    touchtip_source_d = float(touchtip_d)
            if touchtip.lower() == 'dest' or touchtip.lower() == 'both' or touchtip.lower() == 'destination':
                if touchtip_d == '':
                    touchtip_dest_d.append(5)
                else:
                    touchtip_dest_d.append(float(touchtip_d))
            else :
                touchtip_dest_d.append(None)
            if not rate_override == '':
                rate_override_min = min(rate_override_min,float(rate_override))
            mixafter_override_list.append(mixafter_override)
            if not distribute_override == '':
                ctx.comment('CAUTION: Distribute Override was specified by CSV file.')
            dest_filled_list.append([d_slot,d_well] in OT2_state.dest_history and bool(OT2_state.store_dest_history))   # True stands or the dest is in history. False means empty dest.
            if detail_comment and (not [d_slot,d_well] in OT2_state.dest_history and bool(OT2_state.store_dest_history)) :
                ctx.comment('Debug: The destnation of line ' + str(OT2_state.line_num - len(line_cache) + 2 + line_counter) + ' is empty. Destination pipetting is skipped unless specifically overridden by CSV file. Tip is assumed to be clean after use and not replaced if tip_reuse rule is "once".')
                
            OT2_state.dest_history.append([d_slot,d_well])
            line_counter += 1
        # source mixing phase
        mix_cycle = 10     # Default mixing cycle is 10.
        if manual_mix :  #Pause and user mixes the source manually.
            ctx.set_rail_lights(light_map[light_on][2])
            OT2_state.pipette.home()
            ctx.pause('Please mix destination labwares manually, spin them down, and resume the robot. The destination paused the robot is:' + s_well.upper() + ' in ' + str(s_slot) + '.')
            ctx.set_rail_lights(light_map[light_on][1])
        elif not source_mix == 0 :
            select_pipette(source_mix,s_slot,s_well)
            mix_cycle = max(10, round(10*float(source_mix)/OT2_state.max))
            mix_volume = min(float(source_mix),OT2_state.max)
            if mix_cycle > int(mix_cycle_limit):
                ctx.comment('WARNING: Too many mixing cycle (' + str(mix_cycle) + ' cycles) is required to mix source well:' + s_well + ' in Slot ' + s_slot +'. Consider to pause OT-2 to vortex manually (input "0" in the mix configuration column of CSV file) as a faster option or install appropriate pipettes.') 
                if safety_catch :
                    mix_volume = float(source_mix) # If mix cycle is more than user specificed limit, the protocol will return error before run.
                    mix_cycle = int(mix_cycle_limit)
            OT2_state.pipette.mix(mix_cycle,mix_volume,source.bottom(float(source_h)),rate=rate_override_min)
            if not OT2_state.step_delay == 0:
                ctx.delay(seconds=float(OT2_state.step_delay))
            for i in range (int(OT2_state.blowout_cycle)) : 
                OT2_state.pipette.blow_out(source.top(-5))

        # distribute phase
        for hand in OT2_state.name_dict.keys():
            if OT2_state.min_dict[hand] + aspirate_vol <= OT2_state.max_dict[hand] and OT2_state.min_dict[hand] <= min(dispense_vol):
                selected_mount = hand
        aspirate_vol += OT2_state.min_dict[selected_mount]
        select_pipette(aspirate_vol,s_slot,s_well,force_once=((not manual_mix and not source_mix == 0) and mix_same_tip))
        OT2_state.pipette.aspirate(volume=aspirate_vol,location=source.bottom(float(source_h)),rate=float(rate_override_min))
        if not OT2_state.step_delay == 0:
            ctx.delay(seconds=float(OT2_state.step_delay))                                                                         # does it happen where tip dipped in or above?
        if source_touchtip:
            OT2_state.pipette.touch_tip(location=source,v_offset=(-1*int(touchtip_source_d)))
        line_counter = 0
        for dest, vol, dest_h, touchtip_d, mixafter_override, dest_filled in zip(dest_list,dispense_vol,dest_h_list,touchtip_dest_d,mixafter_override_list,dest_filled_list):
            if not dest_h == '':
                mix_after = True                        # to specify pipetting after transfer
                dispense_height = float(dest_h)
                mix_height = float(dest_h)
            else:
                mix_after = None
                dispense_height = min(3,max(1,2*(float(vol)/(4*math.pi)*3)**(1/3) - 1)) # spheric droplet diameter - 1 mm, but ranging between 1 mm - 3 mm.
                mix_height = 1                                                          # Opentrons official default.
                if detail_comment:
                    ctx.comment('Debug: Unspecified destination height is set to ' + str(round(dispense_height,2)) + ' mm from the bottom according to dispensing volume. (ignored when vol is above blowout_above.)')
            pipetting_cycle = OT2_state.mix_after_cycle
            if not mixafter_override == '':
                pipetting_cycle = int(mixafter_override)
                mix_after = True
                if OT2_state.detail_comment:
                    ctx.comment('Debug: Special Pipetting cycle: ' + str(pipetting_cycle) + ' is applied in line ' + str(OT2_state.line_num - len(line_cache) + 2 + line_counter ))
            if pipetting_cycle == 0:
                mix_after = False
            if vol > OT2_state.blowout_above and not mix_after:                              # Dispense to destination well from above or at the bottom of the well.
                OT2_state.pipette.dispense(volume=vol,location=dest.top(-5),rate=float(rate_override_min))
            else:
                OT2_state.pipette.dispense(volume=vol,location=dest.bottom(dispense_height),rate=float(rate_override_min))
                if not dest_filled:
                    if mix_after:                                  # pipetting is forced only when specified.
                        OT2_state.pipette.mix(pipetting_cycle,min(vol,OT2_state.max),dest.bottom(mix_height),rate=float(rate_override_min))
                else:
                    OT2_state.tip_dirty = True
                    ctx.comment('WARNING: Tip is dipped into filled destination during distribute. Pipetting in destination is cancelled (even specified by filling destination height or pipetting override). Contaminated liquid might be returned to source if return_source is True. Clear distribute override in CSV file to avoid cross-contamination')
                    if OT2_state.safety_catch and not OT2_state.tip_reuse == 'never':
                        OT2_state.pipette.drop_tip()    # safety catch for avove comment exception.
                        OT2_state.pipette.drop_tip()
            if not OT2_state.step_delay == 0:
                ctx.delay(seconds=float(OT2_state.step_delay))
            if not touchtip_d == None:
                OT2_state.pipette.touch_tip(location=dest,v_offset=(-1*int(touchtip_d)))
                if dest_filled:
                    OT2_state.tip_dirty = True
                    ctx.comment('WARNING: Tip touched filled destination during distribute. Clear distribute override in CSV file to avoid cross-contamination')
                    if OT2_state.safety_catch and not OT2_state.tip_reuse == 'never':
                            OT2_state.pipette.drop_tip()    # safety catch for avove comment exception.
                            OT2_state.pipette.drop_tip()
            line_counter += 1
        if return_source and (not OT2_state.tip_dirty or tip_reuse == 'never'):
            OT2_state.pipette.aspirate(volume=OT2_state.min,location=dest.top(-5),rate=float(rate_override_min))            # aspirate a bit to avoid deck contamination
            OT2_state.pipette.dispense(volume=OT2_state.min*2,location=source.top(-5),rate=float(rate_override_min))
            if not OT2_state.step_delay == 0:
                ctx.delay(seconds=float(OT2_state.step_delay))
            for i in range (int(OT2_state.blowout_cycle)) :
                OT2_state.pipette.blow_out(location=source.top(-5))    #Blow out user specified times (default = 2), as official blow_out setting is too weak. Blow out is executed every transfering movement including carryover to avoid accumulating remainig liquid.
        else:
            OT2_state.pipette.blow_out(location=ctx.fixed_trash['A1'])
            if OT2_state.detail_comment:
                if OT2_state.tip_dirty:
                    ctx.comment('Debug: Return_source is cancelled since the tip is dirty')
    # load labware
    transfer_info = [[val.strip().lower() for val in line.split(',')]
                     for line in transfer_csv.splitlines()
                     if line.split(',')[0].strip()][1:]
    for line in transfer_info:
        s_lw, s_slot, d_lw, d_slot = line[:2] + line[4:6]
        for slot, lw in zip([s_slot, d_slot], [s_lw, d_lw]):
            if not int(slot) in ctx.loaded_labwares:
                ctx.load_labware(lw.lower(), slot)

    OT2_state = OT2_state_class(parameter_dict)
    OT2_state.tip_last_dict = {'left':converter96well_invert(parse_well(left_tip_last_well)),'right':converter96well_invert(parse_well(right_tip_last_well))}
    if OT2_state.safety_catch == False:
        ctx.comment('WARNING: Safety catch is inactivated. Passing simulation does not certify the protocol is valid.')

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
            OT2_state.pipette_dict[hand].mix(1,OT2_state.min_dict[hand],location=ctx.loaded_labwares[int(transfer_info[0][1])].wells_by_name()[parse_well(transfer_info[0][2])].top())
            ctx.delay(seconds=3)
            OT2_state.pipette_dict[hand].return_tip()
        ctx.comment('Initial verification: Pause manually when calibration or configurations are incorrect. Installed pipette(s) are now picking up the last tip of the first tiprack(s) and move to the center of the top of the first source well. ')
        ctx.set_rail_lights(light_map[light_on][2])

    # Main transfer phase
    ctx.comment('Main transfer phase has started. OT-2 is transfering ' + str(len(transfer_info)) + ' lines.')
    line_cache = []
    OT2_state.line_num = -1 # count up from -1 as the first for loop is virtually skipped to store cache.
    if detail_comment:
        ctx.comment('Debug: Line cache is initialized')
    ctx.set_rail_lights(light_map[light_on][1])
    for line in transfer_info:
        OT2_state.line_num += 1
        if len(line) < 15 and detail_comment:
            ctx.comment('CAUTION: line ' + OT2_state.line_num + ' lacks optional columns and filled by blanks.')
        for i in range (len(line),15):
            line.append('')
        line_cache.append(line)
        if not distributable(line_cache):    # start distribute when it can not continue distibute with this line. Otherwise add the line and continue next loop.
            if len(line_cache) == 1:
                if detail_comment:
                    ctx.comment ('Debug: Now transfering line ' + str(OT2_state.line_num) + ' line cache length:' + str(len(line_cache)))
                transfer(line_cache[0])
                line_cache = []
            elif len(line_cache) == 2:
                if detail_comment:
                    ctx.comment ('Debug: Now transfering line ' + str(OT2_state.line_num) + ' line cache length:' + str(len(line_cache)))
                transfer(line_cache[0])
                line_cache = [line_cache[len(line_cache)-1]]
            else:
                if detail_comment:
                    ctx.comment ('Debug: Now distributing lines ' + str(OT2_state.line_num - len(line_cache) + 2)  + '-' + str(OT2_state.line_num) + ' line cache length:' + str(len(line_cache)))
                distribute(line_cache)
                line_cache = [line_cache[len(line_cache)-1]]
    OT2_state.line_num += 1
    if len(line_cache) == 1:
        if detail_comment:
            ctx.comment ('Debug: Now transfering the last line ' + str(OT2_state.line_num))
        transfer(line_cache[0])
    elif len(line_cache) > 1:
        line_cache.append([])
        if detail_comment:
            ctx.comment ('Debug: Now distributing the last lines ' + str(OT2_state.line_num - len(line_cache) + 2)  + '-' + str(OT2_state.line_num))
        distribute(line_cache)

    for hand in OT2_state.name_dict.keys():
        if mode == 'test_mode':                              # In case of test mode, tip will be returned to tipracks.
            OT2_state.pipette_dict[hand].return_tip()
        if OT2_state.pipette_dict[hand].has_tip:
            OT2_state.pipette_dict[hand].drop_tip()
            if detail_comment:
                ctx.comment('Debug: Tip on ' + hand + ' pipette is dropped into trash as all job completed.')
    ctx.set_rail_lights(light_map[light_on][3])
    ctx.comment('All job completed.')
