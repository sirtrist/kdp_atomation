import os
import zipfile
import shutil
from shutil import rmtree
from tempfile import mkdtemp
from bs4 import BeautifulSoup
from langdetect import detect
from tools.utils import Windows, Reader

def create_ebook_from_directory(input_dir, output_epub):
    try:
        # Create a temporary directory to hold the contents of the ebook
        temp_dir = mkdtemp()

        # Step 1: Copy all files from input_dir to the temporary directory
        for root, _, files in os.walk(input_dir):
            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(temp_dir, os.path.relpath(src_file, input_dir))
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copyfile(src_file, dst_file)

        # Step 2: Create the EPUB file from the temporary directory
        with zipfile.ZipFile(output_epub, 'w') as zout:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    zout.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), temp_dir))

        print(f"Ebook created successfully: {output_epub}")

    except Exception as e:
        print(f"Error creating ebook: {e}")

    finally:
        # Clean up: Remove the temporary directory
        if temp_dir and os.path.exists(temp_dir):
            rmtree(temp_dir)

if __name__ == "__main__":
    # input_directory = r'scripts\epub\filtered\temp_epub_extracted'
    input_directory=r'scripts\epub\filtered\fgsihofjqzpd'
    output_epub_path = r'scripts\epub\filtered\ebook.epub'
    
    create_ebook_from_directory(input_directory, output_epub_path)
