import numpy as np
import h5py
from tomocupy_cli import fourierrec
from cupyx.scipy.fft import rfft, irfft
import cupy as cp
import dxchange

file = '/data/NAISE_Spinal_Cord/010_L7_Left_Half_5x_M_y0_x2.h5'

        
class GPURec():
    def __init__(self,file, shifts):
        with h5py.File(file) as fid:
            nproj = fid['/exchange/data'].shape[0]
            ndark = fid['/exchange/data_dark'].shape[0]
            nflat = fid['/exchange/data_white'].shape[0]
            print(shifts[-1])
            n = fid['/exchange/data'].shape[2]*5 - int(shifts[-1])
            nz = 2
            theta = cp.array(fid['/exchange/theta'][:].astype('float32')/180*np.pi)

        cl_rec = fourierrec.FourierRec(n, nproj, nz, theta)        
        self.nproj = nproj
        self.n = n 
        self.nz = nz 
        self.ndark = ndark
        self.nflat = nflat
        self.cl_rec = cl_rec
        self.shifts = shifts
        
    def darkflat_correction(self, data, dark, flat):
        """Dark-flat field correction"""

        dark0 = cp.mean(dark, axis=0).astype('float32')
        flat0 = cp.mean(flat, axis=0).astype('float32')
        data = (data.astype('float32')-dark0)/(flat0-dark0)
        return data

    def minus_log(self, data):
        """Taking negative logarithm"""

        data = -cp.log(data)
        data[cp.isnan(data)] = 6.0
        data[cp.isinf(data)] = 0
        return data

    def fbp_filter_center(self, data, center):
        """FBP filtering of projections"""

        ne = 4*self.n//2
        t = cp.fft.rfftfreq(ne).astype('float32')
        w = t * (1 - t * 2)**3  # parzen
        w = w*cp.exp(-2*cp.pi*1j*t*(-center+self.n/2))  # center fix
        data = cp.pad(
            data, ((0, 0), (0, 0), (ne//2-self.n//2, ne//2-self.n//2)), mode='edge')

        data = irfft(
            w*rfft(data, axis=2), axis=2).astype('float32')  # note: filter works with complex64, however, it doesnt take much time
        data = data[:, :, ne//2-self.n//2:ne//2+self.n//2]

        return data
    
    def recon(self, data, dark, flat, center):
        """Full reconstruction pipeline for a data chunk"""
        obj = cp.zeros([self.nz, self.n, self.n], dtype='float32')
        # dark-flat field correction
        data = self.darkflat_correction(data, dark, flat)
        # minus log
        data = self.minus_log(data)
        # fbp filter and compensatio for the center
        data = self.fbp_filter_center(data, center)
        # reshape to sinograms
        data = cp.ascontiguousarray(data.swapaxes(0, 1))
        dxchange.write_tiff(data[0].get(),'/data/NAISE_Spinal_Cord/tmp/proj',overwrite=True)        
        # backprojection
        self.cl_rec.backprojection(obj, data, cp.cuda.get_current_stream())
        return obj



for j in range(-40,40,10):
    shifts = [0,542,528,537,541]
    shifts = np.cumsum(shifts)
    shifts[1]+=j
    shifts[2]-=j
    g = GPURec(file,shifts)
    data_all = cp.zeros([g.nproj,2,g.n],dtype='float32')
    dark_all = cp.zeros([g.ndark,2,g.n],dtype='float32')
    flat_all = cp.zeros([g.nflat,2,g.n],dtype='float32')
    for k in range(5):
        file = f'/data/NAISE_Spinal_Cord/{k+8:03}_L7_Left_Half_5x_M_y0_x{k}.h5'
        fid = h5py.File(file,'r')
        data = fid['/exchange/data']
        dark = fid['/exchange/data_dark']
        flat = fid['/exchange/data_white']
        idslice = 799
        n = data.shape[2]
        data = cp.array(np.ascontiguousarray(data[:,idslice:idslice+2]))
        dark = cp.array(np.ascontiguousarray(dark[:,idslice:idslice+2]))*0
        flat = cp.array(np.ascontiguousarray(flat[:,idslice:idslice+2]))*1
        data_all[:,:,k*n-g.shifts[k]:(k+1)*n-g.shifts[k]] = data
        dark_all[:,:,k*n-g.shifts[k]:(k+1)*n-g.shifts[k]] = dark
        flat_all[:,:,k*n-g.shifts[k]:(k+1)*n-g.shifts[k]] = flat


    obj = g.recon(data_all,dark_all,flat_all,g.n//2)
    dxchange.write_tiff(obj[0].get(),f'/data/NAISE_Spinal_Cord/tmp/test{j+40}',overwrite=True)


