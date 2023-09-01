import os
import sys

#######Adjust this#####
file_path = f'/data/staff/tomograms/experiments/TOMCAT/202309_e20597_kidney/{sys.argv[1]}'
nangles = 6000
chunk = 1000# will make independent reconstruction using angles [0,chunk], [chunk,2*chunk].. The results should be then summed
energy = 21
pixel_size = 0.325
propagation_distance = 50
rotation_axis = 50
retrieve_phase_alpha = 0.0006
############################

cmd = f'tomocupy recon_steps --file-type double_fov --reconstruction-type full --file-name {file_path}/tile/tile.h5 \
 --rotation-axis-auto manual --rotation-axis {rotation_axis} --pixel-size {pixel_size} --energy {energy} \
 --propagation-distance {propagation_distance} --nsino-per-chunk 2 --nproj-per-chunk 2 --retrieve-phase-method paganin \
 --remove-stripe-method vo-all --retrieve-phase-alpha {retrieve_phase_alpha} --fbp-filter shepp'
print(cmd)

for k in range(nangles//chunk):
    os.system(cmd+f' --start-proj {k*chunk} --end-proj {(k+1)*chunk} --out-path-name {file_path}/r{k}')
