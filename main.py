from xml.dom import minidom
from Xliff import Xliff
import os

if __name__ == "__main__":
    folder = "/Users/Ricardo/Documents/Ariba"

    for subdirectory, directory, files in os.walk(folder):
        for file in files:
            path = os.path.join(subdirectory, file)

            filename, file_extension = os.path.splitext(path)
            if file_extension == '.xliff':
                xliff = Xliff.read_from_disk(path)
                xliff.combine_translator_comments()

                translator_dir = os.path.join(subdirectory, 'translator')
                if not os.path.exists(translator_dir):
                    os.makedirs(translator_dir)

                xliff.write_to_file(os.path.join(translator_dir, file))
