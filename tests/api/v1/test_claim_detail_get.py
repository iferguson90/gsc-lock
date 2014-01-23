from ..base import APITest
import datetime
import dateutil.parser
import pytz


POST_URL = '/v1/claims/'


class ClaimDetailGetGeneralSuccessTest(APITest):
    def setUp(self):
        super(ClaimDetailGetGeneralSuccessTest, self).setUp()
        self.post_data = {
            'resource': 'post-resource',
            'timeout': 0.010,
        }
        self.post_response = self.post(POST_URL, self.post_data)
        self.url = self.post_response.headers['Location']
        self.response = self.get(self.url)

    def test_should_return_200(self):
        self.assertEqual(200, self.response.status_code)

    def test_should_return_creation_time(self):
        created = dateutil.parser.parse(self.response.DATA['created'])
        now = pytz.UTC.localize(datetime.datetime.utcnow())
        self.assertGreaterEqual(now, created)
        self.assertLessEqual(now - datetime.timedelta(seconds=1), created)

# TODO
#    def test_should_return_metadata(self):
#        pass

    def test_should_return_resource(self):
        self.assertEqual(self.post_data['resource'],
                self.response.DATA['resource'])

    def test_should_return_status(self):
        self.assertEqual('active', self.response.DATA['status'])

    def test_should_return_status_history(self):
        status_history = self.response.DATA['status_history']
        self.assertEqual(['waiting', 'active'],
                [sh['status'] for sh in status_history])

    def test_should_return_timeout(self):
        self.assertEqual(self.post_data['timeout'],
                self.response.DATA['timeout'])


class ClaimDetailGetActiveSuccessTest(APITest):
    pass

# TODO
#    def test_should_return_ttl(self):
#        pass

# TODO
#    def test_should_return_active_duration(self):
#        pass


class ClaimDetailGetWaitingSuccessTest(APITest):
    pass

# TODO
#    def test_should_return_waiting_duration(self):
#        pass


class ClaimDetailGetErrorTest(APITest):
    def test_non_existant_claim_should_return_404(self):
        response = self.get('/claims/77/')
        self.assertEqual(404, response.status_code)
