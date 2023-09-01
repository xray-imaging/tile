import h5py 
import os
import dxchange
import numpy as np
from threading import Thread
import sys
def read_data_chunk(out, fname, st, st_proj, end_proj):    
        """Read a chunk of data """                      
        out[st_proj:end_proj] += dxchange.read_tiff_stack(fname, ind=range(st+st_proj,st+end_proj))

def read_data_parallel(fname,st=0,end=-1,nthreads=16, out=None):
        """Reading data in parallel"""
        tmp = dxchange.read_tiff(fname)
        if out is None:
            out = np.empty([end-st,*tmp.shape], dtype='float32')
        lchunk = int(np.ceil((end-st)/nthreads))
        procs = []
        for k in range(nthreads):
            st_proj = k*lchunk
            end_proj = min((k+1)*lchunk,end-st)
            if st_proj>=end_proj:
                continue
            read_thread = Thread(
                target=read_data_chunk, args=(out, fname, st,st_proj, end_proj))
            procs.append(read_thread)
            read_thread.start()
        for proc in procs:
            proc.join()
        return out



############Adjust this###########
file_path = f'/data/staff/tomograms/experiments/TOMCAT/202309_e20597_kidney/{sys.argv[1]}'
nangles = 6000
chunk = 1000
nslices = 2160
##################################


os.system(f'mkdir {file_path}_rec')
tmp = dxchange.read_tiff(f'{file_path}/r0/recon_00000.tiff')
sum_chunk = 16
print('Summing')
for k in range(int(np.ceil(nslices/sum_chunk))):    
    st = k*sum_chunk
    end = min((k+1)*sum_chunk,nslices)
    print(st,end)
    arr1=read_data_parallel(f'{file_path}/r0/recon_00000.tiff',st,end)
    for k in range(1,nangles//chunk):    
        arr1=read_data_parallel(f'{file_path}/r{k}/recon_00000.tiff', st, end,out=arr1)                
    dxchange.write_tiff_stack(arr1,f'{file_path}_rec/recon.tiff',start=st,overwrite=True)