# -*- coding: utf-8 -*-

from django.conf import settings
if 'localeurl' in settings.INSTALLED_APPS:
    from localeurl.models import patch_reverse
    patch_reverse()

import json
from datetime import datetime
from StringIO import StringIO
from unittest import skipIf

from bs4 import BeautifulSoup
from PIL import Image as PilImage

from django.core.files import File
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.test.utils import override_settings

from model_mommy import mommy

from coop_cms.models import ArticleCategory, Document, Image, ImageSize, MediaFilter
from coop_cms.settings import get_article_class
from coop_cms.tests import BaseArticleTest, BaseTestCase, MediaBaseTestCase


class ImageUploadTest(MediaBaseTestCase):
    
    def test_view_form_no_filters(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        id_filters = soup.select("input#id_filters")
        self.assertEqual(1, len(id_filters))
        self.assertEqual("hidden", id_filters[0]["type"])
        
    def test_view_form_no_sizes(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        id_size = soup.select("input#id_size")
        self.assertEqual(1, len(id_size))
        self.assertEqual("hidden", id_size[0]["type"])

    def test_view_form_with_filters(self):
        f1 = mommy.make(MediaFilter, name="icons")
        f2 = mommy.make(MediaFilter, name="big-images")
        
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        id_filters = soup.select("select#id_filters option")
        self.assertEqual(2, len(id_filters))
    
    def test_view_form_with_sizes(self):
        s1 = mommy.make(ImageSize, name="icons")
        s2 = mommy.make(ImageSize, name="big-images")
        
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)
        id_sizes = soup.select("select#id_size option")
        self.assertEqual(['', str(s1.id), str(s2.id)], [x["value"] for x in id_sizes])
        
    def test_post_form_no_filters(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': ''
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        
        images = Image.objects.all()
        self.assertEquals(1, images.count())
        self.assertEqual(images[0].name, data['descr'])
        self.assertEqual(images[0].filters.count(), 0)
        self.assertEqual(images[0].size, None)
        f = images[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file("unittest1.png").read())
        
    def test_post_form_size(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        img_size = mommy.make(ImageSize, size="128")
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': '',
            'size': img_size.id,
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        
        images = Image.objects.all()
        self.assertEquals(1, images.count())
        self.assertEqual(images[0].name, data['descr'])
        self.assertEqual(images[0].filters.count(), 0)
        self.assertEqual(images[0].size, img_size)
        f = images[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file("unittest1.png").read())
        
    def test_post_form_anonymous(self):
        url = reverse('coop_cms_upload_image')
        
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': ''
        }
        
        response = self.client.post(url, data=data, follow=False)
        self.assertEqual(response.status_code, 302)
        next_url = "http://testserver/accounts/login/?next={0}".format(url)
        self.assertEqual(next_url, response['Location'])
        
        images = Image.objects.all()
        self.assertEquals(0, images.count())
        
    def test_post_form_not_allowed(self):
        self._log_as_mediamgr()
        url = reverse('coop_cms_upload_image')
        
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': ''
        }
        
        response = self.client.post(url, data=data, follow=False)
        self.assertEqual(response.status_code, 403)
        
        images = Image.objects.all()
        self.assertEquals(0, images.count())
        
    def test_post_form_with_filters(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        
        f1 = mommy.make(MediaFilter, name="icons")
        f2 = mommy.make(MediaFilter, name="big-images")
        f3 = mommy.make(MediaFilter, name="small-images")
        
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': [str(f.id) for f in (f1,f3)],
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        
        images = Image.objects.all()
        self.assertEquals(1, images.count())
        self.assertEqual(images[0].name, data['descr'])
        self.assertEqual(images[0].filters.count(), 2)
        self.assertEqual(list(images[0].filters.all().order_by('id')), [f1, f3])
        
        f = images[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file("unittest1.png").read())
        
    def test_post_form_with_filters_no_choice(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        
        f1 = mommy.make(MediaFilter, name="icons")
        f2 = mommy.make(MediaFilter, name="big-images")
        f3 = mommy.make(MediaFilter, name="small-images")
        
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': [],
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        
        images = Image.objects.all()
        self.assertEquals(1, images.count())
        self.assertEqual(images[0].name, data['descr'])
        self.assertEqual(images[0].filters.count(), 0)
        
        f = images[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file("unittest1.png").read())
        
    def test_post_form_with_invalid_size(self):
        self._log_as_mediamgr(perm=self._permission("add", Image))
        url = reverse('coop_cms_upload_image')
        
        data = {
            'image': self._get_file("unittest1.png"),
            'descr': 'a test file',
            'filters': [],
            'size': "hhjk",
        }
        
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        
        images = Image.objects.all()
        self.assertEquals(0, images.count())


class MediaLibraryTest(MediaBaseTestCase):
    
    @override_settings(COOP_CMS_MAX_IMAGE_WIDTH="600")
    def test_image_max_width_size(self):
        image = mommy.make(Image)
        url = image.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = StringIO(response.content)
        img = PilImage.open(data)
        self.assertEqual(img.size[0], 130)
        
    @override_settings(COOP_CMS_MAX_IMAGE_WIDTH="600")
    def test_image_max_width_size(self):
        size = mommy.make(ImageSize, size="60")
        image = mommy.make(Image, size=size)
        url = image.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = StringIO(response.content)
        img = PilImage.open(data)
        self.assertEqual(img.size[0], 60)
        
    @override_settings(COOP_CMS_MAX_IMAGE_WIDTH="60")
    def test_image_max_width_size_no_scale(self):
        image = mommy.make(Image)
        url = image.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = StringIO(response.content)
        img = PilImage.open(data)
        self.assertEqual(img.size[0], 60)
        
    @override_settings(COOP_CMS_MAX_IMAGE_WIDTH="coop_cms.tests.dummy_image_width")
    def test_image_max_width_size_lambda(self):
        image = mommy.make(Image)
        url = image.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = StringIO(response.content)
        img = PilImage.open(data)
        self.assertEqual(img.size[0], 20)
        
    @override_settings(COOP_CMS_MAX_IMAGE_WIDTH="")
    def test_image_max_width_size_none(self):
        image = mommy.make(Image)
        url = image.get_absolute_url()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = StringIO(response.content)
        img = PilImage.open(data)
        self.assertEqual(img.size[0], 130)
    
    def test_show_images_empty(self):
        self._log_as_mediamgr()
        url = reverse('coop_cms_media_images')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        
    def test_show_documents_empty(self):
        self._log_as_mediamgr()
        url = reverse('coop_cms_media_documents')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
            
    def test_show_media_anonymous(self):
        url = reverse('coop_cms_media_images')
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        next_url = "http://testserver/accounts/login/?next={0}".format(url)
        self.assertEqual(next_url, response['Location'])
        
    def test_show_media_not_staff(self):
        self._log_as_mediamgr(is_staff=False)
        url = reverse('coop_cms_media_images')
        response = self.client.get(url)
        self.assertEqual(403, response.status_code)
    
    def test_show_images(self):
        self._log_as_mediamgr()
        images = mommy.make(Image, _quantity=2)
        url = reverse('coop_cms_media_images')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        nodes = soup.select(".library-thumbnail")
        self.assertEqual(2, len(nodes))
        
    def test_show_images_pagination(self):
        self._log_as_mediamgr()
        images = mommy.make(Image, _quantity=16)
        url = reverse('coop_cms_media_images')
        response = self.client.get(url)
        self.assertEqual(200, response.status_code)
        soup = BeautifulSoup(response.content)
        nodes = soup.select(".library-thumbnail")
        self.assertEqual(12, len(nodes))
    
    def test_show_images_page_2(self):
        self._log_as_mediamgr()
        images = mommy.make(Image, _quantity=16)
        url = reverse('coop_cms_media_images')+"?page=2"
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        soup = BeautifulSoup(data['html'])
        nodes = soup.select(".library-thumbnail")
        self.assertEqual(4, len(nodes))
        
    def test_show_images_media_filter(self):
        self._log_as_mediamgr()
        mf = mommy.make(MediaFilter)
        images = []
        for i in range(16):
            images.append(mommy.make(Image, created=datetime(2014, 1, 1, 12, i)))
        images.reverse()
        
        images[5].filters.add(mf)
        images[15].filters.add(mf)
        url = reverse('coop_cms_media_images')+"?page=1&media_filter={0}".format(mf.id)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        soup = BeautifulSoup(data['html'])
        nodes = soup.select(".library-thumbnail")
        self.assertEqual(2, len(nodes))
        expected = [x.file.url for x in (images[5], images[15])]
        actual = [node["rel"] for node in nodes]
        self.assertEqual(expected, actual)
    
    def test_show_images_media_filter_all(self):
        self._log_as_mediamgr()
        mf = mommy.make(MediaFilter)
        
        images = []
        for i in range(16):
            images.append(mommy.make(Image, created=datetime(2014, 1, 1, 12, i)))
        images.reverse()
        
        images[5].filters.add(mf)
        images[15].filters.add(mf)
        url = reverse('coop_cms_media_images')+"?page=1&media_filter={0}".format(0)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(200, response.status_code)
        data = json.loads(response.content)
        soup = BeautifulSoup(data['html'])
        nodes = soup.select(".library-thumbnail")
        self.assertEqual(12, len(nodes))
        expected = [x.file.url for x in images[:12]]
        actual = [node["rel"] for node in nodes]
        self.assertEqual(expected, actual)
    
    def test_image_no_size(self):
        image = mommy.make(Image, size=None)
        url = image.get_absolute_url()
        self.assertEqual(url, image.file.url)
        
    def test_image_size(self):
        image_size = mommy.make(ImageSize, size="128x128")
        image = mommy.make(Image, size=image_size)
        url = image.get_absolute_url()
        self.assertNotEqual(url, image.file.url)
        
    def test_image_wrong_size(self):
        image_size = mommy.make(ImageSize, size="blabla")
        image = mommy.make(Image, size=image_size)
        url = image.get_absolute_url()
        self.assertEqual(url, image.file.url)
        
    def test_image_size_crop(self):
        image_size = mommy.make(ImageSize, size="128x128", crop="center")
        image = mommy.make(Image, size=image_size)
        url = image.get_absolute_url()
        self.assertNotEqual(url, image.file.url)
    
    
class DownloadDocTest(MediaBaseTestCase):
    
    def setUp(self):
        super(DownloadDocTest, self).setUp()
    
    def tearDown(self):
        super(DownloadDocTest, self).tearDown()
    
    def test_upload_public_doc(self):
        self._log_as_mediamgr(perm=self._permission("add", Document))
        data = {
            'file': self._get_file(),
            'is_private': False,
            'name': 'a test file',
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        public_docs = Document.objects.filter(is_private=False)
        self.assertEquals(1, public_docs.count())
        self.assertEqual(public_docs[0].name, data['name'])
        self.assertEqual(public_docs[0].category, None)
        f = public_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
        
    def test_upload_public_doc_category(self):
        self._log_as_mediamgr(perm=self._permission("add", Document))
        cat = mommy.make(ArticleCategory, name="my cat")
        data = {
            'file': self._get_file(),
            'is_private': False,
            'name': 'a test file',
            'category': cat.id,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        public_docs = Document.objects.filter(is_private=False)
        self.assertEquals(1, public_docs.count())
        self.assertEqual(public_docs[0].name, data['name'])
        self.assertEqual(public_docs[0].category, cat)
        f = public_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
        
    def test_upload_doc_missing_fields(self):
        self._log_as_mediamgr(perm=self._permission("add", Document))
        data = {
            'is_private': False,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())

    def test_upload_doc_anonymous_user(self):
        data = {
            'file': self._get_file(),
            'is_private': False,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content, 'close_popup_and_media_slide')
        self.assertEquals(0, Document.objects.all().count())
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        
    def test_upload_not_allowed(self):
        self._log_as_mediamgr()
        data = {
            'file': self._get_file(),
            'is_private': False,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 403)
        
    def test_upload_private_doc(self):
        self._log_as_mediamgr(perm=self._permission("add", Document))
        data = {
            'file': self._get_file(),
            'is_private': True,
        }
        response = self.client.post(reverse('coop_cms_upload_doc'), data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, 'close_popup_and_media_slide')
        private_docs = Document.objects.filter(is_private=True)
        self.assertEquals(1, private_docs.count())
        #TODO : on drone.io filename is unittest1_S0meRandom. Why?
        #self.assertNotEqual(private_docs[0].name, 'unittest1')
        self.assertNotEqual(private_docs[0].name, '')
        self.assertEqual(private_docs[0].category, None)
        f = private_docs[0].file
        f.open('rb')
        self.assertEqual(f.read(), self._get_file().read())
    
    def test_view_docs(self):
        self._log_as_mediamgr(perm=self._permission("add", Document))
        file1 = File(self._get_file())
        doc1 = mommy.make(Document, is_private=True, file=file1)
        file2 = File(self._get_file())
        doc2 = mommy.make(Document, is_private=False, file=file2)
        
        response = self.client.get(reverse('coop_cms_media_documents'))
        self.assertEqual(response.status_code, 200)
        
        self.assertContains(response, reverse('coop_cms_download_doc', args=[doc1.id]))
        self.assertNotContains(response, doc1.file.url)
        self.assertNotContains(response, reverse('coop_cms_download_doc', args=[doc2.id]))
        self.assertContains(response, doc2.file.url)
        
    def test_view_docs_anonymous(self):
        response = self.client.get(reverse('coop_cms_media_documents'), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        
    def test_view_docs_not_allowed(self):
        self._log_as_mediamgr(is_staff=False)
        response = self.client.get(reverse('coop_cms_media_documents'), follow=True)
        self.assertEqual(response.status_code, 403)
    
    def test_download_public(self):
        #create a public doc
        file = File(self._get_file())
        doc = mommy.make(Document, is_private=False, file=file)
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertNotEqual(doc.get_download_url(), private_url)
        
        #login and download
        self._log_as_mediamgr()
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content, self._get_file().read())
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self._get_file().read())
        
    @skipIf('sanza.Profile' in settings.INSTALLED_APPS, "sanza.Profile installed")
    def test_download_private(self):
            
        #create a public doc
        file = File(self._get_file())
        cat = mommy.make(ArticleCategory, name="private-doc")
        doc = mommy.make(Document, is_private=True, file=file, category=cat)
            
        
        #check the url
        private_url = reverse('coop_cms_download_doc', args=[doc.id])
        self.assertEqual(doc.get_download_url(), private_url)
        
        #login and download
        self._log_as_mediamgr()
        response = self.client.get(doc.get_download_url())
        self.assertEqual(response.status_code, 200)
        self.assertEquals(response['Content-Disposition'], "attachment; filename=unittest1.txt")
        self.assertEquals(response['Content-Type'], "text/plain")
        #TODO: This change I/O Exception in UnitTest
        #self.assertEqual(response.content, self._get_file().read()) 
        
        #logout and download
        self.client.logout()
        response = self.client.get(doc.get_download_url(), follow=True)
        self.assertEqual(response.status_code, 200)
        redirect_url = response.redirect_chain[-1][0]
        login_url = reverse('django.contrib.auth.views.login')
        self.assertTrue(redirect_url.find(login_url)>0)
        

class ImageListTemplateTagTest(BaseTestCase):

    def test_non_existing_filter(self):
        tpl = Template('{% load coop_utils %}{% coop_image_list "test" as image_list %}{{image_list|length}}')
        html = tpl.render(Context({}))
        self.assertEqual(html, "0")

    def test_empty_filter(self):
        f = mommy.make(MediaFilter, name="abcd")
        tpl = Template('{% load coop_utils %}{% coop_image_list "abcd" as image_list %}{{image_list|length}}')
        html = tpl.render(Context({}))
        self.assertEqual(html, "0")

    def test_filter_with_images(self):
        f = mommy.make(MediaFilter, name="abcd")
        img1 = mommy.make(Image, filters=[f])
        tpl = Template('{% load coop_utils %}{% coop_image_list "abcd" as image_list %}{{image_list|length}}')
        html = tpl.render(Context({}))
        self.assertEqual(html, "1")

    def test_filter_with_images_var_name(self):
        f = mommy.make(MediaFilter, name="abcd")
        img1 = mommy.make(Image, filters=[f])
        tpl = Template('{% load coop_utils %}{% coop_image_list filter_name as image_list %}{{image_list|length}}')
        html = tpl.render(Context({"filter_name": f.name}))
        self.assertEqual(html, "1")

    def test_filter_as_missing(self):
        f = mommy.make(MediaFilter, name="abcd")
        img1 = mommy.make(Image, filters=[f])
        try:
            tpl = Template('{% load coop_utils %}{% coop_image_list "abcd" image_list %}{{image_list|length}}')
        except Exception, msg:
            self.assertEqual("coop_image_list: usage --> {% coop_image_list 'filter_name' as var_name %}", unicode(msg))
        else:
            self.assertEqual("", "No exception")


class ArticleLogoTest(BaseArticleTest):

    def _get_image(self, file_name='unittest1.png'):
        return self._get_file(file_name)

    def setUp(self):
        super(ArticleLogoTest, self).setUp()
        self._default_article_templates = settings.COOP_CMS_ARTICLE_TEMPLATES
        settings.COOP_CMS_ARTICLE_TEMPLATES = (
            ('test/article_with_logo_size.html', 'Article with logo size'),
            ('test/article_with_logo_size_and_crop.html', 'Article with logo size and crop'),
            ('test/article_no_logo_size.html', 'Article no logo size and crop'),
        )
        self._default_logo_size = getattr(settings, 'COOP_CMS_ARTICLE_LOGO_SIZE', None)
        self._default_logo_crop = getattr(settings, 'COOP_CMS_ARTICLE_LOGO_CROP', None)

    def tearDown(self):
        super(ArticleLogoTest, self).tearDown()
        #restore
        settings.COOP_CMS_ARTICLE_TEMPLATES = self._default_article_templates
        settings.COOP_CMS_ARTICLE_LOGO_SIZE = self._default_logo_size
        settings.COOP_CMS_ARTICLE_LOGO_CROP = self._default_logo_crop

    def test_view_article_no_image(self, template_index=0, image=False):
        Article = get_article_class()
        a = mommy.make(Article,
            title=u"This is my article", content=u"<p>This is my <b>content</b></p>",
            template = settings.COOP_CMS_ARTICLE_TEMPLATES[template_index][0])
        if image:
            a.logo = File(self._get_image())
            a.save()

        response = self.client.get(a.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, a.title)
        self.assertContains(response, a.content)

    def test_view_article_no_image_crop(self):
        self.test_view_article_no_image(1)

    def test_view_article_image_no_crop(self):
        self.test_view_article_no_image(0, True)

    def test_view_article_image_and_crop(self):
        self.test_view_article_no_image(1, True)

    def test_edit_article_no_image(self, template_index=0, image=False, post_image=False):
        Article = get_article_class()
        if image:
            a = mommy.make(Article,
                title=u"This is my article", content=u"<p>This is my <b>content</b></p>", slug="",
                template = settings.COOP_CMS_ARTICLE_TEMPLATES[template_index][0], logo=File(self._get_image())
            )
        else:
            a = mommy.make(Article,
                title=u"This is my article", content=u"<p>This is my <b>content</b></p>", slug="",
                template = settings.COOP_CMS_ARTICLE_TEMPLATES[template_index][0]
            )

        self._log_as_editor()

        response = self.client.post(a.get_edit_url(), follow=True)
        self.assertEqual(response.status_code, 200)

        data = {
            'title': 'Title of the article',
            'content': 'The content',
        }
        if post_image:
            data['logo'] = self._get_image('unittest2.png')
        response = self.client.post(a.get_edit_url(), data=data, follow=True)
        self.assertEqual(response.status_code, 200)

        a = Article.objects.get(id=a.id)

        self.assertEqual(data['title'], a.title)
        self.assertEqual(data['content'], a.content)

        self.assertContains(response, a.title)
        self.assertContains(response, a.content)

    def test_edit_article_no_image_crop(self):
        self.test_edit_article_no_image(1)

    def test_edit_article_image_no_post_no_crop(self):
        self.test_edit_article_no_image(0, True, False)

    def test_edit_article_image_no_post_crop(self):
        self.test_edit_article_no_image(1, True, False)

    def test_edit_article_image_post_no_crop(self):
        self.test_edit_article_no_image(0, True, True)

    def test_edit_article_image_post_crop(self):
        self.test_edit_article_no_image(1, True, True)

    def test_view_article_no_image_template1(self):
        self.test_view_article_no_image(2, False)

    def test_view_article_no_image_template2(self):
        self.test_view_article_no_image(2, True)

    def test_view_article_no_image_template3(self):
        settings.COOP_CMS_ARTICLE_LOGO_SIZE = "x100"
        settings.COOP_CMS_ARTICLE_LOGO_CROP = "top"
        self.test_view_article_no_image(2, True)

    def test_edit_article_no_image_template1(self):
        self.test_edit_article_no_image(2, False, False)

    def test_edit_article_no_image_template2(self):
        self.test_edit_article_no_image(2, True, False)

    def test_edit_article_no_image_template3(self):
        self.test_edit_article_no_image(2, True, True)

    def test_edit_article_no_image_template4(self):
        settings.COOP_CMS_ARTICLE_LOGO_SIZE = "x100"
        settings.COOP_CMS_ARTICLE_LOGO_CROP = "top"
        self.test_edit_article_no_image(2, True, True)
