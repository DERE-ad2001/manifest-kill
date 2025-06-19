import argparse
import os
import zipfile
import shutil
import struct
import subprocess

def extract_apk(apk_path, extract_dir):
    with zipfile.ZipFile(apk_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)

def insert_null_bytes(manifest_bytes, null_bytes):
    FILE_SIZE_OFFSET = 0x04
    STRING_CHUNK_SIZE_OFFSET = 0x0C
    STRING_POOL_OFFSET_OFFSET = 0x1C

    original_file_size = struct.unpack('<I', manifest_bytes[FILE_SIZE_OFFSET:FILE_SIZE_OFFSET+4])[0]
    original_chunk_size = struct.unpack('<I', manifest_bytes[STRING_CHUNK_SIZE_OFFSET:STRING_CHUNK_SIZE_OFFSET+4])[0]
    original_pool_offset = struct.unpack('<I', manifest_bytes[STRING_POOL_OFFSET_OFFSET:STRING_POOL_OFFSET_OFFSET+4])[0]

    insert_pos = original_pool_offset + 8
    patched = (
        manifest_bytes[:insert_pos] +
        (b'\x00' * null_bytes) +
        manifest_bytes[insert_pos:]
    )

    patched = bytearray(patched)
    struct.pack_into('<I', patched, FILE_SIZE_OFFSET, original_file_size + null_bytes)
    struct.pack_into('<I', patched, STRING_CHUNK_SIZE_OFFSET, original_chunk_size + null_bytes)
    struct.pack_into('<I', patched, STRING_POOL_OFFSET_OFFSET, original_pool_offset + null_bytes)

    return bytes(patched)

def rebuild_apk(folder_path, out_apk):
    shutil.make_archive("temp_unsigned", 'zip', folder_path)
    os.rename("temp_unsigned.zip", out_apk)

def zipalign(input_apk, output_apk):
    if os.path.exists(output_apk):
        os.remove(output_apk)
    subprocess.run(["zipalign", "-f", "-p", "4", input_apk, output_apk], check=True)


def sign_apk(input_apk, output_apk, keystore, alias, storepass, keypass):
    subprocess.run([
        "apksigner", "sign",
        "--ks", keystore,
        "--ks-key-alias", alias,
        "--ks-pass", f"pass:{storepass}",
        "--key-pass", f"pass:{keypass}",
        "--min-sdk-version", "21",
        "--out", output_apk,
        input_apk
    ], check=True)

def main():
    parser = argparse.ArgumentParser(description="Glitch manifest and sign APK")
    parser.add_argument("--apk", required=True, help="Input APK file")
    parser.add_argument("--null-bytes", type=int, default=4, help="Null bytes to inject")
    parser.add_argument("--keystore", required=True, help="Keystore path")
    parser.add_argument("--alias", required=True, help="Key alias")
    parser.add_argument("--storepass", required=True, help="Keystore password")
    parser.add_argument("--keypass", required=True, help="Key password")
    parser.add_argument("--output", default="signed.apk", help="Output signed APK")

    args = parser.parse_args()
    
    if args.null_bytes % 4 != 0:
    	print("[-] Error: --null-bytes must be a multiple of 4.")
    	exit(1)

    # Step 0: Make a safe copy of the original APK
    working_apk = "working.apk"
    shutil.copyfile(args.apk, working_apk)
    print(f"[+] Copied {args.apk} -> {working_apk}")

    # Step 1: Extract AndroidManifest.xml from working copy
    subprocess.run(["unzip", "-o", working_apk, "AndroidManifest.xml"], check=True)

    # Step 2: Patch the manifest
    with open("AndroidManifest.xml", "rb") as f:
        manifest_bytes = f.read()

    patched = insert_null_bytes(manifest_bytes, args.null_bytes)

    with open("AndroidManifest.xml", "wb") as f:
        f.write(patched)
    print(f"[+] Patched AndroidManifest.xml with {args.null_bytes} null bytes")

    # Step 3: Inject it back into the working APK
    subprocess.run(["zip", "-u", working_apk, "AndroidManifest.xml"], check=True)

    # Step 4: Zipalign
    aligned_apk = "aligned.apk"
    if os.path.exists(aligned_apk):
        os.remove(aligned_apk)
    subprocess.run(["zipalign", "-f", "-p", "4", working_apk, aligned_apk], check=True)

    # Step 5: Sign it
    if os.path.exists(args.output):
        os.remove(args.output)

    sign_apk(aligned_apk, args.output, args.keystore, args.alias, args.storepass, args.keypass)

    print(f"\n✅ Final APK created: {args.output}")


if __name__ == "__main__":
    main()
