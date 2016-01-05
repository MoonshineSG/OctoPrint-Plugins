#Multiple OctoPrint plugins (mostly for my own use)

####snapshot
required by https://github.com/MoonshineSG/OctoPrint/tree/snapshot_timelapse 

####cooling
Wait for the bed temperature to reach a value set by W parameter of M140 (M140 W0) then play a sound and then printer off.

####half_speed_fan
Rewrite M106 to half speed

####prowl_alerts
Send prowl alerts on elected events.
Change settings by manually editing `config.yaml` under "plugins"

```
  prowl_alerts:
    name: 
    url: 

```
- name: the alert sender (default: Octoprint)
- url: link to the server for downloading timelapse movies (default: vlc://octoprint.local) 

####start_printer
Make sure power is on when starting the heaters

