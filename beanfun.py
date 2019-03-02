import html
import re
import requests
import time
import uptime

from Crypto.Cipher import DES

class BeanfunClient:
    class Account:
        def __init__(self, acc, sotp, name, decode=True):
            self.acc = acc
            self.sotp = sotp
            self.name = html.unescape(name) if decode else name
            self.secreate_time = None

        def __str__(self):
            return self.acc + ', ' + self.sotp + ', ' + self.name

    def __init__(self, service_code='610074', service_region='T9'):
        self.session = requests.session()
        self.service_code = service_code
        self.service_region = service_region
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
        }

    def get_skey(self):
        result = self.session.get('https://tw.beanfun.com/beanfun_block/bflogin/default.aspx?service_code=999999&service_region=T0', headers=self.headers)
        skey_pattern = r'strSessionKey = "(.*?)"'
        skey = re.findall(skey_pattern, result.text)[0]
        return skey

    def login(self, username, password):
        print('[Info] Logging in ...')
        skey = self.get_skey()
        login_page_url = 'https://tw.newlogin.beanfun.com/login/id-pass_form.aspx?skey=' + skey
        login_page = self.session.get(login_page_url, headers=self.headers)

        viewstate_pattern = r'id="__VIEWSTATE" value="(.*?)"'
        viewstate = re.findall(viewstate_pattern, login_page.text)[0]
        
        eventvalidation_pattern = r'id="__EVENTVALIDATION" value="(.*?)"'
        eventvalidation = re.findall(eventvalidation_pattern, login_page.text)[0]

        viewstateGenerator_pattern = r'id="__VIEWSTATEGENERATOR" value="(.*?)"'
        viewstateGenerator = re.findall(viewstateGenerator_pattern, login_page.text)[0]
        
        samplecaptcha_pattern = r'id="LBD_VCID_c_login_idpass_form_samplecaptcha" value="(.*?)"'
        samplecaptcha = re.findall(samplecaptcha_pattern, login_page.text)[0]

        login_data = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate,
            '__VIEWSTATEGENERATOR': viewstateGenerator,
            '__EVENTVALIDATION': eventvalidation,
            't_AccountID': username,
            't_Password': password,
            'CodeTextBox': '',
            'btn_login': '登入',
            'LBD_VCID_c_login_idpass_form_samplecaptcha': samplecaptcha
        }

        login_result = self.session.post(login_page_url, data=login_data, headers=self.headers)
        akey_pattern = r'AuthKey.value = "(.*?)"'
        akey = re.findall(akey_pattern, login_result.text)[0]
        
        auth_url = 'https://tw.newlogin.beanfun.com/login/final_step.aspx?akey=' + akey
        auth_result = self.session.get(auth_url, headers=self.headers)

        data = {
            'SessionKey': skey,
            'AuthKey': akey
        }
        url = 'https://tw.beanfun.com/beanfun_block/bflogin/return.aspx'
        result = self.session.post(url, headers=self.headers, data=data)

        self.session.get('https://tw.beanfun.com', headers=self.headers)
        self.web_token = self.session.cookies['bfWebToken']

    def get_accounts(self):
        game_zone_url = 'https://tw.beanfun.com/beanfun_block/auth.aspx?channel=game_zone&page_and_query=game_start.aspx%3Fservice_code_and_region%3D{}_{}&web_token={}'
        game_zone_url = game_zone_url.format(self.service_code, self.service_region, self.web_token)
        account_result = self.session.get(game_zone_url, headers=self.headers)
        
        account_pattern = r'div id="(.*?)" sn="(.*?)" name="(.*?)"'
        account_list = re.findall(account_pattern, account_result.text)

        self.accounts = []
        for account in account_list:
            if '+' in account[0]:
                continue
            self.accounts.append(BeanfunClient.Account(*account))
        return self.accounts

    def show_accounts(self):
        print("[Info] Account List:")
        for account in self.accounts:
            print("\t - " + str(account))
        print("")

    def get_account_otp(self, account):
        current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
        game_start_url = 'https://tw.beanfun.com/beanfun_block/game_zone/game_start_step2.aspx?service_code={}&service_region={}&sotp={}&dt={}'
        game_start_url = game_start_url.format(self.service_code, self.service_region, account.sotp, current_time)
        game_start_result = self.session.get(game_start_url, headers=self.headers)

        long_polling_key_pattern = r'GetResultByLongPolling&key=(.*?)"'
        long_polling_key = re.findall(long_polling_key_pattern, game_start_result.text)[0]

        if not account.secreate_time:
            secreate_time_pattern = r'ServiceAccountCreateTime: "(.*?)"'
            account.secreate_time = re.findall(secreate_time_pattern, game_start_result.text)[0]

        secretCode_url = 'https://tw.newlogin.beanfun.com/generic_handlers/get_cookies.ashx'
        secretCode_result = self.session.get(secretCode_url)

        secretCode_pattern = r'var m_strSecretCode = \'(.*)\';'
        secretCode = re.findall(secretCode_pattern, secretCode_result.text)[0]

        otp_data = {
            'service_code': self.service_code,
            'service_region': self.service_region,
            'service_account_id': account.acc,
            'service_sotp': account.sotp,
            'service_display_name': account.name,
            'service_create_time': account.secreate_time
        }
        otp_url = 'https://tw.beanfun.com/beanfun_block/generic_handlers/record_service_start.ashx'
        otp_result = self.session.post(otp_url, data=otp_data)
        otp_url = 'https://tw.beanfun.com/generic_handlers/get_result.ashx?meth=GetResultByLongPolling&key=' + long_polling_key
        otp_result = self.session.get(otp_url)
        otp_url = 'http://tw.beanfun.com/beanfun_block/generic_handlers/get_webstart_otp.ashx?SN={}&WebToken={}&SecretCode={}' \
            + '&ppppp=1F552AEAFF976018F942B13690C990F60ED01510DDF89165F1658CCE7BC21DBA&ServiceCode={}' \
            + '&ServiceRegion={}&ServiceAccount={}&CreateTime={}&d={}'

        otp_url = otp_url.format(long_polling_key, self.web_token, secretCode, self.service_code, self.service_region,
            account.acc,account.secreate_time.replace(' ', '%20'), int(uptime.uptime() * 1000))
        otp_result = self.session.get(otp_url)

        print('[INFO] OTP Result: ' + otp_result.text + '\t' + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        status = otp_result.text[0]
        key = otp_result.text[2: 10]
        text = otp_result.text[10:]
        otp = self.decrypt_des(key, text)
        return otp

    def decrypt_des(self, key, text):
        bytes_key = key.encode('ascii')
        bytes_text = bytes.fromhex(text)
        des = DES.new(bytes_key, DES.MODE_ECB)
        decrypted_text = des.decrypt(bytes_text)[:10].decode()
        return decrypted_text