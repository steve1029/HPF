import numpy as np
import os, time, datetime, sys
import matplotlib.pyplot as plt
import reikna.cluda as cld

from reikna.fft import FFT
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import axes3d
from scipy.constants import c, mu_0, epsilon_0

from datacheck import makefolder, datacheck
from plotfunc import plot2D3D
from newIRT import IRT

"""
	Author : Dong gun Lee
	Purpose : casting 3D PSTD algorithms with GPU implementation
"""

makefolder('./2DPlot')
makefolder('./3DPlot')
makefolder('./2D3DPlot')
makefolder('./graph')

#########################################################################################
################################# PSTD SPACE SETTING ####################################
#########################################################################################

IE = 108 
JE = 108
KE = 236 

npml = 10

IEp = IE + 2 * npml
JEp = JE + 2 * npml
KEp = KE + 2 * npml

totalSIZE = IEp * JEp * KEp		# totalSIZE
totalSHAPE= (IEp,JEp,KEp)		# totalSHAPE

ic = int(IEp/2)
jc = int(JEp/2)
kc = int(KEp/2)

S = 1./4
nm = 1e-9
dx, dy, dz = 10*nm, 10*nm, 10*nm

dt = S * min(dx,dy)/c

dtype = np.complex64

#########################################################################################
################################# PML PARAMETER SETTING  ################################
#########################################################################################

kappa_x = np.ones(IEp, dtype=dtype)
kappa_y = np.ones(JEp, dtype=dtype)
kappa_z = np.ones(KEp, dtype=dtype)

sigma_x = np.zeros(IEp, dtype=dtype)
sigma_y = np.zeros(JEp, dtype=dtype)
sigma_z = np.zeros(KEp, dtype=dtype)

kappa_mx = np.ones(IEp, dtype=dtype)
kappa_my = np.ones(JEp, dtype=dtype)
kappa_mz = np.ones(KEp, dtype=dtype)

sigma_mx = np.zeros(IEp, dtype=dtype)
sigma_my = np.zeros(JEp, dtype=dtype)
sigma_mz = np.zeros(KEp, dtype=dtype)

##### Grading of PML region #####

rc0 = 1.e-16		# reflection coefficient
gradingOrder = 3.
impedence = np.sqrt(mu_0/epsilon_0)
boundarywidth_x = npml * dx
boundarywidth_y = npml * dy
boundarywidth_z = npml * dz

sigmax_x = -(gradingOrder+1)*np.log(rc0)/(2*impedence*boundarywidth_x)
sigmax_y = -(gradingOrder+1)*np.log(rc0)/(2*impedence*boundarywidth_y)
sigmax_z = -(gradingOrder+1)*np.log(rc0)/(2*impedence*boundarywidth_z)

kappamax_x = 5.
kappamax_y = 5.
kappamax_z = 5.

sigmax_mx = sigmax_x * impedence**2
sigmax_my = sigmax_y * impedence**2
sigmax_mz = sigmax_z * impedence**2

kappamax_mx = kappamax_x
kappamax_my = kappamax_y
kappamax_mz = kappamax_z

space_eps = np.ones(totalSHAPE,dtype=dtype) * epsilon_0
space_mu  = np.ones(totalSHAPE,dtype=dtype) * mu_0

####################################################################################
################################## APPLYING PML ####################################
####################################################################################

def Apply_PML_3D(x,y,z):
	"""Apply UPML on each boundary.

	Parameters
	-------------
	x	:	string
			ex) x = '+','-','+-'

	y	:	string
			ex) y = '+','-','+-'

	z	:	string
			ex) z = '+','-','+-'
	"""

	npml = 10

	for i in range(npml):

		if x == '-' :
			
			sigma_x[i]  = sigmax_x * (dtype(npml-i)/npml)**gradingOrder
			kappa_x[i]  = 1 + ((kappamax_x - 1) * ((dtype(npml-i)/npml)**gradingOrder))
			sigma_mx[i] = sigma_x[i] * impedence**2
			kappa_mx[i] = kappa_x[i]

		elif x == '+' :

			sigma_x[-i-1]  = sigmax_x * (dtype(npml-i)/npml)**gradingOrder
			kappa_x[-i-1]  = 1 + ((kappamax_x - 1) * ((dtype(npml-i)/npml)**gradingOrder))
			sigma_mx[-i-1] = sigma_x[-i-1] * impedence**2
			kappa_mx[-i-1] = kappa_x[-i-1]
			
		elif x == '+-' :

			sigma_x[i]  = sigmax_x * (dtype(npml-i)/npml)**gradingOrder
			kappa_x[i]  = 1 + ((kappamax_x-1)*((dtype(npml-i)/npml)**gradingOrder))
			sigma_mx[i] = sigma_x[i] * impedence**2
			kappa_mx[i] = kappa_x[i]

			sigma_x[-i-1]  = sigma_x[i]
			kappa_x[-i-1]  = kappa_x[i]
			sigma_mx[-i-1] = sigma_mx[i]
			kappa_mx[-i-1] = kappa_mx[i]
			
	for j in range(npml):

		if y == '-' :
			
			sigma_y[j]  = sigmax_y * (dtype(npml-j)/npml)**gradingOrder
			kappa_y[j]  = 1 + ((kappamax_y - 1) * ((dtype(npml-j)/npml)**gradingOrder))
			sigma_my[j] = sigma_y[j] * impedence**2
			kappa_my[j] = kappa_y[j]

		elif y == '+' :

			sigma_y[-j-1]  = sigmax_y * (dtype(npml-j)/npml)**gradingOrder
			kappa_y[-j-1]  = 1 + ((kappamax_y - 1) * ((dtype(npml-j)/npml)**gradingOrder))
			sigma_my[-j-1] = sigma_y[-j-1] * impedence**2
			kappa_my[-j-1] = kappa_y[-j-1]
			
		elif y == '+-' :

			sigma_y[j]  = sigmax_y * (dtype(npml-j)/npml)**gradingOrder
			kappa_y[j]  = 1 + ((kappamax_y-1)*((dtype(npml-j)/npml)**gradingOrder))
			sigma_my[j] = sigma_y[j] * impedence**2
			kappa_my[j] = kappa_y[j]

			sigma_y[-j-1]  = sigma_y[j]
			kappa_y[-j-1]  = kappa_y[j]
			sigma_my[-j-1] = sigma_my[j]
			kappa_my[-j-1] = kappa_my[j]

	for k in range(npml):

		if z == '-' :
			
			sigma_z[k]  = sigmax_z * (dtype(npml-k)/npml)**gradingOrder
			kappa_z[k]  = 1 + ((kappamax_z - 1) * ((dtype(npml-k)/npml)**gradingOrder))
			sigma_mz[k] = sigma_z[k] * impedence**2
			kappa_mz[k] = kappa_z[k]

		elif z == '+' :

			sigma_z[-k-1]  = sigmax_z * (dtype(npml-k)/npml)**gradingOrder
			kappa_z[-k-1]  = 1 + ((kappamax_z - 1) * ((dtype(npml-k)/npml)**gradingOrder))
			sigma_mz[-k-1] = sigma_z[-k-1] * impedence**2
			kappa_mz[-k-1] = kappa_z[-k-1]
			
		elif z == '+-' :

			sigma_z[k]  = sigmax_z * (dtype(npml-k)/npml)**gradingOrder
			kappa_z[k]  = 1 + ((kappamax_z-1)*((dtype(npml-k)/npml)**gradingOrder))
			sigma_mz[k] = sigma_z[k] * impedence**2
			kappa_mz[k] = kappa_z[k]

			sigma_z[-k-1]  = sigma_z[k]
			kappa_z[-k-1]  = kappa_z[k]
			sigma_mz[-k-1] = sigma_mz[k]
			kappa_mz[-k-1] = kappa_mz[k]

