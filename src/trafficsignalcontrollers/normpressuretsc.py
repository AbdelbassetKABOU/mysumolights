import random
from itertools import cycle
from collections import deque
import traci

from src.trafficsignalcontroller import TrafficSignalController
 
class NormPressureTSC(TrafficSignalController):
    def __init__(self, conn, tsc_id, mode, netdata, red_t, yellow_t, green_t):
        super().__init__(conn, tsc_id, mode, netdata, red_t, yellow_t)
        # print ('----------------------------')
        # print ('  def __init__(self, conn:')
        # print ('----------------------------')
        self.green_t = green_t
        # print('['+tsc_id+']['+self.id+'][10]['+str(self.green_t)+'] Normpressure:__init__(self, ...')        
        self.t = 0
        #for keeping track of vehicle counts for websters calc
        self.phase_deque = deque()
        self.norm_pressure_lanes = self.norm_pressure_lanes()
        self.data = None
        #store how many green movements each phase has
        #for breaking ties in norm-pressure
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
            norm_pressure_phase = self.norm_pressure()
            # print ('     $ len(self.phase_deque) = 0 !!')                        
            # print ('     $ norm_pressure_phase = self.norm_pressure()')                        
            # print ('       > norm_pressure_phase = ', norm_pressure_phase)
            phases = self.get_intermediate_phases(self.phase, norm_pressure_phase)
            # print ('     $ phases = self.get_intermediate_phases(self.phase, norm_pressure_phase)')
            # print ('       > phases = ', phases)
            self.phase_deque.extend(phases+[norm_pressure_phase])
        #     print ('     $ self.phase_deque.extend(phases+[norm_pressure_phase])')
        #     print ('       > self.phase_deque = ', self.phase_deque)            
        # print ('     >>> this function should return self.phase_deque.popleft() ')                                  
        # print ('------------------------------------------------')        
        return self.phase_deque.popleft()

    def norm_pressure_lanes(self):
        """for each green phase, get all incoming
        and outgoing lanes for that phase, store
        in dict for norm-pressure calculation
        """
        # print ('----------------------------')
        # print ('  def norm_pressure_lanes :')
        # print ('----------------------------')
        # print ('  norm_pressure_lanes[g] = {\'inc\':inc_lanes, \'out\':out_lanes}')
        # print('['+self.id+'][38]['+str(self.green_t)+'] def norm_pressure_lanes(self): ...')
        norm_pressure_lanes = {}
        for g in self.green_phases:
            inc_lanes = set()
            out_lanes = set()
            for l in self.phase_lanes[g]:
                inc_lanes.add(l)
                for ol in self.netdata['lane'][l]['outgoing']:
                    out_lanes.add(ol)

            norm_pressure_lanes[g] = {'inc':inc_lanes, 'out':out_lanes}
        # # print ('    norm_pressure_lanes =',norm_pressure_lanes)
        # for phase, content in norm_pressure_lanes.items():
        #     # print ('    ...............')
        #     # print ('    ', phase)
        #     for orientation, inside in content.items():
        # #         print ('     ',orientation, '==>', inside)
        # # print ('---------------------------------------------')
        return norm_pressure_lanes

    def norm_pressure(self):
        # print('['+self.id+'][52]def norm_pressure(self):')
        phase_pressure = {}
        theirphase_pressure = {}        
        no_vehicle_phases = []
        #myadd
        # print('['+self.id+'][54] self.green_phases??')
        # print (type(self.green_phases))
        # print (self.green_phases)

        #What could I do with self.data
        #for lane, content in self.data.items():
            # print ('lane : ',lane)
            # print ('type(lane capacity) = : ', type(self.lane_capacity))
            # #print ('lane capacity : ',self.lane_capacity)
            # print ('lane capacity : ', float(self.netdata['lane'][lane]['length'])/7.5)
            # print ('content : ',content)                
            # traci.lane.getLength(edgeID + "_0")

        # compute pressure for all green movements
        for g in self.green_phases:
            inc_lanes = self.norm_pressure_lanes[g]['inc']
            out_lanes = self.norm_pressure_lanes[g]['out']
            #pressure is defined as the number of vehicles in a lane
            theirinc_pressure = sum([ len(self.data[l]) if l in self.data else 0 for l in inc_lanes])
            inc_pressure = sum([ len(self.data[l])/(float(self.netdata['lane'][l]['length'])/7.5) if l in self.data else 0 for l in inc_lanes])
            theirout_pressure = sum([ len(self.data[l]) if l in self.data else 0 for l in out_lanes])
            out_pressure = sum([ len(self.data[l])/(float(self.netdata['lane'][l]['length'])/7.5) if l in self.data else 0 for l in out_lanes])
            phase_pressure[g] = inc_pressure - out_pressure
            theirphase_pressure[g] = theirinc_pressure - theirout_pressure            

            if inc_pressure == 0 and out_pressure == 0:
                no_vehicle_phases.append(g)

        ###if no vehicles randomly select a phase
        if len(no_vehicle_phases) == len(self.green_phases):
            return random.choice(self.green_phases)
        else:
            #choose phase with norm-pressure
            #if two phases have equivalent pressure
            #select one with more green movements
            #return max(phase_pressure, key=lambda p:phase_pressure[p])
            phase_pressure = [ (p, phase_pressure[p]) for p in phase_pressure]
            phase_pressure = sorted(phase_pressure, key=lambda p:p[1], reverse=True)
            phase_pressure = [ p for p in phase_pressure if p[1] == phase_pressure[0][1] ]

            theirphase_pressure = [ (p, theirphase_pressure[p]) for p in theirphase_pressure]
            theirphase_pressure = sorted(theirphase_pressure, key=lambda p:p[1], reverse=True)
            theirphase_pressure = [ p for p in theirphase_pressure if p[1] == theirphase_pressure[0][1] ]

            mine = random.choice(phase_pressure)[0]
            their = random.choice(theirphase_pressure)[0]
            #if mine != their :
                # print ('____________________')
                # print ('phase_pressure : ', mine)
                # print ('theirphase_pressure : ', their)            
            return random.choice(phase_pressure)[0]

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
        # print('['+self.id+'][99]['+str(self.green_t)+'] def next_phase_duration(self):')
        if self.phase in self.green_phases:
            return self.green_t
        elif 'y' in self.phase:
            return self.yellow_t
        else:
            return self.red_t

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
