# Settings Encryption Tool

This is a simple utility for encrypting and decrypting your `settings.dat` file in the Sushma application.

## Features

- Encrypt your settings file to keep your configurations secure
- Decrypt the settings file when needed
- Uses industry-standard encryption (Fernet symmetric encryption)
- Password-based key derivation
- Simple command-line interface

## Requirements

- Python 3.6+
- cryptography package (already installed in your environment)

## How to Use

### Basic Usage

To encrypt your settings.dat file:

```bash
python settings_crypto.py encrypt settings.dat
```

This will produce an encrypted file called `settings.dat.enc`

To decrypt the file:

```bash
python settings_crypto.py decrypt settings.dat.enc
```

This will produce a decrypted file with the original name (`settings.dat`)

### Advanced Options

#### Custom Output File

To specify a custom output file:

```bash
python settings_crypto.py encrypt settings.dat --output my_encrypted_settings.dat
python settings_crypto.py decrypt my_encrypted_settings.dat --output my_settings.dat
```

#### Custom Password

For added security, you can specify a custom password:

```bash
python settings_crypto.py encrypt settings.dat --password my_secure_password
```

Note: You must use the same password for decryption:

```bash
python settings_crypto.py decrypt settings.dat.enc --password my_secure_password
```

## How It Works

This tool uses a combination of:

1. PBKDF2 (Password-Based Key Derivation Function) - Converts your password into a secure encryption key
2. Fernet symmetric encryption - Uses the derived key to encrypt/decrypt your data
3. Base64 encoding - For safe storage of encrypted data

The encryption process adds a layer of security to your settings file, making it unreadable without the correct password.

## Educational Purpose

This tool is primarily designed for educational purposes to demonstrate basic encryption concepts. In a production environment, you might want to use more robust key management solutions.

## Quick Tips

- Keep your password safe! If you lose it, you won't be able to decrypt your settings.
- The default password is used if none is provided, but it's recommended to use a custom password for better security.
- Always back up your original settings.dat file before encrypting it. 