import re
import xml.etree.ElementTree as Et


class Xliff:
    xmlns = ""
    xmlns_xsi = ""
    version = ""
    xsi_schema_location = ""
    files = []

    def __init__(self, xmlns, xmlns_xsi, version, xsi_schema_location, files):
        self.xmlns = xmlns
        self.xmlns_xsi = xmlns_xsi
        self.version = version
        self.xsi_schema_location = xsi_schema_location
        self.files = files

    @classmethod
    def read_from_disk(cls, filename):
        tree = Et.parse(filename)
        root = tree.getroot()
        tag = Xliff.clean_tag(root.tag)
        if tag == 'xliff':
            return cls.parse(root)

    @classmethod
    def parse(cls, root):
        xmlns = ''.join(filter(lambda y: y is not None, map(lambda x: Xliff.parse_xmlns(x), root.attrib))).strip('{}')
        xsi_schema = root.attrib['{' + xmlns + '}' + 'schemaLocation'].split(' ')
        xmlns_xsi = xsi_schema[0]
        xsi_schema_location = xsi_schema[1]
        version = root.attrib['version']

        files = []

        for element in root:
            tag = Xliff.clean_tag(element.tag)
            if tag == 'file':
                files.append(File.parse(element))

        return Xliff(xmlns, xmlns_xsi, version, xsi_schema_location, files)

    @classmethod
    def clean_tag(cls, tag):
        namespace = Xliff.parse_xmlns(tag)
        if namespace is not None:
            return tag.replace(namespace, "")
        else:
            return None

    @classmethod
    def parse_xmlns(cls, string):
        matches = re.search(r'\{(.*?)\}', string)
        if matches is not None:
            return matches.group(0)
        else:
            return None


class File:
    original = ""
    source_language = ""
    data_type = ""
    target_language = ""
    header = None
    body = None

    def __init__(self, original, source_language, data_type, target_language, header, body):
        self.original = original
        self.source_language = source_language
        self.data_type = data_type
        self.target_language = target_language
        self.header = header
        self.body = body

    @classmethod
    def parse(cls, data):

        original = data.attrib['original']
        source_language = data.attrib['source-language']
        data_type = data.attrib['datatype']
        target_language = data.attrib['target-language']
        header = None
        body = None

        for element in data:
            tag = Xliff.clean_tag(element.tag)

            if tag == 'header':
                header = Header.parse(element)
            elif tag == 'body':
                body = Body.parse(element)

        return File(original, source_language, data_type, target_language, header, body)


class Header:
    tools = []

    def __init__(self, tools):
        self.tools = tools

    @classmethod
    def parse(cls, data):

        tools = []

        for element in data:
            tag = Xliff.clean_tag(element.tag)

            if tag == 'tool':
                tools.append(Tool.parse(element))

        return Header(tools)


class Tool:
    tool_id = ""
    tool_name = ""
    tool_version = ""
    build_num = ""

    def __init__(self, tool_id, tool_name, tool_version, build_num):
        self.tool_id = tool_id
        self.tool_name = tool_name
        self.tool_version = tool_version
        self.build_num = build_num

    @classmethod
    def parse(cls, data):
        tool_id = data.attrib['tool-id']
        tool_name = data.attrib['tool-name']
        tool_version = data.attrib['tool-version']
        build_num = data.attrib['build-num']

        return Tool(tool_id, tool_name, tool_version, build_num)


class Body:
    trans_units = []

    def __init__(self, trans_units):
        self.trans_units = trans_units

    @classmethod
    def parse(cls, data):
        trans_units = []

        for element in data:
            tag = Xliff.clean_tag(element.tag)

            if tag == 'trans-unit':
                trans_units.append(TransUnit.parse(element))

        return Body(trans_units)


class TransUnit:
    trans_unit_id = ""
    sources = []
    targets = []
    notes = []

    def __init__(self, trans_unit_id, sources, targets, notes):
        self.trans_unit_id = trans_unit_id
        self.sources = sources
        self.targets = targets
        self.notes = notes

    @classmethod
    def parse(cls, data):
        trans_unit_id = data.attrib['id']
        sources = []
        targets = []
        notes = []

        for element in data:
            tag = Xliff.clean_tag(element.tag)

            if tag == 'source':
                sources.append(element)
            elif tag == 'target':
                targets.append(element)
            elif tag == 'note':
                Note.parse(element)

        return TransUnit(trans_unit_id, sources, targets, notes)


class Source:
    text = ""

    def __init__(self, text):
        self.text = text

    @classmethod
    def parse(cls, data):
        return Source(data.text)


class Target:
    text = ""

    def __init__(self, text):
        self.text = text

    @classmethod
    def parse(cls, data):
        return Target(data.text)


class Note:
    class_name = ""
    text = ""
    object_id = ""
    translator_comment = ""

    def __init__(self, class_name, text, object_id, translator_comment):
        self.class_name = class_name
        self.text = text
        self.object_id = object_id
        self.translatorComment = translator_comment

    @classmethod
    def parse(cls, data):
        print data