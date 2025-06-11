import argparse
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from pathlib import Path

def sanitize_advertise(wxs_path: Path, shortcut_id: str, in_place: bool):
    ET.register_namespace('', "http://schemas.microsoft.com/wix/2006/wi")  # suppress ns0 in output
    tree = ET.parse(wxs_path)
    root = tree.getroot()

    ns = {'wix': 'http://schemas.microsoft.com/wix/2006/wi'}

    # Find <Shortcut Id="...">
    shortcut = root.find(f".//wix:Shortcut[@Id='{shortcut_id}']", namespaces=ns)

    if shortcut is None:
        print(f"[ERR] No <Shortcut> with Id='{shortcut_id}' found.")
        return

    shortcut.set('Advertise', 'no')
    print(f"[OK] Set Advertise=\"no\" on <Shortcut Id=\"{shortcut_id}\">")
    
    shortcut.set('Target', '[INSTALLDIR]IONOS_HiDrive_Next.exe')
    print(f"[OK] Set Advertise=\"no\" on <Shortcut Id=\"{shortcut_id}\">")

    if in_place:
        tree.write(wxs_path, encoding='utf-8', xml_declaration=True)
        print(f"[OK] Saved changes to: {wxs_path}")
    else:
        output_file = wxs_path.with_name(wxs_path.stem + "_patched.wxs")
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print(f"[OK] Saved to: {output_file}")
        
def element_exists(parent, tag, attrib, ns):
    """Check if an element with the same tag and attributes already exists under the given parent."""
    for child in parent.findall(f"wix:{tag}", namespaces=ns):
        if all(child.get(k) == v for k, v in attrib.items()):
            return True
    return False
        
def repair_ui(wxs_path: Path, extracted_path: Path, in_place: bool):
    ET.register_namespace('', "http://schemas.microsoft.com/wix/2006/wi")  # suppress ns0 in output
    tree = ET.parse(wxs_path)
    root = tree.getroot()

    ns = {'wix': 'http://schemas.microsoft.com/wix/2006/wi'}

    product = root.find(".//wix:Product", namespaces=ns)
    if product is None:
        print("[ERR] No <Product> element found.")
        return

    # ---------------------------------------
    # --- Fixing Banner and Dialog images ---
    # ---------------------------------------

    # Create <WixVariable Id="WixUIBannerBmp" Value="WixUI_Bmp_Banner" />
    extracted_path = Path(extracted_path) / "Binary"
    banner_path = extracted_path / "WixUI_Bmp_Banner"
    banner_var = Element("WixVariable", {
        "Id": "WixUIBannerBmp",
        "Value": str(banner_path) 
    })


    # Create <WixVariable Id="WixUIDialogBmp" Value="WixUI_Bmp_Dialog" />
    dialog_path = extracted_path / "WixUI_Bmp_Dialog"
    dialog_var = Element("WixVariable", {
        "Id": "WixUIDialogBmp",
        "Value": str(dialog_path) 
    })

    if not element_exists(product, banner_var.tag, banner_var.attrib, ns):
        product.append(banner_var)
    if not element_exists(product, banner_var.tag, banner_var.attrib, ns):
        product.append(dialog_var)


    ui = product.find("wix:UI", namespaces=ns)
    if ui is None:
        print("ℹ️ <UI> not found — creating new <UI> section.")
        ui = ET.SubElement(product, f"{{{ns['wix']}}}UI")


    # ---------------------------------------
    # --- Hiding the License Page -----------
    # ---------------------------------------
    
    # Define the elements to add
    ui_items = []
    ui_items.append(Element("UIRef", {"Id": "WixUI_FeatureTree"}))
    ui_items.append(Element("UIRef", {"Id": "WixUI_ErrorProgressText"}))
    ui_items.append(Element("UIRef", {"Id": "WixUI_ErrorProgressText"}))
    element = Element("Publish", {
                    "Dialog": "WelcomeDlg",
                    "Control": "Next",
                    "Event": "NewDialog",
                    "Value": "CustomizeDlg",
                    "Order": "3"
                })
    element.text = "1"
    ui_items.append(element)
    element = Element("Publish", {
                    "Dialog": "CustomizeDlg",
                    "Control": "Back",
                    "Event": "NewDialog",
                    "Value": "WelcomeDlg",
                    "Order": "3"
                })
    element.text = "1"
    ui_items.append(element)
    element = Element("Publish", {
                    "Dialog": "ExitDialog",
                    "Control": "Finish",
                    "Event": "DoAction",
                    "Value": "LaunchApplication",
                })
    element.text = "WIXUI_EXITDIALOGOPTIONALCHECKBOX = 1 and NOT Installed"
    ui_items.append(element)


    # Insert into <UI> (you can use .append or insert if ordering matters)
    for elem in reversed(ui_items):
        if not element_exists(ui, elem.tag, elem.attrib, ns):
            ui.insert(0, elem)

    if in_place:
        tree.write(wxs_path, encoding='utf-8', xml_declaration=True)
        print(f"[OK] Saved changes to: {wxs_path}")
    else:
        output_file = wxs_path.with_name(wxs_path.stem + "_patched.wxs")
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print(f"[OK] Saved to: {output_file}")

# CLI
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set Advertise=\"no\" on a specific <Shortcut> in a .wxs file.")
    parser.add_argument("wxs_path", type=Path, help="Path to the .wxs file")
    # parser.add_argument("shortcut_id", help="Id of the <Shortcut> to fix")
    parser.add_argument("--extracted-path", required=True, help="Path to the extracted binary files")

    args = parser.parse_args()
    sanitize_advertise(args.wxs_path, "Desktop", True)
    sanitize_advertise(args.wxs_path, "StartMenu", True)
    repair_ui(args.wxs_path, args.extracted_path , True)
