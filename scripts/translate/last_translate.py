import re
import csv
import os
from bs4 import BeautifulSoup, Comment
from langdetect import detect, LangDetectException
import pycountry
# from tqdm import tqdm
from rich.progress import Progress, track
from rich.console import Console
from rich.panel import Panel

try:
    from tools.utils import Gpt
except ImportError:
    from utils import Gpt

    
console = Console()



def get_language_name(lang_code):
    """Retourne le nom de la langue à partir du code langue (alpha-2)."""
    return pycountry.languages.get(alpha_2=lang_code).name if pycountry.languages.get(alpha_2=lang_code) else 'Unknown Language'

def translate_ebook_content(content: str, lang_input: str = 'fr', lang_output: str = 'en') -> str:
    """Traduit le contenu d'un ebook en préservant la structure HTML/XML."""
    lang_input_name = get_language_name(lang_input)
    lang_output_name = get_language_name(lang_output)
    
    context = f"""
    You are an expert literary translator, specializing in translating {lang_input_name} ebooks to {lang_output_name}. Your task is to faithfully translate the content while preserving the style, tone, and nuances of the original. You should maintain the HTML/XML structure of the input.

    Translation Guidelines:
    1. Maintain the author's literary style and the original text's register.
    2. Preserve figures of speech and idiomatic expressions, using {lang_output_name} equivalents where appropriate.
    3. Handle proper nouns, places, and culturally specific terms appropriately.
    4. Pay attention to details and subtleties, including puns and rhymes.
    5. Preserve all HTML/XML tags and attributes in their original form, without modifying them !
    6. Only translate the text content within the tags, not the tags themselves.
    7. Maintain the original formatting and structure of the document.
    8. If there are any specific ebook or EPUB-related tags or metadata, not preserve them.
    9. Replace the edition with KDP Amazon, delete the ISBN, if there is "ebook", an internet link, or anything related to electronic publishing, delete the text.
    10. Change translator to Michel Düshtern
    """

    input_text="""<p class="Standard">Le calcul des probabilités est une science vaine, qu'il faut se défier de cet instinct obscur que nous nommions bon sens et auquel nous demandions de légitimer nos conventions.</p>"""
    output_text="""<p class="Standard">The calculation of probabilities is a vain science, and we must be wary of that obscure instinct we called common sense, which we asked to legitimize our conventions.</p>"""
    
    return Gpt.writer(context, input_text, output_text, content)

def split_text_into_chunks(text, max_tokens):
    """Divise le texte en morceaux ne dépassant pas le nombre maximal de tokens."""
    words = text.split()
    chunks, current_chunk, current_length = [], [], 0

    for word in words:
        word_length = len(word) + 1
        if current_length + word_length > max_tokens:
            chunks.append(" ".join(current_chunk))
            current_chunk, current_length = [word], word_length
        else:
            current_chunk.append(word)
            current_length += word_length

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

def initialize_translation_status(csv_file):
    """Crée le fichier CSV pour suivre l'état des traductions si nécessaire."""
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['file_path', 'translated'])

def load_translation_status(csv_file):
    """Charge l'état des traductions depuis le fichier CSV."""
    translation_status = {}
    if os.path.exists(csv_file):
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            translation_status = {row['file_path']: row['translated'] for row in reader}
    return translation_status

def save_translation_status(csv_file, translation_status):
    """Enregistre l'état des traductions dans le fichier CSV."""
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['file_path', 'translated'])
        writer.writerows(translation_status.items())

