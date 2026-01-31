#!/usr/bin/env python3
import usb.core
import usb.util
import struct
import sys
from pathlib import Path
from PIL import Image
import io

VID = 0x87AD
PID = 0x70DB

CHUNK_SIZE = 4096
WRITE_TIMEOUT_MS = 5000


HEADER_FIXED = bytes.fromhex(
    "1234567800000000000000000000000000000000000000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "0100000000000000123456780200000040010000f00000000000000000000000"
    "0000000000000000000000000000000000000000000000000000000000000000"
    "02000000"
)

def resize_cover_320x240(jpeg_path):
    """保证铺满屏幕，多余裁切（cover 模式）"""
    img = Image.open(jpeg_path).convert("RGB")

    target_w, target_h = 320, 240
    src_w, src_h = img.size

    # cover 模式缩放
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # 居中裁切
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    right = left + target_w
    bottom = top + target_h

    img = img.crop((left, top, right, bottom))

    # 编码 JPEG
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def build_packet(jpeg_bytes):
    jpeg_len = len(jpeg_bytes)
    jpeg_len_le = struct.pack("<I", jpeg_len)
    return HEADER_FIXED + jpeg_len_le + jpeg_bytes + b"\x00\x00"

def find_out_endpoint(dev):
    for cfg in dev:
        for intf in cfg:
            for ep in intf:
                if (ep.bEndpointAddress & 0x80) == 0:
                    return intf.bInterfaceNumber, ep.bEndpointAddress
    return None, None

def claim_interface_safe(dev, intf):
    try:
        if dev.is_kernel_driver_active(intf):
            dev.detach_kernel_driver(intf)
        usb.util.claim_interface(dev, intf)
    except Exception as e:
        print("claim interface failed:", e)

def release_interface_safe(dev, intf):
    try:
        usb.util.release_interface(dev, intf)
    except:
        pass

def write_chunks(dev, ep_addr, data):
    offset = 0
    total = len(data)
    while offset < total:
        chunk = data[offset:offset + CHUNK_SIZE]
        dev.write(ep_addr, chunk, timeout=WRITE_TIMEOUT_MS)
        offset += len(chunk)

def main():
    if len(sys.argv) < 2:
        print("未提供图像，不发送任何内容")
        sys.exit(0)

    jpeg_path = sys.argv[1]
    if not Path(jpeg_path).exists():
        print("找不到文件:", jpeg_path)
        sys.exit(1)

    print("处理图像（cover 模式裁切 320x240）...")
    jpeg_bytes = resize_cover_320x240(jpeg_path)
    print("JPEG 大小:", len(jpeg_bytes))

    packet = build_packet(jpeg_bytes)
    print("完整包大小:", len(packet))

    dev = usb.core.find(idVendor=VID, idProduct=PID)
    if dev is None:
        print("未找到设备")
        sys.exit(1)

    try:
        dev.set_configuration()
    except Exception as e:
        print("set_configuration error:", e)

    intf, ep_addr = find_out_endpoint(dev)
    if intf is None:
        print("未找到 OUT 端点，使用默认 0x01")
        ep_addr = 0x01

    print("使用接口:", intf, "端点:", hex(ep_addr))

    if intf is not None:
        claim_interface_safe(dev, intf)

    print("发送图像数据...")
    write_chunks(dev, ep_addr, packet)
    print("发送完成，程序退出")

    if intf is not None:
        release_interface_safe(dev, intf)
    usb.util.dispose_resources(dev)

if __name__ == "__main__":
    main()