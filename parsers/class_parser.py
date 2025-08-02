import struct
from .base_parser import BaseParser

# Java Class File Constants
CONSTANT_Utf8 = 1
CONSTANT_Integer = 3
CONSTANT_Float = 4
CONSTANT_Long = 5
CONSTANT_Double = 6
CONSTANT_Class = 7
CONSTANT_String = 8
CONSTANT_Fieldref = 9
CONSTANT_Methodref = 10
CONSTANT_InterfaceMethodref = 11
CONSTANT_NameAndType = 12
CONSTANT_MethodHandle = 15
CONSTANT_MethodType = 16
CONSTANT_InvokeDynamic = 18


class ClassParser(BaseParser):
    def __init__(self, filepath):
        with open(filepath, "rb") as f:
            self.data = bytearray(f.read())
        self.filepath = filepath
        self.constant_pool = []
        self.constant_pool_raw = []
        self.header = {}
        self.post_cp_data = b""
        self._parse()

    def _parse(self):
        self.header["magic"] = self.data[0:4]
        self.header["minor_version"] = struct.unpack(">H", self.data[4:6])[0]
        self.header["major_version"] = struct.unpack(">H", self.data[6:8])[0]
        self.header["constant_pool_count"] = struct.unpack(">H", self.data[8:10])[0]

        cp_count = self.header["constant_pool_count"]
        offset = 10

        i = 1
        while i < cp_count:
            tag = self.data[offset]
            entry_start_offset = offset
            offset += 1

            info = {"tag": tag, "index": i}
            is_long_or_double = False

            if tag == CONSTANT_Utf8:
                length = struct.unpack(">H", self.data[offset : offset + 2])[0]
                offset += 2
                try:
                    text = self.data[offset : offset + length].decode("utf-8")
                except UnicodeDecodeError:
                    text = self.data[offset : offset + length].decode(
                        "latin-1"
                    )  # Fallback
                info["length"] = length
                info["text"] = text
                offset += length
            elif tag in [CONSTANT_Integer, CONSTANT_Float]:
                offset += 4
            elif tag in [CONSTANT_Long, CONSTANT_Double]:
                offset += 8
                is_long_or_double = True
            elif tag == CONSTANT_Class:
                offset += 2
            elif tag == CONSTANT_String:
                offset += 2
            elif tag in [
                CONSTANT_Fieldref,
                CONSTANT_Methodref,
                CONSTANT_InterfaceMethodref,
                CONSTANT_NameAndType,
            ]:
                offset += 4
            elif tag in [CONSTANT_MethodHandle, CONSTANT_MethodType]:
                offset += 3
            elif tag == CONSTANT_InvokeDynamic:
                offset += 4
            else:
                if i == cp_count - 1 and len(self.constant_pool) == cp_count - 2:
                    break
                raise ValueError(
                    f"Unknown constant pool tag: {tag} at offset {offset - 1}"
                )

            entry_end_offset = offset
            self.constant_pool.append(info)
            self.constant_pool_raw.append(
                self.data[entry_start_offset:entry_end_offset]
            )

            if is_long_or_double:
                self.constant_pool.append(None)
                i += 2
            else:
                i += 1

        self.post_cp_data = self.data[offset:]

    def get_utf8_strings(self):
        strings = []
        for i, entry in enumerate(self.constant_pool):
            if entry and entry["tag"] == CONSTANT_Utf8:
                strings.append(
                    {
                        "id": entry["index"],
                        "original": entry["text"],
                        "translated": entry["text"],
                    }
                )
        return strings

    def update_utf8_string(self, index, new_string):
        entry = self.constant_pool[index - 1]
        if not entry or entry["tag"] != CONSTANT_Utf8:
            raise ValueError(
                f"Constant pool entry at index {index} is not a UTF-8 string."
            )

        try:
            new_bytes = new_string.encode("utf-8")
        except UnicodeEncodeError:
            new_bytes = new_string.encode("latin-1")

        new_len = len(new_bytes)

        new_raw_entry = bytearray()
        new_raw_entry.append(CONSTANT_Utf8)
        new_raw_entry.extend(struct.pack(">H", new_len))
        new_raw_entry.extend(new_bytes)

        self.constant_pool_raw[index - 1] = new_raw_entry
        entry["text"] = new_string
        entry["length"] = new_len

    def save(self, output_path):
        new_data = bytearray()
        new_data.extend(self.data[:10])

        for raw_entry in self.constant_pool_raw:
            new_data.extend(raw_entry)

        new_data.extend(self.post_cp_data)

        with open(output_path, "wb") as f:
            f.write(new_data)