def process_file(file_path, translation_status, csv_file, lang_input: str, lang_output: str):
    """Traite un fichier pour traduction et met à jour l'état dans le fichier CSV."""
    
    file = os.path.basename(file_path)
    
    if translation_status.get(file_path) == 'true':
        console.print(f"[yellow]Skipping {file} as it is already translated.[/yellow]")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    xml_decl = re.search(r'<\?xml[^>]+\?>', content)
    doctype = re.search(r'<!DOCTYPE[^>]+>', content)

    if xml_decl:
        content = content.replace(xml_decl.group(0), '').strip()
    if doctype:
        content = content.replace(doctype.group(0), '').strip()
    
    content = content.replace('&gt;', '>').replace('&lt;', '<')
    content = content.replace('span>', 'span> ').replace('<span', ' <span')
    content = content.replace(' ', ' ')#.replace('’', "'").replace('–', '-')
    
    soup = BeautifulSoup(content, 'xml' if file_path.endswith(('.xml', '.opf', '.ncx')) or content.strip().startswith('<?xml') else 'html.parser')


    text_elements = soup.find_all(string=True)

    for element in track(text_elements, description=f'[cyan]translation {file}'):
        # imortant for save comment in comment string
        if isinstance(element, str) and element.parent.name not in ['script', 'style']:
            if not isinstance(element, Comment):
                # tranlate start
                text = element.strip()
                if text:
                    while True:
                        try:
                            chunks = split_text_into_chunks(text, max_tokens=1000)
                            translated_chunks = [translate_ebook_content(chunk, lang_input, lang_output) for chunk in chunks]
                            # translated_chunks = [chunk for chunk in chunks] # for test
                            translated_text = "".join(translated_chunks)
                            trans_text = translated_text.strip()

                            break
                        
                        except Exception as e:
                            console.print(f'[red]   error : {e}')
                            continue

                    while True:
                        try:
                            try: detected_langs = detect(trans_text)
                            except: detected_langs = ''
                            
                            if detected_langs == lang_input:
                                miss_chunks = translate_ebook_content(trans_text, lang_input, lang_output)
                                # miss_chunks = trans_text # for test
                                miss_text = "".join(miss_chunks)
                                element.replace_with(miss_text)
                            else:
                                element.replace_with(trans_text)

                            break
                        
                        except Exception as e:
                            console.print(f'[red]   error : {e}')
                            continue
                
                
    # keep /!\ very important for initialyze content and correctly use after -> re.search(r'<\?xml[^>]+\?>', content)
    content = str(soup).replace('&gt;', '>').replace('&lt;', '<')


    with open(file_path, 'w', encoding='utf-8') as file:
        
        if xml_decl:
            file.write(xml_decl.group(0) + '\n')
            if re.search(r'<\?xml[^>]+\?>', content):
                if doctype:
                    file.write(doctype.group(0) + '\n')
                
                all_lines_except_first = content.splitlines()[1:]  # Obtenir toutes les lignes sauf la première
                for line in all_lines_except_first:
                    file.write(line + '\n')

        if not re.search(r'<\?xml[^>]+\?>', content):
            if doctype:
                file.write(doctype.group(0) + '\n')
            file.write(str(soup))

    # write translate_status true for this file
    translation_status[file_path] = 'true'
    save_translation_status(csv_file, translation_status)


def translate(lang_input: str = 'fr', lang_output: str = 'en'):
    """Traduit les fichiers dans le répertoire spécifié et met à jour leur état dans le fichier CSV."""
    # temp_dir = r"scripts\epub\filtered\en_US_henri"
    temp_dir = r"scripts\epub\filtered\temp_epub_extracted"
    
    translate_dir = r'scripts\translate'
    csv_file = os.path.join(translate_dir, 'translation_status.csv')

    initialize_translation_status(csv_file)
    translation_status = load_translation_status(csv_file)

    # all_files_translated = True

    for root, _, files in os.walk(temp_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path.endswith(('.xhtml', '.html', '.xml', '.opf', '.ncx')) and os.path.basename(os.path.dirname(file_path)) != 'META-INF':
                process_file(file_path, translation_status, csv_file, lang_input, lang_output)

    if all(status == 'true' for status in translation_status.values()):
        if os.path.exists(csv_file):
            os.remove(csv_file)
            console.print(Panel("[green]All files translated successfully. CSV file deleted.[/green]", style='green', width=50))
    else:
        console.print(Panel("[red]Some files were not translated successfully or CSV file does not exist.[/red]", style='red', width=50))

    console.print(Panel("[blue]Translation completed and saved.[/blue]", style='blue', width=50))

if __name__ == "__main__":
    translate()
