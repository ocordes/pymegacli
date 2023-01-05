#!/usr/bin/env python3

# mcli.py
#
#
# written by: Oliver Cordes 2015-11-13
# changed by: Oliver Cordes 2023-01-05
#
#


import os,sys
import socket
import getopt

# for email sending
from io import StringIO
import smtplib
from email.mime.text import MIMEText


from pymegacli import PyMegacli


__version__ = "0.2.10"
__date__    = '2023-01-05'
__needs__   = 3.6
__author__  = "Oliver Cordes"


# main variables
_verbose    = False
_action     = 'info'
_adaptor    = 0
_do_mail    = False
_mail_from  = '<ocordes@astro.uni-bonn.de>'
_mail_to    = '<ocordes@astro.uni-bonn.de>'
_smtp       = 'localhost'
_smtpport   = 25
_smtpuser   = None
_smtppass   = None
_smtpssl    = None



def syntax( exitcode=0 ):
    print( 'SYNTAX: mcli [PARAMS] (Version %s)' % __version__ )
    print( ' PARAMS: ')
    print( '   -v              : activate verbose mode' )
    print( '   --help|-h|-?    : this help page' )
    print( '   --info          : overview of the current configuration and status' )
    print( '   --ldinfo        : precise information about logical drives (arrays)' )
    print( '   --silence       : Silence the alarm for all adaptors!' )
    print( '   --status        : short summary of currect status' )
    print( '   --smpt=server   : specify the mail server for sending emails' )
    print( '   --smtpport=port : port od the outgoing server' )
    print( '   --smtpuser=user : username for mail authentication' )
    print( '   --smtppass=pass : password for mail authentication' )
    print( '   --mail=addr     : send the status via mail to addr (available only with' )
    print( '                     --status)' )
    print( '   --from=addr     : mail from addess (available only with --mail)' )
    print( '   --ssl           : using SSL encryption for mail sending' )
    print( '   --starttls      : using STARTTLS for mail encryption' )

    
    sys.exit( exitcode )


# check for parameters


if ( len( sys.argv ) < 2 ):
    syntax()

long_options = ['info', 'help', 'nagios', 'status', 'mail=', 'from=',
                'smtp=', 'smtpport=', 'smtpuser=', 'smtppass=',
                'ssl', 'starttls', 'ldinfo', 'silence'  ]


try:
    opts, args = getopt.getopt( sys.argv[1:], 'h?a:', long_options )
except getopt.GetoptError(s):
    print( 'Error while parsing command parameters!' )
    syntax( 1 )

for key,val in opts:
    if ( key == '-?' ) or ( key == '-h' ) or ( key == '--help' ) :
        syntax()
    elif ( key == '--info' ):
        _action = 'info'
    elif ( key == '--nagios' ):
        _action = 'nagios'
    elif ( key == '--status' ):
        _action = 'status'
    elif ( key == '--ldinfo' ):
        _action = 'ldinfo'
    elif ( key == '--silence' ):
        _action = 'silence'

    elif ( key == '-a' ):
        _adaptor = int( val )
    elif ( key == '--mail' ):
        _do_mail = True
        _mail_to = val
    elif ( key == '--from' ):
        _mail_from = val
    elif ( key == '--smtp' ):
        _smtp = val
    elif ( key == '--smtpport' ):
        _smtpport = int( val )
    elif ( key == '--smtpuser' ):
        _smtpuser = val
    elif ( key == '--smtppass' ):
        _smtppass = val
    elif ( key == '--ssl' ):
        _smtpssl = 'SSL'
    elif ( key == '--starttls' ):
        _smtpssl = 'STARTTLS'
        
    elif ( key == '-v' ):
        _verbose = True
    
# main

#print _smtp, _smtpport, _smtpuser, _smtppass

if ( ( _action != 'status' ) and ( _action != 'nagios' ) ):
    print( 'mcli Version %s (C) 2015 by %s' % ( __version__, __author__ ) )
    print( '' )
    mc = PyMegacli( adaptor = _adaptor,
                    verbose = _verbose )
else:
    mc = PyMegacli( adaptor = _adaptor,
                    verbose = _verbose,
                    info    = False )

mc.get_device_info()
mc.get_virtual_drive_info()

if ( _action == 'info' ):
    mc.device_info()
    mc.virtual_drive_info()
elif ( _action == 'nagios' ):
    ret = mc.nagios()
    sys.exit( ret )
elif ( _action == 'ldinfo' ):
    mc.ldinfo()
elif ( _action == 'silence' ):
    mc.alarm_silence()
elif ( _action == 'status' ):
    if ( _do_mail ):
        # change the output direction
        output = StringIO()
        stdout_old = sys.stdout
        sys.stdout = output

        # get the status
        ret = mc.get_status()

        # restore old ourput
        sys.stdout = stdout_old
        output.seek( 0 )

        # if error then send message
        if ( ret != 0 ):
            msg = MIMEText( output.read() )
            msg['Subject'] = 'megacli RAID status on %s' % socket.gethostname()
            msg['From'] = _mail_from
            msg['To'] = _mail_to

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            if ( _smtpssl is not None ):
                if ( _smtpssl == 'SSL' ):
                    s = s = smtplib.SMTP_SSL( _smtp, _smtpport )
                else:
                    s = smtplib.SMTP( _smtp, _smtpport )
                    s.starttls()
            else:
                s = smtplib.SMTP( _smtp, _smtpport )
            if ( _smtpuser is not None ):
                if ( _smtppass is None ):
                    print( 'Can\'t authticate uzser, no password given!Omit authentication!' )
                else:
                    s.login( _smtpuser, _smtppass )
            _mail_to_s = _mail_to.split( ',' )
            try:
                s.sendmail( _mail_from, _mail_to_s, msg.as_string())
            except smtplib.SMTPRecipientsRefused(errmsg):
                # error messages for each sender
                for i in errmsg.recipients:
                    print( 'Mail problem for %s: %s' % ( i, errmsg.recipients[i] ) )
            except smtplib.SMTPDataError(errmsg):
                print( 'Mail problem: %s' % errmsg )
            s.quit()

    else:
        mc.get_status()

