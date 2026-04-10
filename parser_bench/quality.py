"""
Quality test functions for evaluating parser output.

Used by the hard benchmark suite to test reading order,
numeric extraction, table structure, watermark handling,
and column separation.
"""


def test_reading_order(text, ordered_phrases):
    """Test if phrases appear in the expected order.

    Returns (ordered_count, total_pairs, swapped_details).
    """
    positions = []
    for phrase in ordered_phrases:
        idx = text.lower().find(phrase.lower())
        positions.append((phrase, idx))

    ordered = 0
    total = 0
    details = []
    for i in range(len(positions) - 1):
        if positions[i][1] >= 0 and positions[i + 1][1] >= 0:
            total += 1
            if positions[i][1] < positions[i + 1][1]:
                ordered += 1
            else:
                details.append(f"'{positions[i][0]}' after '{positions[i + 1][0]}'")
    return ordered, total, details


def test_numeric_extraction(text, expected_numbers):
    """Test if specific numeric values appear verbatim.

    Returns (found_count, total, missing_list).
    """
    found = 0
    missing = []
    for num in expected_numbers:
        if num in text:
            found += 1
        else:
            missing.append(num)
    return found, len(expected_numbers), missing


def test_table_structure(text, expected_rows):
    """Test if table rows appear with all values on the same line.

    Returns (found_count, total, missing_rows).
    """
    found = 0
    missing = []
    for row_values in expected_rows:
        for line in text.split("\n"):
            if all(v.lower() in line.lower() for v in row_values):
                found += 1
                break
        else:
            missing.append(row_values)
    return found, len(expected_rows), missing


def test_watermark_separation(text, content_phrases, watermark_phrases):
    """Check if content is present and watermark text is interleaved.

    Returns (content_found, content_total, watermark_found, interleaved_count).
    Interleaved watermark lines between content lines is penalized.
    """
    content_found = sum(1 for p in content_phrases if p.lower() in text.lower())
    watermark_found = sum(1 for p in watermark_phrases if p.lower() in text.lower())

    lines = text.split("\n")
    content_line_indices = []
    watermark_line_indices = []
    for li, line in enumerate(lines):
        if any(p.lower() in line.lower() for p in content_phrases[:3]):
            content_line_indices.append(li)
        if any(p.lower() in line.lower() for p in watermark_phrases):
            watermark_line_indices.append(li)

    interleaved = 0
    for wi in watermark_line_indices:
        if content_line_indices and min(content_line_indices) < wi < max(content_line_indices):
            interleaved += 1

    return content_found, len(content_phrases), watermark_found, interleaved


def test_column_separation(text, left_col_phrases, right_col_phrases):
    """Test if two-column text is read column-by-column vs line-by-line.

    Good: all left column phrases appear before right column phrases.
    Bad: left and right phrases are interleaved.

    Returns (correct_pairs, total_pairs, status_str).
    """
    left_positions = [(p, text.lower().find(p.lower())) for p in left_col_phrases]
    right_positions = [(p, text.lower().find(p.lower())) for p in right_col_phrases]

    left_found = [p for p in left_positions if p[1] >= 0]
    right_found = [p for p in right_positions if p[1] >= 0]

    if not left_found or not right_found:
        return 0, 0, "insufficient matches"

    max_left = max(p[1] for p in left_found)
    min_right = min(p[1] for p in right_found)
    columns_separate = max_left < min_right

    interleaved = 0
    total_pairs = 0
    for _, li in left_found:
        for _, ri in right_found:
            if li >= 0 and ri >= 0:
                total_pairs += 1
                if li > ri:
                    interleaved += 1

    return total_pairs - interleaved, total_pairs, "separate" if columns_separate else "interleaved"
