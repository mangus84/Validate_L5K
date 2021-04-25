# Validate_L5K
Python script to validate *.L5K files of Allen-Bradley PLC projects. Script checks presence of tags with defined name i.e. "shunt".


Objective:
-----------------------------------------
- Check all *.L5K files in given directory
- Check against a list of tag names (i.e. names stored in a *.txt file)
- Save results in *.txt files (each for a project file)
- Create UI as intuitive as possible
- Send e-mail with results to the given address (PLC system supervisor)
