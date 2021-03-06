from django import forms
from django.contrib.sites.models import Site
from django.test import TestCase, tag  # noqa
from django.test.utils import override_settings

from ..add_or_update_django_sites import add_or_update_django_sites
from ..get_site_id import get_site_id
from ..forms import SiteModelFormMixin
from ..utils import raise_on_save_if_reviewer, ReviewerSiteSaveError
from .models import TestModelWithSite
from .site_test_case_mixin import SiteTestCaseMixin, default_sites


class TestForm(SiteModelFormMixin, forms.ModelForm):
    class Meta:
        model = TestModelWithSite
        fields = "__all__"


class TestSites(SiteTestCaseMixin, TestCase):
    @override_settings(SITE_ID=20)
    def test_20(self):
        obj = TestModelWithSite.objects.create()
        self.assertEqual(obj.site.pk, 20)
        self.assertEqual(obj.site.pk, Site.objects.get_current().pk)

    @override_settings(SITE_ID=30)
    def test_30(self):
        obj = TestModelWithSite.objects.create()
        self.assertEqual(obj.site.pk, 30)
        self.assertEqual(obj.site.pk, Site.objects.get_current().pk)

    @override_settings(SITE_ID=30)
    def test_override_current(self):
        site = Site.objects.get(pk=40)
        obj = TestModelWithSite.objects.create(site=site)
        self.assertEqual(obj.site.pk, 40)
        self.assertNotEqual(obj.site.pk, Site.objects.get_current().pk)

    @override_settings(SITE_ID=30, REVIEWER_SITE_ID=30)
    def test_reviewer(self):
        site = Site.objects.get(pk=30)
        self.assertRaises(
            ReviewerSiteSaveError, TestModelWithSite.objects.create, site=site
        )

    @override_settings(SITE_ID=30, REVIEWER_SITE_ID=0)
    def test_reviewer_passes(self):
        site = Site.objects.get(pk=30)
        try:
            TestModelWithSite.objects.create(site=site)
        except ReviewerSiteSaveError:
            self.fail("SiteModelError unexpectedly raised")

    @override_settings(SITE_ID=30, REVIEWER_SITE_ID=0)
    def test_raise_on_save_if_reviewer(self):
        try:
            raise_on_save_if_reviewer(site_id=30)
        except ReviewerSiteSaveError:
            self.fail("SiteModelError unexpectedly raised")

        self.assertRaises(ReviewerSiteSaveError, raise_on_save_if_reviewer, site_id=0)

    @override_settings(SITE_ID=30, REVIEWER_SITE_ID=30)
    def test_raise_on_save_in_form(self):
        form = TestForm(data={"f1": "100"})
        self.assertFalse(form.is_valid())
        self.assertIn(
            "Adding or changing data has been disabled", form.errors.get("__all__")[0]
        )

    def test_get_site_id_by_name(self):
        add_or_update_django_sites(sites=self.default_sites)
        self.assertEqual(get_site_id("mochudi"), 10)

    def test_get_site_id_by_title(self):
        add_or_update_django_sites(sites=self.default_sites)
        self.assertEqual(get_site_id("Mochudi"), 10)


class TestSites2(TestCase):
    def test_updates_sites(self):

        self.assertIn("example.com", [str(obj) for obj in Site.objects.all()])

        sites = default_sites

        add_or_update_django_sites(sites=sites)

        for site in default_sites:
            self.assertIn(site[0], [obj.id for obj in Site.objects.all()])

        self.assertNotIn("example.com", [str(obj) for obj in Site.objects.all()])

        add_or_update_django_sites(sites=sites, verbose=True)

        self.assertEqual(len(sites), Site.objects.all().count())
