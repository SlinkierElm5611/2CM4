import subprocess
import numpy as np
import matplotlib.pyplot as plt
import json

flex_code  = """
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
	mfuel20 = 614000/17 - mfuel10 !fuel mass of rocket stage 2 kg


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
	EKin = 1/2*200*magnitude(v)^2


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
TIME 0 TO 3000 halt(p=0 and t>(tfuel1+tfuel2))! or rrelMag<400) { if time dependent }

!MONITORS { show progress }

PLOTS { save result displays }
for t= 0 by endtime/300 to endtime
	history(magnitude(v), m, Ekin, costTotal, p) at(0) printonly Export Format '#t#b#1#b#2#b#3#b#4#b#5' file = 'output.txt'
END
"""

#a function to compute the mass of the second stage fuel depending on the use of the first stage fuel
def compute_second_mass_fuel(mass_of_first_stage_fuel):
	mass2 = 614000/17 - mass_of_first_stage_fuel
	return mass2

#total flight time needed for the simulation	
def flight_time(mass1):
    mass2 = compute_second_mass_fuel(mass1)
    t1 = mass1/2000
    t2 = mass2/300
    tf = t1 + t2
    return tf

try:
	user_name  = subprocess.run("whoami", stdout=subprocess.PIPE).stdout.decode('utf-8')
	config  = json.load(open("project_config.json", 'r'))
	user_config  = config.get(user_name.strip())
	flex_file_name  = user_config.get("flex_file_name") + ".pde"
	flex_path  = user_config.get("path_to_executable")
	output_path  = ""
	flex_version = user_config.get("flex_version")
	if flex_version == 7 :
		output_path = user_config.get("flex_file_name") + "_output/"+user_config.get("output_file_name")
	else:
		output_path = user_config.get("output_file_name")
except:
	flex_file_name  = "output.pde"
	flex_path  = "C:/FlexPDE6student/FlexPDE6s.exe"
	output_path  = "output.txt"
	flex_version = 6


#making initial perameters and empty lists 	
mass_range = np.arange(31015, 31020.1,0.5)
kinetic_energies = []
masses = []

#we want to find the best possible mass to use in the range listed above so we would run it in a for loop
for mass_one in mass_range:
    with open(flex_file_name,"w") as f:
        print(flex_code%(mass_one),file=f)
    result = subprocess.run([flex_path, "-S", flex_file_name])
    print(result.returncode)
    
    #using the output from the flex we import the data
    with open(output_path, "r") as f:
        data = np.loadtxt(f,skiprows=flex_version+1)
        t = data[:,0]
        energy = data[:,3]
        tfinal = flight_time(mass_one)
        
        #interpolating the kinetic energy
        kfinal = energy[-2] + (energy[-1]-energy[-2])/(t[-1]-t[-2])*(tfinal-t[-2])
        
        #appending loop values to the lists 
        kinetic_energies.append(kfinal)
        masses.append(mass_one)
        pass

#finding the connecting vaules 
i = np.argmax(kinetic_energies)
maxmass2 = compute_second_mass_fuel(masses[i])
print('Mass of fuel tank 1 is', masses[i],'kg with the mass of the stecond satge fuel being', round(maxmass2,3),'kg , and the max kinetic energy', round(kinetic_energies[i],3))
plt.plot(masses, kinetic_energies)
plt.title("Max energy based on mass of fuel one")
plt.show()