def Apply_PEC_3D(x,y,z):
	"""Apply PEC on each boundary.

	Parameters
	-------------
	x	:	string

	y	:	string

	z	:	string
	"""

	if x == '-': kappa_x[0]  = 1.e16
	elif x == '+': kappa_x[-1] = 1.e16
	elif x == '+-': 
		kappa_x[0]  = 1.e16
		kappa_x[-1] = 1.e16		

	if y == '-': kappa_y[0]  = 1.e16
	elif y == '+': kappa_y[-1] = 1.e16
	elif y == '+-':
		kappa_y[0]  = 1.e16
		kappa_y[-1] = 1.e16		
	
	if z == '-': kappa_z[0]  = 1.e16
	elif z == '+': kappa_z[-1] = 1.e16
	elif z == '+-':
		kappa_z[0]  = 1.e16
		kappa_z[-1] = 1.e16		

apply_PML = True
apply_PEC = True

if apply_PML == True : Apply_PML_3D(x='',y='',z='+-')
#if apply_PEC == True : Apply_PEC_3D()

px = (2 * epsilon_0 * kappa_x) + (sigma_x * dt)
py = (2 * epsilon_0 * kappa_y) + (sigma_y * dt)
pz = (2 * epsilon_0 * kappa_z) + (sigma_z * dt)

mx = (2 * epsilon_0 * kappa_x) - (sigma_x * dt)
my = (2 * epsilon_0 * kappa_y) - (sigma_y * dt)
mz = (2 * epsilon_0 * kappa_z) - (sigma_z * dt)

mpx = (2 * mu_0 * kappa_mx) + (sigma_mx * dt)
mpy = (2 * mu_0 * kappa_my) + (sigma_my * dt)
mpz = (2 * mu_0 * kappa_mz) + (sigma_mz * dt)

mmx = (2 * mu_0 * kappa_mx) - (sigma_mx * dt)
mmy = (2 * mu_0 * kappa_my) - (sigma_my * dt)
mmz = (2 * mu_0 * kappa_mz) - (sigma_mz * dt)

makefolder('/root/3D_PSTD/coefficient')

np.savetxt('/root/3D_PSTD/coefficient/kappa_x.txt', kappa_x, fmt='%.3e',newline='\r\n',header='kappa_x :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/kappa_y.txt', kappa_y, fmt='%.3e',newline='\r\n',header='kappa_y :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/kappa_z.txt', kappa_z, fmt='%.3e',newline='\r\n',header='kappa_z :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/sigma_x.txt', sigma_x, fmt='%.3e',newline='\r\n',header='sigma_x :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/sigma_y.txt', sigma_y, fmt='%.3e',newline='\r\n',header='sigma_y :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/sigma_z.txt', sigma_z, fmt='%.3e',newline='\r\n',header='sigma_z :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/kappa_mx.txt', kappa_mx, fmt='%.3e',newline='\r\n',header='kappa_mx :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/kappa_my.txt', kappa_my, fmt='%.3e',newline='\r\n',header='kappa_my :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/kappa_mz.txt', kappa_mz, fmt='%.3e',newline='\r\n',header='kappa_mz :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/sigma_mx.txt', sigma_mx, fmt='%.3e',newline='\r\n',header='sigma_mx :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/sigma_my.txt', sigma_my, fmt='%.3e',newline='\r\n',header='sigma_my :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/sigma_mz.txt', sigma_mz, fmt='%.3e',newline='\r\n',header='sigma_mz :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/px.txt', px, fmt='%.3e',newline='\r\n',header='px :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/py.txt', py, fmt='%.3e',newline='\r\n',header='py :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/pz.txt', pz, fmt='%.3e',newline='\r\n',header='pz :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/mx.txt', mx, fmt='%.3e',newline='\r\n',header='mx :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/my.txt', my, fmt='%.3e',newline='\r\n',header='my :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/mz.txt', mz, fmt='%.3e',newline='\r\n',header='mz :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/mpx.txt', mpx, fmt='%.3e',newline='\r\n',header='mpx :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/mpy.txt', mpy, fmt='%.3e',newline='\r\n',header='mpy :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/mpz.txt', mpz, fmt='%.3e',newline='\r\n',header='mpz :\r\n')

