import json
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import Mock,patch
import unittest
from drive_manager.updates import API,REPOSITORY,LIMIT,Update,NoRedirect,check,parse_release,version

class UpdateTests(unittest.TestCase):
    def release(self,tag='v1.16.0'):
        number=tag.removeprefix('v');name='drive-manager-'+number+'-1.fc44.noarch.rpm'
        return {'tag_name':tag,'draft':False,'prerelease':False,'html_url':REPOSITORY+'/releases/tag/'+tag,
            'assets':[{'name':name,'state':'uploaded','browser_download_url':REPOSITORY+'/releases/download/'+tag+'/'+name}]}
    def test_numeric_versions_and_stable_comparison(self):
        self.assertGreater(version('1.10.0'),version('1.9.9'))
        self.assertEqual(version('v1.15.0'),(1,15,0))
        self.assertEqual(parse_release(self.release('v1.16.0'),'1.15.0').state,'update_available')
        self.assertEqual(parse_release(self.release('v1.15.0'),'1.15.0').state,'update_current')
        older=parse_release(self.release('v1.14.0'),'1.15.0')
        self.assertEqual(older.state,'update_ahead');self.assertFalse(older.rpm_url)
    def test_preview_draft_invalid_versions_and_wrong_repository_rejected(self):
        for tag in ['v1.16.0-beta','v1.16.0+build','v01.16.0','SECRET','1.2.3/other','v1.2.٣']:
            self.assertEqual(parse_release(self.release(tag),'1.15.0').state,'update_error')
        for key in ['draft','prerelease']:
            data=self.release();data[key]=True
            self.assertEqual(parse_release(data,'1.15.0').state,'update_error')
        data=self.release();data['html_url']='https://example.com/SECRET'
        result=parse_release(data,'1.15.0');self.assertEqual(result,Update('update_error','1.15.0'))
    def test_only_matching_uploaded_noarch_fedora44_rpm_is_offered(self):
        data=self.release();good=data['assets'][0].copy()
        for mutation in [{'state':'new'},{'name':'drive-manager-1.16.0-1.fc45.noarch.rpm'},
                         {'browser_download_url':'https://example.com/SECRET'}]:
            data['assets']=[good|mutation];result=parse_release(data,'1.15.0')
            self.assertEqual(result.state,'update_available');self.assertFalse(result.rpm_url)
            self.assertTrue(result.release_url.startswith(REPOSITORY))
        data['assets']=[good];self.assertEqual(parse_release(data,'1.15.0').rpm_url,good['browser_download_url'])
    def test_no_matching_asset_keeps_safe_release_page(self):
        data=self.release();data['assets']=[];result=parse_release(data,'1.15.0')
        self.assertTrue(result.release_url);self.assertFalse(result.rpm_url)
        data['assets']='SECRET';self.assertEqual(parse_release(data,'1.15.0').state,'update_error')
    def response(self,payload):
        response=Mock();response.status=200;response.read.return_value=payload
        response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
        return response
    def test_public_request_has_bounds_and_no_authentication(self):
        opener=Mock();response=self.response(json.dumps(self.release()).encode());opener.open.return_value=response
        with patch('drive_manager.updates.build_opener',return_value=opener):result=check('1.15.0')
        self.assertEqual(result.state,'update_available')
        request=opener.open.call_args.args[0]
        self.assertEqual(request.full_url,API);self.assertEqual(request.get_method(),'GET')
        self.assertEqual(opener.open.call_args.kwargs['timeout'],10)
        self.assertNotIn('authorization',{k.lower() for k,v in request.header_items()})
        response.read.assert_called_once_with(LIMIT+1)
    def test_timeout_large_response_and_raw_errors_are_safe(self):
        opener=Mock()
        with patch('drive_manager.updates.build_opener',return_value=opener):
            opener.open.side_effect=TimeoutError('SECRET')
            self.assertEqual(check('1.15.0'),Update('update_error','1.15.0'))
            opener.open.side_effect=None;opener.open.return_value=self.response(b'X'*(LIMIT+1))
            self.assertEqual(check('1.15.0').state,'update_error')
            opener.open.return_value=self.response(b'<html>SECRET</html>')
            self.assertEqual(check('1.15.0').state,'update_error')
    def test_rate_limits_and_other_http_failures(self):
        opener=Mock()
        for code,headers,state in [(429,{},'update_rate_limit'),(403,{'X-RateLimit-Remaining':'0'},'update_rate_limit'),
                                   (403,{},'update_error'),(404,{},'update_error')]:
            opener.open.side_effect=HTTPError(API,code,'SECRET',headers,BytesIO(b'SECRET'))
            with patch('drive_manager.updates.build_opener',return_value=opener):
                self.assertEqual(check('1.15.0').state,state)
    def test_redirects_are_not_followed(self):
        with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,302,'',{},'https://example.com')
