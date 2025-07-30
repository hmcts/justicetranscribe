from backend.utils.markdown import html_to_markdown, markdown_to_html


def test_markdown_to_html_basic():
    """Test basic markdown to HTML conversion"""
    markdown_text = "**Hello** _world_"
    expected_html = "<p><strong>Hello</strong> <em>world</em></p>"
    assert markdown_to_html(markdown_text) == expected_html


def test_markdown_to_html_strip_option():
    """Test strip parameter in markdown_to_html"""
    markdown_text = "# Header"
    expected_html = "<h1>Header</h1>"
    assert markdown_to_html(markdown_text, strip=True) == expected_html
    assert markdown_to_html(markdown_text, strip=False).strip() == expected_html


def test_html_to_markdown_basic():
    """Test basic HTML to markdown conversion"""
    html_text = "<p><strong>Hello</strong> <em>world</em></p>"
    expected_markdown = "**Hello** _world_"
    assert html_to_markdown(html_text).strip() == expected_markdown


def test_roundtrip_conversion():
    """Test markdown -> HTML -> markdown conversion maintains meaning"""
    original_markdown = """
# Header

* List item 1
* List item 2

**Bold** and _italic_ text
"""
    html = markdown_to_html(original_markdown)
    result_markdown = html_to_markdown(html)

    # Convert both to HTML for comparison (since markdown can have different valid representations)
    assert markdown_to_html(result_markdown) == markdown_to_html(original_markdown)


def test_edge_cases():
    """Test edge cases and empty inputs"""
    assert markdown_to_html("") == ""
    assert html_to_markdown("") == ""
    assert markdown_to_html(" ") == ""
    assert html_to_markdown(" ").strip() == ""


def test_markdown_to_html_newlines():
    """Test how markdown newlines are converted to HTML"""
    markdown_text = """First line
Second line

Third line after blank line"""

    expected_html = "<p>First line\nSecond line</p>\n<p>Third line after blank line</p>"
    result = markdown_to_html(markdown_text)
    assert result == expected_html


def test_unordered_lists():
    """Test conversion of unordered lists"""
    markdown_text = """
* First item
* Second item
  * Nested item
  * Another nested item
* Third item
"""
    expected_html = """<ul>
<li>First item</li>
<li>Second item
<ul>
<li>Nested item</li>
<li>Another nested item</li>
</ul>
</li>
<li>Third item</li>
</ul>"""
    result = markdown_to_html(markdown_text.strip())
    assert result.strip() == expected_html.strip()


# def test_ordered_lists():
#     """Test conversion of ordered lists"""
#     markdown_text = """
# 1. First item
# 2. Second item
#    1. Nested item
#    2. Another nested item
# 3. Third item
# """
#     expected_html = """<ol>
# <li>First item</li>
# <li>Second item</li>
# <li>
# <ol>
# <li>Nested item</li>
# <li>Another nested item</li>
# </ol>
# </li>
# <li>Third item</li>
# </ol>"""
#     assert markdown_to_html(markdown_text.strip()).strip() == expected_html.strip()


# def test_mixed_lists():
#     """Test conversion of mixed ordered and unordered lists"""
#     markdown_text = """
# * Unordered item
#   1. Nested ordered item
#   2. Second nested ordered item
# * Another unordered item
# """
#     expected_html = """<ul>
# <li>Unordered item
# 1. Nested ordered item
# 2. Second nested ordered item</li>
# <li>Another unordered item</li>
# </ul>"""
#     assert markdown_to_html(markdown_text.strip()).strip() == expected_html.strip()
