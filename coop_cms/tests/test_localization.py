# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

from unittest import skipIf

from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.utils.translation import activate, get_language

from coop_cms.models import BaseArticle
from coop_cms.settings import is_localized, is_multilang, get_article_class
from coop_cms.tests import BaseTestCase


class UrlLocalizationTest(BaseTestCase):
    
    def setUp(self):
        activate(settings.LANGUAGES[0][0])
    
    def tearDown(self):
        activate(settings.LANGUAGES[0][0])
    
    def _log_as_editor(self):
        self.user = user = User.objects.create_user('toto', 'toto@toto.fr', 'toto')
        
        ct = ContentType.objects.get_for_model(get_article_class())
        
        perm = 'change_{0}'.format(ct.model)
        can_edit_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_edit_article)
        
        perm = 'add_{0}'.format(ct.model)
        can_add_article = Permission.objects.get(content_type=ct, codename=perm)
        user.user_permissions.add(can_add_article)
        
        user.is_active = True
        user.save()
        return self.client.login(username='toto', password='toto')
    
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_get_locale_article(self):
        original_text = '*!-+' * 10
        translated_text = ':%@/' * 9
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        setattr(a1, 'title_'+trans_lang, 'Accueil')
        setattr(a1, 'content_'+trans_lang, translated_text)
        a1.save()
        
        response = self.client.get('/{0}/home/'.format(origin_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        response = self.client.get('/{0}/accueil/'.format(trans_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, translated_text)

    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_change_lang(self):
        
        original_text = '*!-+' * 10
        translated_text = ':%@/' * 9
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        setattr(a1, 'title_'+trans_lang, 'Accueil')
        setattr(a1, 'content_'+trans_lang, translated_text)
        
        a1.save()
        
        origin_url = '/{0}/home'.format(origin_lang)
        response = self.client.get(origin_url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        data = {'language': trans_lang}
        response = self.client.post(reverse('coop_cms_change_language')+'?next={0}'.format(origin_url),
            data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, translated_text)
        
        response = self.client.get('/{0}/accueil/'.format(trans_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, translated_text)
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_change_lang_next_url_after(self):
        
        original_text = '*!-+' * 10
        translated_text = ':%@/' * 9
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        a2 = get_article_class().objects.create(title="Next", content="****NEXT****")
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        setattr(a1, 'title_'+trans_lang, 'Accueil')
        setattr(a1, 'content_'+trans_lang, translated_text)
        
        a1.save()
        
        origin_url = '/{0}/home'.format(origin_lang)
        response = self.client.get(origin_url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        data = {'language': trans_lang, 'next_url_after_change_lang': a2.get_absolute_url()}
        response = self.client.post(reverse('coop_cms_change_language'),
            data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, a2.content)
            
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_change_lang_no_trans(self):
        
        original_text = '*!-+' * 10
        
        a1 = get_article_class().objects.create(title="Home", content=original_text)
        
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        origin_url = '/{0}/home'.format(origin_lang)
        response = self.client.get(origin_url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        data = {'language': trans_lang}
        response = self.client.post(reverse('coop_cms_change_language')+'?next={0}'.format(origin_url),
            data=data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
        
        response = self.client.get('/{0}/home/'.format(trans_lang), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, original_text)
            
    def test_keep_slug(self):
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        original_slug = a1.slug
        a1.title = "Title changed"
        a1.save()
        a1 = Article.objects.get(id=a1.id)
        self.assertEqual(original_slug, a1.slug)
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_keep_localized_slug(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, u'Accueil')
        a1.save()
        
        original_slug = a1.slug
        original_trans_slug = getattr(a1, 'slug_'+trans_lang, u'**dummy**')
        
        a1.title = u"Title changed"
        setattr(a1, 'title_'+trans_lang, u'Titre change')
        
        a1.save()
        a1 = Article.objects.get(id=a1.id)
        
        self.assertEqual(original_slug, a1.slug)
        self.assertEqual(original_trans_slug, getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa")

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, a2.title)
        a1.save()
        
        a2.save()
        
        setattr(a2, 'title_'+trans_lang, a2.title)
        a2.save()
        
        self.assertNotEqual(getattr(a2, 'slug_'+trans_lang), getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing2(self):
        
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa")

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, a2.title)
        a1.save()
        
        setattr(a2, 'title_'+trans_lang, a2.title)
        a2.save()
        
        self.assertNotEqual(getattr(a2, 'slug_'+trans_lang), getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing3(self):
        self._log_as_editor()
        Article = get_article_class()

        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        setattr(a1, 'title_'+trans_lang, a2.title)
        a1.save()
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a2.get_edit_url()
        
        data = {
            'title': a2.title,
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a2_updated = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a2_updated, 'title_'+trans_lang), a2.title)
        
        self.assertNotEqual(getattr(a2_updated, 'slug_'+trans_lang), getattr(a1, 'slug_'+trans_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localize_existing_article1(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a1.get_edit_url()
        
        data = {
            'title': u"Home",
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a1_updated = Article.objects.get(id=a1.id)
        
        self.assertEqual(getattr(a1_updated, 'title_'+trans_lang), a1.title)
        self.assertEqual(getattr(a1_updated, 'slug_'+trans_lang), getattr(a1, 'slug_'+origin_lang))
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localize_existing_article2(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Accueil", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a1.get_edit_url()
        
        data = {
            'title': u"Home",
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a1_updated = Article.objects.get(id=a1.id)
        self.assertEqual(getattr(a1_updated, 'title_'+origin_lang), a1.title)
        self.assertEqual(getattr(a1_updated, 'title_'+trans_lang), data["title"])
        self.assertEqual(getattr(a1_updated, 'slug_'+trans_lang), "home")
        self.assertEqual(getattr(a1_updated, 'slug_'+origin_lang), "accueil")
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing4(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        self.assertEqual(None, getattr(a2, 'slug_'+trans_lang))
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a2.get_edit_url()
        
        data = {
            'title': a1.title,
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a2_updated = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a2_updated, 'title_'+trans_lang), a1.title)
        
        self.assertNotEqual(getattr(a2_updated, 'slug_'+trans_lang), a1.slug)
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_localized_slug_already_existing5(self):
        self._log_as_editor()
        Article = get_article_class()
        a1 = Article.objects.create(title=u"Home", content="aa")
        a2 = Article.objects.create(title=u"Rome", content="aa", template='test/article.html')

        origin_lang = settings.LANGUAGES[0][0]
        trans_lang = settings.LANGUAGES[1][0]
        
        self.assertEqual(None, getattr(a2, 'slug_'+trans_lang))
        
        setattr(a2, 'title_'+trans_lang, a1.title)
        a2.save()
        self.assertNotEqual(a1.slug, getattr(a2, 'slug_'+trans_lang))
        
        #CHANGE LANGUUAGE
        activate(trans_lang)
        
        url = a2.get_edit_url()
        
        data = {
            'title': a1.title,
            'content': 'translation', 
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        a2_updated = Article.objects.get(id=a2.id)
        
        self.assertEqual(getattr(a2_updated, 'title_'+trans_lang), a1.title)
        
        self.assertNotEqual(getattr(a2_updated, 'slug_'+trans_lang), a1.slug)
            
    def test_no_title(self):
        Article = get_article_class()
        
        try:
            a1 = Article.objects.create(title=u"", content="a!*%:"*10, publication=BaseArticle.PUBLISHED)
        except:
            return #OK
        
        self.assertFalse(True) #Force to fail
        
    @skipIf(not is_localized() or not is_multilang(), "not localized")
    def test_create_article_in_additional_lang(self):
        
        Article = get_article_class()
        
        default_lang = settings.LANGUAGES[0][0]
        other_lang = settings.LANGUAGES[1][0]
        
        activate(other_lang)
        
        a1 = Article.objects.create(title=u"abcd", content="a!*%:"*10, publication=BaseArticle.PUBLISHED)
        
        response = self.client.get(a1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, a1.content)
        
        activate(default_lang)
        
        response = self.client.get(a1.get_absolute_url())
        self.assertEqual(200, response.status_code)
        self.assertContains(response, a1.content)