np.savetxt('/root/3D_PSTD/coefficient/mmx.txt', mmx, fmt='%.3e',newline='\r\n',header='mmx :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/mmy.txt', mmy, fmt='%.3e',newline='\r\n',header='mmy :\r\n')
np.savetxt('/root/3D_PSTD/coefficient/mmz.txt', mmz, fmt='%.3e',newline='\r\n',header='mmz :\r\n')

##########################################################################################
################################### MATERIAL SETTING  ###################################
#########################################################################################

def rectangle_3D(backend_lower_left,front_upper_right, eps_r, mu_r, conductivity):
	"""Put 3D Cubic in main space.

	PARAMETERS
	--------------
	backend_lower_left : int tuple
		coordinates of backend_lower_left

	front_upper_right : int tuple
		coordinates of front_upper_right

	eps_r : float or tuple
		relative epsilon of rectanguler slab
		anisotropic magnetic materials can be applied by tuple.

	mu_r : float or tuple
		relative epsilon of rectanguler slab
		anisotropic dielectric materials can be applied by tuple.
		
	
	Returns
	-------------
	None
	"""
	assert eps_r != 0, "Relative dielctric constant of material should be bigger than 0"
	assert mu_r  != 0, "Relative magnetic constantof matherial should be bigger than 0"

	if type(eps_r) == int : eps_r = dtype(eps_r)
	elif type(eps_r) == dtype:
		eps_rx = eps_r
		eps_ry = eps_r
		eps_rz = eps_r
	elif type(eps_r) == tuple:
		eps_rx = eps_r[0]
		eps_ry = eps_r[1]
		eps_rz = eps_r[2]

	if type(mu_r) == dtype:
		mu_rx = mu_r
		mu_ry = mu_r
		mu_rz = mu_r
	elif type(mu_r) == int:
		mu_rx = dtype(mu_r)
		mu_ry = dtype(mu_r)
	elif type(mu_r) == tuple:
		mu_rx = mu_r[0]
		mu_ry = mu_r[1]
		mu_rz = mu_r[2]

	if type(conductivity) == int:
		conductivity_x = dtype(conductivity)
		conductivity_y = dtype(conductivity)
		conductivity_z = dtype(conductivity)

	elif type(conductivity) == dtype:
		conductivity_x = conductivity
		conductivity_y = conductivity
		conductivity_z = conductivity

	elif type(conductivity) == tuple:
		conductivity_x = conductivity[0] / eps_rx
		conductivity_y = conductivity[1] / eps_ry
		conductivity_z = conductivity[2] / eps_rz

	xcoor = backend_lower_left[0]
	ycoor = backend_lower_left[1]
	zcoor = backend_lower_left[2]
	
	height = front_upper_right[0] - backend_lower_left[0]
	depth  = front_upper_right[1] - backend_lower_left[1]
	width  = front_upper_right[2] - backend_lower_left[2]

	#### applying isotropic slab ####
	for i in range(height):
		for j in range(depth):
			for k in range(width):
				space_eps[xcoor+i,ycoor+j,zcoor+k] = eps_r * epsilon_0
				space_mu [xcoor+i,ycoor+j,zcoor+k] = mu_r  * mu_0

	return None

rectangle_3D((0,0,110),(IEp,JEp,130),eps_r=4.,mu_r=1.,conductivity=0.)
rectangle_3D((0,0,130),(IEp,JEp,170),eps_r=9.,mu_r=1.,conductivity=0.)

###########################################################################################
############################## FIELD AND COEFFICIENT ARRAYS ###############################
###########################################################################################

Ex = np.zeros(totalSHAPE, dtype=dtype)
Ey = np.zeros(totalSHAPE, dtype=dtype)
Ez = np.zeros(totalSHAPE, dtype=dtype)

Dx = np.zeros(totalSHAPE, dtype=dtype)
Dy = np.zeros(totalSHAPE, dtype=dtype)
Dz = np.zeros(totalSHAPE, dtype=dtype)

Hx = np.zeros(totalSHAPE, dtype=dtype)
Hy = np.zeros(totalSHAPE, dtype=dtype)
Hz = np.zeros(totalSHAPE, dtype=dtype)

Bx = np.zeros(totalSHAPE, dtype=dtype)
By = np.zeros(totalSHAPE, dtype=dtype)
Bz = np.zeros(totalSHAPE, dtype=dtype)

kx = np.fft.fftfreq(IEp,dx) * 2. * np.pi
ky = np.fft.fftfreq(JEp,dy) * 2. * np.pi
kz = np.fft.fftfreq(KEp,dz) * 2. * np.pi

nax   = np.newaxis
ones  = np.ones (totalSHAPE,dtype=dtype)
zeros = np.zeros(totalSHAPE,dtype=dtype)

ikx = (1j) * (kx[:,nax,nax] * ones)
iky = (1j) * (ky[nax,:,nax] * ones)
ikz = (1j) * (kz[nax,nax,:] * ones)

ikx = ikx.astype(dtype)
iky = iky.astype(dtype)
ikz = ikz.astype(dtype)

assert ikx.dtype == dtype, "dtype of ikx must be equal to %s" %dtype
assert iky.dtype == dtype, "dtype of iky must be equal to %s" %dtype
assert ikz.dtype == dtype, "dtype of ikz must be equal to %s" %dtype
assert ikx.real.all() == 0.
assert iky.real.all() == 0.
assert ikz.real.all() == 0.

print("Size of each field array : %.2f M bytes." %(ones.nbytes/1024/1024))

CDx1 = (my[nax,:,nax] * ones) / (py[nax,:,nax] * ones)
CDy1 = (mz[nax,nax,:] * ones) / (pz[nax,nax,:] * ones)
CDz1 = (mx[:,nax,nax] * ones) / (px[:,nax,nax] * ones)

