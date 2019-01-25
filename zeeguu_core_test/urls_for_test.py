import os

from zeeguu_core.model import Url

TESTDATA_FOLDER = os.path.join(os.path.dirname(__file__), "test_data")

onion_us_military = "https://www.theonion.com/u-s-military-announces-plan-to-consolidate-all-wars-in-1824018300"

vols_americans = "http://www.lemonde.fr/ameriques/article/2018/03/24/quand-les-vols-americains-se-transforment-en-arche-de-noe_5275773_3222.html"

fish_will_be_gone = "https://www.newscientist.com/" \
                    "article/2164774-in-30-years-asian-pacific-fish-will-be-gone-and-then-were-next/"

investing_in_index_funds = "https://www.propublica.org/article/" \
                           "warren-buffett-recommends-investing" \
                           "-in-index-funds-but-many-of-his-employees-do-not-have-that-option"

diesel_fahrverbote = \
    "http://www.spiegel.de/politik/deutschland/diesel-fahrverbote-schuld-sind-die-grenzwerte-kolumne-a-1197123.html"

spiegel_rss = "http://www.spiegel.de/index.rss"
spiegel_png = "http://www.spiegel.de/spiegel.png"

spiegel_venezuela = "http://www.spiegel.de/politik/ausland/venezuela-juan-guaido-und-sein-riskanter-konter-gegen-nicolas-maduro-a-1249613.html"

spiegel_militar = "http://www.spiegel.de/politik/ausland/venezuela-militaer-unterstuetzt-nicolas-maduro-im-machtkampf-gegen-juan-guaido-a-1249616.html"

formation_professionnelle = 'https://www.lemonde.fr/idees/article/2018/02/21/formation-le-big-bang-attendra_5260297_3232.html'

plane_crashes = 'https://edition.cnn.com/2018/03/12/asia/kathmandu-plane-crash/index.html'

test_urls = {

    vols_americans: 'vols_americans.html',
    onion_us_military: 'onion_us_military.html',
    fish_will_be_gone: 'fish_will_be_gone.html',
    investing_in_index_funds: 'investing_in_index_funds.html',
    spiegel_rss: 'spiegel.rss',
    spiegel_venezuela: 'spiegel_venezuela.html',
    spiegel_militar: 'spiegel_militar.html',
    diesel_fahrverbote: 'diesel_fahrverbote.html',
    formation_professionnelle: 'formation_professionnelle.html',
    plane_crashes: 'plane_crashes.html'

}


def mock_url(m, url):
    f = open(os.path.join(TESTDATA_FOLDER, test_urls[url]))
    content = (f.read())

    m.get(url, text=content)


def mock_urls(m):
    # Url.canonical_url_cache = {}
    for each in test_urls.keys():
        mock_url(m, each)
        # Url.canonical_url_cache[each] = each

