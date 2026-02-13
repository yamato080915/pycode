import cssutils, logging
import xml.etree.ElementTree as ET

cssutils.log.setLevel(logging.CRITICAL)
ET.register_namespace("", "http://www.w3.org/2000/svg")

def get_css_property(style, selector, property_name, default=None):
	"""CSSファイルから指定セレクタのプロパティ値を取得"""
	try:
		parser = cssutils.CSSParser(validate=False)
		for rule in parser.parseFile(style["style"]):
			if rule.type == rule.STYLE_RULE:
				if rule.selectorText == selector:
					value = rule.style.getPropertyValue(property_name)
					if value:
						return value
	except:
		pass
	return default

def css_color(style):
	return get_css_property(style, "QPlainTextEdit", "color", "#000000")

def icon_color(svgpath, color):
	tree = ET.parse(svgpath)
	root = tree.getroot()
	for elem in root.iter():
		if 'fill' in elem.attrib:
			elem.attrib['fill'] = color
	tree.write(svgpath, encoding="utf-8", xml_declaration=False)
