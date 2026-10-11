import re
import zlib
import base64
import lzw

def patch_and_repack(input_path, output_path, root_password="turktelekom1"):
    with open(input_path, 'rb') as f:
        header = f.read(60)
        match = re.search(b'<compressed alg=lzw len=(\\d+)>', header)
        if not match:
            raise ValueError("Invalid Zyxel backup header")
        data_len = int(match.group(1))
        comp_data = f.read(data_len)

    decoder = lzw.PagingDecoder(initial_code_size=258)
    xml_bytes = b"".join([b"".join(pg) for pg in decoder.decodepages(comp_data)])
    xml_text = xml_bytes.decode('utf-8')

    # 1. Enable root and update root password
    # Base64 with trailing null byte as used in Zyxel configs
    encoded_root_pwd = base64.b64encode((root_password + '\x00').encode('utf-8')).decode('ascii')
    
    # Replace root block
    old_root_block = re.search(
        r'<Use_Login_Info instance="1">\s*<UserName>root</UserName>.*?</Use_Login_Info>',
        xml_text,
        re.DOTALL
    )
    if not old_root_block:
        raise ValueError("Root user block not found in XML!")
    
    new_root_block = f'''<Use_Login_Info instance="1">
          <UserName>root</UserName>
          <Password>{encoded_root_pwd}</Password>
          <Enable>TRUE</Enable>
        </Use_Login_Info>'''
    
    xml_text = xml_text.replace(old_root_block.group(0), new_root_block)

    # 2. Enable Telnet in LocalAccess
    old_local_access = re.search(
        r'<LocalAccess>\s*<Port>([^<]+)</Port>\s*<Protocol>([^<]+)</Protocol>\s*</LocalAccess>',
        xml_text
    )
    if old_local_access:
        new_local_access = '''<LocalAccess>
          <Port>80,443,23</Port>
          <Protocol>HTTP,HTTPS,TELNET</Protocol>
        </LocalAccess>'''
        xml_text = xml_text.replace(old_local_access.group(0), new_local_access)

    modified_xml_bytes = xml_text.encode('utf-8')

    # 3. Compress with LZW PagingEncoder
    encoder = lzw.PagingEncoder(258, 2**12)
    new_comp_data = b"".join(encoder.encodepages([modified_xml_bytes]))

    # 4. Calculate CRC (JAMCRC = CRC32 ^ 0xFFFFFFFF)
    crc = zlib.crc32(new_comp_data) ^ 0xFFFFFFFF

    # 5. Build 60-byte header
    h_prefix = f'<compressed alg=lzw len={len(new_comp_data)}>'.encode('ascii')
    crc_str = f'<crc=0x{crc:08x}>'.encode('ascii')
    new_header = h_prefix.ljust(40, b'\x00') + crc_str
    new_header = new_header.ljust(60, b'\x00')

    with open(output_path, 'wb') as f:
        f.write(new_header + new_comp_data)

    print(f"Repacked successfully to {output_path}!")
    print(f"Header: {new_header}")
    print(f"Compressed length: {len(new_comp_data)}, CRC: 0x{crc:08x}")

if __name__ == '__main__':
    patch_and_repack('configuration-backupsettings.conf', 'modified-backupsettings.conf')
