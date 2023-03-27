from decimal import ROUND_HALF_UP, Decimal


def calculate_rounded_total_price(
    *, unit_price: Decimal, amount: int, rounding=ROUND_HALF_UP
) -> Decimal:
    total = Decimal(str(unit_price)) * Decimal(str(amount))
    return total.quantize(Decimal(".01"), rounding=rounding)

def clean_hex(hex_value):
    if hex_value[:2] == "0x":
        return hex_value[2:]
    return hex_value

def hex_to_dec(hex_value):
    if len(hex_value) <= 2:
        return 0
    return int(clean_hex(hex_value), base=16)

def hex_to_text(hex_value):
    return bytes.fromhex(clean_hex(hex_value)).decode('utf-8')

def hex_remove_zeros(hex_value):
    return hex(hex_to_dec(hex_value))

def hex_to_metamask(hex_value):
    raw_hex = hex_remove_zeros(hex_value)
    if len(raw_hex) < 42:
        raw_hex = '0x' + '0' * (42 - len(raw_hex)) + raw_hex[2:]
    return raw_hex
