from pathlib import Path
from io import BytesIO
import csv
import hashlib
import json
import struct
import subprocess
import sys
import zlib

import numpy as np
from PIL import Image, ImageCms

REPO = next(p for p in Path(__file__).resolve().parents if (p/'Cargo.toml').is_file() and (p/'crates/bern-backend-swiftui').is_dir())
OUT = Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = REPO / 'examples/showcase/images/hdr-pq.png'
REFERENCE = REPO / 'Docs/Evidence/macOS14-reference-normal/images-layout-light.png'


def png16_rgba(path):
    data = path.read_bytes()
    assert data[:8] == b'\x89PNG\r\n\x1a\n'
    chunks = []
    offset = 8
    while offset < len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        assert zlib.crc32(kind + body) == struct.unpack_from('>I', data, offset + 8 + length)[0]
        chunks.append((kind.decode(), body))
        offset += length + 12
    w, h, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunks[0][1])
    assert (depth, color, compression, filtering, interlace) == (16, 6, 0, 0, 0)
    packed = zlib.decompress(b''.join(body for kind, body in chunks if kind == 'IDAT'))
    stride, bpp = w * 8, 8
    previous = bytearray(stride)
    rows = []
    for y in range(h):
        filt = packed[y * (stride + 1)]
        row = bytearray(packed[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
        for i in range(stride):
            left = row[i - bpp] if i >= bpp else 0
            up = previous[i]
            upper_left = previous[i - bpp] if i >= bpp else 0
            if filt == 1:
                row[i] = (row[i] + left) & 255
            elif filt == 2:
                row[i] = (row[i] + up) & 255
            elif filt == 3:
                row[i] = (row[i] + ((left + up) // 2)) & 255
            elif filt == 4:
                p = left + up - upper_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - upper_left)
                predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                row[i] = (row[i] + predictor) & 255
            else:
                assert filt == 0
        rows.append(bytes(row))
        previous = row
    values = np.frombuffer(b''.join(rows), dtype='>u2').reshape(h, w, 4).astype(np.float64) / 65535
    return values, chunks


def pq_eotf(n):
    n = np.asarray(n, dtype=float)
    m1, m2, c1, c2, c3 = 2610 / 16384, 2523 / 32, 3424 / 4096, 2413 / 128, 2392 / 128
    power = np.maximum(n, 0) ** (1 / m2)
    return 10000 * (np.maximum(power - c1, 0) / (c2 - c3 * power)) ** (1 / m1)


def pq_inverse(luminance):
    luminance = np.asarray(luminance, dtype=float)
    m1, m2, c1, c2, c3 = 2610 / 16384, 2523 / 32, 3424 / 4096, 2413 / 128, 2392 / 128
    v = np.maximum(luminance / 10000, 0) ** m1
    return ((c1 + c2 * v) / (1 + c3 * v)) ** m2


def srgb_encode(linear):
    linear = np.clip(linear, 0, 1)
    return np.where(linear <= 0.0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - 0.055)


def srgb_decode(encoded):
    return np.where(encoded <= 0.04045, encoded / 12.92, ((encoded + 0.055) / 1.055) ** 2.4)


def annex5(luminance, source_black, source_peak, target_black, target_peak):
    # ITU-R BT.2408-6 Annex 5, equations Step 1–5.
    low, high = pq_inverse(source_black), pq_inverse(source_peak)
    delta = high - low
    x = np.clip((pq_inverse(luminance) - low) / delta, 0, 1)
    b = (pq_inverse(target_black) - low) / delta
    p = (pq_inverse(target_peak) - low) / delta
    knee = 1.5 * p - 0.5
    t = np.clip((x - knee) / (1 - knee), 0, 1)
    spline = (2 * t**3 - 3 * t**2 + 1) * knee + (t**3 - 2 * t**2 + t) * (1 - knee) + (-2 * t**3 + 3 * t**2) * p
    z = np.where(x < knee, x, spline)
    u = z + b * (1 - z)**4
    return pq_eotf(u * delta + low) / target_peak


def method_a(luminance):
    # BT.2446-1 Table 2: the neutral-axis reduction of Method A.
    # All chroma corrections vanish for R=G=B. Fixed normative 1000→100.
    hdr_peak, sdr_peak = 1000.0, 100.0
    y = np.clip(luminance / hdr_peak, 0, 1) ** (1 / 2.4)
    rho_hdr = 1 + 32 * (hdr_peak / 10000) ** (1 / 2.4)
    rho_sdr = 1 + 32 * (sdr_peak / 10000) ** (1 / 2.4)
    yp = np.log1p((rho_hdr - 1) * y) / np.log(rho_hdr)
    yc = np.where(yp <= 0.7399, 1.0770 * yp,
                  np.where(yp < 0.9909, -1.1510 * yp**2 + 2.7811 * yp - 0.6302, 0.5 * yp + 0.5))
    ysdr_gamma = (rho_sdr ** yc - 1) / (rho_sdr - 1)
    return ysdr_gamma ** 2.4


def error_metrics(predicted, measured, mask=None):
    difference = predicted - measured
    if mask is not None:
        difference = difference[mask]
    return dict(mae_srgb_255=float(np.abs(difference).mean()), rmse_srgb_255=float(np.sqrt((difference**2).mean())),
                max_abs_srgb_255=float(np.abs(difference).max()), mean_bias_srgb_255=float(difference.mean()))


def screenshot_srgb(path):
    im = Image.open(path)
    source = ImageCms.ImageCmsProfile(BytesIO(im.info['icc_profile']))
    converted = ImageCms.profileToProfile(im, source, ImageCms.createProfile('sRGB'), outputMode='RGB', renderingIntent=0)
    return np.asarray(converted, dtype=float), ImageCms.getProfileName(source).strip()


def main():
    # Numerical checks are independent of captured values.
    checks = np.array([0, 0.0005, 1, 100, 203, 812, 1000, 10000], dtype=float)
    assert np.max(np.abs(pq_eotf(pq_inverse(checks)) - checks)) < 1e-7
    assert abs(float(annex5(1000, 0, 1000, 0, 203)) - 1) < 1e-10
    assert abs(float(method_a(1000)) - 1) < 1e-10
    source, chunks = png16_rgba(SOURCE)
    upstream = subprocess.check_output(['git', 'show', 'ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee:examples/showcase/images/hdr-pq.png'], cwd=REPO)
    assert upstream == SOURCE.read_bytes(), 'Source must be byte-identical to upstream.'
    assert np.all(source[:, :, 3] == 1), 'Opaque source expected.'
    # The ramp is exactly the final third, identical on every row.
    assert np.all(source[240:, :, :] == source[240:241, :, :])
    # The nominal gray encoding can have channel-level rounding differences.
    source_n = source[280, :, :3]
    source_l = pq_eotf(source_n)
    reference, profile_name = screenshot_srgb(REFERENCE)
    # Exact screenshot geometry: 640×360 source at [435,330,192,108].
    # Keep away from top discontinuity, bottom edge and rounded containers.
    origin_x, origin_y, width, height = 435, 330, 192, 108
    y0, y1 = 409, 432
    target = reference[y0:y1, origin_x:origin_x + width, :]
    # Sample source at screen pixel centers; fixed geometric mapping, no phase fit.
    xs = np.arange(width)
    source_x = (xs + 0.5) * source.shape[1] / width - 0.5
    luminance = np.stack([np.interp(source_x, np.arange(640), source_l[:, c]) for c in range(3)], axis=-1)
    measured = target.mean(axis=0)
    measured_std = target.std(axis=0)
    lin_target = srgb_decode(target / 255).mean(axis=0)
    peak = float(source_l.max())
    candidates = {}
    parameters = {}
    for source_peak, tag in [(1000, 'ISO_reference_1000'), (peak, 'observed_asset_peak'), (10000, 'unknown_master_10000')]:
        for target_peak in [100, 203]:
            name = f'BT2408_A5_{tag}_to_{target_peak}'
            parameters[name] = dict(source_black_nit=0, source_peak_nit=source_peak, target_black_nit=0, target_peak_nit=target_peak,
                                    output_normalization_nit=target_peak, source_peak_status='hypothesis; no MDCV in source')
            candidates[name] = srgb_encode(annex5(luminance, 0, source_peak, 0, target_peak)) * 255
    parameters['BT2446_A_1000_to_100'] = dict(source_peak_nit=1000, target_peak_nit=100, method='neutral-axis Method A, Table 2, SDR gamma 2.4 decoded then encoded sRGB')
    candidates['BT2446_A_1000_to_100'] = srgb_encode(method_a(luminance)) * 255
    # Transparent controls, not claims of official tone-mapping algorithms.
    for white in [100, 203]:
        name = f'linear_clip_reference_{white}'
        parameters[name] = dict(reference_white_nit=white, purpose='no-tone-map control')
        candidates[name] = srgb_encode(luminance / white) * 255
    metrics = {}
    valid = (xs >= 2) & (xs < width - 2)
    for name, predicted in candidates.items():
        metrics[name] = error_metrics(predicted, measured, valid)
    best = candidates['BT2408_A5_ISO_reference_1000_to_203']
    robustness = {'all_192_columns': error_metrics(best, measured)}
    for a,b in [(405,410),(409,432),(423,435)]:
        robustness[f'A14_rows_{a}_{b}'] = error_metrics(best,reference[a:b,435:627,:].mean(axis=0),valid)
    for a,b in [(0,0.0005),(0.0005,0.0005)]:
        pred = srgb_encode(annex5(luminance,a,1000,b,203))*255
        robustness[f'black_sensitivity_source_{a}_target_{b}'] = error_metrics(pred,measured,valid)
    # Alternative interpolation is a bounded renderer uncertainty, not a phase fit.
    n_interp=np.stack([np.interp(source_x,np.arange(640),source_n[:,c]) for c in range(3)],axis=-1)
    pq_filtered=srgb_encode(annex5(pq_eotf(n_interp),0,1000,0,203))*255
    robustness['PQ_signal_interpolation_instead_of_linear_nit'] = error_metrics(pq_filtered,measured,valid)
    for intent in [0,1,2,3]:
        im=Image.open(REFERENCE)
        srcprofile=ImageCms.ImageCmsProfile(BytesIO(im.info['icc_profile']))
        rgb=np.asarray(ImageCms.profileToProfile(im,srcprofile,ImageCms.createProfile('sRGB'),outputMode='RGB',renderingIntent=intent),dtype=float)
        robustness[f'ICC_intent_{intent}']=error_metrics(best,rgb[y0:y1,435:627,:].mean(axis=0),valid)
    comparison_path=REPO/'Docs/Evidence/macOS14-port-comparison/showcase-images-layout-light.png'
    if comparison_path.exists():
        comp,comp_profile=screenshot_srgb(comparison_path)
        # Measured flat white runs are y331..<439, exactly +1 point vs A14.
        comp_measured=comp[y0+1:y1+1,435:627,:].mean(axis=0)
        robustness['B14_plus_one_y_rows_410_433']=error_metrics(best,comp_measured,valid)
        robustness['B14_vs_A14_aligned']=error_metrics(comp_measured,measured,valid)
        robustness['B14_provenance']=dict(path=str(comparison_path.relative_to(REPO)),sha256=hashlib.sha256(comparison_path.read_bytes()).hexdigest(),
                                          profile_name=comp_profile,image_rect=[435,331,192,108],ramp_roi=[435,410,627,433])
    knee_pq=(1.5*pq_inverse(203)/pq_inverse(1000)-0.5)*pq_inverse(1000)
    edr_predictions=[]
    for hd in [1,1.5,2,3,4,1000/203]:
        l=np.array([203.,812.])
        edr=l/203 if hd>=1000/203 else annex5(l,0,1000,0,203*hd)*hd
        edr_predictions.append(dict(display_headroom=hd,target_peak_nit=203*hd,edr_linear_white_203_peak_812=edr.tolist()))
    samples = []
    for nominal in [0.1, 0.25, 0.5, 1, 2, 3, 3.8]:
        i = int(np.argmin(np.abs(luminance.mean(axis=1) / 203 - nominal)))
        samples.append(dict(screen_x=int(origin_x + i), source_x=float(source_x[i]), source_nit=luminance[i].tolist(), source_relative_203=float(luminance[i].mean() / 203), measured_srgb_255=measured[i].tolist(),
                            measured_linear_srgb=lin_target[i].tolist(), candidates={name:float(values[i].mean()) for name, values in candidates.items()}))
    report = dict(source=dict(path=str(SOURCE.relative_to(REPO)), sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(), upstream_commit='ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee', byte_identical_to_upstream=True,
                              shape=list(source.shape), chunk_types=[kind for kind, body in chunks], cicp=next(body.hex() for kind, body in chunks if kind=='cICP'),
                              ramp_y=[240,360], ramp_rgb_pq_max_difference=float(np.ptp(source_n, axis=1).max()), ramp_peak_nit=peak,
                              top_left_nit=pq_eotf(source[100,100,:3]).tolist(), top_right_nit=pq_eotf(source[100,500,:3]).tolist(),
                              ramp_monotone=bool(np.all(np.diff(source_l,axis=0)>=0)), valid_alpha_opaque=True),
                  reference=dict(path=str(REFERENCE.relative_to(REPO)), sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(), image_size=[reference.shape[1],reference.shape[0]], profile_name=profile_name,
                                 image_rect=[origin_x,origin_y,width,height], ramp_roi=[origin_x,y0,origin_x+width,y1], pixel_mapping='source_x=(screen_index+0.5)*640/192-0.5; linear-nit interpolation',
                                 valid_screen_x=[origin_x+2,origin_x+width-2], color_pipeline='embedded ICC → LittleCMS perceptual sRGB 8-bit; average 23 interior rows',
                                 max_row_std_srgb_255=float(measured_std[valid].max()), mean_row_std_srgb_255=float(measured_std[valid].mean()),
                                 max_measured_channel_spread=float(np.ptp(measured[valid],axis=1).max())),
                  parameters=parameters, metrics=metrics, samples=samples, robustness=robustness,
                  candidate_geometry=dict(knee_input_nit=float(pq_eotf(knee_pq)),knee_input_relative_203=float(pq_eotf(knee_pq)/203),
                                          full_sampled_nit_interval=[float(luminance[0].mean()),float(luminance[-1].mean())],
                                          inner_188_sampled_nit_interval=[float(luminance[2].mean()),float(luminance[-3].mean())],
                                          linear_srgb_rmse=float(np.sqrt(np.mean((srgb_decode(best[valid]/255)-lin_target[valid])**2))),
                                          left_plateau_predicted_srgb_255=float(srgb_encode(annex5(pq_eotf(source[100,100,0]),0,1000,0,203))*255),
                                          right_plateau_predicted_srgb_255=float(srgb_encode(annex5(pq_eotf(source[100,500,0]),0,1000,0,203))*255)),
                  unvalidated_edr_extension=edr_predictions,
                  constraints=['No fitting or geometry optimization.', 'Source/master peak and target absolute white are explicit alternative hypotheses, not observed macOS parameters.', 'Only neutral SDR captured axis: color treatment and current-headroom HDR behavior not identified.'])
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'ramp.csv').open('w',newline='') as f:
        writer=csv.writer(f)
        writer.writerow(['screen_x','source_x','pq_r','pq_g','pq_b','nit_mean','source_relative_203','measured_r','measured_g','measured_b','measured_linear_mean']+list(candidates))
        for i in range(width):
            pq=[float(np.interp(source_x[i],np.arange(640),source_n[:,c])) for c in range(3)]
            writer.writerow([origin_x+i,source_x[i],*pq,float(luminance[i].mean()),float(luminance[i].mean()/203),*measured[i],float(lin_target[i].mean()),*[float(v[i].mean()) for v in candidates.values()]])
    print(json.dumps({'metrics':metrics,'robustness':robustness,'candidate_geometry':report['candidate_geometry'],'unvalidated_edr_extension':edr_predictions},indent=2))


if __name__=='__main__': main()
