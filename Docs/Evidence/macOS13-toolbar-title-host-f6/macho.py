import hashlib
import struct

def sha(data):
    return hashlib.sha256(data).hexdigest()

def macho(path):
    raw = path.read_bytes()
    header = struct.unpack_from('<8I', raw)
    assert header[0] == 0xfeedfacf and header[1] == 0x100000c
    sections, segments, signature, offset = [], [], None, 32
    for _ in range(header[4]):
        command, size = struct.unpack_from('<II', raw, offset)
        assert size >= 8 and offset+size <= len(raw)
        if command == 0x1d:
            data_offset, data_size = struct.unpack_from('<II', raw, offset+8)
            signature = dict(command_offset=offset, command_size=size,
                             data_offset=data_offset, data_size=data_size)
        if command == 0x19:
            name = raw[offset+8:offset+24].rstrip(b'\0').decode()
            values = struct.unpack_from('<4Q', raw, offset+24)
            segments.append(dict(name=name, command_offset=offset,
                                 vmaddr=values[0], vmsize=values[1], fileoff=values[2], filesize=values[3]))
            count = struct.unpack_from('<I', raw, offset+64)[0]
            for index in range(count):
                values = struct.unpack_from('<16s16sQQIIIIIIII', raw, offset+72+80*index)
                section, segment, address, length, start = values[:5]
                zero = values[8] & 255 in (1, 0xc, 0x12)
                data = b'' if zero else raw[start:start+length]
                assert zero or len(data) == length
                sections.append(dict(segment=segment.rstrip(b'\0').decode(),
                    section=section.rstrip(b'\0').decode(), address=address, size=length,
                    file_offset=start, zero_fill=zero, sha256=None if zero else sha(data)))
        offset += size
    assert offset == 32+header[5] and signature
    lo = signature['command_offset']; hi = lo+signature['command_size']
    start = signature['data_offset']; end = start+signature['data_size']
    assert hi <= start and end <= len(raw)
    strict = sha(raw[:lo]+raw[hi:start]+raw[end:])
    normalized = bytearray(raw)
    for segment in segments:
        if segment['name'] == '__LINKEDIT':
            n = segment['command_offset']
            normalized[n+32:n+40] = bytes(8)
            normalized[n+48:n+56] = bytes(8)
    return dict(path=str(path), bytes=len(raw), sha256=sha(raw), signature=signature,
        segments=segments, sections=sections,
        signature_command_blob_excluded_sha256=strict,
        signature_storage_sizes_normalized_sha256=sha(normalized[:lo]+normalized[hi:start]+normalized[end:]))
