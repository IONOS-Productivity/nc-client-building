import xml.etree.ElementTree as ET
import argparse
import sys

def main():
    parser = argparse.ArgumentParser(
        description="Find <File> elements in a .wxs file by matching the Name attribute."
    )
    parser.add_argument("wxs_file", help="Path to the .wxs file")
    parser.add_argument("filename", help="Filename to search for (case-insensitive)")
    parser.add_argument("--first", action="store_true", help="Only return the first match")

    args = parser.parse_args()

    try:
        tree = ET.parse(args.wxs_file)
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading WXS file: {e}", file=sys.stderr)
        return 2

    ns = {'wix': 'http://schemas.microsoft.com/wix/2006/wi'}
    ET.register_namespace('', ns['wix'])

    matches = []
    for file_elem in root.findall(".//wix:File", ns):
        name = file_elem.attrib.get("Name")
        if name and name.lower() == args.filename.lower():
            source = file_elem.attrib.get("Source")
            if source:
                matches.append(source)

    if matches:
        if args.first:
            print(matches[0])
        else:
            for match in matches:
                print(match)
        return 0  # Success
    else:
        return 1  # No match found

if __name__ == "__main__":
    sys.exit(main())
