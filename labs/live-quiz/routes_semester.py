"""The full-semester companion to the established first-six-week mastery path."""
from flask import Blueprint, abort, render_template
import content as C
import semester_journey as J

bp = Blueprint('semester', __name__)
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
       "font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; connect-src 'none'")

@bp.after_request
def headers(response):
    response.headers['Content-Security-Policy'] = CSP
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response

def course(slug):
    if slug != 'software-security' or not C.course(slug):
        abort(404)
    return C.course(slug)

@bp.get('/learn/<course_slug>/journey')
def index(course_slug):
    return render_template('semester_index.html', course=course(course_slug), weeks=J.WEEKS)

@bp.get('/learn/<course_slug>/journey/week/<int:number>')
def week(course_slug, number):
    c = course(course_slug)
    w = J.week(number)
    if not w:
        abort(404)
    # Links reflect this deployment's actual public content registry.
    unit = next((u for u in C.list_weeks(course_slug) if u['slug'] == w['slug']), None)
    if unit is None:
        abort(404)
    resources = [{'label':C.kind_label(kind), 'href':f"/learn/{course_slug}/{w['slug']}/{kind}"}
                 for kind in unit['available']]
    sims = [{'label':C.SIMS[s], 'href':f'/sim/{s}'} for s in w['simulations'] if s in C.SIMS]
    return render_template('semester_week.html', course=c, week=w, resources=resources,
                           sims=sims, labs=[{'label':v.title(), 'href':J.lab_url(number,v)}
                           for v in ('vulnerable','defended')], weeks=J.WEEKS)
