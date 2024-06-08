import os
import zipfile


class Tools:
    @staticmethod
    def  zip_directory(directory_path, zip_file_path):
        # Create a ZipFile object in write mode
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through the directory
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    # Create the full file path
                    full_path = os.path.join(root, file)
                    # Add file to the zip file, preserving the directory structure
                    zipf.write(full_path, os.path.relpath(full_path, directory_path))

