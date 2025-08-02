import xml.etree.ElementTree as ET
from xml.dom import minidom
import logging
import time
from collections import Counter

from core.models.string_entry import StringEntry


class ProjectService:
    """Handles saving and loading of project files."""

    def save_project(self, file_path, string_data):
        """
        Saves the current state of string data to an XML project file.

        Args:
            file_path (str): The path to save the project file.
            string_data (list): A list of StringEntry objects.
        """
        try:
            root = ET.Element(
                "ClassEditorProject", version="1.0", created=str(int(time.time()))
            )

            # --- Project Info --- #
            project_info = ET.SubElement(root, "ProjectInfo")
            ET.SubElement(project_info, "TotalEntries").text = str(len(string_data))

            # File statistics
            if string_data:
                file_types = [entry.file_type for entry in string_data]
                stats = Counter(file_types)
                file_stats_elem = ET.SubElement(project_info, "FileStats")
                for f_type, count in stats.items():
                    ET.SubElement(file_stats_elem, "File", type=f_type).text = str(
                        count
                    )

            # --- String Entries --- #
            entries_elem = ET.SubElement(root, "StringEntries")
            for entry in string_data:
                entry_elem = ET.SubElement(entries_elem, "Entry", id=str(entry.id))
                ET.SubElement(entry_elem, "Original").text = entry.original
                ET.SubElement(entry_elem, "Translated").text = entry.translated
                ET.SubElement(entry_elem, "FileName").text = entry.file_name
                ET.SubElement(entry_elem, "LineNumber").text = str(entry.line_number)
                ET.SubElement(entry_elem, "FileType").text = entry.file_type

            # Pretty print XML
            rough_string = ET.tostring(root, "utf-8")
            reparsed = minidom.parseString(rough_string)
            pretty_xml = reparsed.toprettyxml(indent="  ", encoding="utf-8")

            with open(file_path, "wb") as f:
                f.write(pretty_xml)

            logging.info(f"Project successfully saved to {file_path}")
            return True, f"工程已成功保存到 {file_path}"
        except Exception as e:
            logging.error(f"Failed to save project: {e}")
            return False, f"工程保存失败: {e}"

    def load_project(self, file_path):
        """
        Loads string data from an XML project file.

        Args:
            file_path (str): The path to the project file.

        Returns:
            tuple: A tuple containing (list_of_string_entries, project_metadata) or (None, None) on failure.
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            string_data = []
            for entry_elem in root.findall(".//StringEntries/Entry"):
                entry = StringEntry(
                    id=int(entry_elem.get("id")),
                    original=entry_elem.find("Original").text or "",
                    translated=entry_elem.find("Translated").text or "",
                    file_name=entry_elem.find("FileName").text or "",
                    line_number=int(entry_elem.find("LineNumber").text or 0),
                    file_type=entry_elem.find("FileType").text or "",
                )
                string_data.append(entry)

            # Extract metadata
            metadata = {
                "total_entries": root.find(".//TotalEntries").text,
                "created": root.get("created"),
                "version": root.get("version"),
                "stats": {
                    elem.get("type"): elem.text
                    for elem in root.findall(".//FileStats/File")
                },
            }

            logging.info(f"Project successfully loaded from {file_path}")
            return string_data, metadata
        except Exception as e:
            logging.error(f"Failed to load project: {e}")
            return None, None
