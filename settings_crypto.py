#!/usr/bin/env python
"""
Settings Encrypter/Decrypter

A utility to encrypt and decrypt settings.dat file with a simple encryption scheme.
This is for educational purposes to demonstrate basic encryption concepts.
"""

import base64
import os
import argparse
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SettingsCrypto:
    """Handles encryption and decryption of settings.dat file."""
    
    def __init__(self, password=None):
        """Initialize with optional password."""
        # Default password if none provided
        self.password = password or "sushma_default_key"
        # Salt should ideally be stored separately in a real application
        self.salt = b'sushma_salt_value_123'
        self.key = self._derive_key()
        
    def _derive_key(self):
        """Derive encryption key from password."""
        password_bytes = self.password.encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt_file(self, input_file, output_file=None):
        """Encrypt the settings file."""
        if output_file is None:
            output_file = input_file + '.enc'
            
        try:
            # Read the input file
            with open(input_file, 'rb') as f:
                data = f.read()
            
            # Encrypt the data
            fernet = Fernet(self.key)
            encrypted_data = fernet.encrypt(data)
            
            # Write the encrypted data
            with open(output_file, 'wb') as f:
                f.write(encrypted_data)
                
            print(f"File encrypted successfully: {output_file}")
            return True
        except Exception as e:
            print(f"Encryption error: {str(e)}")
            return False
    
    def decrypt_file(self, input_file, output_file=None):
        """Decrypt the settings file."""
        if output_file is None:
            # Remove .enc extension if present
            if input_file.endswith('.enc'):
                output_file = input_file[:-4]
            else:
                output_file = input_file + '.dec'
                
        try:
            # Read the encrypted file
            with open(input_file, 'rb') as f:
                encrypted_data = f.read()
            
            # Decrypt the data
            fernet = Fernet(self.key)
            decrypted_data = fernet.decrypt(encrypted_data)
            
            # Write the decrypted data
            with open(output_file, 'wb') as f:
                f.write(decrypted_data)
                
            print(f"File decrypted successfully: {output_file}")
            return True
        except Exception as e:
            print(f"Decryption error: {str(e)}")
            return False


def main():
    """Command line interface for the encryption tool."""
    parser = argparse.ArgumentParser(description='Encrypt or decrypt settings.dat file')
    parser.add_argument('action', choices=['encrypt', 'decrypt'], 
                        help='Action to perform: encrypt or decrypt')
    parser.add_argument('file', help='Path to the file to process')
    parser.add_argument('--output', '-o', help='Output file path (optional)')
    parser.add_argument('--password', '-p', help='Custom password (optional)')
    
    args = parser.parse_args()
    
    crypto = SettingsCrypto(args.password)
    
    if args.action == 'encrypt':
        crypto.encrypt_file(args.file, args.output)
    else:  # decrypt
        crypto.decrypt_file(args.file, args.output)


if __name__ == "__main__":
    main() 