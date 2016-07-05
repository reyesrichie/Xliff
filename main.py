from Xliff import Xliff

if __name__ == "__main__":
    filename = "fr.xliff"
    xliff = Xliff.read_from_disk(filename)

    for file in xliff.files:
        for unit in file.body.trans_units:
            print unit
