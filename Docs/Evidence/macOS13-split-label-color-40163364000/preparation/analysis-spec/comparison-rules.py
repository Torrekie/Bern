"""Frozen pure comparison rules only. No paths, candidate loading or execution entry."""


def channel_differences(left, right, channels, included=None):
    if len(left) != len(right) or len(left) % channels:
        raise ValueError('Aligned complete byte pixels required')
    pixels = range(len(left)//channels) if included is None else included
    sums, maxima, changed = [0]*channels, [0]*channels, [0]*channels
    count = changed_pixels = 0
    for pixel in pixels:
        if not 0 <= pixel < len(left)//channels:
            raise ValueError('Pixel outside frozen region')
        offset = pixel*channels
        diff = [abs(left[offset+c]-right[offset+c]) for c in range(channels)]
        count += 1
        changed_pixels += any(diff)
        for c, value in enumerate(diff):
            sums[c] += value; maxima[c] = max(maxima[c],value); changed[c] += value != 0
    return {'pixels':count,'changed_pixels':changed_pixels,
            'channel_mean_abs':[value/count for value in sums] if count else None,
            'channel_max_abs':maxima,'channel_changed_pixels':changed,
            'exact':changed_pixels == 0}


def outside_label_pixels(frame_width, frame_height, label_relative_pixels):
    x0,y0,x1,y1 = label_relative_pixels
    if not (0 <= x0 < x1 <= frame_width and 0 <= y0 < y1 <= frame_height):
        raise ValueError('Frozen label rectangle is outside Frame ROI')
    return (y*frame_width+x for y in range(frame_height) for x in range(frame_width)
            if not (x0 <= x < x1 and y0 <= y < y1))


def error_change(original, candidate, target, channels):
    if len(original) != len(candidate) or len(candidate) != len(target) or len(target) % channels:
        raise ValueError('Aligned full diagnostic arrays required')
    n = len(target)//channels
    sums_old,sums_new = [0]*channels,[0]*channels
    maxima_old,maxima_new = [0]*channels,[0]*channels
    improved,worsened,tied = [0]*channels,[0]*channels,[0]*channels
    for offset in range(0,len(target),channels):
        for c in range(channels):
            a = abs(original[offset+c]-target[offset+c])
            b = abs(candidate[offset+c]-target[offset+c])
            sums_old[c] += a; sums_new[c] += b
            maxima_old[c] = max(maxima_old[c],a); maxima_new[c] = max(maxima_new[c],b)
            improved[c] += b < a; worsened[c] += b > a; tied[c] += b == a
    return {'pixels':n,'original_channel_mean_abs':[v/n for v in sums_old] if n else None,
            'candidate_channel_mean_abs':[v/n for v in sums_new] if n else None,
            'delta_candidate_minus_original':[float(b-a)/n for a,b in zip(sums_old,sums_new)] if n else None,
            'original_channel_max_abs':maxima_old,'candidate_channel_max_abs':maxima_new,
            'channel_improved_pixels':improved,'channel_worsened_pixels':worsened,'channel_tied_pixels':tied}


def frozen_foreground(original_rgba, candidate_rgba, size, mask_runs, target_rgb_mean):
    width,height = size
    if len(original_rgba) != len(candidate_rgba) or len(original_rgba) != width*height*4 or len(target_rgb_mean) != 3:
        raise ValueError('Frozen native label shape required')
    selected=[]; previous_y=-1
    for row in mask_runs:
        y=row['y']
        if not previous_y < y < height:
            raise ValueError('Invalid frozen mask row')
        previous_y=y; previous_x=0
        for x0,x1 in row['runs_half_open_x']:
            if not previous_x <= x0 < x1 <= width:
                raise ValueError('Invalid frozen mask run')
            previous_x=x1
            selected.extend(y*width+x for x in range(x0,x1))
    if not selected:
        raise ValueError('No original foreground; never retune from candidate')
    n=len(selected)
    sums_old,sums_new,signed_delta = [0.0]*3,[0.0]*3,[0]*3
    max_old,max_new = [0.0]*3,[0.0]*3
    improved,worsened,tied = [0]*3,[0]*3,[0]*3
    for pixel in selected:
        offset=pixel*4
        if original_rgba[offset+3] != 255 or candidate_rgba[offset+3] != 255:
            raise ValueError('Frozen opaque foreground alpha changed')
        for c in range(3):
            old=abs(original_rgba[offset+c]-target_rgb_mean[c])
            new=abs(candidate_rgba[offset+c]-target_rgb_mean[c])
            sums_old[c]+=old; sums_new[c]+=new
            max_old[c]=max(max_old[c],old); max_new[c]=max(max_new[c],new)
            signed_delta[c]+=candidate_rgba[offset+c]-original_rgba[offset+c]
            improved[c]+=new < old; worsened[c]+=new > old; tied[c]+=new == old
    old_mean=[v/n for v in sums_old];new_mean=[v/n for v in sums_new]
    return {'pixels':n,'target14_channel_mean':target_rgb_mean,
            'original_channel_mean_abs_error':old_mean,'candidate_channel_mean_abs_error':new_mean,
            'delta_candidate_minus_original':[b-a for a,b in zip(old_mean,new_mean)],
            'original_channel_max_abs_error':max_old,'candidate_channel_max_abs_error':max_new,
            'channel_improved_pixels':improved,'channel_worsened_pixels':worsened,'channel_tied_pixels':tied,
            'channel_signed_mean_color_delta':[v/n for v in signed_delta],
            'color_direction_rule_met':all(b <= a for a,b in zip(old_mean,new_mean)) and any(b < a for a,b in zip(old_mean,new_mean)),
            'epsilon':0,'scope':'All RGB channels separately; not a complete acceptance result'}
