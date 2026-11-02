from PLC_motion_controller import initiate, run_gcode_file, wait_ready


initiate()
# wait_ready()
run_gcode_file('test.nc')