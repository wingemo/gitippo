import sys
import os
import zlib
import hashlib

# At a bare minimum, a .git directory should contain the following files & directories:
# - .git/
#    - objects/
#    - refs/
#    - HEAD (should contain "ref: refs/heads/main\n" for a new repository)
def init_repo():
    try:
        os.mkdir(".gitippo")
        os.mkdir(".gitippo/objects")
        os.mkdir(".gitippo/refs")
        with open(".gitippo/HEAD", "w", encoding="utf-8") as write_head:
            write_head.write("ref: refs/heads/master\n")
        print("Successfully initialized git directory")
    except Exception as err:
        print(f"Error initializing repo: {err}")
        raise

# Read the contents of the blob object file from the .git/objects directory
# Decompress the contents using Zlib
# Extract the actual "content" from the decompressed data
# Print the content to stdout
def cat_file():
    # Hämta object_sh
    blob_sha = sys.argv[3] 

    # Bygg sökvägen till blob-filen
    object_path = f".gitippo/objects/{blob_sha[0:2]}/{blob_sha[2:]}"
    
    # Läs innehållet från blob-filen
    with open(object_path, 'rb') as file:
        compressed_data = file.read()

    # Dekomprimera datan
    decompressed_data = zlib.decompress(compressed_data)

    # Hitta positionen för null-byten (0x00)
    null_index = decompressed_data.index(b'\x00')

    # Ta bort metadata-prefixet och extrahera det råa innehållet
    content = decompressed_data[null_index + 1:]
    print(content.decode("utf-8"), end="")

# compute the hash, insert the header, zlib-compress everything 
# The input for the SHA hash is the header (blob <size>\0) + the actual contents of the file, not just the contents of the file.
# blob 11\0hello world
def hash_object():
    path = sys.argv[3]
    size = os.path.getsize(path)
    file_content = f"blob {size}\x00"

    file = open(path, "r") 
    file_content += file.read()
    file.close()

    hash = hashlib.sha1(file_content.encode("UTF-8")).hexdigest()
    contents = bytes(file_content, encoding="utf-8")
    contents = zlib.compress(contents)
    os.mkdir(f".gitippo/objects/{hash[:2]}")

    with open(f".gitippo/objects/{hash[:2]}/{hash[2:]}", "wb") as file:
        file.write(contents)

    print(hash)

#100644 blob a3e0eb5d8b2fb225f7c968b5001b2abfa1f7f3ef    file1.txt
#100644 blob 76b2a51cf4f8353ae2d4d4ec34a95d4e6af3033e    file2.txt
#040000 tree 7b7d28f0e6730c43b7b66b158c8b46f9cb4a8bfe    subdir
def write_tree():
    entries = []

    # Gå igenom alla filer och kataloger i den givna mappen
    for entry in os.listdir(directory):
        if entry == '.git':  # Ignorera .git-katalogen
            continue

        # Konstruera sökväg
        path = os.path.join(directory, entry)

        # Om det är en katalog, rekursivt skriv dess träd
        if os.path.isdir(path):
            subtree_hash = write_tree(path)
            entries.append(f'{subtree_hash} directory {entry}')
        else:
            # Läsa innehållet i filen
            with open(path, 'rb') as file:
                data = file.read()
            # Beräkna hash för filens innehåll
            file_hash = hashlib.sha1(data).hexdigest()
            entries.append(f'{file_hash} blob {entry}')

    # Sortera inmatningen för stabilitet
    entries.sort()

    # Konstruera trädets innehåll
    tree_content = '\n'.join(entries)

    # Beräkna trädets hash
    tree_hash = hashlib.sha1(tree_content.encode()).hexdigest()

    # Skriv trädets innehåll till en fil med trädets hash som namn
    tree_filename = os.path.join('.gitippo', 'objects', tree_hash[:2], tree_hash[2:])
    os.makedirs(os.path.dirname(tree_filename), exist_ok=True)
    with open(tree_filename, 'w') as tree_file:
        tree_file.write(tree_content)

    return tree_hash

def main():
    match sys.argv[1]:
        case "cat-file"     : cat_file()
        case "hash-object"  : hash_object()
        case "init"         : init(args)
        case _              : print("Bad command.")
                                        
    main()
