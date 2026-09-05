import importlib.util
import json
from pathlib import Path
import re
import sys
import pytest
from app import app
import learner_store as L
import campus_bridge
import routes_campus

ROOT=Path(__file__).resolve().parents[3]


@pytest.fixture
def learner(tmp_path,monkeypatch):
    monkeypatch.setenv('LEARNER_DB_PATH',str(tmp_path/'learners.db'))
    monkeypatch.setenv('LEARNER_REQUIRE_VPN','1')
    return L.enroll('1234567890','Practice learner',1,'10.66.0.10','a-long-test-password')


def signed(client,learner):
    with client.session_transaction() as s:
        s['learner_id']=learner;s['csrf']='test-token'
        with app.app_context():s['learner_auth']=routes_campus.auth_tag(L.get(learner))
    return {'X-Campus-Peer':'10.66.0.10','X-CSRF-Token':'test-token'}


@pytest.mark.parametrize('week',range(1,20))
def test_all_rooms_have_sources_slides_and_mechanism(week):
    with app.test_client() as c:
        r=c.get(f'/campus/week/{week}')
        assert r.status_code==200
        body=r.get_data(as_text=True)
        assert len(re.findall(r'data-slide(?:\s|>)',body))==6
        assert 'data-flow' in body
        for path in re.findall('href="([^"]+)"',body):
            if path.startswith(('/sim/','/learn/','/static/')):
                assert c.get(path.split('#')[0]).status_code==200,path


def test_guest_cannot_use_broker():
    with app.test_client() as c:
        assert c.post('/campus/api/start',json={'lab':'threat'}).status_code==401
        assert c.get('/campus/dashboard').status_code==302


def test_other_peer_cannot_use_stolen_session(learner):
    with app.test_client() as c:
        h=signed(c,learner);h['X-Campus-Peer']='10.66.0.11'
        assert c.post('/campus/api/start',json={'lab':'threat'},headers=h).status_code==401


def test_login_is_separate_from_teacher_and_peer_bound(learner):
    with app.test_client() as c:
        c.get('/campus/login')
        with c.session_transaction() as s: token=s['csrf'];s['teacher_id']=1
        r=c.post('/campus/login',data={'student_id':'1234567890','password':'a-long-test-password','csrf_token':token},headers={'X-Campus-Peer':'10.66.0.11'})
        assert r.status_code==200
        r=c.post('/campus/login',data={'student_id':'1234567890','password':'a-long-test-password','csrf_token':token},headers={'X-Campus-Peer':'10.66.0.10'})
        assert r.status_code==302
        with c.session_transaction() as s:
            assert s['learner_id']==learner
            assert 'teacher_id' not in s
            assert s['csrf']!=token


def test_csrf_and_catalog_rejection_precede_broker(learner,monkeypatch):
    monkeypatch.setattr(campus_bridge,'call',lambda *a,**k:pytest.fail('broker must not run'))
    with app.test_client() as c:
        h=signed(c,learner)
        assert c.post('/campus/api/start',json={'lab':'threat'},headers={'X-Campus-Peer':'10.66.0.10'}).status_code==400
        assert c.post('/campus/api/start',json={'lab':'../../docker.sock'},headers=h).status_code==400
        assert c.post('/campus/api/guide',json={'question':'hello','week':True},headers=h).status_code==400
        assert c.post('/campus/api/guide',json={'question':'x'*1501,'week':1},headers=h).status_code==400


def test_broker_receives_only_current_slot(learner,monkeypatch):
    observed=[]
    def call(action,user,**fields):
        observed.append((action,user['slot'],fields));return {'state':'stopped'}
    monkeypatch.setattr(campus_bridge,'call',call)
    with app.test_client() as c:
        h=signed(c,learner)
        r=c.post('/campus/api/start',json={'lab':'threat','slot':3,'student_id':'other'},headers=h)
        assert r.status_code==200
        assert observed==[('start',1,{'lab':'threat'})]


def test_disabled_account_and_restart_limits(learner):
    assert L.admit('practice',1,3600)
    assert not L.admit('practice',1,3600)
    with L.connection() as db:db.execute('UPDATE learners SET active=0 WHERE id=?',(learner,))
    assert L.get(learner) is None


def test_progress_is_per_account_and_not_a_grade(learner):
    other=L.enroll('1234567891','Another learner',2,'10.66.0.11','another-long-password')
    with app.test_client() as c:
        h=signed(c,learner)
        r=c.post('/campus/api/progress',json={'week':10,'checkpoint':'practice','value':True,'learner_id':other},headers=h)
        assert r.status_code==200 and r.json['completed']==1
        assert L.progress(other)==[]
        assert c.post('/campus/api/progress',json={'week':20,'checkpoint':'grade','value':True},headers=h).status_code==400


def test_password_reset_invalidates_prior_session(learner):
    with app.test_client() as c:
        h=signed(c,learner)
        with L.connection() as db:db.execute('UPDATE learners SET password_hash=? WHERE id=?',(L.password_hash('new-long-secret-password'),learner))
        assert c.post('/campus/api/status',json={},headers=h).status_code==401


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'deploy/personal-labs'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_gateway_binds_every_target_to_one_real_peer(tmp_path):
    gen=module('personal_generator','generate.py')
    gen.generate({'team':1,'zone':'team1.labs.test','peers':{'1':'10.66.0.10','2':'10.66.0.11'}},tmp_path)
    text=(tmp_path/'Caddyfile').read_text()
    assert 'header_up X-Campus-Peer {remote_host}' in text
    assert text.count('@owner remote_ip')==2
    assert text.count('403')==2
    data=json.loads((tmp_path/'compose.override.json').read_text())
    for n,s in data['services'].items():
        if n.startswith('personal-'):
            assert s['read_only'] and s['cap_drop']==['ALL'] and 'ports' not in s
    with pytest.raises(ValueError):gen.generate({'team':1,'zone':'team1.labs.test','peers':{'1':'10.66.0.20'}},tmp_path)


def test_guide_sources_are_public_no_roster_or_grade_bank():
    guide=module('outsiders_guide','guide.py')
    sources=guide.context(ROOT,11)
    assert all(s['url'].startswith(('/campus','/learn/')) for s in sources)
    assert not any('instructor/' in s['url'] or 'quiz' in s['url'] for s in sources)
    assert 'ownership' in sources[0]['text']
    assert '6631503092' not in guide.clean_question('My ID is 6631503092')
    assert 'sk-examplekey123456789' not in guide.clean_question('sk-examplekey123456789')


def test_budget_survives_new_object_and_rejects_overspend(tmp_path):
    guide=module('outsiders_budget','guide.py');p=tmp_path/'budget.db'
    assert guide.Budget(p,monthly=.02,daily=.02).reserve(1)
    assert not guide.Budget(p,monthly=.02,daily=.02).reserve(2)


def test_model_html_is_not_interpreted_in_client():
    js=(ROOT/'labs/live-quiz/static/campus.js').read_text()
    assert '.innerHTML' not in js
    assert 'answer.textContent=' in js
    assert "credentials:'same-origin'" in js
