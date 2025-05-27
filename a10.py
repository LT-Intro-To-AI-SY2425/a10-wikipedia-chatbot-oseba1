import re, string
from wikipedia import WikipediaPage
import wikipedia
from bs4 import BeautifulSoup
from typing import List, Callable, Tuple, Any, Match
from match import match

def get_page_html(title: str) -> str:
    results = wikipedia.search(title)
    return WikipediaPage(results[0]).html()

def get_first_infobox_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")
    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text

def clean_text(text: str) -> str:
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines

def get_match(text: str, pattern: str, error_text: str = "Page doesn't appear to have the property you're expecting") -> Match:
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)
    if not match:
        raise AttributeError(error_text)
    return match

def get_polar_radius(planet_name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Polar radius.*?)(?: ?[\d]+ )?(?P<radius>[\d,.]+)(?:.*?)km"
    error_text = "Page infobox has no polar radius information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("radius")

def get_birth_date(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = "Page infobox has no birth information (at least none in xxxx-xx-xx format)"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("birth")

def get_country_capital(country_name: str) -> str:
    try:
        infobox_text = clean_text(get_first_infobox_text(get_page_html(country_name)))
    except Exception as e:
        raise AttributeError(f"Could not retrieve page or infobox for {country_name}: {e}")
    pattern = r"Capital\s*(?:\[\d+\])?\s*(?P<capital>[A-Za-z\s,\(\)\-]+)"
    match = get_match(infobox_text, pattern, "Page infobox has no capital city information")
    return match.group("capital").strip()

def get_country_population(country_name: str) -> str:
    try:
        infobox_text = clean_text(get_first_infobox_text(get_page_html(country_name)))
    except Exception as e:
        raise AttributeError(f"Could not retrieve page or infobox for {country_name}: {e}")
    pattern = r"Population(?:\s*\([^)]*\))?\s*(?:\[\d+\])?.*?(?P<population>\d{1,3}(?:,\d{3})+)"
    match = get_match(infobox_text, pattern, "Page infobox has no population information")
    return match.group("population").replace(",", "")

def get_country_languages(country_name: str) -> List[str]:
    try:
        infobox_text = clean_text(get_first_infobox_text(get_page_html(country_name)))
    except Exception as e:
        raise AttributeError(f"Could not retrieve page or infobox for {country_name}: {e}")
    pattern = r"Official languages?\s*(?:\[\d+\])?\s*(?P<languages>[A-Za-z,\s\(\)\-]+)"
    match = get_match(infobox_text, pattern, "Page infobox has no official language information")
    languages_raw = match.group("languages")
    languages_list = re.split(r",\s*|\s+and\s+", languages_raw)
    return [lang.strip() for lang in languages_list if lang.strip()]

def birth_date(matches: List[str]) -> List[str]:
    return [get_birth_date(" ".join(matches))]

def polar_radius(matches: List[str]) -> List[str]:
    return [get_polar_radius(matches[0])]

def country_capital(matches: List[str]) -> List[str]:
    try:
        capital = get_country_capital(" ".join(matches))
        return [f"The capital of {matches[0]} is {capital}"]
    except AttributeError as e:
        return [f"Could not find capital: {e}"]

def country_population(matches: List[str]) -> List[str]:
    try:
        pop = get_country_population(" ".join(matches))
        return [f"The population of {matches[0]} is {pop}"]
    except AttributeError as e:
        return [f"Could not find population: {e}"]

def country_languages(matches: List[str]) -> List[str]:
    try:
        languages = get_country_languages(" ".join(matches))
        return [f"The official language(s) of {matches[0]}: {', '.join(languages)}"]
    except AttributeError as e:
        return [f"Could not find language info: {e}"]

def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt

Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

pa_list: List[Tuple[Pattern, Action]] = [
    ("when was % born".split(), birth_date),
    ("what is %'s birth date".split(), birth_date),
    ("what is the polar radius of %".split(), polar_radius),
    ("how big is %".split(), polar_radius),
    ("what is the capital of %".split(), country_capital),
    ("how many people live in %".split(), country_population),
    ("what language is spoken in %".split(), country_languages),
    ("what are the official languages of %".split(), country_languages),
    (["bye"], bye_action)
]

#what is the capital of tanzania
#how many people live in mexico
#what language is spoken in germany
def search_pa_list(src: List[str]) -> List[str]:
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            answer = act(mat)
            return answer if answer else ["No answers"]
    return ["I don't understand"]

def query_loop() -> None:
    while True:
        try:
            print()
            query = input("Your query? ").replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)
        except (KeyboardInterrupt, EOFError):
            break
    print("\nSo long!\n")

query_loop()
