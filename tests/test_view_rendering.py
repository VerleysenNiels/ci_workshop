import os

from flask.testing import FlaskClient
from typing import Optional
from unittest import mock

import ci_demo
from tests import base


class TestViewRendering(base.BaseTestCase):
    render_templates = False
    workshop_pdf = 'workshop.pdf'

    def assert_that_page_uses_the_right_template(self, url: str, expected_template: str,
                                                 client: Optional[FlaskClient] = None) -> None:
        if client is None:
            client = self.app.test_client()

        client.get(url)
        self.assert_template_used(expected_template)

    def assert_that_my_workshop_renders_the_correct_template_for_step(self, step: int, expected_template: str) -> None:
        u = self.create_user()
        self.set_workshop_step_for_user(u, step)
        with self.app.test_client() as c:
            self.store_user_id_in_session(c, u)
            self.assert_that_page_uses_the_right_template('/my_workshop', expected_template, c)
            self.assertContext('current_step', step)
            self.assertContext('max_step', len(ci_demo.workshop_steps))

    def render_dashboard_with_image(self, image_index: int) -> None:
        with mock.patch('random.randint') as m_r:
            m_r.return_value = image_index
            self.assert_that_page_uses_the_right_template('/', 'dashboard.html')
            self.assert_context('image', ci_demo.dashboard_images[image_index])

    def test_that_the_about_page_uses_the_right_template(self):
        self.assert_that_page_uses_the_right_template('/about', 'about.html')

    def test_that_the_workshop_page_uses_the_right_template(self):
        self.assert_that_page_uses_the_right_template('/workshop', 'workshop.html')

    def test_that_the_login_page_passes_the_redirect_if_not_defined(self):
        with self.app.test_client() as c:
            self.assert_that_page_uses_the_right_template('/login', 'login.html', c)
            self.assertContext('next', '')

    def test_that_the_login_page_passes_the_redirect_if_defined(self):
        redirect = 'foo.bar'
        with self.app.test_client() as c:
            self.assert_that_page_uses_the_right_template('/login?next=' + redirect, 'login.html', c)
            self.assertContext('next', redirect)

    def test_that_the_workshop_page_returns_the_correct_order_of_steps(self):
        for idx in range(len(ci_demo.workshop_steps)):
            self.assert_that_my_workshop_renders_the_correct_template_for_step(idx + 1, ci_demo.workshop_steps[idx])

    def test_that_the_dashboard_is_rendered_with_the_correct_arguments(self):
        for i in range(len(ci_demo.dashboard_images)):
            self.render_dashboard_with_image(i)

    def test_that_the_pdf_download_serves_the_correct_file(self):
        file_content = b"foo bar baz"
        with open(self.workshop_pdf, 'wb') as fh:
            fh.write(file_content)

        with self.app.test_client() as c:
            response = c.get("/download_pdf")
            self.assertEqual(file_content, response.data)

    def test_that_the_pdf_download_generates_a_pdf_when_none_is_present(self):
        self.assertFalse(os.path.isfile(self.workshop_pdf))
        with self.app.test_client() as c:
            response = c.get("/download_pdf")
            with open(self.workshop_pdf, "rb") as fh:
                expected_content = fh.read()
                self.assertEqual(expected_content, response.data)

    def test_that_the_pdf_download_raises_a_400_error(self):
        self.assertFalse(os.path.isfile(self.workshop_pdf))
        with mock.patch('xhtml2pdf.pisa.CreatePDF') as m_pdf:
            class MockError:
                err = True
            m_pdf.return_value = MockError()
            with self.app.test_client() as c:
                self.assert400(c.get("/download_pdf"))

    def tearDown(self):
        try:
            os.remove(self.workshop_pdf)
        except FileNotFoundError:
            pass



