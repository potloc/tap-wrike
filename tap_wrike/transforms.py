from singer import Transformer

class Transformer(Transformer):
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    def transform(self, record, schema, metadata=None):
        transforms = self.stream.get("transforms", [])
        for transform in transforms:
            transforms_map[transform["name"]](transform.get("config"), record, schema, metadata)

        return super().transform(record, schema, metadata)

def transform_decode_ids(config, record, schema, metadata=None):
    """
    Transform selected list of string ids to their integer counterpart
    """

    def base32_decode(string_value):
        """
        Decode a Wrike string ID to it's integer counterpart.
        Wrike uses the following format for their string IDs:
        - The first part of the ID contains the account ID - 8 characters (except for users)
        - Then the next 2 characters represent the entity type (e.g. 'KU' for users)
        - Finally, the last 6 characters correspond to the integer ID of the entity
          - This ID is base32 encoded using the following character set: A-Z 2-7 (in this order)
          - It seems like this ID is signed and therefore that the string ID is encoded using
            the two's complement binary representation of the integer ID
        """
        encoded_entity_id = string_value[-6:]
        num = 0
        for i, char in enumerate(reversed(encoded_entity_id)):
            digit = ord(char) - ord('A') if char >= 'A' else 26 + ord(char) - ord('2')
            num += digit * (32 ** i)

        # The number is stored in 30 bits: 32^6 = (2^5)^6 = 2^30
        # 2^30 is the largest number that can be represented in 30 bits
        # And everything above 2^29 is negative due to the two's complement representation
        return num if num < 2**29 else num - 2**30

    def apply_to_keymap(records, keymap):
        records = records if isinstance(records, list) else [records]
        string_key, keymap_value = keymap

        for record in records:
            if isinstance(keymap_value, dict): # Support deep nesting of properties
                for new_keymap in keymap_value.items():
                    apply_to_keymap(record[string_key], new_keymap)
            else:
                integer_key = keymap_value
                record[integer_key] = base32_decode(record[string_key])

    keymaps = config.get("keymaps", {})
    for keymap in keymaps.items():
        apply_to_keymap(record, keymap)

    return record

transforms_map = {
    "decode_ids": transform_decode_ids
}
