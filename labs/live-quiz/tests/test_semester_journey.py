"""Protect course scope, real links, escaping, launch policy and assessment separation."""
import json
import re
from pathlib import Path
import pytest
from app import app
import content as C
import semester_journey as J

@pytest.mark.parametrize('number', range(1,20))
def test_week_links_resolve_and_content_is_complete(number):
    with app.test_client() as client:
        response=client.get(f'/learn/software-security/journey/week/{number}')
        assert response.status_code == 200
        body=response.get_data(as_text=True)
        for href in re.findall(r'href="([^"]+)"',body):
            if href.startswith(('/learn/','/sim/','/static/')):
                assert client.get(href).status_code == 200, (number,href)
        assert 'connect-src \'none\'' in response.headers['Content-Security-Policy']
        assert 'Set-Cookie' not in response.headers
        assert 'data-checkpoint="defend"' in body
        assert len(J.week(number)['questions']) >= 2
        assert len(J.week(number)['foundation']) > 150
        assert len(J.week(number)['advanced']) > 150

@pytest.mark.parametrize('path', ['/learn/unknown/journey','/learn/unknown/journey/week/1',
    '/learn/software-security/journey/week/0','/learn/software-security/journey/week/20'])
def test_out_of_scope_is_404(path):
    with app.test_client() as client: assert client.get(path).status_code == 404

def test_not_a_submission_api():
    with app.test_client() as client:
        assert client.post('/learn/software-security/journey/week/1',json={'grade':100}).status_code == 405

def test_question_answers_are_valid_and_no_graded_banks_loaded():
    for week in J.WEEKS:
        for question in week['questions']:
            assert 0 <= question['answer'] < len(question['options'])
            assert question['why']
        assert all(n < week['number'] for n in week['prerequisites'])
    assert len(J.WEEKS) == 19
    assert 'quizzes/weekly' not in Path(J.__file__).read_text()

@pytest.mark.parametrize('value', ['javascript:alert(1)','http://lab.test','https://user:pass@lab.test',
    '//lab.test','https://lab.test:bad','https://lab.test/\nfoo','https://lab.test\\@evil.test'])
def test_launch_rejects_unsafe_urls(monkeypatch,value):
    monkeypatch.setenv('SEMESTER_WEEK10_VULNERABLE_URL',value)
    assert J.lab_url(10,'vulnerable') is None

def test_launch_accepts_private_https_and_never_invents_target(monkeypatch):
    monkeypatch.setenv('SEMESTER_WEEK10_VULNERABLE_URL','https://api.team1.labs.test:9443')
    assert J.lab_url(10,'vulnerable') == 'https://api.team1.labs.test:9443'
    monkeypatch.delenv('SEMESTER_WEEK10_DEFENDED_URL',raising=False)
    assert J.lab_url(10,'defended') is None
    assert J.lab_url(11,'vulnerable') is None

def test_content_remains_escaped(monkeypatch):
    original=J.week
    def hostile(n):
        w=original(n);w['foundation']='<script>alert(1)</script>';return w
    monkeypatch.setattr(J,'week',hostile)
    with app.test_client() as client:
        body=client.get('/learn/software-security/journey/week/10').get_data(as_text=True)
        assert '<script>alert(1)</script>' not in body
        assert '&lt;script&gt;alert(1)&lt;/script&gt;' in body

def test_course_content_does_not_claim_mock_is_final():
    assert 'differs' in J.week(17)['core']
    assert 'deterministic mock' in J.week(14)['core']
    assert 'not real authentication' in J.week(10)['core']
