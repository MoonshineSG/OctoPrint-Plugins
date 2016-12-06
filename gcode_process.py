# coding=utf-8

import octoprint.plugin
import octoprint.filemanager
import octoprint.filemanager.util
import os

class ReplaceKeywords(octoprint.filemanager.util.LineProcessorStream):
	
	dual_extruder = False
	single_nozzle = False
	accelerated = False
	volcano = False
	pva = False
	
	saved_line = ""
	
	def get_gcode(self, line):
		code_file = os.path.join("/home/pi/.octoprint/scripts/gcode/preprocessor", "%s.gcode"%line)
		if os.path.isfile(code_file):
			with open(code_file) as foo:
				return foo.read()
		return "M117 No valid PID found for '%s'. Using default."%line
		
	def process_line(self, line):
		prev_line = self.saved_line
		self.saved_line = line
		
		if line.startswith(";   printExtruders"):
			self.dual_extruder = "single" not in line
			self.single_nozzle = "cyclops" in line
			self.volcano = "volcano" in line

		elif line.startswith(";   printMaterial"):
			self.pva = "PVA" in line

		elif line.startswith("; ACCELERATED"):
			self.accelerated = True

		elif line.startswith("T0"):
			if self.pva:
				return "\nM92 E425\nT0"

		elif line.startswith("T1"):
			if self.pva:
				#+ 10%
				return "\nM92 E467.5\nT1" 

		elif line.startswith("; SET_PID"):
			if self.single_nozzle:
				return self.get_gcode("set_pid_cyclops")
			elif self.volcano:
				return self.get_gcode("set_pid_volcano")
			else:
				return self.get_gcode("set_pid")

		elif line.startswith("; SET_TEMPERATURES"): #;SET_TEMPERATURES 60 195 0
			newline = """
; SET_TEMPERATURES
G1 X100 Y100 Z10  F10000   ; move to middle

M190 S%s	; wait for bed temp
M300 @temperature_bed		; beep

M109 T0 S%s 	; wait for left extruder temp
M300 @temperature_extruder	; beep

"""%(line.split()[2], line.split()[3])
			
			if self.dual_extruder:
				newline = """%s
M109 T1 S%s	; wait for right extruder temp
M300 @temperature_extruder	; beep

"""%(newline, line.split()[4])
			return newline

		elif line.startswith("; PRIME_NOZZLE"):
			if self.dual_extruder or self.single_nozzle:
				newline = """
; PRIME_NOZZLE DUAL
M808 active_extruders 2

; move outside bed
G1 X-30 Y0 F8000
G1 Z10 F3000

; purge nozzles one by one
T0
G1 E15 F150
G4 P500
T1
G1 E15 F150
G4 P500
T0
G1 E5 F250
G4 P800
T1
G1 E5 F250
G4 P800
T0
G1 E10 F350
G4 P1000
T1
G1 E10 F350
G4 P1000
T0
G1 E15 F500
G4 P1500
T1
G1 E15 F500
G4 P1500

;whipe
G1 Y10 F8000
G1 Z0 F3000
G1 X10 F8000
G1 Z1 F3000

;retract
G1 E-5 F3000
T0
G1 E-5 F3000

"""
			else:
				newline = """
; PRIME_NOZZLE SINGLE
M808 active_extruders 1

; move outside bed
G1 X-10 Y0 F8000 	
G1 Z10 F3000 	

; purge nozzle
G1 E15 F150
G4 P500
G1 E5 F250
G4 P800
G1 E10 F350
G4 P1000
G1 E15 F500
G4 P1500

;whipe
G1 Y10 F8000
G1 Z0 F3000
G1 X10 F8000
G1 Z1 F3000

;retract
G1 E-5 F3000
"""

			return newline

		elif line.startswith("; SET_E0"):
			if self.dual_extruder:
				newline = """
; SET_E0 DUAL
T1
G92 E0
T0
G92 E0

"""
			else:
				newline = "; SET_E0 SINGLE\nG92 E0\n"
			return newline
		elif line.startswith("; outer perimeter") and self.accelerated:
			return "\n; outer perimeter\nM204 P250\n\n"
			
		elif line.startswith("; inner perimeter") and self.accelerated:
			return "\n; inner perimeter\nM204 P250\n\n"

		elif line.startswith("; solid layer") and self.accelerated:
			return "\n; solid layer\nM204 P600\n\n"

		elif line.startswith("; ooze shield") and self.accelerated:
			return "\n; ooze shield\nM204 P1200\n\n"
		
		elif line.startswith("; infill") and self.accelerated:
			return "\n; infill\nM204 P800\n\n"

		elif line.startswith("; bridge") and self.accelerated:
			return "\n; bridge\nM204 P1200\n\n"

		elif line.startswith("; layer"):
			if line.startswith("; layer end"):
				return "\nM808 zchange Done.\n\n"
			else:
				if line.split()[2] == "2,":
					return "\nM808 zchange Layer %s %smm\n\n;disallow baby stepping\nM988\n\n"%(line.split()[2], line.split()[5])
				else:	
					return "\nM808 zchange Layer %s %smm\n\n"%(line.split()[2], line.split()[5])

		return line #don't do anything...

def replace_keywords(path, file_object, links=None, printer_profile=None, allow_overwrite=True, *args, **kwargs):
	if not octoprint.filemanager.valid_file_type(path, type="gcode"):
		return file_object

	return octoprint.filemanager.util.StreamWrapper(file_object.filename, ReplaceKeywords(file_object.stream()))

__plugin_name__ = "GCODE Process"
__plugin_description__ = "replace keywords in gcode based on type of extruder/nozzle combination."
__plugin_hooks__ = {
		"octoprint.filemanager.preprocessor": replace_keywords
	}