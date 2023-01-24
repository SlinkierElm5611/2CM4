import subprocess
import numpy as np
import matplotlib.pyplot as plt
import json

flex_code: str = """
TITLE '2CM4 Assignment 1 GGL' { the problem identification }
COORDINATES cartesian1 { coordinate system, 1D,2D,3D, etc }
VARIABLES { system variables }
	r(threshold=1e-3) = vector(rx,ry)
	v(threshold=1e-3)=vector(vx,vy)
	Wdrag(threshold=1e-3)
SELECT { method controls }
	ngrid = 1 !low FEM density speeds up solution with no downside when not using FEM
DEFINITIONS { parameter definitions }

!dynamic parameters

	!stage 1 rocket
	mfuel10 = %s !fuel mass of rocket stage 1 kg

	!stage 2 rocket
	mfuel20 = %s !fuel mass of rocket stage 2 kg


!static parameters

	mpayload = 200
	
	!stage 1 rocket
	q1 = 2000 !fuel flow/comsumption rate kg/s
	ve1 = 2500 !fuel release speed m/s
	meng1 = 320 !engine mass kg
	mtank1 = 30*(1+mfuel10/2000) !mass of fuel tank kg
	
	!stage 2 rocket
	q2 = 300 !fuel flow/comsumption rate kg/s
	ve2 = 2800 !fuel release speed m/s
	meng2 = 150 !engine mass kg
	mtank2 = 15*(1+mfuel20/1000) !mass of fuel tank kg


!thrust force
	m0 = mpayload + meng1 + mtank1 + mfuel10 + meng2 + mtank2 + mfuel20 

    tthrust = 0
	tfuel1 = mfuel10/q1 

	Fthrustmag1 = if t>tthrust and t<(tfuel1+ tthrust) then q1*ve1 else 0 
	Fthrust1 =  Fthrustmag1*v/(magnitude(v)+1e-3)
    mfuelused1 = if t<tthrust then 0 else if t<(tthrust+tfuel1) then q1*(t-tthrust) else mfuel10
	!m = m0 - mfuelused1

	tfuel2 = mfuel20/q2 

	Fthrustmag2 = if t>tthrust+tfuel1 and t<(tthrust +tfuel1 + tfuel2) then q2*ve2 else 0 
	Fthrust2 =  Fthrustmag2*v/(magnitude(v)+1e-3)
    mfuelused2 = if t<(tthrust+tfuel1) then 0 else if t<(tthrust+tfuel1+tfuel2) then q2*(t-tfuel1-tthrust) else mfuel20
	!m = m0 -mtank1 - meng1 - mfuelused1 - mfuelused2
	m = if t<=tthrust then m0 else if t<=(tthrust+tfuel1) then (m0 - mfuelused1) 
		else if t<=(tthrust+tfuel1+tfuel2) then (m0 - mtank1 - meng1 - mfuelused1 - mfuelused2)
		else mpayload


!force of gravity
    bigG = 6.674e-11
    mEarth = 5.9722e24
    rEarth = 6.3781e6
	rad = r-vector(0,-rEarth)
	radMag = magnitude(rad)
	radHat = rad/radMag
    g = bigG*mEarth/radMag^2*radHat
	gMag = magnitude(g)
	Fgrav =-m*g
    
    vwind = vector(0, 0)
	vrel = v-vwind
    
	h =radMag - rEarth


!drag force
	temp0 = 288.15
	LTLR=.0065
	Rgasconst = 8.31447
	molarmassdryair = .0289644
	Temperature = temp0-LTLR *h
	p0 = 101325
	p = if(LTLR*h/Temp0 < 1) then p0*(1-LTLR*h/Temp0)^(gMag*molarmassdryair/(Rgasconst*LTLR))else 0
	rho=p*MolarmassDryAir/(Rgasconst*Temperature)
	Area=1
	CD = .15
	Fdrag = -.5*rho*area*cd*vrel*magnitude(vrel)
    
	
!F=ma
	Fnet = Fgrav + Fthrust1 + Fthrust2 + Fdrag
	a =Fnet/m


!initial conditions
    theta0 =90 *pi/180 !launch angle in rad
	v0 =1e-3 !initial speed in m/s
	ay = dot(a, vector(0,1))

!costs
	fuelcostperkg = 5 !kg
	costfuel = fuelcostperkg*(mfuel10+mfuel20) !dollars

	fueltankcostperkg = 800 !kg
	costfueltank = fueltankcostperkg*(mtank1 + mtank2)

	enginecostperkg = 5000
	costengines = enginecostperkg*(meng1 + meng2)

	costTotal = costfuel + costfueltank + costengines


!kinetic energy
	EKin = 1/2*m*magnitude(v)^2

    
INITIAL VALUES
	v = v0*vector(cos(theta0), sin(theta0))
	r = vector(0,0)

EQUATIONS { PDE's, one for each variable }
	r: dt(r) = v
	v: dt(v) = a
	Wdrag: dt(Wdrag) = dot(Fdrag, v)

! CONSTRAINTS { Integral constraints }

BOUNDARIES { The????ain definition }
REGION 1 START(0) LINE TO (1)
TIME 0 TO 3000 halt(radMag<rEarth or p=0)! or rrelMag<400) { if time dependent }

!MONITORS { show progress }

PLOTS { save result displays }
for t= 0 by endtime/300 to endtime
	history(ry, vy*20, ay*100) at(0)
	history(ry) at (0) vs rx
	report rx
	report ry
	report t
	report Ekin
	report costTotal
	report m
	report magnitude(v)
	!history(rrelMag) at (0)
	!history(Fc) at (0)
	history(Fthrust1, Fthrust2, Fgrav) at (0)
	history(Fdrag) at (0)
	report t
	history(magnitude(Fgrav))at(0)
	report(magnitude(Fgrav))
	history(gMag) at (0)
	history(gMag) at (0) vs (h)
	history(m) at (0)
	history(magnitude(v), m, Ekin, costTotal, p) at(0) printonly Export Format '#t#b#1#b#2#b#3#b#4#b#5' file = 'output.txt'
END
"""


def compute_second_mass_fuel(mass_of_first_stage_fuel: float) -> float:
    total_cost: float = 3000000
    cost_of_engine_one: float = 320*5000
    cost_of_engine_two: float = 160*5000
    return (total_cost-cost_of_engine_one-cost_of_engine_two-17*mass_of_first_stage_fuel-24000-12000)/17


def match_fuel_masses(mass_fuel: list[float]) -> list[float]:
    masses_of_second_stage: list[float] = []
    for j in mass_fuel:
        second_mass_fuel = compute_second_mass_fuel(j)
        masses_of_second_stage.append(second_mass_fuel)
    return masses_of_second_stage
    

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
	
    subprocess.run([flex_path, "-S", flex_file_name])
    plt.title("Trajectory for various launch angles")
    plt.show()