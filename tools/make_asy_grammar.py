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
    matched_words = set()

    asy_list_raw = input()

    operator_list = []

    print(json.dumps(base_grammar, indent=4))
    return

    for asydef in asy_list_raw.splitlines():
        pass

    for asy_def in asy_list_raw.split(';'):
        asy_def = asy_def.strip()
        if not asy_def:
            continue
        asy_type, asy_signature = asy_def.split(' ', 1)
        if '(' in asy_signature:
            if 'operator' in asy_signature:
                if 'init()' in asy_signature: # type
                    match_word = str.format('\\b({0})\\b', asy_type)
                    match_type = 'storage.type'
                elif 'cast(' not in asy_signature: # operator
                    operator_signature = asy_signature.split(' ', 1)[1]
                    operator_symbol = operator_signature.split('(')[0]
                    parsed_operator = []
                    for character in operator_symbol:
                        if character in {'|', '+', '*', '$', '.', '\\', '^'}:
                            parsed_operator.append('\\' + character)
                        else:
                            parsed_operator.append(character)
                    parsed_op_text = ''.join(parsed_operator)
                    if parsed_op_text.isalpha():
                        match_word = str.format('\\b({0})\\b', parsed_op_text)
                    else:
                        if parsed_op_text not in matched_words and ' ' not in parsed_op_text:
                            matched_words.add(parsed_op_text)
                            operator_list.append(parsed_op_text)
                        continue
                    match_type = 'keyword.operator'
            else: # function
                function_name = asy_signature.split('(')[0]
                match_word = str.format('\\b({0})\\b', function_name)
                match_type = 'support.function'
        else: # constant
            match_word = str.format('\\b({0})\\b', asy_signature)
            match_type = 'constant.language'
        if match_word not in matched_words:
            base_pattern.append({
            'match' : match_word,
            'name' : match_type
            })
            matched_words.add(match_word)

    base_pattern.append({
    'match': '|'.join(operator_list),
    'name' : 'keyword.operator'
    })

    base_grammar['patterns'] = base_pattern
    final_output = json.dumps(base_pattern, indent=4)

    print(final_output)

if __name__ == '__main__':
    sys.exit(main() or 0)
