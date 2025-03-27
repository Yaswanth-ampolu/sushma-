#!/usr/bin/env python
"""
Settings Reader

A simple utility to read and display .dat file contents in a readable format.
"""

import json
import argparse
from pathlib import Path
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

def try_decrypt(data, password="sushma_default_key"):
    """Try to decrypt the data if it's encrypted."""
    try:
        # Generate key from password
        salt = b'sushma_salt_value_123'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        # Try to decrypt
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(data)
        return decrypted_data
    except:
        return None

def format_json(data):
    """Format JSON data for better readability."""
    try:
        parsed = json.loads(data)
        return json.dumps(parsed, indent=2)
    except:
        return data

def read_dat_file(file_path, password=None):
    """Read and display the contents of a .dat file."""
    try:
        # Read the file
        with open(file_path, 'rb') as f:
            data = f.read()
        
        # Check if data looks encrypted (Fernet format starts with gAAAAA)
        if data.startswith(b'gAAAAA'):
            print("File appears to be encrypted.")
            if password:
                decrypted = try_decrypt(data, password)
                if decrypted:
                    print("\nDecrypted contents:")
                    print("-" * 50)
                    print(format_json(decrypted.decode('utf-8')))
                    return
                else:
                    print("Failed to decrypt with provided password.")
            
            # Try with default password
            decrypted = try_decrypt(data)
            if decrypted:
                print("Successfully decrypted with default password.")
                print("\nDecrypted contents:")
                print("-" * 50)
                print(format_json(decrypted.decode('utf-8')))
                return
            else:
                print("Failed to decrypt with default password.")
                print("Please provide the correct password using --password option.")
                return
        
        # Try to decode as UTF-8 and format if it's JSON
        try:
            decoded = data.decode('utf-8')
            print("\nFile contents:")
            print("-" * 50)
            print(format_json(decoded))
        except UnicodeDecodeError:
            print("\nFile contains binary data:")
            print("-" * 50)
            print("Hex dump:")
            print(data.hex())
            
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except Exception as e:
        print(f"Error reading file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Read and display .dat file contents')
    parser.add_argument('file', help='Path to the .dat file')
    parser.add_argument('--password', '-p', help='Password for encrypted files')
    
    args = parser.parse_args()
    read_dat_file(args.file, args.password)

if __name__ == "__main__":
    main() 