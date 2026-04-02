# #########################################################################
# Copyright (c) 2022, UChicago Argonne, LLC. All rights reserved.         #
# #########################################################################

"""
Pre- and post-processing steps for the tile mosaic pipeline:

  tile bin        – spatially bin raw tile HDF5 files
  tile dump-flats – collect flat field basis from binned files
  tile vstitch    – vertically stitch per-row tile.h5 files
  tile double-fov – convert 360° acquisition to 180° by stitching paired projections
"""

import glob
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import h5py
import numpy as np

from tile import log

__all__ = ['bin_data', 'dump_flats', 'vstitch', 'double_fov']


# ─────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ─────────────────────────────────────────────────────────────────────────────

def _quintic_ramp(n):
    """Quintic blending ramp 1→0 of length n (same kernel used everywhere)."""
    v = np.linspace(1, 0, n, endpoint=False)
    return v**5 * (126 - 420*v + 540*v**2 - 315*v**3 + 70*v**4)


def _bin2d(arr, factor):
    """Average-bin the last two axes of arr by factor."""
    n0 = arr.shape[-2] // factor * factor
    n1 = arr.shape[-1] // factor * factor
    a = arr[..., :n0, :n1]
    shape = a.shape[:-2] + (n0 // factor, factor, n1 // factor, factor)
    return a.reshape(shape).mean(axis=(-3, -1)).astype(np.float32)


def _resolve_path(base, name):
    """Return name as-is if absolute, else join with base."""
    if os.path.isabs(name):
        return name
    return os.path.join(str(base), name)


# ─────────────────────────────────────────────────────────────────────────────
# tile bin
# ─────────────────────────────────────────────────────────────────────────────

def _copy_item(src_item, dst_parent, bin_factor, proj_step, chunk_size=16):
    """Recursively copy groups/datasets; bin exchange datasets."""
    DATASETS_TO_BIN   = {'/exchange/data', '/exchange/data_white', '/exchange/data_dark'}
    DATASETS_SUBSAMPLE = {'/exchange/data'}
    THETA_PATH = '/exchange/theta'

    name = src_item.name.split('/')[-1]

    if isinstance(src_item, h5py.Group):
        grp = dst_parent.require_group(name)
        for k, v in src_item.attrs.items():
            grp.attrs[k] = v
        for child in src_item.values():
            _copy_item(child, grp, bin_factor, proj_step, chunk_size)

    elif isinstance(src_item, h5py.Dataset):
        full_path = src_item.name

        if full_path in DATASETS_TO_BIN:
            raw_shape = src_item.shape
            subsample = full_path in DATASETS_SUBSAMPLE
            indices = list(range(0, raw_shape[0], proj_step)) if subsample else list(range(raw_shape[0]))
            n_out = len(indices)
            H_out = raw_shape[-2] // bin_factor * bin_factor // bin_factor
            W_out = raw_shape[-1] // bin_factor * bin_factor // bin_factor
            ds = dst_parent.create_dataset(name, shape=(n_out, H_out, W_out), dtype=np.float32,
                                           chunks=(min(chunk_size, n_out), H_out, W_out))
            for k, v in src_item.attrs.items():
                ds.attrs[k] = v
            batches = [indices[i:i+chunk_size] for i in range(0, n_out, chunk_size)]
            out_pos = 0
            for batch in batches:
                chunk = src_item[list(batch)]
                end_pos = out_pos + len(batch)
                ds[out_pos:end_pos] = _bin2d(chunk, bin_factor)
                out_pos = end_pos
                log.info(f'  {name}: {out_pos}/{n_out} frames ({100*out_pos/n_out:.0f}%)')

        elif full_path == THETA_PATH:
            theta_sub = src_item[::proj_step]
            ds = dst_parent.create_dataset(name, data=theta_sub)
            for k, v in src_item.attrs.items():
                ds.attrs[k] = v
            log.info(f'  theta: {len(theta_sub)} values (every {proj_step}th)')

        else:
            dst_parent.copy(src_item, name)


def bin_data(args):
    """Spatially bin raw tile HDF5 files and optionally subsample projections."""

    log.info('Run bin')
    folder = str(args.folder_name)
    bin_factor = 2 ** args.binning
    proj_step = args.bin_step

    if args.bin_output_dir:
        dest_dir = args.bin_output_dir
    else:
        dest_dir = os.path.join(folder, f'bin{bin_factor}x{bin_factor}')

    os.makedirs(dest_dir, exist_ok=True)

    files = sorted(glob.glob(os.path.join(folder, '*.h5')))
    if not files:
        raise RuntimeError(f'No .h5 files found in {folder}')

    log.info(f'Found {len(files)} file(s) → {dest_dir}  '
             f'(bin={bin_factor}x{bin_factor}, proj_step={proj_step})')

    for src_path in files:
        fname = os.path.basename(src_path)
        dst_path = os.path.join(dest_dir, fname)
        log.info(f'[{fname}] → {dst_path}')
        with h5py.File(src_path, 'r') as src, h5py.File(dst_path, 'w') as dst:
            for k, v in src.attrs.items():
                dst.attrs[k] = v
            for item in src.values():
                _copy_item(item, dst, bin_factor, proj_step)
        log.info(f'  done.')

    log.info('Bin complete.')


# ─────────────────────────────────────────────────────────────────────────────
# tile dump-flats
# ─────────────────────────────────────────────────────────────────────────────

def dump_flats(args):
    """Collect flat field basis from binned tile HDF5 files.

    For each input file two averaged frames are written:
      frame 2i   – mean of first  half of data_white frames
      frame 2i+1 – mean of second half of data_white frames
    """

    log.info('Run dump-flats')
    folder = str(args.folder_name)
    step = -1 if args.reverse_step == 'True' else 1

    if args.y_folders:
        yfolders = [y.strip() for y in args.y_folders.split(',')]
        all_files = []
        for yf in yfolders:
            ydir = os.path.join(folder, yf)
            files = sorted(glob.glob(os.path.join(ydir, '*.h5')))
            if not files:
                log.warning(f'No .h5 files in {ydir}')
            else:
                log.info(f'{yf}: {len(files)} file(s)')
                all_files.extend(files)
    else:
        all_files = sorted(glob.glob(os.path.join(folder, '*.h5')))
        log.info(f'Found {len(all_files)} file(s) in {folder}')

    if not all_files:
        raise RuntimeError('No HDF5 files found for dump-flats.')

    with h5py.File(all_files[0], 'r') as f0:
        flat0 = f0['/exchange/data_white'][:, :, ::step].astype('float32')
        H, W = flat0.shape[1], flat0.shape[2]

    N = len(all_files)
    out_flats = np.zeros((2 * N, H, W), dtype='float32')

    for i, fpath in enumerate(all_files):
        with h5py.File(fpath, 'r') as fin:
            flat = fin['/exchange/data_white'][:, :, ::step].astype('float32')
        n = flat.shape[0]
        out_flats[2*i]   = np.mean(flat[:n//2], axis=0)
        out_flats[2*i+1] = np.mean(flat[n//2:], axis=0)
        log.info(f'  [{i+1}/{N}] {os.path.relpath(fpath, folder)}  ({n} frames)')

    output = _resolve_path(folder, args.dump_flats_output)
    if os.path.exists(output):
        os.remove(output)

    with h5py.File(output, 'w') as fout:
        fout.create_dataset('/exchange/data_white', data=out_flats, chunks=(1, H, W))
        dt = h5py.string_dtype()
        fout.create_dataset('file_names', data=np.array(all_files, dtype=object), dtype=dt)

    log.info(f'Flat basis shape: {2*N} x {H} x {W}')
    log.info(f'Output: {output}')


# ─────────────────────────────────────────────────────────────────────────────
# tile vstitch
# ─────────────────────────────────────────────────────────────────────────────

def vstitch(args):
    """Vertically stitch per-row tile.h5 files into a single dataset."""

    log.info('Run vstitch')

    if args.y_shifts == 'None':
        raise RuntimeError('--y-shifts is required for tile vstitch (e.g. "[0,450,450]")')

    y_shifts = np.fromstring(args.y_shifts[1:-1], sep=',', dtype='int')
    folder = str(args.folder_name)

    # resolve input files
    if args.vstitch_pattern:
        files = sorted(glob.glob(args.vstitch_pattern))
    elif args.y_folders:
        yfolders = [y.strip() for y in args.y_folders.split(',')]
        files = []
        for yf in yfolders:
            p = os.path.join(folder, yf, 'tile', 'tile.h5')
            if not os.path.exists(p):
                raise RuntimeError(f'Expected tile.h5 not found: {p}')
            files.append(p)
    else:
        candidate = os.path.join(folder, 'tile', 'tile.h5')
        if os.path.exists(candidate):
            files = [candidate]
        else:
            raise RuntimeError(
                'Cannot determine input files. Provide --y-folders, --vstitch-pattern, '
                'or place tile.h5 under <folder-name>/tile/tile.h5.')

    if len(files) != len(y_shifts):
        raise RuntimeError(f'{len(files)} files found but {len(y_shifts)} y-shifts given.')

    log.info(f'Found {len(files)} file(s):')
    for f, ys in zip(files, y_shifts):
        log.info(f'  y_shift={ys:4d}  {f}')

    with h5py.File(files[0], 'r') as f0:
        N_proj, H, W = f0['/exchange/data'].shape
        theta = f0['/exchange/theta'][:]

    cum = np.array([int(np.sum(y_shifts[:i+1])) for i in range(len(y_shifts))])
    H_out = H + int(cum[-1])

    log.info(f'Input  shape: {N_proj} x {H} x {W}')
    log.info(f'Output shape: {N_proj} x {H_out} x {W}')

    output = _resolve_path(folder, args.vstitch_output)
    if os.path.exists(output):
        os.remove(output)

    nchunk = args.nproj_per_chunk

    def process_chunk(st_p):
        end_p = min(st_p + nchunk, N_proj)
        n = end_p - st_p
        buf = np.zeros((n, H_out, W), dtype='float32')
        ref_overlap_mean = None

        for itile, (fpath, row_st) in enumerate(zip(files, cum)):
            row_end = row_st + H
            ww = np.ones(H, dtype='float32')
            if itile < len(files) - 1:
                overlap_bot = H - y_shifts[itile + 1]
                if overlap_bot > 0:
                    ww[y_shifts[itile + 1]:] = _quintic_ramp(overlap_bot)
            if itile > 0:
                overlap_top = H - y_shifts[itile]
                if overlap_top > 0:
                    ww[:overlap_top] = 1.0 - _quintic_ramp(overlap_top)

            with h5py.File(fpath, 'r') as fin:
                chunk = fin['/exchange/data'][st_p:end_p].astype('float32')

            # intensity scale calibration in overlap with previous tile
            if itile > 0 and ref_overlap_mean is not None:
                overlap_top = H - y_shifts[itile]
                if overlap_top > 0:
                    cur_means = np.mean(chunk[:, :overlap_top, :], axis=(1, 2))
                    valid = cur_means > 1e-6
                    scales = np.where(valid, ref_overlap_mean / np.where(valid, cur_means, 1.0), 1.0)
                    chunk *= scales[:, np.newaxis, np.newaxis]
            if itile < len(files) - 1:
                overlap_bot = H - y_shifts[itile + 1]
                if overlap_bot > 0:
                    ref_overlap_mean = np.mean(chunk[:, -overlap_bot:, :], axis=(1, 2))

            buf[:, row_st:row_end, :] += chunk * ww[np.newaxis, :, np.newaxis]

        np.nan_to_num(buf, nan=0.0, posinf=0.0, neginf=0.0, copy=False)
        return st_p, end_p, buf

    with h5py.File(output, 'w') as fout:
        data_out = fout.create_dataset('/exchange/data', shape=(N_proj, H_out, W),
                                       dtype='float32', chunks=(1, H_out, W))
        fout.create_dataset('/exchange/data_white', data=np.ones((1, H_out, W), dtype='float32'))
        fout.create_dataset('/exchange/data_dark',  data=np.zeros((1, H_out, W), dtype='float32'))
        fout.create_dataset('/exchange/theta', data=theta)

        chunk_starts = list(range(0, N_proj, nchunk))
        pending = {}
        next_write = 0

        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {pool.submit(process_chunk, st): st for st in chunk_starts}
            for fut in as_completed(futures):
                st_p, end_p, buf = fut.result()
                pending[st_p] = (end_p, buf)
                while next_write in pending:
                    ep, b = pending.pop(next_write)
                    log.info(f'Writing projections {next_write:4d} - {ep:4d}')
                    data_out[next_write:ep] = b
                    next_write = ep

    log.info(f'vstitch output: {output}')


# ─────────────────────────────────────────────────────────────────────────────
# tile double-fov
# ─────────────────────────────────────────────────────────────────────────────

def double_fov(args):
    """Convert 360° acquisition to 180° by stitching paired projections.

    For each index i, stitches projection[i] with fliplr(projection[i + N//2]).
    The rotation axis position controls the overlap/shift between the two halves.
    """

    log.info('Run double-fov')
    folder = str(args.folder_name)

    input_path  = _resolve_path(folder, args.double_fov_input)
    output_path = _resolve_path(folder, args.double_fov_output)

    if args.rotation_axis <= 0:
        raise RuntimeError('--rotation-axis must be set for tile double-fov.')

    with h5py.File(input_path, 'r') as fin:
        N_proj, H, W = fin['/exchange/data'].shape
        theta = fin['/exchange/theta'][:]

    if N_proj % 2 != 0:
        raise RuntimeError(f'Number of projections ({N_proj}) must be even for 360→180 conversion.')

    N_half = N_proj // 2
    cen = args.rotation_axis
    shift_val = int(round(2 * cen)) - W + 1
    abs_shift = abs(shift_val)
    W_out = (W + abs_shift) // 4 * 4
    overlap = W - abs_shift

    if overlap <= 0:
        raise RuntimeError(
            f'No overlap between the two halves (shift={shift_val}, W={W}). '
            f'Check --rotation-axis value.')

    p0_off = 0         if shift_val >= 0 else abs_shift
    p1_off = shift_val if shift_val >= 0 else 0

    blend_p0 = _quintic_ramp(overlap)
    blend_p1 = 1.0 - _quintic_ramp(overlap)

    if shift_val >= 0:
        ov_col_p0 = slice(W - overlap, W)
        ov_col_p1 = slice(0, overlap)
        out_ov    = slice(p1_off, p1_off + overlap)
    else:
        ov_col_p0 = slice(0, overlap)
        ov_col_p1 = slice(W - overlap, W)
        out_ov    = slice(p0_off, p0_off + overlap)

    out_col_p0 = slice(p0_off, p0_off + W)
    out_col_p1 = slice(p1_off, p1_off + W)

    log.info(f'Input  shape : {N_proj} x {H} x {W}')
    log.info(f'Output shape : {N_half} x {H} x {W_out}')
    log.info(f'Rotation axis: {cen:.1f}  shift: {shift_val}  overlap: {overlap}')

    nchunk = args.nproj_per_chunk

    def process_chunk(st_p, end_p):
        with h5py.File(input_path, 'r') as fin:
            proj0 = fin['/exchange/data'][st_p:end_p].astype('float32')
            proj1 = fin['/exchange/data'][N_half + st_p:N_half + end_p].astype('float32')
        proj1 = proj1[:, :, ::-1]

        n = end_p - st_p
        buf = np.zeros((n, H, W + abs_shift), dtype='float32')
        buf[:, :, out_col_p0] += proj0
        buf[:, :, out_col_p1] += proj1
        buf[:, :, out_ov] = (proj0[:, :, ov_col_p0] * blend_p1[np.newaxis, np.newaxis, :]
                           + proj1[:, :, ov_col_p1] * blend_p0[np.newaxis, np.newaxis, :])
        np.nan_to_num(buf, nan=1.0, posinf=1.0, neginf=1.0, copy=False)
        return st_p, end_p, buf[:, :, :W_out]

    if os.path.exists(output_path):
        os.remove(output_path)

    with h5py.File(output_path, 'w') as fout:
        data_out = fout.create_dataset('/exchange/data', shape=(N_half, H, W_out),
                                       dtype='float32', chunks=(1, H, W_out))
        fout.create_dataset('/exchange/data_white', data=np.ones((1, H, W_out), dtype='float32'))
        fout.create_dataset('/exchange/data_dark',  data=np.zeros((1, H, W_out), dtype='float32'))
        fout.create_dataset('/exchange/theta', data=theta[:N_half])

        chunk_starts = list(range(0, N_half, nchunk))
        pending = {}
        next_write = 0

        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {pool.submit(process_chunk, st, min(st + nchunk, N_half)): st
                       for st in chunk_starts}
            for fut in as_completed(futures):
                st_p, end_p, buf = fut.result()
                pending[st_p] = (end_p, buf)
                while next_write in pending:
                    ep, b = pending.pop(next_write)
                    log.info(f'Writing projections {next_write:4d} - {ep:4d}')
                    data_out[next_write:ep] = b
                    next_write = ep

    log.info(f'double-fov output: {output_path}')
