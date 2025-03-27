#!/usr/bin/env python
"""
Demo script for encrypting and decrypting settings.dat from the appdata directory.
This shows a practical example of how to use the SettingsCrypto class.
"""

from settings_crypto import SettingsCrypto
import os
import shutil

def main():
    """Demonstrate encryption and decryption of settings.dat file."""
    # Path to the settings file
    settings_path = os.path.join("appdata", "settings.dat")
    
    # Backup the original settings file
    backup_path = os.path.join("appdata", "settings.dat.backup")
    print(f"Making backup of settings file: {backup_path}")
    shutil.copy2(settings_path, backup_path)
    
    # Create a SettingsCrypto instance with a custom password
    password = "my_secret_password"
    crypto = SettingsCrypto(password)
    
    # Paths for encrypted and decrypted files
    encrypted_path = os.path.join("appdata", "settings.dat.enc")
    decrypted_path = os.path.join("appdata", "settings_decrypted.dat")
    
    # Encrypt the file
    print(f"\n===== Encrypting settings file =====")
    print(f"Source: {settings_path}")
    print(f"Destination: {encrypted_path}")
    success = crypto.encrypt_file(settings_path, encrypted_path)
    
    if success:
        # Print file sizes to demonstrate the encryption occurred
        original_size = os.path.getsize(settings_path)
        encrypted_size = os.path.getsize(encrypted_path)
        print(f"\nOriginal file size: {original_size} bytes")
        print(f"Encrypted file size: {encrypted_size} bytes")
        
        # Now decrypt the file
        print(f"\n===== Decrypting settings file =====")
        print(f"Source: {encrypted_path}")
        print(f"Destination: {decrypted_path}")
        success = crypto.decrypt_file(encrypted_path, decrypted_path)
        
        if success:
            # Verify the decrypted file is identical to the original
            decrypted_size = os.path.getsize(decrypted_path)
            print(f"\nDecrypted file size: {decrypted_size} bytes")
            
            # Compare the content of original and decrypted files
            with open(settings_path, 'rb') as f1, open(decrypted_path, 'rb') as f2:
                original_content = f1.read()
                decrypted_content = f2.read()
                
            if original_content == decrypted_content:
                print("\n✅ SUCCESS: Decrypted file is identical to the original!")
            else:
                print("\n❌ ERROR: Decrypted file differs from the original!")
        
        print("\nDemonstration complete!")
        print(f"Original backup: {backup_path}")
        print(f"Encrypted file: {encrypted_path}")
        print(f"Decrypted file: {decrypted_path}")

if __name__ == "__main__":
    main() 