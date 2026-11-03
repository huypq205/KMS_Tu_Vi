"""T10: validate useful structure and links, including negative inputs."""
import subprocess
import sys
from pathlib import Path
import pytest
from scripts.validate_skill import validate_skill

ROOT=Path(__file__).resolve().parents[1]


def make_skill(tmp_path,front='name: tu-vi-kms\ndescription: Tra cứu KMS',body='Dùng API KMS.'):
    skill=tmp_path/'skills'/'tu-vi-kms';skill.mkdir(parents=True)
    (skill/'SKILL.md').write_text('---\n'+front+'\n---\n'+body+'\n',encoding='utf-8')
    return skill


def test_repo_skill_and_cli():
    assert validate_skill(ROOT/'skills/tu-vi-kms',repo_root=ROOT)==[]
    run=subprocess.run([sys.executable,str(ROOT/'scripts/validate_skill.py')],capture_output=True,text=True,encoding='utf-8')
    assert run.returncode==0,run.stdout+run.stderr


@pytest.mark.parametrize('front',[
    'description: missing name','name: Wrong_Name\ndescription: X',
    'name: other\ndescription: X','name: tu-vi-kms\ndescription: ""',
    'name: tu-vi-kms\nname: tu-vi-kms\ndescription: X',
    'name: tu-vi-kms\ndescription: [wrong type]',
])
def test_invalid_frontmatter(tmp_path,front):
    skill=make_skill(tmp_path,front=front)
    assert validate_skill(skill,repo_root=tmp_path)


def test_strict_under_500_lines(tmp_path):
    skill=make_skill(tmp_path,body='\n'.join('Text' for _ in range(495)))
    assert len((skill/'SKILL.md').read_text().splitlines())==499
    assert validate_skill(skill,repo_root=tmp_path)==[]
    with (skill/'SKILL.md').open('a',encoding='utf-8') as out:out.write('Line500\n')
    assert any('500' in error for error in validate_skill(skill,repo_root=tmp_path))


def test_linked_references_checked_recursively_and_repo_docs_allowed(tmp_path):
    skill=make_skill(tmp_path,body='[reference](references/api.md) [docs](../../docs/gate.md)')
    (skill/'references').mkdir();(tmp_path/'docs').mkdir()
    (tmp_path/'docs/gate.md').write_text('Policy',encoding='utf-8')
    (skill/'references/api.md').write_text('[missing](missing.md)',encoding='utf-8')
    assert any('missing.md' in e for e in validate_skill(skill,repo_root=tmp_path))
    (skill/'references/missing.md').write_text('OK',encoding='utf-8')
    assert validate_skill(skill,repo_root=tmp_path)==[]


def test_path_escape_and_absolute_link_rejected(tmp_path):
    skill=make_skill(tmp_path,body='[escape](../../../outside.md) [absolute](C:/Windows/win.ini)')
    errors=validate_skill(skill,repo_root=tmp_path)
    assert len(errors)==2


def test_no_frontmatter_or_empty_body_is_invalid(tmp_path):
    skill=make_skill(tmp_path,body='')
    assert validate_skill(skill,repo_root=tmp_path)
    (skill/'SKILL.md').write_text('# No frontmatter',encoding='utf-8')
    assert validate_skill(skill,repo_root=tmp_path)


def test_broken_anchor_and_malformed_url_fail_without_crashing(tmp_path):
    skill=make_skill(tmp_path,body='## ASK\n[ok](#ask) [bad](#absent) [bad-url](https://[broken)')
    errors=validate_skill(skill,repo_root=tmp_path)
    assert len(errors)==2


def test_documented_modes_work_against_real_kms_contracts():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    from tests.horoscope_support import BIRTH
    client=TestClient(app)
    payload={**BIRTH,'provider':'mock','input_confidence':'C','target_year':2026}
    first=client.post('/api/v1/horoscope/read',json=payload)
    second=client.post('/api/v1/horoscope/read',json={**payload,'chi_gio':6})
    assert first.status_code==second.status_code==200
    a,b=first.json(),second.json()
    assert len(a['la_so']['thap_ni_cung'])==12
    assert a['la_so']!=b['la_so']
    assert a['meta']['is_mock'] and a['thong_tin_co_ban']['input_confidence']=='C'
    ask=client.post('/api/v1/horoscope/ask',json={**payload,'topic':'su_nghiep','question':'Cung Quan lộc có gì cần đối chiếu?'})
    assert ask.status_code==200 and ask.json()['fact_ids']
    assert 'C/D' in ask.json()['gioi_han']
    dossier=client.get('/api/v1/stars/vu%20khuc/dossier',params={'include_seeds':False})
    assert dossier.status_code==200 and dossier.json()['slots']['source_citations']['entries']
    annual=client.post('/api/v1/horoscope/annual',json=payload)
    assert annual.status_code==200
    assert annual.json()['annual_report']['bang_kich_hoat'][0]['luu_nguyet']['status']=='missing'
