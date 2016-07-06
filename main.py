from xml.dom import minidom

from Xliff import Xliff

if __name__ == "__main__":
    filename = "fr.xliff"
    xliff = Xliff.read_from_disk(filename)
    xliff.combine_translator_comments()
    xliff.write_to_file('output.xml')
