import unittest
from unittest.mock import patch, MagicMock
from scraper import category

# Sample HTML snippets for mocking
MAIN_CAT_HTML = """
<html>
<body>
<a href="/produkter/kopglas/">Kopglas</a>
<a href="/produkter/assietter/">Assietter</a>
<a href="/produkter/nyheter/">Nyheter</a>
<a href="/produkter/kopglas/vinglas/">Vinglas</a>
<a href="/produkter/kopglas/whiskyglas/">Whiskyglas</a>
<a href="/produkter/assietter/dessert/">Dessert</a>
</body>
</html>
"""

SUB_CAT_HTML = """
<html>
<body>
<a href="/produkter/kopglas/vinglas/">Vinglas</a>
<a href="/produkter/kopglas/whiskyglas/">Whiskyglas</a>
</body>
</html>
"""

EMPTY_HTML = "<html><body></body></html>"

def mock_get_soup(url, timeout=20):
    # Return different soup depending on the URL
    if url.endswith("/produkter/"):
        return MagicMock(**{'find_all.return_value': [
            MagicMock(get_text=MagicMock(return_value="Kopglas"), get=MagicMock(return_value="/produkter/kopglas/")),
            MagicMock(get_text=MagicMock(return_value="Assietter"), get=MagicMock(return_value="/produkter/assietter/")),
            MagicMock(get_text=MagicMock(return_value="Nyheter"), get=MagicMock(return_value="/produkter/nyheter/")),
        ]})
    elif "kopglas" in url and url != "https://www.table.se/produkter/kopglas/whiskyglas/":
        return MagicMock(**{'find_all.return_value': [
            MagicMock(get_text=MagicMock(return_value="Vinglas"), get=MagicMock(return_value="/produkter/kopglas/vinglas/")),
            MagicMock(get_text=MagicMock(return_value="Whiskyglas"), get=MagicMock(return_value="/produkter/kopglas/whiskyglas/")),
        ]})
    else:
        return MagicMock(**{'find_all.return_value': []})

class CategoryExtractionTest(unittest.TestCase):
    @patch("scraper.category.get_soup", side_effect=mock_get_soup)
    @patch("scraper.category.is_excluded", return_value=False)
    def test_full_tree_no_exclusions(self, mock_excluded, mock_soup):
        tree = category.extract_category_tree()
        self.assertIsInstance(tree, list)
        self.assertEqual(len(tree), 2)  # Kopglas and Assietter, not Nyheter
        names = set(node['name'] for node in tree)
        self.assertIn("Kopglas", names)
        self.assertIn("Assietter", names)
        # Check subcategories exist
        kopglas = next(node for node in tree if node['name'] == "Kopglas")
        sub_names = set(sub['name'] for sub in kopglas['subs'])
        self.assertIn("Vinglas", sub_names)
        self.assertIn("Whiskyglas", sub_names)

    @patch("scraper.category.get_soup", side_effect=mock_get_soup)
    @patch("scraper.category.is_excluded", side_effect=lambda url: "whiskyglas" in url)
    def test_exclusion(self, mock_excluded, mock_soup):
        tree = category.extract_category_tree()
        kopglas = next(node for node in tree if node['name'] == "Kopglas")
        sub_names = set(sub['name'] for sub in kopglas['subs'])
        self.assertIn("Vinglas", sub_names)
        self.assertNotIn("Whiskyglas", sub_names)

    @patch("scraper.category.get_soup", return_value=None)
    @patch("scraper.category.is_excluded", return_value=False)
    def test_empty_html(self, mock_excluded, mock_soup):
        tree = category.extract_category_tree()
        self.assertEqual(tree, [])

if __name__ == "__main__":
    unittest.main()
