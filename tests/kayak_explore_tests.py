import unittest

def test_scrape_kayak(response, df):
    test = unittest.TestCase()
    test.assertTrue(response)
    test.assertFalse(df.empty)
    test.assertEqual(df.shape[1], 7)
    #test.assertEqual(type(df['Price']), int)

def test_wikipedia_page(soup):
    test = unittest.TestCase()
    text = soup.find('div', {'id':'mw-content-text'})
    test.assertIsNotNone(text)
    
def test_wiki_scraper(df):
    test = unittest.TestCase()
    characters = ['\[', '\]', '\(', '\)']
    test.assertFalse(df.empty)
    test.assertEqual(df.shape[1], 2)
    test.assertEqual(len(df['Continent'].unique()),6)
    
    for character in characters:
        char_search = df[df['Country'].str.match(character)]
        test.assertTrue(char_search.empty)
