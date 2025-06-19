
# 📄 manifest-kill.py — Usage Guide

This shitty script that injects null bytes into the `AndroidManifest.xml` of an APK file and re-signs it properly using a provided keystore. 

---

## ✅ Basic Usage

```bash
python3 manifest-kill.py \
  --apk <input_apk> \
  --null-bytes <number_of_bytes> \
  --keystore <keystore_path> \
  --alias <key_alias> \
  --storepass <keystore_password> \
  --keypass <key_password> \
  --output <signed_output_apk>
```

## 🔧 Required Arguments

| Argument        | Description                                       |
|----------------|---------------------------------------------------|
| `--apk`        | Input APK file to be patched.                     |
| `--null-bytes` | Number of null bytes to inject (**must be multiple of 4**). |
| `--keystore`   | Path to your `.jks` keystore file.                |
| `--alias`      | Alias name used in the keystore.                  |
| `--storepass`  | Password for the keystore.                        |
| `--keypass`    | Password for the key inside the keystore.         |
| `--output`     | Output file name for the signed APK.              |

---

## ⚠️ Important Rules

- The `--null-bytes` value **must be a multiple of 4**.  

```bash
