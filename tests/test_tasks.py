import pytest
from backend.tasks import (
    hex_to_rgb,
    parse_colors_file,
    parse_colors_file_bytes,
    _parse_colors_text,
    job_id_safe,
)


class TestHexToRgb:
    def test_red(self):
        assert hex_to_rgb('#ff0000') == (255, 0, 0)

    def test_without_hash(self):
        assert hex_to_rgb('00ff00') == (0, 255, 0)

    def test_white(self):
        assert hex_to_rgb('#ffffff') == (255, 255, 255)

    def test_black(self):
        assert hex_to_rgb('#000000') == (0, 0, 0)


class TestParseColorsText:
    def test_basic_parsing(self):
        text = 'GARMENT: T恤\nCOLORS\n红色: #ff0000\n蓝色: #0000ff'
        name, colors = _parse_colors_text(text)
        assert name == 'T恤'
        assert colors == [('红色', '#ff0000'), ('蓝色', '#0000ff')]

    def test_chinese_colon(self):
        text = 'COLORS\n绿色：#00ff00'
        _, colors = _parse_colors_text(text)
        assert colors == [('绿色', '#00ff00')]

    def test_no_garment_defaults(self):
        text = 'COLORS\n红色: #ff0000'
        name, _ = _parse_colors_text(text)
        assert name == 'garment'

    def test_no_colors_raises(self):
        with pytest.raises(ValueError):
            _parse_colors_text('GARMENT: T恤\n')

    def test_empty_lines_ignored(self):
        text = 'COLORS\n\n红色: #ff0000\n\n'
        _, colors = _parse_colors_text(text)
        assert len(colors) == 1

    def test_hex_case_normalized(self):
        text = 'COLORS\n红色: #FF0000'
        _, colors = _parse_colors_text(text)
        assert colors[0][1] == '#ff0000'

    def test_invalid_hex_length_skipped(self):
        text = 'COLORS\n坏的: #12\n好的: #aabbcc'
        _, colors = _parse_colors_text(text)
        assert len(colors) == 1
        assert colors[0] == ('好的', '#aabbcc')


class TestParseColorsFileBytes:
    def test_utf8_bom(self):
        data = 'GARMENT: 衬衫\nCOLORS\n白色: #ffffff'.encode('utf-8-sig')
        name, colors = parse_colors_file_bytes(data)
        assert name == '衬衫'
        assert colors == [('白色', '#ffffff')]

    def test_plain_utf8(self):
        data = 'COLORS\n黑色: #000000'.encode('utf-8')
        _, colors = parse_colors_file_bytes(data)
        assert colors == [('黑色', '#000000')]


class TestParseColorsFile:
    def test_from_file(self, tmp_path):
        p = tmp_path / 'colors.txt'
        p.write_text('GARMENT: 裤子\nCOLORS\n灰色: #888888', encoding='utf-8')
        name, colors = parse_colors_file(p)
        assert name == '裤子'
        assert colors == [('灰色', '#888888')]


class TestJobIdSafe:
    def test_alphanumeric(self):
        assert job_id_safe('abc123') == 'abc123'

    def test_special_chars_replaced(self):
        result = job_id_safe('a/b:c*d')
        assert '/' not in result
        assert ':' not in result
        assert '*' not in result

    def test_max_length(self):
        result = job_id_safe('a' * 100)
        assert len(result) <= 40

    def test_empty(self):
        result = job_id_safe('')
        assert result == ''