CDx2 = 2. * epsilon_0 * dt / (py[nax,:,nax] * ones)
CDy2 = 2. * epsilon_0 * dt / (pz[nax,nax,:] * ones)
CDz2 = 2. * epsilon_0 * dt / (px[:,nax,nax] * ones)

CEx1 = (mz[nax,nax,:] * ones) / (pz[nax,nax,:] * ones)
CEx2 = (px[:,nax,nax] * ones) / (pz[nax,nax,:] * ones) / space_eps
CEx3 = (mx[:,nax,nax] * ones) / (pz[nax,nax,:] * ones) / space_eps * (-1)

CEy1 = (mx[:,nax,nax] * ones) / (px[:,nax,nax] * ones)
CEy2 = (py[nax,:,nax] * ones) / (px[:,nax,nax] * ones) / space_eps
CEy3 = (my[nax,:,nax] * ones) / (px[:,nax,nax] * ones) / space_eps * (-1)

CEz1 = (my[nax,:,nax] * ones) / (py[nax,:,nax] * ones)
CEz2 = (pz[nax,nax,:] * ones) / (py[nax,:,nax] * ones) / space_eps
CEz3 = (mz[nax,nax,:] * ones) / (py[nax,:,nax] * ones) / space_eps * (-1)

CBx1 = (mmy[nax,:,nax] * ones) / (mpy[nax,:,nax] * ones)
CBy1 = (mmz[nax,nax,:] * ones) / (mpz[nax,nax,:] * ones)
CBz1 = (mmx[:,nax,nax] * ones) / (mpx[:,nax,nax] * ones)

CBx2 = 2. * mu_0 * dt / (mpy[nax,:,nax] * ones) * (-1)
CBy2 = 2. * mu_0 * dt / (mpz[nax,nax,:] * ones) * (-1)
CBz2 = 2. * mu_0 * dt / (mpx[:,nax,nax] * ones) * (-1)

CHx1 = (mmz[nax,nax,:] * ones) / (mpz[nax,nax,:] * ones)
CHx2 = (mpx[:,nax,nax] * ones) / (mpz[nax,nax,:] * ones) / space_mu
CHx3 = (mmx[:,nax,nax] * ones) / (mpz[nax,nax,:] * ones) / space_mu * (-1)

CHy1 = (mmx[:,nax,nax] * ones) / (mpx[:,nax,nax] * ones)
CHy2 = (mpy[nax,:,nax] * ones) / (mpx[:,nax,nax] * ones) / space_mu
CHy3 = (mmy[nax,:,nax] * ones) / (mpx[:,nax,nax] * ones) / space_mu * (-1)

CHz1 = (mmy[nax,:,nax] * ones) / (mpy[nax,:,nax] * ones)
CHz2 = (mpz[nax,nax,:] * ones) / (mpy[nax,:,nax] * ones) / space_mu
CHz3 = (mmz[nax,nax,:] * ones) / (mpy[nax,:,nax] * ones) / space_mu * (-1)

assert CDx1.dtype == dtype, "dtype of coefficient array must be equal to %s" %(dtype)
assert CEx1.dtype == dtype, "dtype of coefficient array must be equal to %s" %(dtype)
assert CBx1.dtype == dtype, "dtype of coefficient array must be equal to %s" %(dtype)
assert CHx1.dtype == dtype, "dtype of coefficient array must be equal to %s" %(dtype)

###########################################################################################
#################################### INITIALIZE GPU #######################################
###########################################################################################

api = cld.get_api('cuda')
dev1 = api.get_platforms()[0].get_devices()[0]
dev2 = api.get_platforms()[0].get_devices()[1]

dev1_para = api.DeviceParameters(dev1)

print("MAX_WORK_GROUP_SIZE : ", dev1_para.max_work_group_size)
print("MAX_WORK_ITEM_SIZES : ", dev1_para.max_work_item_sizes)
print("MAX_NUM_GROUPS : ", dev1_para.max_num_groups)

thr1 = api.Thread(dev1)

program = thr1.compile("""
KERNEL void MUL(
	GLOBAL_MEM ${ctype} *dest,
	GLOBAL_MEM ${ctype} *a,
	GLOBAL_MEM ${ctype} *b)
{
	SIZE_T i = get_global_id(0);
	dest[i] = ${mul}(a[i],b[i]);
}

KERNEL void ADD(
	GLOBAL_MEM ${ctype} *dest,
	GLOBAL_MEM ${ctype} *a,
	GLOBAL_MEM ${ctype} *b)
{
	SIZE_T i = get_global_id(0);
	dest[i] = ${add}(a[i],b[i]);
}

KERNEL void CONJ(
	GLOBAL_MEM ${ctype} *target)
{
	SIZE_T i = get_global_id(0);
	target[i] = ${conj}(target[i]);
}
""",render_kwds=dict( ctype = cld.dtypes.ctype(dtype),
						mul = cld.functions.mul(dtype,dtype,out_dtype=dtype),
						add = cld.functions.add(dtype,dtype,out_dtype=dtype),
						conj= cld.functions.conj(dtype)))

MUL  = program.MUL
ADD  = program.ADD
CONJ = program.CONJ

Ex_dev = thr1.to_device(Ex)
Ey_dev = thr1.to_device(Ey)
Ez_dev = thr1.to_device(Ez)

Dx_dev = thr1.to_device(Ex)
Dy_dev = thr1.to_device(Ey)
Dz_dev = thr1.to_device(Ez)

Hx_dev = thr1.to_device(Hx)
Hy_dev = thr1.to_device(Hy)
Hz_dev = thr1.to_device(Hz)

Bx_dev = thr1.to_device(Bx)
By_dev = thr1.to_device(By)
Bz_dev = thr1.to_device(Bz)

