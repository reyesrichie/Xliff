import re
import xml
from xml.dom import minidom
from xml.etree.ElementTree import SubElement, Element, tostring


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
        tree = xml.etree.ElementTree.parse(filename)
        root = tree.getroot()
        tag = Xliff.clean_tag(root.tag)
        if tag == 'xliff':
            return cls.parse(root)

    @classmethod
    def parse(cls, root):
        raw_xmlns = ''.join(filter(lambda y: y is not None, map(lambda x: Xliff.parse_xmlns(x), root.attrib))).strip(
            '{}')
        xsi_schema = root.attrib['{' + raw_xmlns + '}' + 'schemaLocation'].split(' ')
        xmlns = xsi_schema[0]
        xmlns_xsi = raw_xmlns
        xsi_schema_location = xsi_schema[1]
        version = root.attrib['version']

        files = []

        for element in root:
            tag = Xliff.clean_tag(element.tag)
            if tag == 'file':
                files.append(File.parse(element))

        return Xliff(xmlns, xmlns_xsi, version, xsi_schema_location, files)

    def toxml(self):
        xliff = Element('xliff')
        xliff.attrib = {'xmlns': self.xmlns, 'xmlns:xsi': self.xmlns_xsi, 'version': self.version,
                        'xsi:schemaLocation': self.xmlns + ' ' + self.xsi_schema_location}
        map(lambda file: file.toxml(xliff), self.files)
        return minidom.parseString(tostring(xliff, 'utf-8')).toprettyxml(indent="    ")

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

    @classmethod
    def is_translator_comment(cls, string):
        return 'ibExternalUserDefinedRuntimeAttributes' in string

    def combine_translator_comments(self):
        for file in self.files:
            comments = Body.get_translator_comments(file.body)

            for comment in comments:
                object_id = TransUnit.get_object_id(comment.trans_unit_id)
                units = Body.get_units_with_id(file.body, object_id)

                for unit in units:
                    for note in unit.notes:
                        if 'ibExternalUserDefinedRuntimeAttributesLocalizableStrings[0]' in comment.trans_unit_id:
                            note.translator_comment = reduce(lambda x, y: x.join(y.translator_comment), comment.notes,
                                                             '')
                        elif 'ibExternalUserDefinedRuntimeAttributesLocalizableStrings[1]' in comment.trans_unit_id:
                            note.size = reduce(lambda x, y: x.join(y.size), comment.notes,
                                               '')
                file.body.trans_units.remove(comment)

    def write_to_file(self, filename):
        output = self.toxml()
        output_file = file(filename, 'w')
        output_file.write(output)


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

    def toxml(self, parent):
        file = SubElement(parent, 'file')
        file.attrib = {'original': self.original, 'source-language': self.source_language, 'datatype': self.data_type,
                       'target-language': self.target_language}
        self.header.toxml(file)
        self.body.toxml(file)
        return file


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

    def toxml(self, parent):
        header = SubElement(parent, 'header')
        map(lambda tool: tool.toxml(header), self.tools)
        return header


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

    def toxml(self, parent):
        tool = SubElement(parent, 'tool')
        tool.attrib = {'tool-id': self.tool_id, 'tool-name': self.tool_name, 'tool-version': self.tool_version,
                       'build-num': self.build_num}
        return tool


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

    def toxml(self, parent):
        body = SubElement(parent, 'body')
        map(lambda unit: unit.toxml(body), self.trans_units)

        return body

    @classmethod
    def get_translator_comments(cls, body):
        comments = []

        for unit in body.trans_units:
            if Xliff.is_translator_comment(unit.trans_unit_id):
                comments.append(unit)

        return comments

    @classmethod
    def get_units_with_id(cls, body, unit_id):
        return filter(lambda trans_unit: (unit_id in trans_unit.trans_unit_id) and not (
            Xliff.is_translator_comment(trans_unit.trans_unit_id)), body.trans_units)


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
                sources.append(Source.parse(element))
            elif tag == 'target':
                targets.append(Target.parse(element))
            elif tag == 'note':
                notes.append(Note.parse(element))

        return TransUnit(trans_unit_id, sources, targets, notes)

    @classmethod
    def get_object_id(cls, string):
        components = string.split('.')
        if len(components) > 0:
            return components[0]
        else:
            return ""

    def toxml(self, parent):
        unit = SubElement(parent, 'trans-unit')
        unit.attrib = {'id': self.trans_unit_id}
        map(lambda source: source.toxml(unit), self.sources)
        map(lambda target: target.toxml(unit), self.targets)
        map(lambda note: note.toxml(unit), self.notes)

        return unit


class Source:
    text = ""

    def __init__(self, text):
        self.text = text

    @classmethod
    def parse(cls, data):
        return Source(data.text)

    def toxml(self, parent):
        source = SubElement(parent, 'source')
        source.text = self.text
        return source


class Target:
    text = ""

    def __init__(self, text):
        self.text = text

    @classmethod
    def parse(cls, data):
        return Target(data.text)

    def toxml(self, parent):
        target = SubElement(parent, 'target')
        target.text = self.text
        return target


class Note:
    class_name = ""
    size = ""
    text = ""
    object_id = ""
    translator_comment = ""

    def __init__(self, class_name, size, text, object_id, translator_comment):
        self.class_name = class_name
        self.size = size
        self.text = text
        self.object_id = object_id
        self.translator_comment = translator_comment

    @classmethod
    def parse(cls, data):
        class_name = ""
        size = ""
        text = ""
        object_id = ""
        translator_comment = ""

        if data.text is not None:
            if "Class = " in data.text:
                properties = Note.properties_from_string(data.text)
                class_name = properties['Class']
                if 'text' in properties:
                    text = properties['text']
                elif 'title' in properties:
                    text = properties['title']
                elif 'normalTitle' in properties:
                    text = properties['normalTitle']
                elif 'placeholder' in properties:
                    text = properties['placeholder']

                if 'ObjectID' in properties:
                    object_id = properties['ObjectID']

                if "ibExternalUserDefinedRuntimeAttributesLocalizableStrings[0]" in data.text:
                    key = object_id + '.ibExternalUserDefinedRuntimeAttributesLocalizableStrings[0]'
                    translator_comment = properties[key]

                if "ibExternalUserDefinedRuntimeAttributesLocalizableStrings[1]" in data.text:
                    key = object_id + '.ibExternalUserDefinedRuntimeAttributesLocalizableStrings[1]'
                    size = properties[key]
            else:
                translator_comment = data.text

        return Note(class_name, size, text, object_id, translator_comment)

    def toxml(self, parent):
        note = SubElement(parent, 'note')
        translator = ''

        if self.class_name != '':
            translator += self.class_name
        if self.size != '':
            translator += ', ' + self.size
        if self.translator_comment != '':
            if translator == '':
                translator = self.translator_comment
            else:
                translator += ': ' + self.translator_comment

        note.text = translator

        return note

    @classmethod
    def list_to_dict(cls, list):
        return {list[0].strip(): list[1].strip().replace(r'"', "")}

    @classmethod
    def list_of_dicts_to_dict(self, list):
        dicts = {}

        for dict in list:
            dicts[dict.keys()[0]] = dict.values()[0]

        return dicts

    @classmethod
    def properties_from_string(cls, string):
        separated_elements = filter(lambda x: x != '', string.split(';'))
        separated_key_value = map(lambda y: Note.list_to_dict(y), map(lambda x: x.split('='), separated_elements))
        return Note.list_of_dicts_to_dict(separated_key_value)
