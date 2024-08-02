import os
import zipfile
import tempfile
from bs4 import BeautifulSoup
from langdetect import detect
from tools.utils import Windows, Reader
from tools.translator import translate
# from tools.test_translate import translate

from rich.progress import Progress
from rich.console import Console
from rich.panel import Panel

console = Console()

def create_epub_with_filtered_content(input_epub, output_epub, keep_temp_dir=False, copyright:int = 3, lang_input:str = 'fr', lang_output:str ='en'):
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
        # for file in tqdm(files, desc="Processing files"):
        for file in files:

            if file.endswith('.xhtml') or file.endswith('.html') or file.endswith('.xml') or file.endswith('.opf')or file.endswith('.ncx'):
                
                file_path = os.path.join(root, file)
                
                parent_dir = os.path.dirname(file_path)

                if os.path.basename(parent_dir) == 'META-INF':
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
             
                if file.endswith('.xml') or file.endswith('.opf')or file.endswith('.ncx'):
                    soup = BeautifulSoup(content, 'xml')
                else:
                    soup = BeautifulSoup(content, 'html.parser')
            
                # if Reader.unloop(count):
                #     count += 1
                #     try:
                #         # lang = detect(soup.get_text())
                #         lang = 'fr'
                        
                #     except:
                #         lang = 'fr'
                
                tags_to_check = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'b', 'div', 'title', 'body', 'head', 'header', 'section', 'div', 'span', 'text', 'i', 'a', 'li', 'ul']
                keywords_path = os.path.join('scripts', 'epub', 'tools', 'keywords')
                
                # delete row or fullpage content keywords
                keywords_to_remove = Reader.keywords_from_txt(os.path.join(keywords_path, f'{lang_input}.txt'))
                
                decompose_count = 0
                for tag_name in tags_to_check:
                    tags = soup.find_all(tag_name)
                    for tag in tags:
                        text = tag.get_text().lower()
                        if any(keyword in text for keyword in keywords_to_remove):
                            if decompose_count >= copyright:
                                if os.path.exists(file_path):
                                    os.remove(file_path)
                                    removed_files.append(file)
                                    console.print(f"[red]Removing {file}: {tag.get_text()[:50]}...[/red]")
                            else:
                                decompose_count += 1
                                console.print(f"[yellow]{decompose_count} Removing tag {tag_name} from {file}: {tag.get_text()[:50]}...[/yellow]")
                                tag.decompose()

                
                rm_tags = ['dc:title', 'dc:creator', 'dc:date', 'dc:contributor', 'dc:language', 'dc:identifier']
                
                for tag_name in rm_tags:
                    tags = soup.find_all(tag_name)
                    for tag in tags:
                        tag.decompose()
                        
                        

                
                # rewrite page without tag decomposed
                if os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(str(soup))
                
                
    
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
    
    # Remove <opf:meta> tag with name="cover"
    meta_cover = soup_opf.find('opf:meta', {'name': 'cover'})
    if meta_cover:
        meta_cover.decompose()
    
    # Remove <guide> section and any <reference> to cover.xhtml
    guide = soup_opf.find('guide')
    if guide:
        reference_cover = guide.find('reference', {'href': 'cover.xhtml'})
        if reference_cover:
            reference_cover.decompose()
        guide.decompose()
    
    # Remove references to deleted files in <item> and <itemref>
    for itemref in soup_opf.find_all('itemref'):
        idref = itemref.get('idref')
        for item in soup_opf.find_all('item'):
            id = item.get('id')
            href = item.get('href')
            if idref == id and href.split('/')[-1] in removed_files:
                itemref.decompose()
                

    for item in soup_opf.find_all('item'):
        href = item.get('href')
        if href and href.split('/')[-1] in removed_files:
            item.decompose()

    
    # Save the modified content.opf
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
    
    # Remove references to deleted files in ncx
    for nav_point in soup_ncx.find_all('navPoint'):
        try: content_src = nav_point.find('content').get('src')
        except Exception as e: console.print(f'[red]error: {e}')
        if content_src and content_src.split('#')[0] in removed_files:
            nav_point.decompose()
            
    
    # Save the modified epb.ncx
    with open(ncx_path, 'w', encoding='utf-8') as f:
        f.write(str(soup_ncx))
        
    
    # translate(lang_input, lang_output)
    
    ##################################################################################################################################

    # Step 5: Create the filtered EPUB
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.epub') as temp_file:
            temp_output_path = temp_file.name
        
        with zipfile.ZipFile(temp_output_path, 'w') as zout:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    zout.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), temp_dir))
        
        # Move the temporary file to the final output path
        os.replace(temp_output_path, output_epub)
        console.print(Panel(f"[green]Filtered EPUB created successfully: {output_epub}[/green]", style='green', width=50))
    
    except Exception as e:
        console.print(Panel(f"[red]Error creating filtered EPUB: {e}[/red]", style='red', width=50))
    
    finally:
        # Clean up temporary directory
        if not keep_temp_dir:
            for root, _, files in os.walk(temp_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in os.listdir(root):
                    os.rmdir(os.path.join(root, dir))
            os.rmdir(temp_dir)



if __name__ == "__main__":

    input_epub_path = Windows.file_path(ext=[("EPUB files", "*.epub")])
    print(input_epub_path)
    
    lang_input = 'fr' # of file
    lang_output = 'en' # make output prompte for change it
    
    file_name = os.path.basename(input_epub_path).split('.')[0]
    output_epub_path = rf'scripts\epub\filtered\({lang_output}){file_name.lower()[:10]}.epub'
    
    create_epub_with_filtered_content(
                                        input_epub      =   input_epub_path,
                                        output_epub     =   output_epub_path,
                                        keep_temp_dir   =   True,
                                        copyright       =   3,
                                        lang_input      =   lang_input,
                                        lang_output     =   lang_output
                                      )
