"""Immersive course companion and separate personal learner workspace."""
import functools
import hashlib
import hmac
import ipaddress
import os
from flask import Blueprint, abort, current_app, jsonify, redirect, render_template, request, session
import auth
import content as C
import semester_journey as J
import learner_store as L
import campus_bridge

bp = Blueprint('campus', __name__)
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'")


@bp.before_request
def course_scope():
    if not C.course('software-security'):
        abort(404)


@bp.after_request
def headers(response):
    response.headers['Content-Security-Policy'] = CSP
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


def address():
    value = request.headers.get('X-Campus-Peer', '') if os.environ.get('LEARNER_REQUIRE_VPN') == '1' else request.remote_addr
    try:
        return str(ipaddress.IPv4Address(value))
    except (ValueError, TypeError):
        return ''


def current_learner():
    learner = L.get(session.get('learner_id')) if session.get('learner_id') else None
    if learner and os.environ.get('LEARNER_REQUIRE_VPN') == '1' and address() != learner['vpn_ip']:
        return None
    if learner and not hmac.compare_digest(session.get('learner_auth',''), auth_tag(learner)):
        return None
    return learner


def auth_tag(learner):
    return hmac.new(current_app.secret_key.encode(),learner['password_hash'].encode(),hashlib.sha256).hexdigest()


def learner_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not current_learner():
            if request.path.startswith('/campus/api/'):
                return jsonify(error='Sign in with your student account on your assigned VPN.'), 401
            return redirect('/campus/login')
        return view(*args, **kwargs)
    return wrapped


def csrf():
    token = request.headers.get('X-CSRF-Token') if request.is_json else request.form.get('csrf_token')
    if not auth.csrf_ok(session.get('csrf'), token):
        abort(400)


@bp.get('/campus')
def index():
    return render_template('campus_index.html', weeks=J.WEEKS, units=C.list_weeks('software-security'),
                           learner=current_learner(), csrf_token=current_app.config['ISSUE_CSRF']())


@bp.get('/campus/architecture')
def architecture():
    return render_template('campus_architecture.html')


@bp.get('/campus/week/<int:number>')
def week(number):
    w = J.week(number)
    if not w:
        abort(404)
    unit = next((u for u in C.list_weeks('software-security') if u['slug'] == w['slug']), None)
    if not unit:
        abort(404)
    import immersive_content as I
    return render_template('campus_week.html', week=w, extra=I.week(number), unit=unit,
                           learner=current_learner(), csrf_token=current_app.config['ISSUE_CSRF']())


@bp.route('/campus/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.content_length is None or request.content_length > 4096:
            abort(413)
        csrf()
        if not L.admit('login:' + address(), 8, 900):
            return render_template('campus_login.html', error='Too many attempts. Wait 15 minutes.',
                                   csrf_token=current_app.config['ISSUE_CSRF']()), 429
        learner = L.authenticate(request.form.get('student_id', '')[:32], request.form.get('password', '')[:129])
        if learner and (os.environ.get('LEARNER_REQUIRE_VPN') != '1' or learner['vpn_ip'] == address()):
            session.clear()
            session['learner_id'] = learner['id']
            session['learner_auth'] = auth_tag(learner)
            session['csrf'] = auth.new_csrf_token()
            return redirect('/campus/dashboard')
        error = 'Check your student ID, password and assigned VPN connection.'
    return render_template('campus_login.html', error=error, csrf_token=current_app.config['ISSUE_CSRF']())


@bp.post('/campus/logout')
def logout():
    csrf()
    session.clear()
    return redirect('/campus')


@bp.get('/campus/dashboard')
@learner_required
def dashboard():
    import immersive_content as I
    return render_template('campus_dashboard.html', learner=current_learner(), labs=I.LABS,
                           csrf_token=current_app.config['ISSUE_CSRF']())


@bp.post('/campus/api/<action>')
@learner_required
def api(action):
    csrf()
    if action not in ('start', 'stop', 'status', 'guide', 'progress'):
        abort(404)
    if request.content_length is None or request.content_length > 8000 or not request.is_json:
        abort(413)
    data = request.get_json()
    if not isinstance(data, dict):
        abort(400)
    learner = current_learner()
    limit, period = (8, 60) if action == 'guide' else (30, 60)
    if not L.admit(action + ':' + learner['id'], limit, period):
        return jsonify(error='Please pause briefly before another request.'), 429
    fields = {}
    if action == 'progress':
        try:
            rows = L.progress(learner['id'],data.get('week'),data.get('checkpoint'),data.get('value'))
            return jsonify(progress=rows,completed=sum(r['value'] for r in rows))
        except ValueError:
            abort(400)
    if action == 'guide':
        question = data.get('question')
        week = data.get('week', 1)
        if not isinstance(question, str) or not 3 <= len(question.strip()) <= 1500 or type(week) is not int or not 1 <= week <= 19:
            abort(400)
        fields = {'question': question.strip(), 'week': week}
    elif action == 'start':
        import immersive_content as I
        if not isinstance(data.get('lab'),str) or data['lab'] not in I.LABS:
            abort(400)
        fields = {'lab': data['lab']}
    try:
        from eventlet import tpool
        return jsonify(tpool.execute(campus_bridge.call, action, learner, **fields))
    except campus_bridge.BridgeUnavailable as error:
        return jsonify(error=str(error)), 503
