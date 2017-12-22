import re
from log_setup import log, log_html


class CrucialFBDataNotFound(Exception):
    pass


class FBProfile:
    '''
    Manages the user's profile data
    '''

    profile_url = "https://www.facebook.com/profile.php?id={}/about"
    fields_reg_mapping = {
        "name": r'<title id="pageTitle">(.+)</title>',
        "dob": r'<[^>]*>', #restrict search to text after birthday (is actually a replace, not a match)
        "gender": r'">(Male|Female)</span>',
        "city_state_country": r'Lives in .*>(.+)</a',
    }

    def __init__(self, user_id, sess, uid):
        '''
        :param user_id: the logged user id
        :param sess: requests.Session instance
        :param uid: the viewed user id
        '''
        self.profile_sections = {}  # cache already loaded sections
        self.user_id = user_id
        self.sess = sess
        self.profile_page = self.sess.get(self.profile_url.format(uid))  # will get redirected to vanity url if that exists
        log('Retrieving profile page at url {}'.format(self.profile_page.url))
        self.vanity_url = self.profile_page.url
        self.secured_url = self.get_secured_url()
        self.about_page = self.get_about_section('overview')

    def get_secured_url(self):
        # extract page search keys
        secure_url_pat = r'{}\?lst={}(.+)">About<span'.format(self.vanity_url + '/about', self.user_id)
        secured_string = re.search(secure_url_pat, self.profile_page.text)
        if secured_string is None:
            raise CrucialFBDataNotFound('No secure url to about section found on user\'s page')
        return self.vanity_url + '/about?lst={}{}'.format(self.user_id, secured_string.group(1))

    def get_about_section(self, section):
        if section not in self.profile_sections:
            self.profile_sections[section] = self.sess.get(self.secured_url, params={
                'section': section
            })
            log_html(self.profile_sections[section], section)
        return self.profile_sections[section]

    def get_user_data(self):
        firstname, lastname = self.get_name()
        log('Firstname, Lastname - {}, {}'.format(firstname, lastname))
        dob = self.get_dob()
        log('DOB is {}'.format(dob))
        country_state_city = self.get_country_state_city()
        log('Country state city are {}'.format(country_state_city))
        gender = self.get_gender()
        log('Gender is {}'.format(gender))
        return {
            'id': self.user_id, #temporary
            'firstname': firstname,
            'lastname': lastname,
            'gender': gender,
            'dob': dob,
            'country_state_city': country_state_city,
        }

    def get_name(self):
        full_name = re.search(self.fields_reg_mapping['name'], self.about_page.text).group(1)
        firstname = full_name.split()[len(full_name.split()) - 1]
        lastname = full_name.split()[0]
        return firstname, lastname

    def get_dob(self):
        bday_text = re.search(r'Birthday(<.{120,140}>)', self.get_about_section('contact-info').text)
        if bday_text is not None:
            return re.sub(r'<[^>]*>', '', bday_text.group(1))
        else:
            return ''

    def get_country_state_city(self):
        csc = re.search(self.fields_reg_mapping['city_state_country'], self.get_about_section('overview').text)
        return csc.group(1) if csc is not None else ''

    def get_gender(self):
        basic_info_page = self.get_about_section('contact-info')
        gender = re.search(self.fields_reg_mapping['gender'], basic_info_page.text)
        return gender.group(1) if gender is not None else ''
