# pymegacli.py
#
#
# written by: Oliver Cordes 2015-11-13
# changed by: Oliver Cordes 2017-02-06

import os, sys
import shlex
import subprocess

class PyMegacli( object ):
    def __init__( self, adaptor=0, verbose=None, info=True ):
        self._adaptor  = adaptor
        self._verbose  = verbose
        self._info     = info
	
	self._errorlog = []

        ret = self._test_megacli()

        if ( ret != 0 ):
            raise NameError( 'megacli not found!')

        self.get_adaptor_info()

        if ( self._info ):
            print( 'Adaptor %i :' % self._adaptor )
            print( '  Product Name : %s ' % self._adaptor_info['Product Name'] )
            print( '  Serial No    : %s ' % self._adaptor_info['Serial No'] )
            print( '  FW Build     : %s' % self._adaptor_info['FW Package Build'] )
            print( '' )
        



    def _test_megacli( self ):
        cmd = 'which megacli'
        p = subprocess.Popen( cmd, shell=True, bufsize=-1,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, close_fds=True )
        p.wait()
        line = p.stdout.readlines()

        return p.returncode


    def _run_megacli( self, command='-PDList' ):

        cmd = 'megacli %s -a%i -NoLog' % ( command, self._adaptor )
        #print cmd

        scmd = shlex.split( cmd )

        p = subprocess.Popen( cmd, shell=True, bufsize=-1,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, close_fds=True )

        #p = subprocess.Popen( cmd, shell=True,
        #                        stdout=subprocess.PIPE,
        #                        close_fds=True )

        p.wait()
        line = p.stdout.readlines()
        lines = []
        for i in line:
            lines.append( i.replace( '\n', '' ) )

        return_code = p.returncode
        return return_code, lines


    def get_adaptor_info( self ):
        # get info on the adaptor
        ret,lines = self._run_megacli( command='-AdpAllInfo' )

        self._adaptor_info = {}
        
        for i in lines:
            s = i.split( ':', 1 )
            if len(s) > 1:
                # some string shaping
                s[0] = s[0].lstrip().rstrip()
                s[1] = ' '.join( s[1].split() )

                #print s
            if ( s[0] != '' ) and ( len(s) > 1 ):
                self._adaptor_info[s[0]] = s[1]
        
    
    def get_device_info( self ):
        # get list of all devices

        ret,lines = self._run_megacli( command='-PDList' )

        self._devices = []
        dev = None
        for i in lines:
            s = i.split( ':', 1 )
            if len(s) > 1:
                # some string shaping
                s[0] = s[0].rstrip()
                s[1] = ' '.join( s[1].split() )
            if ( s[0] == 'Enclosure Device ID' ):
                if ( dev is not None ):
                    self._devices.append( dev )
                dev = {}
                dev['error'] = 0

            if ( s[0] != '' ) and ( len(s) > 1 ):
                dev[s[0]] = s[1]

            if ( s[0] == 'Firmware state' ):
                if ( ( s[1] == 'Online, Spun Up' )
                    #or ( s[1] == 'Hotspare, Spun down' )
                    #or ( s[1] == 'Hotspare, Spun Up' ) ):
                    or ( 'Hotspare' in s[1] ) ):
                    dev['state'] = 0
                elif ( ( s[1] == 'Copyback' ) or ( s[1] == 'Rebuild' )):
                    dev['state'] = 2
                elif ( ( s[1] == 'Unconfigured(good), Spun down' )
                    or ( s[1] == 'Unconfigured(good), Spun Up' ) ):
                    dev['state'] = 3
                else:
                    # assuming some unknown state, report
                    self._errorlog.append( 'Firmware status of [%s:%s] is unknown/failed: %s' % ( dev['Enclosure Device ID'], dev['Slot Number'], s[1] ) ) 
                    dev['state'] = 1
            if ( s[0] == 'Raw Size' ):
                dev['size'] = ' '.join( s[1].split()[0:2] )
            if ( s[0] == 'Media Error Count' ):
                dev['error'] += int( s[1] )
            if ( s[0] == 'Other Error Count' ):
                dev['error'] += int( s[1] )
            if ( s[0] == 'Predictive Failure Count' ):
                dev['error'] += int( s[1] )

        # add the last drive
        if dev is not None:
            self._devices.append( dev )


    def get_virtual_drive_info( self ):
        # get list of all devices

        ret,lines = self._run_megacli( command='-LDInfo -Lall' )

        self._virtual_drives = []
        drive = None
        for i in lines:
            if ( i == '' ):
                continue
            s = i.split( ':', 1 )
            if len(s) > 1:
                # some string shaping
                s[0] = s[0].rstrip()
                s[1] = ' '.join( s[1].split() )
            
            if ( s[0] == 'Virtual Drive' ):
                if ( drive is not None ):
                    self._virtual_drives.append( drive )
                drive = {}

            if ( s[0] != '' ) and ( len(s) > 1 ):
                if drive is not None:
                    drive[s[0]] = s[1]
                    
            if ( s[0] == 'State' ):
                if (  s[1] == 'Optimal' ) :
                    drive['state'] = 0
                elif ( s[1] == 'Partially Degraded' ):
                    drive['state'] = 2
                else:
                    drive['state'] = 1

            if ( s[0] == 'Virtual Drive' ):
                drive['id'] = int( s[1].split()[0] )

            if ( s[0] == 'RAID Level' ):
                drive['raid'] = -1
                t = s[1].split( ',' )
                for i in t:
                    u = i.lstrip().rstrip().split( '-' )
                    if ( u[0] == 'Primary' ):
                        drive['raid'] = int( u[1] )
            if ( s[0] == 'Sector Size' ):
                drive['sector_size'] = s[1]
            if ( s[0] == 'Is VD emulated' ):
                drive['is_vd_emulated'] = s[1]
            if ( s[0] == 'Parity Size' ):
                drive['parity_size'] = s[1]
            if ( s[0] == 'Strip Size' ):
                drive['strip_size'] = s[1]
            if ( s[0] == 'Span Depth' ):
                drive['span_depth'] = s[1]
            if ( s[0] == 'Default Cache Policy' ):
                u = s[1].split( ',' )
                drive['write_policy'] = u[0]
                drive['read_policy']  = u[1].lstrip()
                drive['io_policy']    = '%s (%s)' % ( u[2].lstrip(), u[3].lstrip() )
            if ( s[0] == 'Current Cache Policy' ):
                u = s[1].split( ',' )
                drive['current_write_policy'] = u[0]
                drive['current_read_policy']  = u[1].lstrip()
                drive['current_io_policy']    = '%s (%s)' % ( u[2].lstrip(), u[3].lstrip() )
            if ( s[0] == 'Default Access Policy' ):
                drive['access_policy'] = s[1]
            if ( s[0] == 'Current Access Policy' ):
                drive['current_access_policy'] = s[1]
                                                      
            

        # add the last drive
        if drive is not None:
            self._virtual_drives.append( drive )


        # do some sanity checks:
        for i in self._virtual_drives:
            span_depth = int( i['Span Depth'] )
            if ( span_depth > 1 ):
                nrdisks = int( i['Number Of Drives per span'] )
                i['Number Of Drives'] = '%i' % ( span_depth * nrdisks )

            
            
    def device_info( self ):
        print( 'DEVICE LIST (%i devies):' % ( len(self._devices) )  )
        print( 'ID      Name                                            Capacity   Errors Status' )
        for i in self._devices:
            if ( i['state'] == 0 ):
                state = 'OK'
            elif ( i['state'] == 3 ):
                state = 'Free' 
            elif ( i['state'] == 2 ):
                state = 'Rebuild'
            else:
                state = 'Fail'
            did = '[%s:%s]' % ( i['Enclosure Device ID'], i['Slot Number'] )
            print( '%-7s %-47s %-10s %-6i %s' % ( did, i['Inquiry Data'], i['size'], i['error'], state ) )
            if i.has_key( 'Drive\'s position' ):
                print( '   %s' % ( i['Drive\'s position'] ) )
            elif( i['Firmware state'].find( 'Hotspare' ) != -1 ):
                print( '   HotSpare' )
            else:
                print( '   free' )
        print( '' )


    def ldinfo( self ):
        print( 'VIRTUAL DRIVE LIST (%i drives):' % ( len( self._virtual_drives) ) )
        print( 'LDx  Name                                    Raid    Nr.Disks Size        Status' )
        print( '--------------------------------------------------------------------------------' )
        for i in self._virtual_drives:
            if ( i['state'] == 0 ):
                state = 'OK'
            else:
                state = 'Fail'
            print( '%-3i  %-39s Raid-%-2i %-8s %-11s %s' % ( i['id'], i['Name'], i['raid'], i['Number Of Drives'], i['Size'], state ) )
            print( ' Options: ')
            if ( 'sector_size' in i ):
                print( '  Sector Size           : %s' % i['sector_size'] )
            if ( 'is_vd_emulated' in i ):    
                print( '  Is VD emulated        : %s' % i['is_vd_emulated'])
            if ( 'parity_size' in i ):
                print( '  Parity Size           : %s' % i['parity_size'])
            if ( 'strip_size' in i ):
                print( '  Strip Size            : %s' % i['strip_size'] )
            if ( 'span_depth' in i ):
                print( '  Span Depth            : %s' % i['span_depth'] )
            if ( 'rad_policy' in i ):
                print( '  Read Policy           : %s' % i['read_policy'] )
                print( '  Write Policy          : %s' % i['write_policy'] )
                print( '  IO Policy             : %s' % i['io_policy'] )
            if ( 'access:policy' in i ):
                print( '  Access Policy         : %s' % i['access_policy'] )
            if ( 'current_read_policy' in i ):
                print( '  Current Read Policy   : %s' % i['current_read_policy'] )
                print( '  Current Write Policy  : %s' % i['current_write_policy'] )
                print( '  Current IO Policy     : %s' % i['current_io_policy'] )
            if ( 'current_access_poliy' in i ):
                print( '  Current Access Policy : %s' % i['current_access_policy'] )
            print( '--------------------------------------------------------------------------------' )
        print( '')


    def virtual_drive_info( self ):
        print( 'VIRTUAL DRIVE LIST (%i drives):' % ( len( self._virtual_drives) ) )
        print( 'LDx  Name                                    Raid    Nr.Disks Size        Status' )
        for i in self._virtual_drives:
            if ( i['state'] == 0 ):
              state = 'OK'
            elif ( i['state'] == 2 ):
	      state = 'Partially Degraded or Rebuild'
            else:
              state = 'Fail'
            print( '%-3i  %-39s Raid-%-2i %-8s %-11s %s' % ( i['id'], i['Name'], i['raid'], i['Number Of Drives'], i['Size'], state ) )
        print( '')


    # check for error states
    def get_status( self ):
        gerror = False
        # check the physical devices
        error = False
        for i in self._devices:
            if ( ( i['state'] == 1 ) or ( i['state'] == 2 ) ):
                if error == False:
                    print( 'Devices status: Failed/Rebuilding' )
                    print( 'ID      Name                                            Capacity   Errors Status' )
                    error = True
                    gerror = True
                did = '[%s:%s]' % ( i['Enclosure Device ID'], i['Slot Number'] )
                if ( i['state'] == 1 ):
                    print( '%-7s %-47s %-10s %-6i %s' % ( did, i['Inquiry Data'], i['size'], i['error'], 'Fail' ) )
                else:
                    print( '%-7s %-47s %-10s %-6i %s' % ( did, i['Inquiry Data'], i['size'], i['error'], 'Rebuild' ) )
                #if i.has_key( 'Drive\'s position' ):
                #    print( '   %s' % ( i['Drive\'s position'] ) )
                #else:
                #    print( '   free' )

        if ( error == False ):
            print( 'Devices status: OK' )

        # check the physical devices
        error = False
        for i in self._virtual_drives:
            if ( i['state'] == 1 ):
                if error == False:
                    print( 'Virtual drives status: Failed' )
                    print( 'LDx  Name                                    Raid    Nr.Disks Size        Status' )
                    error = True
                    gerror = True
                print( '%-3i  %-39s Raid-%-2i %-8s %-11s %s' % ( i['id'], i['Name'], i['raid'], i['Number Of Drives'], i['Size'], state ) )

        if ( error == False ):
            print( 'Virtual drives status: OK' )

	if ( self.write_errorlog() == 1 ):
	    gerror = True

        if ( gerror ):
            return 1
        else:
            return 0

    def nagios( self ):
        rebuild = 0
        error = 0
        s = ''
        failed_drives = 0	
        for i in self._devices:
            if ( ( i['state'] == 1 ) or ( i['state'] == 2 ) ):
                failed_drives += 1
                if ( s != '' ):
                    s += ' ; ' 
                did = '[%s:%s]' % ( i['Enclosure Device ID'], i['Slot Number'] )
                if ( i['state'] == 1 ):
               	    error = 1
                    s += 'Drive in slot %s falied' % did
                else:
                    rebuild = 1
                    s += 'Drive in slot %s rebuilding' % did
              

        if ( error == 1 ) :
            print( 'CRITICAL - %s | Failed_drives=%i;1;1;0' % ( s, failed_drives ) )
            return 2

        if ( rebuild == 1 ):
            print( 'WARNING - %s | Failed_drives=%i;1;1;0' % ( s, failed_drives ) )
            return 1

        print( 'OK - %i drives, %i virtual drives | Failed_drives=0;1;1;0' % ( len( self._devices ), len( self._virtual_drives ) ) )
        return 0

    def write_errorlog( self ):
	if ( len( self._errorlog ) > 0 ):
	   print( 'Errorlog:' )
           nr = 1
           for i in self._errorlog:
             print( '%3i: %s' % ( nr, i ) )
             nr +=1
           return 1
        else:
	   return 0
                

    def geteventlog( self ):
        # megacli AdpEventLog GetEvents {info warning critical fatal} {f test.log }  a0
	return 


    def alarm_silence( self ):
        # megacli -AdpSetProp -AlarmSilence -aALL
        ret,lines = self._run_megacli( command='-AdpSetProp -AlarmSilence' )
        if ( ret == 0 ):
          print( 'Alarm Silence succesfull!')
        else:
          print( 'Alarm Silence failed!')
        return
