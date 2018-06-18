#!/usr/bin/env python3
# import cson
import json
import io
import sys
import re


def generate_base_pattern():
    return [
        { 
            'match': '\/\/.*$', 
            'name':'comment.line.double-slash' 
        },
        {
            'match' : '\\b(const|static|explicit|struct|typedef)\\b', 
            'name' : 'storage.modifier'
        },
        { 
            'begin' : '/\\*', 'end' : '\\*/', 
            'name' : 'comment.block' },
        {
            'match':'([:blank:]{1}?)("{1})(.*)("{1})',
            'name': 'string.quoted.double'
        },
        {
            'begin':'([^[:blank:]]{1}?)("{1})',
            'beginCaptures':
                {
                    '2': 'string.quoted.double'
                },
            'end':'("{1})',
            'endCaptures':
                {
                    '1': 'string.quoted.double'
                },
            'patterns': [ {'include': 'text.tex.latex'} ]
        },
        { 
            'match' : '\'.*?\'', 
            'name' : 'string.quoted.single' },
        { 
            'match' : '\\b(if|else|while|for|do|break|return|continue|unravel)\\b',
            'name' : 'keyword.control' },
        { 
            'match' :'\\b(new|operator)\\b', 
            'name' : 'keyword.operator' },
        { 
            'match' : '\\b(import|include|as|access|from)\\b',
            'name' : 'keyword.other' 
        },
        { 
            'match' : '\\b(\\d*)(\\.?)\\d+', 
            'name' : 'constant.numeric'
        }, 
        {
            # see https://regex101.com/r/IViUjM/1 for info
            
            'match': '\\b([a-zA-Z_]\\w*)\\s*\\(', 
            'captures': {
                '1': {
                    'name': 'entity.name.function'
                }
            }
        }
    ]

def main():
    base_grammar = {
        '$schema': 'https://raw.githubusercontent.com/martinring/tmlanguage/master/tmlanguage.json', 
        'scopeName': 'source.asymptote',
        'name': 'Asymptote'
    }

    # basic semantics not covered by asy -l

    base_pattern = generate_base_pattern()
    base_grammar['patterns'] = base_pattern

    asy_list_raw = sys.stdin.read()

    operator_list = set()
    const_list = set()
    type_list = set()

    # print(json.dumps(base_grammar, indent=4))

    for asydef in asy_list_raw.splitlines():
        if parse_constant(asydef) is not None:
            const_list.add(parse_constant(asydef))
        elif parse_type(asydef) is not None:
            type_list.add(parse_type(asydef))
        elif parse_operators(asydef) is not None:
            operator_list.add(parse_operators(asydef))

    print(const_list)
    print(type_list)
    print(operator_list)
    return 0



    base_pattern.append({
    'match': '|'.join(operator_list),
    'name' : 'keyword.operator'
    })

    base_grammar['patterns'] = base_pattern
    final_output = json.dumps(base_pattern, indent=4)

    print(final_output)

def parse_constant(line):
    # parse constant in <type><[]*> <kw>;
    # see https://regex101.com/r/dSExOo/3/ for format. 
    match_data = re.match(r"^[a-zA-Z_]\w*\s*(?:\[\]\s*)*\w*\s+([a-zA-Z_]\w*)\s*;$", line)
    if match_data is None:
        return None
    else:
        return match_data.group(1)

def parse_type(line):
    # See https://regex101.com/r/sf4Mj7/1 for format
    match_data = re.match(r"^([a-zA-Z_]\w*)\s*operator\s*init\s*\(\s*\)\s*;$", line)
    if match_data is None:
        return None
    else:
        return match_data.group(1)

def parse_operators(line):
    # See https://regex101.com/r/F9DUaQ/1 for format. 
    match_data = re.match(r"^(?:[a-zA-Z_]\w*)\s*operator\s*([\W]+)\(.*\);$", line)
    if match_data is None:
        return None
    else:
        return match_data.group(1)

if __name__ == '__main__':
    sys.exit(main() or 0)
