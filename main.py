import subprocess
import numpy as np
import matplotlib.pyplot as plt
import json

flex_code: str = """
TITLE 'Projectile Motion'
COORDINATES cartesian2
VARIABLES
vx(threshold=0.1) !velocity in x
vy(threshold=0.1) !velocity in y
xd(threshold=0.1) !x-displacement
yd(threshold=0.1) !y-displacement
SELECT
ngrid = 1 !since we're not using spatial depenedence within the object we don't need a dense mesh
DEFINITIONS
xi=0 !initial coordinates
yi=0
vi = 21 !initial velocity
theta_i = %s*pi/180 !initial angle
g = 9.8
m=1
! theoretical equations of motion (no drag)
vx_ideal = vi*cos(theta)
vy_ideal = vi*sin(theta)
xd_ideal = xi + vx_ideal*t
yd_ideal = yi + vy_ideal*t - 0.5*g*t^2
ax = 0
ay = -g !acceleration due to gravity only
INITIAL VALUES
vx = vi*cos(theta_i)
vy = vi*sin(theta_i)
xd = xi
yd = yi
EQUATIONS
vx: dt(vx) = ax
vy: dt(vy) = ay
xd: dt(xd) = vx
yd: dt(yd) = vy
BOUNDARIES { The domain definition }
REGION 1 { For each material region }
START(0,0) { Walk the domain boundary }
LINE TO (1,0) TO (1,1) TO (0,1) TO CLOSE
TIME 0 TO 50 halt yd<0 { if time dependent }
PLOTS
for t = 0 by 0.1 to endtime
history(xd,yd) at (0,0) PrintOnly Export Format '#t#b#1#b#2' file = 'output.txt'
SUMMARY
report val(xd,0,0) as 'xd'
report val(yd,0,0) as 'yd'
report t
END
"""


def compute_second_mass_fuel(mass_of_first_stage_fuel: float) -> float:
    total_cost = 3000000
    cost_of_engine_one = 320*5000
    cost_of_engine_two = 160*5000
    return (total_cost-cost_of_engine_one-cost_of_engine_two-17*mass_of_first_stage_fuel-24000-12000)/17

def match_fuel_masses(mass_fuel: list[float]) -> list[list[float]]:
    masses_of_first_stage: list[float] = []
    masses_of_second_stage: list[float] = []
    for j in mass_fuel:
        second_mass_fuel = compute_second_mass_fuel(j)
        masses_of_first_stage.append(j)
        masses_of_second_stage.append(second_mass_fuel)
    return [masses_of_first_stage, masses_of_second_stage]
    

if __name__ == "__main__":
    try:
        user_name: str = subprocess.run("whoami", stdout=subprocess.PIPE).stdout.decode('utf-8')
        config: dict = json.load(open("project_config.json", 'r'))
        user_config: dict = config.get(user_name.strip())
        flex_file_name: str = user_config.get("flex_file_name") + ".pde"
        flex_path: str = user_config.get("path_to_executable")
        output_path: str = ""
        if user_config.get("flex_version") == 7 :
            output_path = user_config.get("flex_file_name") + "_output/"+user_config.get("output_file_name")
        else:
            output_path = user_config.get("output_file_name")
    except:
        flex_file_name: str = "output.pde"
        flex_path: str = "C:/FlexPDE6student/FlexPDE6s.exe"
        output_path: str = "output.txt"
    
    #add optimization codes below this line!

    plt.title("Trajectory for various launch angles")
    plt.show()