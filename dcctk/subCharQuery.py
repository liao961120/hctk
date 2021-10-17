from typing import Sequence
from CompoTree import ComponentTree, Radicals, CharLexicon, IDC
from CompoTree import CTFounds
from hanziPhon import Moe
from .UtilsConcord import match_mode

ctree = ComponentTree.load()
radicals = Radicals.load()
match_cache = dict()
radical_map = None
phon_map = None


def char_match_compo(char:str, tk:dict, lexicon:CharLexicon, hash):
    key = (char, str(tk), hash)
    if key in match_cache:
        return match_cache[key]
    match_cache[key] = False
    if char in find_compo(tk, lexicon, hash):
        match_cache[key] = True
    return match_cache[key]
    

def find_compo(tk:dict, lexicon:CharLexicon, hash):
    """Search hanzi by sub-character features (component, radical, sound) 
    """
    global radical_map, phon_map

    if 'phon' in tk['match']:
        return phonetic_search(tk, lexicon)
    elif 'radical' in tk['match']:
        return radical_search(tk, lexicon)
    elif 'compo' in tk['match']:
        return component_search(tk, lexicon)
    else:
        raise Exception('Invalid CQL attributes.')
    

# Sub-character search functions
def phonetic_search(tk, lexicon):
    """Search hanzi with phonetic representations

        .. code-block:: python

            {
                'match': {
                    'phon': ['ㄅㄨ'],
                    'tone': ['1'],
                    'tp': ['pinyin'],  # bpm, pinyin, ipa
                    'system': ['moe']
                },
                'not_match': {}
            }
    """
    build_phon_map(lexicon)
    sp = {
        'phon': '',
        'tone': None,
        'tp': "bpm",
        'system': 'moe'
    }
    for k, v in tk['match'].items():
        if k in sp: sp[k] = v[0]
    sys = phon_map.get(sp['system'])
    if sys is None: 
        raise Exception('Unsupported phonetic system')
    phon, mode = match_mode(sp['phon'])
    exact = mode == 'literal'
    return sys.find(repr=phon, tone=sp['tone'], tp=sp['tp'], exact=exact)


def radical_search(tk, lexicon):
    """Search hanzi with radical

    .. code-block:: python
        
        {
            'match': {
                'radical': ['人']
            },
            'not_match': {}
        }
    """
    build_radical_map(lexicon)
    rad = tk['match']['radical'][0]
    return radical_map.get(rad, set())


def component_search(tk, lexicon):
    """Search hanzi with character component

    .. code-block:: python
        
        {
            'match': {
                'compo': ['忄'],
                'idc': ['horz2'],
                'pos': ['0'],
                'max_depth': ['1']
            },
            'not_match': {}
        }
    """
    sp = {
        "compo": '',
        "max_depth": 1,
        'idc': None,  # IDC['horz2'].value,
        'pos': -1,
    }
    for k, v in tk['match'].items():
        if k in sp:
            v = v[0]
            if k in ['max_depth', 'pos']: v = int(v)
            if k == 'idc': v = IDC[v].value
            sp[k] = v
    
    bottom_hits = ctree.find(sp['compo'], max_depth=sp['max_depth'], bmp_only=True)
    if sp['idc'] is None:
        return set( x[0] for x in CTFounds(bottom_hits)\
            .filter_with_lexicon(lexicon)\
            .tolist() )

    return set( x[0] for x in CTFounds(bottom_hits)\
        .filter(idc=sp['idc'], pos=sp['pos'])\
        .filter_with_lexicon(lexicon)\
        .tolist() )


# Helper functions
def get_radicals(lexicon:CharLexicon):
    build_radical_map(lexicon)
    return set(radical_map.keys())


def build_radical_map(lexicon:CharLexicon):
    global radical_map
    if radical_map is None:
        print('Building index for character radicals...')
        radical_map = {}
        for char in lexicon.lexicon:
            rad = radicals.query(char)[0]
            radical_map.setdefault(rad, set()).add(char)


def build_phon_map(lexicon:CharLexicon):
    global phon_map
    if phon_map is None:
        phon_map = {}
        print('Building index for character phones...')
        phon_map['moe'] = Moe(lexicon=lexicon.lexicon)


def load_lexicon(lexicon: Sequence):
        lexicon = set(lexicon)
        return CharLexicon(lexicon, [], [])
