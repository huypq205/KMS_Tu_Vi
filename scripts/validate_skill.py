#!/usr/bin/env python3
"""Validate KMS skills and repo-local references offline (T10).

Inspired by Duan Digi's MIT validate_skill.py at commit 91f8a06 (see skill LICENSE).
KMS differences: duplicate YAML keys fail, <500 lines is mandatory, linked
references are checked recursively, and links may target existing KMS repo docs.
"""
from __future__ import annotations
import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlsplit
import yaml

ROOT=Path(__file__).resolve().parents[1]
NAME=re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
LINK=re.compile(r'\[[^\]]*\]\(([^)]+)\)')


def _anchors(path):
    result=set();counts={}
    for heading in re.findall(r'^#{1,6}\s+(.+?)\s*#*$',path.read_text(encoding='utf-8-sig'),re.M):
        slug=''.join(c for c in unicodedata.normalize('NFC',heading.lower())
                     if c.isalnum() or c in (' ','-','_')).replace(' ','-')
        number=counts.get(slug,0);counts[slug]=number+1
        result.add(slug+(f'-{number}' if number else ''))
    return result


class UniqueLoader(yaml.SafeLoader):
    pass


def _unique_mapping(loader,node):
    pairs=loader.construct_pairs(node,deep=True)
    data={}
    for key,value in pairs:
        if not isinstance(key,str) or key in data:
            raise ValueError('YAML keys must be distinct strings.')
        data[key]=value
    return data


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,_unique_mapping)


def validate_skill(skill_path:Path, *, repo_root:Path=ROOT) -> list[str]:
    skill=Path(skill_path).resolve();scope=Path(repo_root).resolve()
    errors=[]
    if not skill.is_relative_to(scope): return ['Skill path is outside repo root.']
    path=skill/'SKILL.md'
    if not path.is_file(): return ['SKILL.md is missing.']
    try:
        content=path.read_text(encoding='utf-8-sig')
        match=re.match(r'\A---\n(.*?)\n---(?:\n|$)',content,re.S)
        if not match: return ['Missing or malformed YAML frontmatter.']
        metadata=yaml.load(match[1],Loader=UniqueLoader)
    except (OSError,UnicodeError,yaml.YAMLError,ValueError) as exc:
        return ['Invalid frontmatter: '+str(exc)]
    if not isinstance(metadata,dict): return ['Frontmatter must be a map.']
    name=metadata.get('name')
    if (not isinstance(name,str) or not 1<=len(name)<=64 or not NAME.fullmatch(name)
            or name!=skill.name): errors.append('name must be hyphen-case and match its folder (1–64 characters).')
    description=metadata.get('description')
    if not isinstance(description,str) or not description.strip() or len(description)>1024:
        errors.append('description must be a nonempty string of at most 1024 characters.')
    if len(content.splitlines())>=500: errors.append('SKILL.md must contain fewer than 500 lines.')
    if not content[match.end():].strip(): errors.append('Skill body is empty.')
    if re.search(r'\[TODO:',content): errors.append('Unfinished skill scaffold.')
    pending=[path];seen=set()
    while pending:
        current=pending.pop()
        if current in seen: continue
        seen.add(current)
        try: markdown=current.read_text(encoding='utf-8-sig')
        except (OSError,UnicodeError) as exc:
            errors.append(str(exc));continue
        markdown=re.sub(r'^```.*?^```[^\n]*$', '',markdown,flags=re.M|re.S)
        for target in LINK.findall(markdown):
            target=target.strip().strip('<>')
            try: parsed=urlsplit(target)
            except ValueError:
                errors.append('Malformed link: '+target);continue
            if parsed.scheme in ('http','https') and parsed.netloc: continue
            if parsed.scheme=='mailto' and parsed.path: continue
            if parsed.scheme or parsed.netloc or target.startswith(('/', '\\')):
                errors.append('Absolute/unsupported link: '+target);continue
            relative=unquote(parsed.path)
            linked=(current.parent/relative).resolve() if relative else current
            if not linked.is_relative_to(scope): errors.append('Link escapes repository: '+target)
            elif not linked.is_file(): errors.append('Broken local link: '+target)
            elif linked.suffix.lower()=='.md':
                try:
                    if parsed.fragment and unquote(parsed.fragment) not in _anchors(linked):
                        errors.append('Broken local anchor: '+target)
                    if linked.is_relative_to(skill): pending.append(linked)
                except (OSError,UnicodeError) as exc: errors.append(str(exc))
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('skill',nargs='?',type=Path,default=ROOT/'skills/tu-vi-kms')
    parser.add_argument('--repo-root',type=Path,default=ROOT)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    errors=validate_skill(args.skill,repo_root=args.repo_root)
    if args.json: print(json.dumps({'passed':not errors,'errors':errors},ensure_ascii=False))
    else:
        for error in errors: print('ERROR: '+error)
        print('FAILED' if errors else 'PASSED: skill frontmatter, name, length and local references.')
    return 1 if errors else 0


if __name__=='__main__': raise SystemExit(main())
