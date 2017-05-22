# UCL input validation module

# validate the provided username
def user(username):
    # usernames must exist and be 7 characters
    if (len(username) != 7):
        raise ValueError("Invalid username, must be 7 characters: {}".format(username))
# end user