ikx_dev = thr1.to_device(ikx)
iky_dev = thr1.to_device(iky)
ikz_dev = thr1.to_device(ikz)

CDx1_dev = thr1.to_device(CDx1)
CDy1_dev = thr1.to_device(CDy1)
CDz1_dev = thr1.to_device(CDz1)

CDx2_dev = thr1.to_device(CDx2)
CDy2_dev = thr1.to_device(CDy2)
CDz2_dev = thr1.to_device(CDz2)

CEx1_dev = thr1.to_device(CEx1)
CEx2_dev = thr1.to_device(CEx2)
CEx3_dev = thr1.to_device(CEx3)

CEy1_dev = thr1.to_device(CEy1)
CEy2_dev = thr1.to_device(CEy2)
CEy3_dev = thr1.to_device(CEy3)

CEz1_dev = thr1.to_device(CEz1)
CEz2_dev = thr1.to_device(CEz2)
CEz3_dev = thr1.to_device(CEz3)

CBx1_dev = thr1.to_device(CBx1)
CBy1_dev = thr1.to_device(CBy1)
CBz1_dev = thr1.to_device(CBz1)

CBx2_dev = thr1.to_device(CBx2)
CBy2_dev = thr1.to_device(CBy2)
CBz2_dev = thr1.to_device(CBz2)

CHx1_dev = thr1.to_device(CHx1)
CHx2_dev = thr1.to_device(CHx2)
CHx3_dev = thr1.to_device(CHx3)

CHy1_dev = thr1.to_device(CHy1)
CHy2_dev = thr1.to_device(CHy2)
CHy3_dev = thr1.to_device(CHy3)

CHz1_dev = thr1.to_device(CHz1)
CHz2_dev = thr1.to_device(CHz2)
CHz3_dev = thr1.to_device(CHz3)

storage_host = zeros
storage1_dev = thr1.to_device(zeros)
storage2_dev = thr1.to_device(zeros)
storage3_dev = thr1.to_device(zeros)

previous_dev = thr1.to_device(zeros)

minus1 = ones * (-1) 
assert minus1.dtype == dtype, "dtype of minus1 is not %s" %(dtype)
minus1_dev = thr1.to_device(minus1)

fftx = FFT(ones, axes=(0,))
ffty = FFT(ones, axes=(1,))
fftz = FFT(ones, axes=(2,))

fftxc = fftx.compile(thr1, fast_math=True)
fftyc = ffty.compile(thr1, fast_math=True)
fftzc = fftz.compile(thr1, fast_math=True)

###########################################################################################
######################################## SOURCE ###########################################
###########################################################################################

wavelength = np.arange(400,800,.5) * nm
wlc   = (wavelength[0] + wavelength[-1])/2
freq  = (c / wavelength)
freqc = (freq[0] + freq[-1]) / 2

w0 = 2 * np.pi * freqc
ws = 0.2 * w0

ts = 1./ws
tc = 1500. * dt

src_xpos = 20 + npml
src_ypos = 20 + npml
src_zpos = 20 + npml 

trs_xpos = -20 - npml
trs_ypos = -20 - npml
trs_zpos = -20 - npml

ft  = np.fft.fftn
ift = np.fft.ifftn

###########################################################################################
###################################### TIME LOOP  #########################################
###########################################################################################

nsteps = 8001
tstart = datetime.datetime.now()
today  = datetime.date.today()
localsize = JEp

Ex_inp = np.zeros(nsteps, dtype=dtype)
Ex_src = np.zeros(nsteps, dtype=dtype)
Ex_ref = np.zeros(nsteps, dtype=dtype)
Ex_trs = np.zeros(nsteps, dtype=dtype)

print("Simulation Start")

timeloop = True

