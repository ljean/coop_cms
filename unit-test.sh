cd coop_cms/ci/ci_project
python manage.py test coop_cms.tests
python manage.py test coop_cms.apps.email_auth.tests
python manage.py test coop_cms.apps.test_app.tests
