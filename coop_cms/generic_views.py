# -*- coding: utf-8 -*-
"""generic views"""

from django.contrib.contenttypes.models import ContentType
from django.contrib.messages.api import success as success_message, error as error_message
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView
from django.views.generic.base import View
from django.views.generic.list import ListView as DjangoListView

from djaloha import utils as djaloha_utils

from coop_cms.logger import logger


class ListView(DjangoListView):
    """generic list view"""
    ordering = ''
    
    def get_context_data(self, **kwargs):
        context = super(ListView, self).get_context_data(**kwargs)
        context['model'] = self.model
        return context
    
    def get_queryset(self):
        if self.ordering:
            if type(self.ordering) in (list, tuple):
                return self.model.objects.order_by(*self.ordering)
            else:
                return self.model.objects.order_by(self.ordering)
        else:
            return self.model.objects.all()


class EditableObjectView(View):
    """Base class for aloha-editable objects"""
    model = None
    template_name = ""
    form_class = None
    field_lookup = "pk"
    edit_mode = False
    varname = "object"
    object = None
    form = None

    def can_edit_object(self):
        """check edit perms"""
        can_edit_perm = 'can_edit_{0}'.format(self.varname)
        user = self.request.user
        return user.is_authenticated() and user.is_active and user.has_perm(can_edit_perm, self.object)
        
    def can_access_object(self):
        """check access perms: 404 if not"""
        return True
    
    def can_view_object(self):
        """check view perm: 403 if not"""
        if self.edit_mode:
            return self.can_edit_object()
        else:
            can_view_perm = 'can_view_{0}'.format(self.varname)
            return self.request.user.has_perm(can_view_perm, self.object)
    
    def get_object(self):
        """get the object to edit"""
        lookup = {self.field_lookup: self.kwargs[self.field_lookup]}
        return get_object_or_404(self.model, **lookup)
    
    def get_context_data(self):
        """template context"""
        return {
            'form': self.form if self.edit_mode else None,
            'editable': self.can_edit_object(),
            'edit_mode': self.edit_mode,
            'title': getattr(self.object, 'title', unicode(self.object)),
            'coop_cms_edit_url': self.get_edit_url(),
            'coop_cms_cancel_url': self.get_cancel_url(),
            'coop_cms_can_view_callback': self.can_view_object,
            'coop_cms_can_edit_callback': self.can_edit_object,
            self.varname: self.object,
            'raw_'+self.varname: self.object,
        }
        
    def get_edit_url(self):
        """url for object editing"""
        return self.object.get_edit_url()
    
    def get_cancel_url(self):
        """url after cancel editing"""
        if hasattr(self.object, 'get_cancel_url'):
            return self.object.get_cancel_url()
        else:
            return self.object.get_absolute_url()
        
    def get_template(self):
        """get template"""
        return self.template_name
    
    def handle_object_not_found(self):
        """called if object not found"""
        pass

    def get_form_class(self):
        return self.form_class

    def get_form_kwargs(self):
        return {}

    def get_form(self, *args, **kwargs):
        kwargs.update(self.get_form_kwargs())
        form_class = self.get_form_class()
        return form_class(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        """handle http get -> view"""
        try:
            self.object = self.get_object()
        except Http404:
            return_this = self.handle_object_not_found()
            if return_this:
                return return_this
            else:
                raise
        
        if not self.can_access_object():
            raise Http404
        
        if not self.can_view_object():
            logger.warning("PermissionDenied")
            raise PermissionDenied
        
        self.form = self.get_form(instance=self.object)
        
        return render_to_response(
            self.get_template(),
            self.get_context_data(),
            context_instance=RequestContext(request)
        )
    
    def after_save(self, object):
        """called after save"""
        pass
    
    def post(self, request, *args, **kwargs):
        """handle http post -> edit"""
        if not self.edit_mode:
            raise Http404
        
        self.object = self.get_object()
        
        if not self.can_edit_object():
            logger.warning("PermissionDenied")
            raise PermissionDenied

        self.form = self.get_form(request.POST, request.FILES, instance=self.object)

        forms_args = djaloha_utils.extract_forms_args(request.POST)
        djaloha_forms = djaloha_utils.make_forms(forms_args, request.POST)

        if self.form.is_valid() and all([f.is_valid() for f in djaloha_forms]):

            self.object = self.form.save()
            
            self.after_save(self.object)
            
            if djaloha_forms:
                [f.save() for f in djaloha_forms]

            success_message(request, _(u'The object has been saved properly'))

            return HttpResponseRedirect(self.object.get_absolute_url())
        else:
            error_text = u'<br />'.join([unicode(f.errors) for f in [self.form]+djaloha_forms if f.errors])
            error_message(request, _(u'An error occured: {0}').format(error_text))
            logger.debug(u"error: {0}".format(error_text))
    
        return render_to_response(
            self.get_template(),
            self.get_context_data(),
            context_instance=RequestContext(request)
        )


class EditableFormsetView(TemplateView):
    """Base class for editing several objects on the same page"""
    template_name = ""
    model = None
    form_class = None
    extra = 1
    edit_mode = False
    success_url = ""
    success_view_name = ""
    formset = None
    
    def can_edit_objects(self):
        """check edit perms"""
        ct = ContentType.objects.get_for_model(self.model)
        can_edit_perm = '{0}.change_{1}'.format(ct.app_label, ct.model)
        user = self.request.user
        return user.is_authenticated() and user.is_active and user.has_perm(can_edit_perm, None)
        
    def can_view_objects(self):
        """check view perms"""
        if self.edit_mode:
            return self.can_edit_objects()
        return True
    
    def get_context_data(self):
        """template context"""
        context = {
            'editable': True,
            'edit_mode': self.edit_mode,
            'coop_cms_edit_url': self.get_edit_url(),
            'coop_cms_cancel_url': self.get_cancel_url(),
            'coop_cms_can_view_callback': self.can_view_objects,
            'coop_cms_can_edit_callback': self.can_edit_objects,
            'objects': self.get_queryset(),
            'raw_objects': self.get_queryset(),
        }
        if self.edit_mode:
            context['formset'] = self.formset
        return context
        
    def get_form_class(self):
        """get form class"""
        return self.form_class
    
    def get_queryset(self):
        """get objects"""
        return self.model.objects.all()
    
    def get_template(self):
        """get template"""
        return self.template_name
    
    def get_cancel_url(self):
        """url to go after cancel edition"""
        return self.get_success_url()
    
    def get_edit_url(self):
        """url for editing object"""
        return ''
        
    def get_success_url(self):
        """url to go after edition success"""
        return self.success_url or reverse(self.success_view_name) if self.success_view_name else ''
    
    def get_formset_class(self):
        """formset class"""
        return modelformset_factory(self.model, self.get_form_class(), extra=self.extra)
    
    def get_formset(self, *args, **kwargs):
        """formset"""
        Formset = self.get_formset_class()
        return Formset(queryset=self.get_queryset(), *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        """handle http get --> view"""
        if not self.can_view_objects():
            raise PermissionDenied
            
        self.formset = self.get_formset()
        return render_to_response(
            self.get_template(),
            self.get_context_data(),
            context_instance=RequestContext(request)
        )
    
    def _pre_save_object(self, form):
        """before saving an object"""
        return True
    
    def _post_save_object(self, obj, form):
        """after saving an object"""
        pass
    
    def post(self, request, *args, **kwargs):
        """handle http post -> edit"""
        if not self.edit_mode:
            raise Http404
    
        if not self.can_edit_objects():
            raise PermissionDenied
        
        self.formset = self.get_formset(request.POST, request.FILES)
        
        forms_args = djaloha_utils.extract_forms_args(request.POST)
        djaloha_forms = djaloha_utils.make_forms(forms_args, request.POST)

        #Handle case where formset post data has value which are not in the queryset
        formset_index_error = False
        try:
            formset_is_valid = self.formset.is_valid()
        except IndexError:
            formset_index_error = True
            formset_is_valid = False

        if formset_is_valid and all([f.is_valid() for f in djaloha_forms]):
            for form in self.formset:
                if self._pre_save_object(form):
                    obj = form.save()
                    self._post_save_object(obj, form)
            
            if djaloha_forms:
                [f.save() for f in djaloha_forms]
            
            success_message(request, _(u'The objects have been saved properly'))

            url = self.get_success_url()
            return HttpResponseRedirect(url)
        else:
            if formset_index_error:
                logger.warning(_(u'Index error in formset: some objects may be missing'))
                error_message(request, _(u'An error occured: At least one object is missing. Please try again.'))
                return HttpResponseRedirect(self.get_cancel_url())
            else:
                for f in self.formset:
                    errors = f.errors
                    if errors:
                        logger.warning(errors)
        
        return render_to_response(
            self.get_template(),
            self.get_context_data(),
            context_instance=RequestContext(request)
        )
