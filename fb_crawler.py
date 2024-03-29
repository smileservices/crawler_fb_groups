import requests
from log_setup import log, log_html

from bs4 import BeautifulSoup

from fb_group import FBGroup, RepeatingMembers
from fb_profile import FBProfile, CrucialFBDataNotFound, FBProfilesRgistry

class FBCrawler:
    def __init__(self, user):
        self.user = user
        self.groups = {}
        self.sess = requests.Session()
        self.current_result = ''
        self.login()
        self.results_csv = 'results/members_group_{}.csv'

    def login(self):
        log('Getting to login page...')
        login_url = "https://www.facebook.com/"
        self.current_result = self.sess.get(login_url)

        # we need to parse login form for constructing the post data
        page_soup = BeautifulSoup(self.current_result.text, 'html.parser')
        login_form = page_soup.find_all('form', id='login_form')[0]
        send_login_form_to = login_form["action"]
        post_data = {}
        for input_field in login_form.find_all('input'):
            if input_field.has_attr("name"):
                name = input_field["name"]
                value = input_field["value"] if input_field.has_attr("value") else ''
                post_data[name] = value
        post_data['email'] = self.user['username']
        post_data['pass'] = self.user['password']
        log('Sending login request to {}'.format(send_login_form_to))
        self.current_result = self.sess.post(send_login_form_to, post_data)
        log_html(self.current_result, 'login')

    def refresh_members(self):
        self.get_groups_members()
        self.export_group_members()

    def get_groups_members(self):
        log('Getting group members for user {}'.format(self.user['user_id']))
        for group_id in self.user['groups']:
            self.groups[group_id] = FBGroup(
                group_id=group_id,
                user_id=self.user['user_id'],
                basket_size=15,
                sess=self.sess
            )
            self.groups[group_id].get_members()


    def export_group_members(self):
        '''
        Exports to csv
        :return:
        '''
        import csv

        try:
            #instantiate profiles registry
            fbProfilesRegistry = FBProfilesRgistry()
            for group_id, group_obj in self.groups.items():
                with open(self.results_csv.format(group_id), 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
                    writer.writerow(['UID','Firstname', 'Lastname', 'Gender', 'Date of birth', 'Location'])
                    for member_id in group_obj.members:
                        log('Resolving member id {} ...'.format(member_id))
                        try:
                            if not fbProfilesRegistry.profile_exist(member_id):
                                fbuser = FBProfile(self.user['user_id'], self.sess, member_id)
                                fbProfilesRegistry.add_profile(member_id, fbuser.get_user_data())
                            user_data = fbProfilesRegistry.retrieve_profile(member_id)
                            writer.writerow([
                                user_data['id'],
                                user_data['firstname'],
                                user_data['lastname'],
                                user_data['gender'],
                                user_data['dob'],
                                user_data['country_state_city']
                            ])
                        except CrucialFBDataNotFound as e:
                            log(str(e))
                            continue
            #save fb profile registry to cache
            fbProfilesRegistry.save_to_cache()
        except PermissionError as detail:
            log('PermissionError: {}'.format(detail))
