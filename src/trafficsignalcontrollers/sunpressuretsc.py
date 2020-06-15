import random
from itertools import cycle
from collections import deque
import traci

from src.trafficsignalcontroller import TrafficSignalController
 
class SunPressureTSC(TrafficSignalController):
    def __init__(self, conn, tsc_id, mode, netdata, red_t, yellow_t, green_t):
        super().__init__(conn, tsc_id, mode, netdata, red_t, yellow_t)
        # print ('----------------------------')
        # print ('  def __init__(self, conn:')
        # print ('----------------------------')
        self.mysunpressure = self.last_sunpressure = ''
        self.green_t = green_t
        # print('['+tsc_id+']['+self.id+'][10]['+str(self.green_t)+'] Normpressure:__init__(self, ...')        
        self.t = 0
        #for keeping track of vehicle counts for websters calc
        self.phase_deque = deque()
        self.sun_pressure_lanes = self.sun_pressure_lanes()
        self.data = None
        #store how many green movements each phase has
        #for breaking ties in sun-pressure
        self.phase_g_count = {}
        for p in self.green_phases:
            self.phase_g_count[p] = sum([1 for m in p if m == 'g' or m == 'G'])        

        # print("   We are at the TSC named: ", tsc_id) #[mycode] it was commented
        # print("   self.green_t: ",  self.green_t) 
        # print('   self.phase_deque ==>', self.phase_deque)  
        # print('   self.green_phases ==>', self.green_phases)                            
        # print('   self.t ==>', self.t)  
        # print('   self.phase_time ==>', self.phase_time)                         
        # print('----------------------------')

    def next_phase(self):
        ###need to do deque here
        # print('['+self.id+'][26]['+str(self.green_t)+'] next_phase(self) ...')
        # print ('----------------------------')
        # print ('def next_phase(self):')
        # print ('----------------------------')
        # print ('     self.phase_deque ==>', self.phase_deque)
        # print ('     -- its type is :', type(self.phase_deque))
        # print ('     self.phase :', self.phase)
        # print ('     self.t ==>', self.t)         
        # print ('     self.phase_time ==>', self.phase_time)  
        if len(self.phase_deque) == 0:
            self.last_sunpressure = self.mysunpressure
            sun_pressure_phase = self.sun_pressure()
            # print ('     $ len(self.phase_deque) = 0 !!')                        
            # print ('     $ sun_pressure_phase = self.sun_pressure()')                        
            # print ('       > sun_pressure_phase = ', sun_pressure_phase)
            phases = self.get_intermediate_phases(self.phase, sun_pressure_phase)
            # print ('     $ phases = self.get_intermediate_phases(self.phase, sun_pressure_phase)')
            # print ('       > phases = ', phases)
            self.phase_deque.extend(phases+[sun_pressure_phase])
        #     print ('     $ self.phase_deque.extend(phases+[sun_pressure_phase])')
        #     print ('       > self.phase_deque = ', self.phase_deque)            
        # print ('     >>> this function should return self.phase_deque.popleft() ')                                  
        # print ('------------------------------------------------')        
        return self.phase_deque.popleft()

    def sun_pressure_lanes(self):
        """for each green phase, get all incoming
        and outgoing lanes for that phase, store
        in dict for sun-pressure calculation
        """
        # print ('----------------------------')
        # print ('  def sun_pressure_lanes :')
        # print ('----------------------------')
        # print ('  sun_pressure_lanes[g] = {\'inc\':inc_lanes, \'out\':out_lanes}')
        # print('['+self.id+'][38]['+str(self.green_t)+'] def sun_pressure_lanes(self): ...')
        sun_pressure_lanes = {}
        for g in self.green_phases:
            inc_lanes = set()
            out_lanes = set()
            for l in self.phase_lanes[g]:
                inc_lanes.add(l)
                for ol in self.netdata['lane'][l]['outgoing']:
                    out_lanes.add(ol)

            sun_pressure_lanes[g] = {'inc':inc_lanes, 'out':out_lanes}
        # # print ('    sun_pressure_lanes =',sun_pressure_lanes)
        # for phase, content in sun_pressure_lanes.items():
        #     # print ('    ...............')
        #     # print ('    ', phase)
        #     for orientation, inside in content.items():
        # #         print ('     ',orientation, '==>', inside)
        # # print ('---------------------------------------------')
        return sun_pressure_lanes

    def sun_pressure(self):
        # print ('------------------------------------------------')                
        # print (' >>> def sun_pressure(self):')
        # print ('------------------------------------------------')        
        phase_pressure = {}
        theirphase_pressure = {}        
        no_vehicle_phases = []
        #myadd
        # print('['+self.id+'][54] self.green_phases??')
        # print (type(self.green_phases))
        # print ('      self.last_sunpressure = ', self.last_sunpressure)        
        # print ('      self.green_phases = ', self.green_phases)
        exists = self.mysunpressure in self.green_phases
        # print ('      is self.mysunpressure in green_phases ?? ', exists)
        if exists :
            myindex = self.green_phases.index(self.last_sunpressure)
        else :
            myindex = -1
        #     print ('  this is normally just the start ...')
        # print ('      index of ', self.last_sunpressure, ' is ', myindex)
        self.mysunpressure = self.green_phases [(myindex+1)%len(self.green_phases)]
        # print ('      self.mysunpressure = ', self.mysunpressure)
        # print ('-----------------------------------------------')
        return self.mysunpressure

        '''
        if len(phase_pressure) == 1:
            return phase_pressure[0][0]
        else:
            #if two phases have same pressure and same number of green movements
            green_count = [ (p[0], self.phase_g_count[p[0]]) for p in phase_pressure ]
            green_count = sorted(green_count, key=lambda p:p[1], reverse=True)
            green_count = [ p for p in green_count if p[1] == green_count[0][1] ]
            if len(green_count) == 1:
                return green_count[0][0]
            else:
                return random.choice(green_count)[0]
        '''


    def next_phase_duration(self):
        if self.phase in self.green_phases:
            #return self.green_t
            return self.get_green_duration ()
        elif 'y' in self.phase:
            return self.yellow_t
        else:
            return self.red_t

    def get_green_duration(self):
        print ('----------------------------------')
        print ('  def get_green_duration(self):') 
        print ('----------------------------------') 
        phase_pressure = {}
        no_vehicle_phases = []       
        total_phasepressure = 0

        # compute pressure for all green movements
        for g in self.green_phases:
            inc_lanes = self.sun_pressure_lanes[g]['inc']
            out_lanes = self.sun_pressure_lanes[g]['out']
            #pressure is defined as the number of vehicles in a lane
            inc_pressure = sum([ len(self.data[l])/(float(self.netdata['lane'][l]['length'])/7.5) if l in self.data else 0 for l in inc_lanes])
            out_pressure = sum([ len(self.data[l])/(float(self.netdata['lane'][l]['length'])/7.5) if l in self.data else 0 for l in out_lanes])
            phase_pressure[g] = inc_pressure - out_pressure
            total_phasepressure =+ phase_pressure[g]
            if inc_pressure == 0 and out_pressure == 0:
                print ('    ga3 = 0: inc_pressure = out_pressure = 0 ...')
                no_vehicle_phases.append(g)

        ###if no vehicles randomly select a phase
        if len(no_vehicle_phases) == len(self.green_phases):
            #return random.choice(self.green_phases)
            print ('      len(no_vehicle_phases) = len(self.green_phases) :/')
            print ('      so return min green')
            print ('-------------------------------------')
            #return self.green_t
        else:
            # choose phase with sun-pressure
            # if two phases have equivalent pressure
            # select one with more green movements
            # return max(phase_pressure, key=lambda p:phase_pressure[p])
            if total_phasepressure == 0:
                print ('      total_phasepressure = 0 (avoid devision by zero)')
                print ('      so return min green')
                print ('-------------------------------------')
                return self.mingreen_t
            else:
                mycalculation = phase_pressure[self.mysunpressure]/total_phasepressure
                print ('      len(no_vehicle_phases) != len(self.green_phases) :/') 
                print ('      return mycalculation = ', mycalculation)
                #return mycalculation
        print ('-------------------------------------')
        return self.green_t

    def update(self, data):
        #print('['+self.id+'][108]['+str(self.green_t)+'] def update(self, data): ...')
        # print ('----------------------------')
        # print ('def update(self, data):')
        # print ('----------------------------')
        # print ('     $ self.data = data')
        # print ('       -- self.phase_deque ==>', self.phase_deque)
        # print ('       -- self.phase :', self.phase)
        # print ('       -- self.t :', self.t)        
        # print ('       -- self.phase_time ==>', self.phase_time)  
        self.data = data 
        # print ('self.data = ', self.data)
        # print ('----------------------------')        
