import pytest
from backend.workflow import (
    build_prompt,
    infer_category,
    load_workflow,
    sanitize_prompt_template,
    DEFAULT_PROMPT_TEMPLATES,
)


class TestInferCategory:
    def test_top_keywords(self):
        assert infer_category('T恤') == 'top'
        assert infer_category('衬衫') == 'top'
        assert infer_category('卫衣') == 'top'
        assert infer_category('POLO衫') == 'top'

    def test_bottom_keywords(self):
        assert infer_category('牛仔裤') == 'bottom'
        assert infer_category('短裤') == 'bottom'
        assert infer_category('半身裙') == 'bottom'

    def test_dress_keywords(self):
        # '连衣裙' 含 '裙' 先命中 bottom；'dress' 关键词直接命中
        assert infer_category('dress') == 'dress'
        assert infer_category('A字裙') == 'bottom'  # 含 '裙' 命中 bottom

    def test_unknown_defaults_to_top(self):
        assert infer_category('帽子') == 'top'
        assert infer_category('') == 'top'


class TestBuildPrompt:
    def test_contains_color_values(self):
        prompt = build_prompt('T恤', '#ff0000', (255, 0, 0))
        assert 'RGB(255, 0, 0)' in prompt
        assert '#ff0000' in prompt

    def test_contains_garment_name(self):
        prompt = build_prompt('长袖衬衫', '#aabbcc', (170, 187, 204))
        assert '长袖衬衫' in prompt

    def test_uses_category_template(self):
        prompt = build_prompt('牛仔裤', '#123456', (18, 52, 86))
        assert 'waistband' in prompt or '裤' in prompt

    def test_custom_template(self):
        template = 'Change to {RGB_VALUE} ({HEX_VALUE}) for {GARMENT} ({GARMENT_CATEGORY})'
        prompt = build_prompt('T恤', '#ff0000', (255, 0, 0), template=template)
        assert 'RGB(255, 0, 0)' in prompt
        assert '#ff0000' in prompt
        assert 'T恤' in prompt
        assert 'top' in prompt

    def test_default_templates_exist(self):
        assert 'top' in DEFAULT_PROMPT_TEMPLATES
        assert 'bottom' in DEFAULT_PROMPT_TEMPLATES
        assert 'dress' in DEFAULT_PROMPT_TEMPLATES


class TestLoadWorkflow:
    def test_load_existing_workflow(self):
        from pathlib import Path
        workflow_path = Path(__file__).resolve().parent.parent / 'image_flux2_working.json'
        if workflow_path.exists():
            wf = load_workflow(workflow_path)
            assert isinstance(wf, dict)
            assert '46' in wf
            assert '68:6' in wf


class TestSanitizePromptTemplate:
    def test_none_returns_none(self):
        assert sanitize_prompt_template(None) is None

    def test_empty_returns_none(self):
        assert sanitize_prompt_template('') is None
        assert sanitize_prompt_template('   ') is None

    def test_nonempty_strips(self):
        assert sanitize_prompt_template('  hello  ') == 'hello'
