#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Usage:
#
#   python test.py [--test <all(default)|database|email>] 
#                  [--database <memory(default)|heroku|sqlite>] 
#
#   test items can be chained. I.E. `--test database email`

from clint import args
from clint.textui import puts, colored, indent

errors = []
def record_error(message, e):
  errors.append([message, e])

# ========================================================================
# Arguments
# ========================================================================

# Defaults
db_type  = 'memory'
test = {'database': True, 'email': True}

if args.contains('--database'):
  arg = args.grouped['--database'][0]
  if arg == 'heroku':
    db_type = 'heroku'
  if arg == 'sqlite':
    db_type = 'sqlite'
if args.contains('--test'):
  test_args = args.grouped['--test']
  if 'all' in test_args:
    pass
  elif 'database' not in test_args:
    test['database'] = False
  elif 'email' not in test_args:
    test['email'] = False

puts('Testing:')
with indent(4):
  for key, value in test.items():
    if value:
      puts(colored.blue(key))

if args.contains('--database'):
  puts('Database: %s' % db_type)

# ========================================================================
# Database
# ========================================================================

if test['database']:
  puts(colored.blue('\nTesting database...'))

  from models import Reservation, Flight, FlightLeg, FlightLegLocation
  from db import Database

  if db_type == 'memory':
    db = Database()
  elif db_type == 'sqlite':
    db = Database('test.db')
  elif db_type == 'heroku':
    db = Database(heroku=True)

  db.create_all()

  puts('Adding a reservation...')
  try:
    res = Reservation('Bob', 'Smith', '999999', 'email@email.com')
    db.Session.add(res)
    db.Session.commit()
  except Exception, e:
    record_error('Failed on adding the reservation', e)

  puts('Adding a flight...')
  try:
    flights = []
    flights.append(Flight())
    flights[0].sched_time = 10.0
    flights.append(Flight())
    res.flights = flights
    db.Session.commit()
  except Exception, e:
    record_error('Failed on adding the flight', e)

  puts('Adding a flight leg...')
  try:
    res.flights[0].legs.append(FlightLeg())
    res.flights[1].legs.append(FlightLeg())
    res.flights[0].legs[0].flight_number = "1234"
    db.Session.commit()
  except Exception, e:
    record_error('Failed on adding a flight leg', e)

  puts('Adding a flight location...')
  try:
    res.flights[0].legs[0].depart = FlightLegLocation()
    res.flights[0].legs[0].depart.airport = 'AUS'
    db.Session.commit()
  except Exception, e:
    record_error('Failed on adding the reservation', e)

  puts('Querying data...')
  try:
    for instance in db.Session.query(Reservation): 
      with indent(4, quote='>'):
        puts('Reservation: %s %s' % (instance.first_name, instance.code))
        puts('First flight scheduled time: %s ' % str(instance.flights[0].sched_time))
        puts('First flight, first leg, flight #: %s' % instance.flights[0].legs[0].flight_number)
        puts("First flight, first leg location's airport: %s" % instance.flights[0].legs[0].depart.airport)
  except Exception, e:
    record_error('Failed on querying', e)

  if db_type == 'heroku':
    try:
      puts('Deleting test data from Heroku database...')
      db.deleteReservation(res)
    except Exception, e:
      record_error('Failed on deletion', e)

  if db_type == 'sqlite':
    try:
      puts('Deleting sqlite test database...')
      from os import remove
      remove('test.db')
    except Exception, e:
      record_error('Failed to delete test database', e)

# ========================================================================
# Email
# ========================================================================

if test['email']:
  puts(colored.blue('\nTesting email...'))

  import getpass
  from datetime import datetime
  from sw_checkin_email import (should_send_email, email_from,
    smtp_user, smtp_password, smtp_auth, send_email)

  email_to = 'sw.automatic.checkin@gmail.com'

  if should_send_email:
      if not email_from:
        record_error('There is no from email configured', 'From email address missing')
      if email_from:
        if not smtp_user:
          smtp_user = email_from
        if not smtp_password and smtp_auth:
          record_error('There is no smtp password configured', 'SMTP password missing')
        try:
          send_email('Southwest Checkin Test ' + str(datetime.now()), 'Test email body', boarding_pass=None, email=email_to)
        except Exception, e:
          record_error('Failed sending email', e)
      else:
        should_send_email = False
        record_error('Did not get user input to send email', 'The user did not enter a from email address')

# ========================================================================
# Results
# ========================================================================

if len(errors) == 0:
  puts(colored.green('Success!'))
else:
  puts(colored.red(':( There were some errors:'))
  for i, e in enumerate(errors, 1):
    puts(colored.red('ERROR %s:' % i))
    with indent(4, quote=colored.red('>')):
      puts('Message: %s' % e[0])
      puts('Exception: %s' % e[1])
