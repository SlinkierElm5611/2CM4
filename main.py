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

def MassFuel2(mf1):
    TotalCost = 3000000
    Engine1Cost = 320*5000
    Engine2Cost = 160*5000
    MF2 = (TotalCost-Engine1Cost-Engine2Cost-17*mf1-24000-12000)/11
    return MF2

def MatchMass(MassFuel):
    for j in MassFuel1:
        MF2 = MassFuel2(j)
        MS1.append(j)
        MS2.append(MF2)

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
    angle_range = np.arange(5,91,5)
    for Angle in angle_range:
        with open(flex_file_name, 'w') as f:
            print(flex_code%Angle ,file=f)
        completed = subprocess.run([flex_path, "-S", flex_file_name])
        print("returned: ", completed.returncode)
        with open(output_path) as f:
            data = np.loadtxt(f, skiprows=8)
            t = data[:,0]
            xd = data[:,1]
            yd = data[:,2]
            plt.plot(xd, yd)
    plt.title("Trajectory for various launch angles")
    plt.legend(angle_range)
    plt.show()