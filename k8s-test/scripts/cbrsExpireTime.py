#!/usr/bin/python
# Example usage
# while :; do date >> exp_time.txt ; python cbrsExpireTime.py "cmedit get LTE40dg2ERBS00001;LTE78dg2ERBS00044;LTE38dg2ERBS00001;LTE40dg2ERBS00003 EUtranCellTDD.(CbrsTxExpireTime)" | grep cbrs | sort >> exp_time.txt ; sleep 10 ; done &
import enmscripting
import sys

if (len(sys.argv) != 2):
  sys.exit(1)

command = sys.argv[1]

print("Command is: " + command)

terminal = enmscripting.open().terminal()

print("Executing CLI command: " + command)

response = terminal.execute(command)
list = []

fdn = ""
for line in response.get_output():
  if "FDN" in line:
    fdn = line.split("EUtranCellTDD=")[1]
  elif "cbrsTxExpireTime" in line:
    print(fdn + " : " + line)
    fdn = ""
