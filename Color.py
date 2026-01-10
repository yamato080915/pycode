import cssutils, logging
import xml.etree.ElementTree as ET

cssutils.log.setLevel(logging.CRITICAL)
ET.register_namespace("", "http://www.w3.org/2000/svg")

def css_color(style):
	parser = cssutils.CSSParser(validate=False)
	for rule in parser.parseFile(style["style"]):
		if rule.type == rule.STYLE_RULE:
			if rule.selectorText == "QPlainTextEdit":
				color = rule.style.getPropertyValue("color")
	if not color:color = "#000000"
	return color

def icon_color(svgpath, color):
	tree = ET.parse(svgpath)
	root = tree.getroot()
	for elem in root.iter():
		if 'fill' in elem.attrib:
			elem.attrib['fill'] = color
	tree.write(svgpath, encoding="utf-8", xml_declaration=False)
