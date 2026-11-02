from PLC_motion_controller_mod import initiate, run_gcode_file
from GO_make_pillar_array import write_light_harvesting_gcode
initiate()

# run_gcode_file("test.nc")
run_gcode_file("set_height.nc")

# run_gcode_file("EGaln_line.nc")
# run_gcode_file("light_harvesting.nc")

# run_gcode_file("single_line.nc")



# write_light_harvesting_gcode(
#     v_star=0.2,
#     h=2,
#     d_star=3,
#     start_x=30,
#     start_y=320,
#     initial_height=10.01,
# )




# bounds = {
#     "H_star": (2.0, 10),
#     "V_star": (0.01, 1.0),
#     "d_star": (1.0, 10.0),
# }