if timeloop == True : 

	for step in range(nsteps):
		
		pulse = np.exp((-.5) * (((step*dt-tc)*ws)**2)) * np.cos(w0*(step*dt-tc))
		pulse3D = zeros

		assert pulse3D.shape == totalSHAPE, "Shape of pulse3D is not equal to totalSHAPE"
		
		for i in range(IEp):
			for j in range(JEp):
				pulse3D[i,j,src_zpos] = pulse

		assert pulse3D.dtype == dtype , "dtype of pulse3D is not %s" %(dtype)
		assert pulse3D.imag.all() == 0., "Source in real space has imaginary parts"

		pulse_dev = thr1.to_device(pulse3D)

		# Adding soft source
		ADD(Ex_dev, Ex_dev, pulse_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		# Collect reflected and transmitted wave
		storage_host = Ex_dev.get()
		
		assert storage_host.dtype == dtype
		#assert storage_host.imag.all() == 0.

		Ex_inp[step] = (storage_host[:,:,src_zpos]).mean()
		Ex_ref[step] = (storage_host[:,:,src_zpos]).mean() - pulse/2./S
		Ex_trs[step] = (storage_host[:,:,trs_zpos]).mean()

		# Update Bx field
		thr1.copy_array(Bx_dev, dest=previous_dev) ; thr1.synchronize()
		thr1.copy_array(Ez_dev, dest=storage2_dev) ; thr1.synchronize() 
		thr1.copy_array(Ey_dev, dest=storage3_dev) ; thr1.synchronize()
		
		fftyc(storage2_dev, storage2_dev) ; thr1.synchronize()
		fftzc(storage3_dev, storage3_dev) ; thr1.synchronize()
		
		MUL(storage2_dev, iky_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, ikz_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		fftyc(storage2_dev, storage2_dev, inverse=True) ; thr1.synchronize()
		fftzc(storage3_dev, storage3_dev, inverse=True) ; thr1.synchronize()

		MUL(storage3_dev, minus1_dev,   storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(storage2_dev, storage2_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		MUL(storage2_dev, CBx2_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage1_dev, CBx1_dev, Bx_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(Bx_dev, storage1_dev, storage2_dev,   local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Hx field
		MUL(storage1_dev, CHx1_dev, Hx_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage2_dev, CHx2_dev, Bx_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, CHx3_dev, previous_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(storage1_dev, storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Hx_dev,       storage1_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		# Update By field
		thr1.copy_array(By_dev, dest=previous_dev) ; thr1.synchronize()
		thr1.copy_array(Ex_dev, dest=storage2_dev) ; thr1.synchronize()
		thr1.copy_array(Ez_dev, dest=storage3_dev) ; thr1.synchronize()

		fftzc(storage2_dev, storage2_dev) ; thr1.synchronize()
		fftxc(storage3_dev, storage3_dev) ; thr1.synchronize()

		MUL(storage2_dev, ikz_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, ikx_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		fftzc(storage2_dev, storage2_dev, inverse=True) ; thr1.synchronize()
		fftxc(storage3_dev, storage3_dev, inverse=True) ; thr1.synchronize()

		MUL(storage3_dev, minus1_dev,   storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(storage2_dev, storage2_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		MUL(storage2_dev, CBy2_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage1_dev, CBy1_dev, By_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(By_dev, storage1_dev, storage2_dev,   local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Hy field
		MUL(storage1_dev, CHy1_dev, Hy_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage2_dev, CHy2_dev, By_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, CHy3_dev, previous_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(storage1_dev, storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Hy_dev,       storage1_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		# Update Bz field
		thr1.copy_array(Bz_dev, dest=previous_dev) ; thr1.synchronize()	
		thr1.copy_array(Ey_dev, dest=storage2_dev) ; thr1.synchronize()
		thr1.copy_array(Ex_dev, dest=storage3_dev) ; thr1.synchronize() 
		
		fftxc(storage2_dev, storage2_dev) ; thr1.synchronize()
		fftyc(storage3_dev, storage3_dev) ; thr1.synchronize()
		
		MUL(storage2_dev, ikx_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, iky_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		fftxc(storage2_dev, storage2_dev, inverse=True) ; thr1.synchronize()
		fftyc(storage3_dev, storage3_dev, inverse=True) ; thr1.synchronize()

		MUL(storage3_dev, minus1_dev,   storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(storage2_dev, storage2_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		MUL(storage2_dev, CBz2_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage1_dev, CBz1_dev, Bz_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(Bz_dev, storage1_dev, storage2_dev,   local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Hz field
		MUL(storage1_dev, CHz1_dev, Hz_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage2_dev, CHz2_dev, Bz_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, CHz3_dev, previous_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(storage1_dev, storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Hz_dev,       storage1_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		# Update Dx field
		thr1.copy_array(Dx_dev, dest=previous_dev) ; thr1.synchronize()
		thr1.copy_array(Hz_dev, dest=storage2_dev) ; thr1.synchronize()
		thr1.copy_array(Hy_dev, dest=storage3_dev) ; thr1.synchronize()

		fftyc(storage2_dev, storage2_dev) ; thr1.synchronize()
		fftzc(storage3_dev, storage3_dev) ; thr1.synchronize()

		MUL(storage2_dev, iky_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, ikz_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		fftyc(storage2_dev, storage2_dev, inverse=True) ; thr1.synchronize()
		fftzc(storage3_dev, storage3_dev, inverse=True) ; thr1.synchronize()

		MUL(storage3_dev, minus1_dev,   storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(storage2_dev, storage2_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		MUL(storage2_dev, CDx2_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage1_dev, CDx1_dev, Dx_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(Dx_dev, storage1_dev, storage2_dev,   local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Ex field
		MUL(storage1_dev, CEx1_dev, Ex_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage2_dev, CEx2_dev, Dx_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, CEx3_dev, previous_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(storage1_dev, storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Ex_dev,       storage1_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		# Update Dy field
		thr1.copy_array(Dy_dev, dest=previous_dev) ; thr1.synchronize()
		thr1.copy_array(Hx_dev, dest=storage2_dev) ; thr1.synchronize()
		thr1.copy_array(Hz_dev, dest=storage3_dev) ; thr1.synchronize()

		fftzc(storage2_dev, storage2_dev) ; thr1.synchronize()
		fftxc(storage3_dev, storage3_dev) ; thr1.synchronize()

		MUL(storage2_dev, ikz_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, ikx_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		fftzc(storage2_dev, storage2_dev, inverse=True) ; thr1.synchronize()
		fftxc(storage3_dev, storage3_dev, inverse=True) ; thr1.synchronize()

		MUL(storage3_dev, minus1_dev,   storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(storage2_dev, storage2_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		MUL(storage2_dev, CDy2_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage1_dev, CDy1_dev, Dy_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Dy_dev, storage1_dev,   storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Ey field
		MUL(storage1_dev, CEy1_dev, Ey_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage2_dev, CEy2_dev, Dy_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, CEy3_dev, previous_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(storage1_dev, storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Ey_dev,       storage1_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Dz field
		thr1.copy_array(Dz_dev, dest=previous_dev) ; thr1.synchronize()
		thr1.copy_array(Hy_dev, dest=storage2_dev) ; thr1.synchronize()
		thr1.copy_array(Hx_dev, dest=storage3_dev) ; thr1.synchronize()

		fftxc(storage2_dev, storage2_dev) ; thr1.synchronize()
		fftyc(storage3_dev, storage3_dev) ; thr1.synchronize()

		MUL(storage2_dev, ikx_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, iky_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		fftxc(storage2_dev, storage2_dev, inverse=True) ; thr1.synchronize()
		fftyc(storage3_dev, storage3_dev, inverse=True) ; thr1.synchronize()

		MUL(storage3_dev, minus1_dev,    storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(storage2_dev, storage2_dev,  storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		MUL(storage2_dev, CDz2_dev, storage2_dev , local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage1_dev, CDz1_dev, Dz_dev,        local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Dz_dev,    storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		
		# Update Ez field
		MUL(storage1_dev, CEz1_dev, Ez_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage2_dev, CEz2_dev, Dz_dev,       local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		MUL(storage3_dev, CEz3_dev, previous_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		ADD(storage1_dev, storage1_dev, storage2_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()
		ADD(Ez_dev,       storage1_dev, storage3_dev, local_size=localsize, global_size=totalSIZE) ; thr1.synchronize()

		if step % 100 == 0 : print("time : %s, step : %05d" %(datetime.datetime.now()-tstart,step),end='\r',flush=True)
		if step % 500 == 0 :
			print("")
			plot2D3D((Ex_dev.get())[ic,:,:],'/root/3D_PSTD/2D3DPlot/', step=step, stride=2, zlim=2.2, colordeep=2.2)
			os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/2D3DPlot/%s_%s.png Python/MyPSTD/3D_PSTD/2D3DPlot/'%(str(today),step))
		if step == (nsteps -1) : print("\n")

print("")
print("Simulation Finished")

######################################################################################
##################################### PLOTTING #######################################
######################################################################################

print("Plotting Start")

tsteps = np.arange(nsteps, dtype=dtype)
t = tsteps * dt
Ex_src = np.exp((-.5)*(((tsteps*dt-tc)*ws)**2)) * np.cos(w0*(tsteps*dt-tc)) /S/2

Ex_inp_ft = (dt * Ex_inp[nax,:] * np.exp(1.j * 2.*np.pi*freq[:,nax] * t[nax,:]) ).sum(1) / np.sqrt(2.*np.pi)
Ex_src_ft = (dt * Ex_src[nax,:] * np.exp(1.j * 2.*np.pi*freq[:,nax] * t[nax,:]) ).sum(1) / np.sqrt(2.*np.pi)
Ex_ref_ft = (dt * Ex_ref[nax,:] * np.exp(1.j * 2.*np.pi*freq[:,nax] * t[nax,:]) ).sum(1) / np.sqrt(2.*np.pi)
Ex_trs_ft = (dt * Ex_trs[nax,:] * np.exp(1.j * 2.*np.pi*freq[:,nax] * t[nax,:]) ).sum(1) / np.sqrt(2.*np.pi)

fftfreq = np.fft.fftfreq(nsteps,dt)

makefolder('/root/3D_PSTD/field_data')
datacheck(Ex,'/root/3D_PSTD/field_data/Ex.txt')

####################################### RT graph #######################################

Trs = (abs(Ex_trs_ft)**2)/(abs(Ex_src_ft)**2)
Ref = (abs(Ex_ref_ft)**2)/(abs(Ex_src_ft)**2)
Total  = Trs + Ref

print("Ratio of input and source : ",abs(Ex_inp.max())/(Ex_src.max()))
np.savetxt('/root/3D_PSTD/graph/Ex_inp.txt', Ex_inp, fmt='%.3e', newline='\r\n', header='Ex_inp :\r\n')
np.savetxt('/root/3D_PSTD/graph/Ex_src.txt', Ex_src, fmt='%.3e', newline='\r\n', header='Ex_src :\r\n')
np.savetxt('/root/3D_PSTD/graph/Ex_trs.txt', Ex_trs, fmt='%.3e', newline='\r\n', header='Ex_trs :\r\n')
np.savetxt('/root/3D_PSTD/graph/Ex_ref.txt', Ex_ref, fmt='%.3e', newline='\r\n', header='Ex_ref :\r\n')
np.savetxt('/root/3D_PSTD/graph/Trans.txt' , Trs,    fmt='%.3e', newline='\r\n', header='Trans :\r\n')
np.savetxt('/root/3D_PSTD/graph/Reflec.txt', Ref,    fmt='%.3e', newline='\r\n', header='Reflec:\r\n')
np.savetxt('/root/3D_PSTD/graph/Total.txt' , Total,  fmt='%.3e', newline='\r\n', header='Total :\r\n')

wl = wavelength

RTgraph = plt.figure(figsize=(21,9))

ax1 = RTgraph.add_subplot(121)
ax1.set_title("Wavelength vs Ref,Trs")
ax1.plot(wl/nm, Ref.real,   label ='Ref',   color='green')
ax1.plot(wl/nm, Trs.real,   label ='Trs',   color='red')
ax1.plot(wl/nm, Total.real, label ='Total', color='blue')
ax1.set_xlabel('wavelength, nm')
ax1.set_ylabel('Ratio')
#ax1.set_ylim(0.,1.1)
ax1.legend(loc='best')
ax1.grid(True)

ax2 = RTgraph.add_subplot(122)
ax2.set_title("Frequency vs Ref,Trs")
ax2.plot(freq/1.e12, Ref.real,   label='Ref',   color='green')
ax2.plot(freq/1.e12, Trs.real,   label='Trs',   color='red')
ax2.plot(freq/1.e12, Total.real, label='Total', color='blue')
ax2.set_xlabel('freq, THz')
ax2.set_ylabel('Ratio')
#ax2.set_ylim(0.,1.1)
ax2.legend(loc='best')
ax2.grid(True)

RTgraph.savefig('/root/3D_PSTD/graph/RTgraph.png')
plt.close()

################################## Comparing with Theoratical graph ##################################

TMM = IRT()
TMM.wavelength(wl)
TMM.incidentangle(angle=0, unit='radian')
TMM.mediumindex(1.,2.,3.,1.)
TMM.mediumtype('nonmagnetic')
TMM.mediumthick(200*nm,400*nm)
TMM.cal_spol_matrix()

TMMref = TMM.Reflectance()
TMMtrs = TMM.Transmittance()
TMMfreq = TMM.frequency

fig = plt.figure(figsize=(15,15))

ax1 = fig.add_subplot(221)
ax2 = fig.add_subplot(222)
ax3 = fig.add_subplot(223)
ax4 = fig.add_subplot(224)

ax1.plot(wl/nm,      TMMref.real, color='red', alpha=.5, linewidth=3, label='Theoratical')
ax2.plot(wl/nm,      TMMtrs.real, color='red', alpha=.5, linewidth=3, label='Theoratical')
ax3.plot(freq/1.e12, TMMref.real, color='red', alpha=.5, linewidth=3, label='Theoratical')
ax4.plot(freq/1.e12, TMMtrs.real, color='red', alpha=.5, linewidth=3, label='Theoratical')

ax1.plot(wl/nm, Ref.real, 	label='Simulation')
ax2.plot(wl/nm, Trs.real, 	label='Simulation')
ax3.plot(freq/1.e12, Ref.real, label='Simulation')
ax4.plot(freq/1.e12, Trs.real,  label='Simulation')

ax1.set_xlabel('wavelength')
ax2.set_xlabel('wavelength')
ax3.set_xlabel('frequency')
ax4.set_xlabel('frequency')

ax1.set_ylabel('ratio')
ax2.set_ylabel('ratio')
ax3.set_ylabel('ratio')
ax4.set_ylabel('ratio')

ax1.set_title('Reflectance')
ax2.set_title('Transmittance')
ax3.set_title('Reflectance')
ax4.set_title('Transmittance')

ax1.legend(loc='best')
ax2.legend(loc='best')
ax3.legend(loc='best')
ax4.legend(loc='best')

ax1.grid(True)
ax2.grid(True)
ax3.grid(True)
ax4.grid(True)

ax1.set_ylim(-.1, 1.1)
ax2.set_ylim(-.1, 1.1)
ax3.set_ylim(-.1, 1.1)
ax4.set_ylim(-.1, 1.1)

fig.savefig('/root/3D_PSTD/graph/Theory_vs_Simul.png')
plt.close()

####################################### Src graph #########################################

Srcgraph = plt.figure(figsize=(31,9))

ax1 = Srcgraph.add_subplot(131)
ax1.set_title("freq vs "+r"$E_{\omega}$")
ax1.plot(freq/1.e12, abs(Ex_src_ft)**2, label=r'$E_{src}(\omega)$')
ax1.plot(freq/1.e12, abs(Ex_ref_ft)**2, label=r'$E_{ref}(\omega)$')
ax1.plot(freq/1.e12, abs(Ex_trs_ft)**2, label=r'$E_{trs}(\omega)$')
ax1.set_xlabel('freq, THz')
ax1.set_ylabel('ratio')
ax1.legend(loc='best')
ax1.grid(True)

ax2 = Srcgraph.add_subplot(132)
ax2.set_title("wavelength vs " + r"$E_{\omega}$")
ax2.plot(wl/nm, abs(Ex_src_ft)**2, label=r'$E_{src}(\lambda)$')
ax2.plot(wl/nm, abs(Ex_ref_ft)**2, label=r'$E_{ref}(\lambda)$')
ax2.plot(wl/nm, abs(Ex_trs_ft)**2, label=r'$E_{trs}(\lambda)$')
ax2.set_xlabel('wavelength, nm')
ax2.legend(loc='best')
ax2.grid(True)

ax3 = Srcgraph.add_subplot(133)
ax3.set_title('src vs inp, $t_c = %gdt $' %(tc/dt))
#ax3.plot(tsteps.real[0:int(4*tc/dt)],((Ex_src.real)**2)[0:int(4*tc/dt)], label=r'$|E_x(t)|^2,src$')
#ax3.plot(tsteps.real[0:int(4*tc/dt)],((Ex_inp.real)**2)[0:int(4*tc/dt)], label=r'$|E_x(t)|^2,inp$')
ax3.plot(tsteps.real[0:int(4*tc/dt)],Ex_src.real[0:int(4*tc/dt)], label=r'$E_x(t),src$', color='r', alpha=0.4, linewidth=4.)
ax3.plot(tsteps.real[0:int(4*tc/dt)],Ex_inp.real[0:int(4*tc/dt)], label=r'$E_x(t),inp$', color='b')
ax3.get_xaxis().set_visible(False)
ax3.text(2000,-2,r'$E(t)=e^{-\frac{1}{2}(\frac{t-t_c}{ts})^{2}}\cos(\omega_{0}(t-t_c))$', fontsize=18)
ax3.set_ylim(-3,3)
ax3.legend()
ax3.grid(True)

divider = make_axes_locatable(ax3)
ax4 = divider.append_axes("bottom",size="100%",pad=0.2, sharex=ax3)
ax4.plot(tsteps.real[0:int(4*tc/dt)],((Ex_ref.real)**2)[0:int(4*tc/dt)], label=r'$|E_r(t)|^2$',color='green')
ax4.plot(tsteps.real[0:int(4*tc/dt)],((Ex_trs.real)**2)[0:int(4*tc/dt)], label=r'$|E_t(t)|^2$',color='red')
#ax4.set_ylim(-2,2)
ax4.set_xlabel('time step, dt=%.2g' %(dt))
ax4.legend()
ax4.grid(True)
Srcgraph.savefig('./graph/Srcgraph.png')

thr1.release()
print("Plotting Finished")
############################################################################################
################################### CLOUD SYNCHRONIZING ####################################
############################################################################################

print("Start uploading to Dropbox")
myname = os.path.basename(__file__)

#os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/%s Python/MyPSTD/3D_PSTD' %myname)
os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/*.py Python/MyPSTD/3D_PSTD')
#os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/2D3DPlot/*.png Python/MyPSTD/3D_PSTD/2D3DPlot/')
#os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/coefficient Python/MyPSTD/3D_PSTD/')
#os.system('../dropbox_uploader.sh upload ../3D_PSTD/field_data/Ex.txt Python/MyPSTD/3D_PSTD/field_data/')
os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/graph/* Python/MyPSTD/3D_PSTD/graph/')
#os.system('/root/dropbox_uploader.sh upload /root/3D_PSTD/graph/Theory_vs_Simul.png Python/MyPSTD/3D_PSTD/graph/')