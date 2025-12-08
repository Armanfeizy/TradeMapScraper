import os
import re
from pathlib import Path
import csv


def parse(raw_text: str) -> list[list]:
    # Process header separately
    matrix = []

    header_line = raw_text.split("\n")[0]
    header_parts = [p.replace('"', '').strip() for p in header_line.split("\t")]
    # Remove trailing empty columns
    while header_parts and header_parts[-1] == "":
        header_parts.pop()
    max_cols = len(header_parts)

    # Build header row
    header_row = []
    for i, p in enumerate(header_parts):
        if i == 0:
            header_row.append("Country")
        else:
            match = re.search(r"\b\d{4}\b", p)
            header_row.append(match.group() if match else p)
    matrix.append(header_row)

    # Process remaining lines
    for line in raw_text.split("\n")[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        row = []

        for i in range(max_cols):
            if i < len(parts):
                p = parts[i].replace('"', '').strip()
                if i == 0:
                    row.append(p)
                else:
                    try:
                        row.append(int(p))
                    except:
                        row.append(-1)
            else:
                row.append(-1)  # missing column
        matrix.append(row)

    return matrix


def convert_txt_to_csv(txt_file: Path):
    relative_parts = txt_file.parts[txt_file.parts.index("out") + 1:]
    trade_flow = relative_parts[0]
    hs_code = relative_parts[1]
    unit_type = relative_parts[2]
    country_name = txt_file.stem

    results_dir = Path("results") / trade_flow / hs_code / unit_type
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_file = results_dir / f"{country_name}.csv"
    with open(txt_file, 'r', encoding='utf-8') as f_in, open(csv_file, 'w', encoding="utf-8", newline="") as f_out:
        raw_text = f_in.read()
        table = parse(raw_text)
        csv.writer(f_out).writerows(table)
    print(f"Converted: {txt_file.name} → {csv_file.name}")


if __name__ == '__main__':
    out_dir = Path("out")

    for txt_file in out_dir.rglob("*.txt"):  # recursive search
        convert_txt_to_csv(txt_file)

