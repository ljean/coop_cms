# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from bs4 import BeautifulSoup

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.template import Template, Context

from model_mommy import mommy
from coop_cms.models import BaseArticle, Fragment, FragmentType, FragmentFilter
from coop_cms.settings import get_article_class
from coop_cms.tests import BaseTestCase

class FragmentsTest(BaseTestCase):
    
    editable_field_tpl = '<div class="djaloha-editable" id="djaloha_djaloha__coop_cms__Fragment__id__{0}__content">' + \
        '{1}</div>\n<input type="hidden" id="djaloha_djaloha__coop_cms__Fragment__id__{0}__content_hidden" ' + \
        'name="djaloha__coop_cms__Fragment__id__{0}__content" value="{1}">'
    
    def setUp(self):
        super(FragmentsTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article_with_fragments.html', 'Article with fragments'),
            ('test/article_with_fragments_extra_id.html', 'Article with fragments extra id'),
            ('test/article_with_fragments_template.html', 'Article with fragments template'),
        )
        
    def tearDown(self):
        super(FragmentsTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates

    def test_fragment_position(self):
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        
        f1 = mommy.make(Fragment, type=ft1)
        f2 = mommy.make(Fragment, type=ft1)
        f3 = mommy.make(Fragment, type=ft1)
        f4 = mommy.make(Fragment, type=ft1)
        
        g1 = mommy.make(Fragment, type=ft2)
        g2 = mommy.make(Fragment, type=ft2)
        g3 = mommy.make(Fragment, type=ft2)
        
        f5 = mommy.make(Fragment, type=ft1)
        
        for idx, elt in enumerate([f1, f2, f3, f4, f5]):
            self.assertEqual(idx+1, elt.position)
        
        for idx, elt in enumerate([g1, g2, g3]):
            self.assertEqual(idx+1, elt.position)
            
    def test_fragment_position_extra_id(self):
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        ff1 = mommy.make(FragmentFilter)
        ff2 = mommy.make(FragmentFilter)
        
        f1 = mommy.make(Fragment, type=ft1, filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, filter=ff1)
        
        f4 = mommy.make(Fragment, type=ft1, filter=ff2)
        
        g1 = mommy.make(Fragment, type=ft2, filter=ff1)
        g2 = mommy.make(Fragment, type=ft2, filter=ff2)
        g3 = mommy.make(Fragment, type=ft2, filter=ff2)
        
        f5 = mommy.make(Fragment, type=ft1, filter=ff1)
        
        f6 = mommy.make(Fragment, type=ft1)
        f7 = mommy.make(Fragment, type=ft1)
        
        for idx, elt in enumerate([f1, f2, f3, f5]):
            self.assertEqual(idx+1, elt.position)
            
        for idx, elt in enumerate([f4]):
            self.assertEqual(idx+1, elt.position)
        
        for idx, elt in enumerate([g1]):
            self.assertEqual(idx+1, elt.position)
            
        for idx, elt in enumerate([g2, g3]):
            self.assertEqual(idx+1, elt.position)
            
        for idx, elt in enumerate([f6, f7]):
            self.assertEqual(idx+1, elt.position)
            
    def test_fragment_position_update(self):
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        
        f1 = mommy.make(Fragment, type=ft1)
        f2 = mommy.make(Fragment, type=ft1)
        f3 = mommy.make(Fragment, type=ft1)
        
        f1.save()
        f2.save()
        f3.save()
        
        for idx, elt in enumerate([f1, f2, f3]):
            self.assertEqual(idx+1, elt.position)
            
    def test_view_fragments(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2, f3]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def test_view_fragments_extra_id(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ff1 = mommy.make(FragmentFilter, extra_id="1")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name x %}')
        html = tpl.render(Context({"ft_name": ft_name, "x": 1}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        soup = BeautifulSoup(html)
        ft_tags = soup.select(".coop-fragment-type")
        self.assertEqual(len(ft_tags), 1)
        ft_tag = ft_tags[0]
        self.assertEqual(ft_tag['rel'], str(ft1.id))
        self.assertEqual(ft_tag['data-filter'], str(ff1.id))
        
        
        for f in [f3, f4]:
            self.assertTrue(html.find(f.content)<0)
        
    def test_fragments_with_extra_id(self):
        ft_name = u"contacts"
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name x %}')
        html = tpl.render(Context({"ft_name": ft_name, 'x': 2}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)

        self.assertEqual(FragmentFilter.objects.count(), 1)
        self.assertEqual(FragmentFilter.objects.filter(extra_id='2').count(), 1)
        
    def test_view_fragments_name_as_string(self):
        ft1 = mommy.make(FragmentType, name="contacts")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments "contacts" %}')
        html = tpl.render(Context({"ft_name": "contacts"}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2, f3]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def test_view_fragments_name_and_extra_id_as_string(self):
        ft1 = mommy.make(FragmentType, name="contacts")
        ff1 = mommy.make(FragmentFilter, extra_id="hello")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments "contacts" "hello" %}')
        html = tpl.render(Context({"ft_name": "contacts"}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f1, f2]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        for f in [f3, f4]:
            self.assertTrue(html.find(f.content)<0)
        
    def test_view_fragments_order(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", position=3)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", position=1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", position=2)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f2, f3, f1]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
    def test_view_only_specified_fragments(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f2, f3, f1]]
        for pos in positions:
            self.assertTrue(pos>=0)
        
        positions = [html.find('{0}'.format(f.content)) for f in [g1]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_view_only_specified_fragments_extra_id(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        ff1 = mommy.make(FragmentFilter, extra_id="hello")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT", filter=ff1)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name "hello" %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        positions = [html.find('{0}'.format(f.content)) for f in [f2, f1]]
        for pos in positions:
            self.assertTrue(pos>=0)
        
        positions = [html.find('{0}'.format(f.content)) for f in [g1, f3, f4]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_view_fragments_edit_mode(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty")
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh")
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn")
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name %}')
        html = tpl.render(Context({"ft_name": ft_name, "form": True}))
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [f1, f2, f3]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [g1]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_view_fragments_extra_id_edit_mode(self):
        ft_name = u"contacts"
        ft1 = mommy.make(FragmentType, name=ft_name)
        ft2 = mommy.make(FragmentType, name="AAAA")
        
        ff1 = mommy.make(FragmentFilter, extra_id="hello")
        ff2 = mommy.make(FragmentFilter, extra_id="2")
        
        f1 = mommy.make(Fragment, type=ft1, content="Azerty", filter=ff1)
        f2 = mommy.make(Fragment, type=ft1, content="Qsdfgh", filter=ff1)
        f3 = mommy.make(Fragment, type=ft1, content="Wxcvbn", filter=ff2)
        f4 = mommy.make(Fragment, type=ft1, content="Zsxdrg", filter=None)
        
        g1 = mommy.make(Fragment, type=ft2, content="POIUYT")
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name "hello" %}')
        html = tpl.render(Context({"ft_name": ft_name, "form": True}))
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [f1, f2]]
        for pos in positions:
            self.assertTrue(pos>=0)
        sorted_positions = positions[:]
        sorted_positions.sort()
        self.assertEqual(positions, sorted_positions)
        
        positions = [html.find(self.editable_field_tpl.format(f.id, f.content)) for f in [g1, f3, f4]]
        for pos in positions:
            self.assertTrue(pos==-1)
            
    def test_fragments_with_template(self):
        ft_name = u"contacts"
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name template_name="test/_fragment.html" %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)
        
        soup = BeautifulSoup(html)
        self.assertEqual(0, len(soup.select('.panel')))
        
    def test_view_fragments_with_template(self):
        ft_name = u"contacts"
        ft = mommy.make(FragmentType, name=ft_name)
        
        f = mommy.make(Fragment, type=ft)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name template_name="test/_fragment.html" %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)
        
        soup = BeautifulSoup(html)
        self.assertEqual(1, len(soup.select('.panel')))
        
    def test_view_fragments_with_template_edit_mode(self):
        ft_name = u"contacts"
        ft = mommy.make(FragmentType, name=ft_name)
        
        f = mommy.make(Fragment, type=ft)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name template_name="test/_fragment.html" %}')
        html = tpl.render(Context({"ft_name": ft_name, 'form': True}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)
        
        soup = BeautifulSoup(html)
        self.assertEqual(1, len(soup.select('.panel')))
        self.assertEqual(1, len(soup.select('.panel input')))
        self.assertEqual(1, len(soup.select('.panel .djaloha-editable')))
    
    def test_view_fragments_with_template2(self):
        ft_name = u"contacts"
        ft = mommy.make(FragmentType, name=ft_name)
        
        f = mommy.make(Fragment, type=ft)
        f = mommy.make(Fragment, type=ft)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name template_name="test/_fragment.html" %}')
        html = tpl.render(Context({"ft_name": ft_name}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)
        soup = BeautifulSoup(html)
        self.assertEqual(2, len(soup.select('.panel')))
        
    def test_view_fragments_with_template3(self):
        ft_name = u"contacts"
        ft = mommy.make(FragmentType, name=ft_name)
        
        f = mommy.make(Fragment, type=ft)
        f = mommy.make(Fragment, type=ft)
        
        tpl = Template('{% load coop_edition %}{% coop_fragments ft_name template_name="test/_fragment.html" %}')
        html = tpl.render(Context({"ft_name": ft_name, 'form': True}))
        
        self.assertEqual(FragmentType.objects.count(), 1)
        self.assertEqual(FragmentType.objects.filter(name=ft_name).count(), 1)
        soup = BeautifulSoup(html)
        self.assertEqual(3, len(soup.select('.panel'))) # 1 extra panel if_cms_edition and fragment index > 0
    
    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct1 = ContentType.objects.get_for_model(get_article_class())
        ct2 = ContentType.objects.get_for_model(Fragment)
        
        for ct in (ct1, ct2):
            
            perm = 'change_{0}'.format(ct.model)
            can_edit = Permission.objects.get(content_type=ct, codename=perm)
            user.user_permissions.add(can_edit)
            
            perm = 'add_{0}'.format(ct.model)
            can_add = Permission.objects.get(content_type=ct, codename=perm)
            user.user_permissions.add(can_add)
        
        user.is_active = True
        user.save()
        return self.client.login(username='toto', password='toto')
    
    def _log_as_regular_user(self):
        user = User.objects.create_user('titi', 'titi@toto.fr', 'titi')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        user.is_active = True
        user.save()
        return self.client.login(username='titi', password='titi')
        
    
    def _check_article(self, response, data):
        for (key, value) in data.items():
            self.assertContains(response, value)
    #        
    #def _check_article_not_changed(self, article, data, initial_data):
    #    article = get_article_class().objects.get(id=article.id)
    #
    #    for (key, value) in data.items():
    #        self.assertNotEquals(getattr(article, key), value)
    #        
    #    for (key, value) in initial_data.items():
    #        self.assertEquals(getattr(article, key), value)

    def test_view_article_no_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, FragmentType.objects.count())
        self.assertEqual("parts", FragmentType.objects.all()[0].name)
        
    def test_view_article_with_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop")
        
        response = self.client.get(article.get_absolute_url())
        
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.content)
        
    def test_view_article_with_fragments_extra_id(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[1][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        ff1 = mommy.make(FragmentFilter, extra_id=str(article.id))
        ff2 = mommy.make(FragmentFilter, extra_id="hello")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop", filter=ff1)
        f2 = mommy.make(Fragment, type=ft, content="QSDFGHJKLM", filter=ff2)
        f3 = mommy.make(Fragment, type=ft, content="Wxcvbn,;:=", filter=None)
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.content)
        self.assertNotContains(response, f2.content)
        self.assertNotContains(response, f3.content)
        
    def test_view_article_with_fragment_with_css(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop", css_class="this-is-my-fragment")
        
        response = self.client.get(article.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.content)
        
        soup = BeautifulSoup(response.content)
        fragment = soup.select("div."+f1.css_class)[0]
        self.assertEqual(f1.content, fragment.text)
        
    def test_edit_article_no_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        data = {"title": 'salut', 'content': 'bonjour!'}
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
        data = {"title": 'bye', 'content': 'au revoir'}
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self._check_article(response, data)
        
    def test_edit_article_with_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop")
        
        new_f1_content = u"Qsdfghjklm"
        data = {
            "title": 'salut',
            'content': 'bonjour!',
            'djaloha__coop_cms__Fragment__id__{0}__content'.format(f1.id): new_f1_content,
        }
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, data['title'])
        self.assertContains(response, data['content'])
        self.assertContains(response, new_f1_content)
        
    def test_edit_article_with_fragments_extra_id(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[1][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        ff = mommy.make(FragmentFilter, extra_id=str(article.id))
        f1 = mommy.make(Fragment, type=ft, content="Azertyuiop", filter=ff)
        
        new_f1_content = u"Qsdfghjklm"
        data = {
            "title": 'salut',
            'content': 'bonjour!',
            'djaloha__coop_cms__Fragment__id__{0}__content'.format(f1.id): new_f1_content,
        }
        
        self._log_as_editor()
        response = self.client.post(article.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, data['title'])
        self.assertContains(response, data['content'])
        self.assertContains(response, new_f1_content)
        
    def test_view_add_fragment(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
    def test_view_add_fragment_check_filters(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[1][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        #url = reverse("coop_cms_add_fragment")
        url = article.get_edit_url()
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        ft_tags = soup.select(".coop-fragment-type")
        ft_objs = FragmentType.objects.all()
        ff_objs = FragmentFilter.objects.all()
        
        self.assertEqual(len(ft_tags), 2)
        self.assertEqual(ft_objs.count(), 2)
        self.assertEqual(ff_objs.count(), 1)
        
        for i in range(2):
            self.assertEqual(int(ft_tags[i]["rel"]), ft_objs[i].id)
        
        self.assertEqual(ft_tags[0]["data-filter"], '')
        self.assertEqual(ft_tags[1]["data-filter"], str(ff_objs[0].id))
        
        
    def test_view_add_fragment_no_filter_check_filters(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        #url = reverse("coop_cms_add_fragment")
        url = article.get_edit_url()
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        
        ft_tags = soup.select(".coop-fragment-type")
        ft_objs = FragmentType.objects.all()
        ff_objs = FragmentFilter.objects.all()
        
        self.assertEqual(len(ft_tags), 1)
        self.assertEqual(ft_objs.count(), 1)
        self.assertEqual(ff_objs.count(), 0)
        
        self.assertEqual(int(ft_tags[0]["rel"]), ft_objs[0].id)
        
        self.assertEqual(ft_tags[0]["data-filter"], '')
        
    def test_view_add_fragment_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        
        self._log_as_regular_user()
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)
        
    def _add_fragment(self, data, errors_count=0):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        if errors_count:
            self.assertEqual(errors_count, len(errs))
        else:
            self.assertEqual([], errs)
            expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
            self.assertEqual(response.content, expected)
        
        return response        
        
    def test_add_fragment(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 0,
            'filter': '',
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')   
        self.assertEqual(f.position, 1)
        self.assertEqual(f.filter, None)

        
    def test_add_fragment_filter(self):
        ft = mommy.make(FragmentType, name="parts")
        ff = mommy.make(FragmentFilter, extra_id="2")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 0,
            'filter': ff.id
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')   
        self.assertEqual(f.position, 1)
        self.assertEqual(f.filter, ff)
        
    def test_add_fragment_position(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 2,
            'filter': '',
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')
        self.assertEqual(f.position, 2)
        
    def test_add_fragment_invalid_filter(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'position': 2,
            'filter': '0',
        }
        
        response = self._add_fragment(data, 1)
        self.assertEqual(0, Fragment.objects.count())
        
    def test_add_fragment_css(self):
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft.id,
            'name': 'abcd',
            'css_class': 'okidki',
            'position': 0,
        }
        
        response = self._add_fragment(data)
        f = Fragment.objects.all()[0]
        
        self.assertEqual(f.type, ft)
        self.assertEqual(f.name, data['name'])
        self.assertEqual(f.css_class, '')   
        self.assertEqual(f.position, 1)
            
    def test_view_add_fragment_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft = mommy.make(FragmentType, name="parts")
        data = {
            'type': ft,
            'name': 'abcd',
            'css_class': 'okidoki',
            'position': 0,
        }
        
        url = reverse("coop_cms_add_fragment")
        response = self.client.post(url, data=data, follow=False)
        self.assertEqual(302, response.status_code)
        next_url = "http://testserver/accounts/login/?next={0}".format(url)
        self.assertEqual(next_url, response['Location'])
        
        self._log_as_regular_user()
        response = self.client.post(url, data=data, follow=False)
        self.assertEqual(403, response.status_code)
        
        self.assertEqual(0, Fragment.objects.count())
        
    def test_view_edit_fragments_empty(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        
    def test_view_edit_fragments(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        f1 = mommy.make(Fragment, name="azerty")
        f2 = mommy.make(Fragment, name="qwerty")
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.get(url)
        
        self.assertEqual(200, response.status_code)
        self.assertContains(response, f1.name)
        self.assertContains(response, f2.name)
        
    def test_view_edit_fragments_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.get(url)
        
        self.assertEqual(302, response.status_code)
        
        self._log_as_regular_user()
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)    
    
    def test_edit_fragment(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 5)
    
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty+")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 2)

    def test_edit_fragment_css_allowed(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType, allowed_css_classes="oups")
        ft2 = mommy.make(FragmentType, allowed_css_classes="aaa,bbb")
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "oups")   
        self.assertEqual(f1.position, 5)
    
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty+")
        self.assertEqual(f2.css_class, "aaa")   
        self.assertEqual(f2.position, 2)
  
    def test_edit_fragment_css_not_allowed(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType, allowed_css_classes="")
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 5)
    
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty+")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 2)
  
      
    def test_edit_fragment_delete(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "",
            'form-1-position': 2,
            'form-1-delete_me': True,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual([], errs)
        
        expected = u'<script>$.colorbox.close(); window.location=window.location;</script>'.format()
        self.assertEqual(response.content, expected)
        
        self.assertEqual(1, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        self.assertEqual(Fragment.objects.filter(id=f2.id).count(), 0)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty!")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 5)
        
    def test_edit_fragment_invalid_position(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': "AAA",
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual(1, len(errs))
    
    def test_edit_fragment_empty_name(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': "",
            'form-0-css_class': "oups",
            'form-0-position': 1,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        self._log_as_editor()
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(200, response.status_code)
        
        soup = BeautifulSoup(response.content)
        errs = soup.select("ul.errorlist li")
        self.assertEqual(1, len(errs))
        
    
    def test_edit_fragment_permission_denied(self):
        template = settings.COOP_CMS_ARTICLE_TEMPLATES[0][0]
        article = get_article_class().objects.create(title="test", template=template, publication=BaseArticle.PUBLISHED)
        
        ft1 = mommy.make(FragmentType)
        ft2 = mommy.make(FragmentType)
        f1 = mommy.make(Fragment, name="azerty", type=ft1)
        f2 = mommy.make(Fragment, name="qwerty", type=ft2)
        
        data = {
            'form-0-id': f1.id,
            'form-0-type': f1.type.id,
            'form-0-name': f1.name+"!",
            'form-0-css_class': "oups",
            'form-0-position': 5,
            'form-0-delete_me': False,
            
            'form-1-id': f2.id,
            'form-1-type': f2.type.id,
            'form-1-name': f2.name+"+",
            'form-1-css_class': "aaa",
            'form-1-position': 2,
            'form-1-delete_me': False,
            
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-MAX_NUM_FORMS': 2
        }
        
        url = reverse("coop_cms_edit_fragments")
        response = self.client.post(url, data=data, follow=False)
        
        self.assertEqual(302, response.status_code)
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 1)
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 1)

        self._log_as_regular_user()
        response = self.client.post(url, data=data)
        self.assertEqual(403, response.status_code)  
        
        self.assertEqual(2, Fragment.objects.count())
        f1 = Fragment.objects.get(id=f1.id)
        f2 = Fragment.objects.get(id=f2.id)

        self.assertEqual(f1.type, ft1)
        self.assertEqual(f1.name, "azerty")
        self.assertEqual(f1.css_class, "")   
        self.assertEqual(f1.position, 1)
    
        self.assertEqual(f2.type, ft2)
        self.assertEqual(f2.name, "qwerty")
        self.assertEqual(f2.css_class, "")   
        self.assertEqual(f2.position, 1)
