# FB Crawler for closed groups

## What is this meant for
This was started as a toy project for messing around with scavenging data.

It cycles through a json file of users and their closed fb groups and retrieves the members info - id,name,email,age,etc. These are saved into a csv file for each group.
Doing this requires circumventing the fb protection - some hash values that is passed through each page. However, if many requests are executed from the same user, fb halts the connection. This can be overcome by cycling the users and using proxies. Not a biggie, it's on the list.

example of users.json:
[
  {
    "username": "xxxx@gmail.com",
    "password": "yyyyyxxxx",
    "user_id": "55555555555",
    "groups": [
      "111111111","222222222","333333333"
    ]
  }
]

## How does it work:
The crawler logs in with the user credentials and visits the groups page, then it makes subsequent ajax requests for the groups users. After it gathered all users into a file, it goes through each user and visits its profile, goes for the about page and scraps that info. After it's done or it encountered a halting error/exception, it saves the data to a csv file.