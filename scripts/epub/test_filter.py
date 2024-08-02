import os
import zipfile
import tempfile
from bs4 import BeautifulSoup
from langdetect import detect
from tools.utils import Windows, Reader
from tools.translator import translate, get_translator

def create_epub_with_filtered_content(input_epub, output_epub, keep_temp_dir=False, full_page=False):
    temp_dir = r"scripts\epub\filtered\temp_epub_extracted"
    
    # Remove temp_dir if it exists
    if os.path.exists(temp_dir):
        for root, _, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in os.listdir(root):
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)

    # Step 1: Extract the original EPUB file to a temporary directory
    with zipfile.ZipFile(input_epub, 'r') as zin:
        zin.extractall(temp_dir)
    
    # Step 2: Filter out HTML files with keywords
    count = 0
    removed_files = []
    for root, _, files in os.walk(temp_dir):
        for file in files:            
            if file.endswith(('.xhtml', '.html', '.xml')):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
             
                if file.split('.')[1] != 'xml':
                    soup = BeautifulSoup(content, 'html.parser')
                else:
                    soup = BeautifulSoup(content, file.split('.')[1])
            
                if Reader.unloop(count):
                    count += 1
                    try:
                        # lang = detect(soup.get_text())
                        lang = 'fr'
                        
                    except:
                        lang = 'fr'
                
                tags_to_check = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'div', 'title', 'body', 'head', 'header', 'section', 'div']
                keywords_path = os.path.join('scripts', 'epub', 'tools', 'keywords')
                
                # delete row or fullpage content keywords
                keywords_to_remove = Reader.keywords_from_txt(os.path.join(keywords_path, f'{lang}.txt'))
                
                decompose_count = 0
                for tag_name in tags_to_check:
                    tags = soup.find_all(tag_name)
                    for tag in tags:
                        text = tag.get_text().lower()
                        if any(keyword in text for keyword in keywords_to_remove):
                            if full_page or decompose_count >= 3:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    removed_files.append(file)
                                    print(f"Removing {file}: {tag.get_text()[:50]}...")
                            else:
                                decompose_count += 1
                                print(f"{decompose_count} Removing tag {tag_name} from {file}: {tag.get_text()[:50]}...")
                                tag.decompose()
                
                if os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(str(soup))
                
                # change traductor
                traductor_keywords = Reader.keywords_from_txt(os.path.join(keywords_path, f'traductor_{lang}.txt'))
                
                for tag_name in tags_to_check:
                    tags = soup.find_all(tag_name)
                    for tag in tags:
                        text = tag.get_text().lower()
                        if any(keyword in text for keyword in traductor_keywords):
                            tanslator_variant = get_translator(tag)
                            if any(tanslator in text for tanslator in tanslator_variant):
                                print(f"Removing {file}: {tag.get_text()[:50]}...")
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    removed_files.append(file)
                
                
                
    print(f'Filtered in: {lang}')
    
    # Step 3: Update the content.opf file to remove references to deleted files, cover.xhtml, and guide references
    content_opf_path = None
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.opf'):
                content_opf_path = os.path.join(root, file)
                break
        if content_opf_path:
            break
    
    if not content_opf_path:
        raise FileNotFoundError("content.opf file not found in the EPUB structure.")
    
    with open(content_opf_path, 'r', encoding='utf-8') as f:
        content_opf = f.read()
    
    soup_opf = BeautifulSoup(content_opf, 'xml')
    
    meta_cover = soup_opf.find('opf:meta', {'name': 'cover'})
    if meta_cover:
        meta_cover.decompose()
    
    guide = soup_opf.find('guide')
    if guide:
        reference_cover = guide.find('reference', {'href': 'cover.xhtml'})
        if reference_cover:
            reference_cover.decompose()
        guide.decompose()
    
    for item in soup_opf.find_all('item'):
        href = item.get('href')
        if href and href.split('/')[-1] in removed_files:
            item.decompose()
    
    for itemref in soup_opf.find_all('itemref'):
        idref = itemref.get('idref')
        if idref in [os.path.splitext(file)[0] for file in removed_files]:
            itemref.decompose()
    
    with open(content_opf_path, 'w', encoding='utf-8') as f:
        f.write(str(soup_opf))
    
    # Step 4: Update the epb.ncx file to remove references to deleted files
    ncx_path = None
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith('.ncx'):
                ncx_path = os.path.join(root, file)
                break
        if ncx_path:
            break
    
    if not ncx_path:
        raise FileNotFoundError("epb.ncx file not found in the EPUB structure.")
    
    with open(ncx_path, 'r', encoding='utf-8') as f:
        ncx_content = f.read()
    
    soup_ncx = BeautifulSoup(ncx_content, 'xml')
    
    for nav_point in soup_ncx.find_all('navPoint'):
        content_src = nav_point.find('content').get('src')
        if content_src and content_src.split('#')[0] in removed_files:
            nav_point.decompose()
    
    with open(ncx_path, 'w', encoding='utf-8') as f:
        f.write(str(soup_ncx))
        
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            temp_output_path = temp_file.name
        
        with zipfile.ZipFile(temp_output_path, 'w') as zout:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    zout.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), temp_dir))
        
        os.replace(temp_output_path, output_epub)
        print(f"Filtered EPUB created successfully: {output_epub}")
    
    except Exception as e:
        print(f"Error creating filtered EPUB: {e}")
    
    finally:
        if not keep_temp_dir:
            for root, _, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in os.listdir(root):
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(temp_dir)

if __name__ == "__main__":
    input_epub_path = Windows.file_path()
    output_epub_path = r'scripts\epub\filtered\ebook.epub'
    
    create_epub_with_filtered_content(input_epub_path, output_epub_path, keep_temp_dir=1, full_page=False)
