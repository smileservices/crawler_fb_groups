import re, pickle
from log_setup import log, log_html


class CrucialFBDataNotFound(Exception):
    pass


class NotFoundInCache(Exception):
    pass


class FBProfilesRgistry:
    profiles_cache = 'cache/profiles_register.pkl'  # all profiles are saved here

    def __init__(self):
        try:
            self.profiles = pickle.load(open(self.profiles_cache, 'rb'))
        except FileNotFoundError:
            log('No cache found for fb profiles...')

    def profile_exist(self, uid):
        return True if uid in self.profiles else False

    def add_profile(self, uid, data):
        self.profiles[uid] = data

    def retrieve_profile(self, uid):
        if self.profile_exist(uid):
            return self.profiles[uid]
        else:
            raise NotFoundInCache('Profile does not exist in cache!')

    def save_to_cache(self):
        pickle.dump(self.profiles, open(self.profiles_cache, 'wb'))


class FBProfile:
    '''
    Manages the user's profile data
    '''

    profile_url = "https://www.facebook.com/profile.php?id={}"
    fields_reg_mapping = {
        "name": r'<title id="pageTitle">(.+)</title>',
        "dob": r'Birthday(<.{120,140}>)',  # restrict search to text after birthday (is actually a replace, not a match)
        "gender": r'">(Male|Female)</span>',
        "city_state_country": r'Lives in (<.{100,250}>)',
    }

    def __init__(self, user_id, sess, uid):
        '''
        :param user_id: the logged user id
        :param sess: requests.Session instance
        :param uid: the viewed user id
        '''
        self.profile_sections = {}  # cache already loaded sections
        self.user_id = user_id
        self.uid = uid
        self.sess = sess
        self.profile_page = self.sess.get(
            self.profile_url.format(uid))  # will get redirected to vanity url if that exists
        log('Retrieving profile page at url {}'.format(self.profile_page.url))
        self.vanity_url = self.profile_page.url
        self.secured_url = self.get_secured_url()
        self.about_page = self.get_about_section('overview')

    def get_secured_url(self):
        # extract page search keys
        secure_url_pat = r'{}\?lst={}(.+?)"'.format(self.vanity_url + '/about', self.user_id)
        secured_string = re.search(secure_url_pat, self.profile_page.text)
        if secured_string is None:
            log('Does not have vanity url')
            secure_url_pat = r'{}&amp;lst={}(.+?)"'.format(re.sub(r'([\?])', r'\\\1', self.vanity_url), self.user_id)
            secured_string_old = re.search(secure_url_pat, self.profile_page.text)
            if secured_string_old is None:
                raise CrucialFBDataNotFound('No secure url to about section found on user\'s page')
            # https://www.facebook.com/profile.php?id=100004400105419&amp;lst=100000189256900%3A100004400105419%3A1514026608&amp;sk=about
            return self.vanity_url + '&amp;lst={}{}&amp;sk=about'.format(self.user_id, secured_string_old.group(1))
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
            'id': self.uid,  # temporary
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
        bday_text = re.search(self.fields_reg_mapping['dob'], self.get_about_section('contact-info').text)
        if bday_text is not None:
            return re.sub(r'<[^>]*>', '', bday_text.group(1))
        else:
            return ''

    def get_country_state_city(self):
        location_text = re.search(self.fields_reg_mapping['city_state_country'],
                                  self.get_about_section('overview').text)
        if location_text is not None:
            return re.sub(r'<[^>]*>', '', location_text.group(1))
        else:
            return ''

    def get_gender(self):
        basic_info_page = self.get_about_section('contact-info')
        gender = re.search(self.fields_reg_mapping['gender'], basic_info_page.text)
        return gender.group(1) if gender is not None else ''
